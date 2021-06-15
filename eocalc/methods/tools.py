# -*- coding: utf-8 -*-
# tools.py
# build by Enrico Dammers (TNO, enrico.dammers@tno.nl)
# last edited <_2020_08_12-03:29:22_AM > too lazy to update this
# %%
#  for testing move to other directory
import os

from pandas.core.base import DataError
os.chdir('../../')


"""Basic toolbox for space emission calculator used in emission calcs."""
from re import sub
from eocalc.methods.fioletov import *
import numpy as np
import pandas as pd
import scipy.special
#import binas as binas
import eocalc.methods.binas as binas
import netCDF4
from datetime import date, timedelta
import glob
import matplotlib.dates as dates
import datetime
import time
# fixed fileformat < batch tropomi obs in monthly 20x15 degree files
interval_lon = 20
interval_lat = 15

# formulas gaussian plumes
# based on (Fioletov et al., 2017; Dammers et al., 2021)
# https://acp.copernicus.org/articles/17/12597/2017/
# any location can be described as VCD(x,y) = sum(flow_contribution_i(x,y) * emis_i) + bias
# for this we need VCD's, added windfields to calculate flow, and potential source locations (grid)
# x,y are in km x km space, not degrees, so rotation and adjustment needed compared to lat lon.
# %%
# winddir/speed back to u,v 
def winddir_speed_to_u_v(wind_spd, wind_dir):
    dir_rp1 = wind_dir * 2 * np.pi / 360.
    dir_rp = np.array(dir_rp1) + np.pi / 2
    u = wind_spd * np.cos(dir_rp)
    v = -wind_spd * np.sin(dir_rp)
    return u, v
        
# wind speed
def calc_wind_speed(u,v):
    return np.sqrt(np.array(u)**2.+np.array(v)**2.)

# winddirection
def calc_wind_direction(u, v):
    # calc wind direction from u,v
    # ensure array form
    u = np.array(u)
    v = np.array(v)
    wind_dir = np.zeros(len(u),float)
    
    sel_lzero = (v >= 0.)
    sel_neg_both = ((u < 0.) & ( v < 0.))
    sel_negv_posu = ((u >= 0.) &( v < 0.))
    
    if len(wind_dir[sel_lzero])>0:
        wind_dir[sel_lzero] = ((180. / np.pi) * np.arctan(u[sel_lzero] / v[sel_lzero]) + 180.)
    if len(wind_dir[sel_neg_both])>0:
        wind_dir[sel_neg_both] = ((180. / np.pi) * np.arctan(u[sel_neg_both] / v[sel_neg_both]) + 0.)
    if len(wind_dir[sel_negv_posu])>0:
        wind_dir[sel_negv_posu] = ((180. / np.pi) * np.arctan(u[sel_negv_posu] / v[sel_negv_posu]) + 360.)

    return wind_dir
    
# rotation
def rotate_plume_around_point(reflon, reflat, lon, lat, wind_direction):
    # rotate lat/lon grid plume in relation to a point
    dtr = np.pi / 180. # conversion degrees to rad
    x_globe = binas.earth_radius * dtr * (lon - reflon) * np.cos(reflat * dtr)
    y_globe = binas.earth_radius * dtr * (lat - reflat)
    cos_wd = np.cos(-wind_direction * dtr)
    sin_wd = np.sin(-wind_direction * dtr)
    x_grid = x_globe * cos_wd + y_globe * sin_wd
    y_grid = -x_globe * sin_wd + y_globe * cos_wd
    return x_grid, y_grid
    
# footprint mapper --> for if we want to oversample individual observations to create more contrast/sharpness


# plumewidth adjustment, shown to fit real life plumes better than basic function.
# plumewidth can also be calculated in more detail using radiation etc (Nassar, et al., 201?, CO2 powerplant paper), not used here
def function_adjust_plumewidth(y, plumewidth):
    if np.size(y) > 1:
        plumewidth_adj = np.full(len(y), plumewidth)
        sel_y = np.where(y <= 0)
        plumewidth_adj[sel_y] = np.sqrt((plumewidth ** 2) - 1.5 * y[sel_y])
    else:
        if y <= 0:
            plumewidth_adj = np.sqrt((plumewidth ** 2) - 1.5 * y)
        else:
            plumewidth_adj = plumewidth
    return plumewidth_adj

# crosswind diffusion
def flow_function_f(x, y, plumewidth):
    val = 1. / (function_adjust_plumewidth(y, plumewidth) * np.sqrt(2. * np.pi))
    val2 = val * np.exp(-(x ** 2.) / (2. * function_adjust_plumewidth(y, plumewidth) ** 2.))
    return val2

# downwind advection / diffusion
def flow_function_g(y, s, plumewidth, decay):
    decay_adj = decay / s
    val = (decay_adj / 2.) * np.exp((decay_adj * (decay_adj * plumewidth ** 2. + 2. * y)) / 2.)
    var1 = (decay_adj * (plumewidth ** 2.) + y) / (np.sqrt(2) * plumewidth)
    val2 = val * scipy.special.erfc(var1)
    return val2

# i.e. flowfun to calculate the factors in arrays etc
# convolution of f/g essentially.
def constant_flowfuntion(x1, x2, s1, decay, plumewidth): 
    fout = flow_function_f(x1, x2, plumewidth) * flow_function_g(x2, s1, plumewidth, decay)
    return fout




# legendre bias function or other

# setup_lin_matrix --> create the matrix for AX=B
def calc_entry_linear_system(datadf,nss,lin_shape_1,source_lon,source_lat,lon_var,lat_var,windspeed_var,winddirec_var,decay,plumewidth):
    flow_rot = np.zeros(lin_shape_1,float)
    x_rot = np.zeros(lin_shape_1,float)
    y_rot = np.zeros(lin_shape_1,float)
    # build in something to limit number of operations
    # for example only obs within a square of the nearest 4 degrees all round?
    # TODO: better lifetime dependent...
    selec = ((np.abs(datadf[lon_var].values - source_lon) < 4.0) & (
            np.abs(datadf[lat_var].values - source_lat) < 4.0))
    # if len(datadf[lon_var].values[selec]) == 0:
        # continue
    rotated = np.array(
        rotate_plume_around_point(source_lon,source_lat, datadf[lon_var].values[selec], datadf[lat_var].values[selec],
                            datadf[winddirec_var].values[selec]))
    # write to rotation x,y matrices
    x_rot[selec] = rotated[0, :]
    y_rot[selec] = rotated[1, :]

    if len(flow_rot[selec]) > 1:  # [selec2]) > 1:
        indexi = np.arange(lin_shape_1)[selec]  # [selec2]
        flow_rot[indexi] = constant_flowfuntion(
            x_rot[indexi], y_rot[indexi], datadf[windspeed_var].values[indexi],
            decay,plumewidth)
    else:
        print('x_rot/y_rot length wrong')
        raise ValueError

    if np.mod(nss,100)==0:
        print('done',nss)
    return nss,flow_rot,x_rot,y_rot

# fitting operator?

def multisource_emission_fit(df_sources, df_obs, lon_var, lat_var, plumewidth, decay, west,east,south,north,
                             minflow=0.0, multiprocessing=False,multiprocessing_workers=16):
    # define arrays
    n_sources =  len(df_sources)
    n_obs =  len(df_obs)
    print('Observations:',n_obs)
    print('Sources:',n_sources)
    x_rotated = np.zeros((n_sources, n_obs))
    y_rotated = np.zeros((n_sources, n_obs))
    wind_obs = df_obs.windspeed.values
    # TODO add options for different bias'
    linear_array = np.zeros((n_obs, n_sources), np.float32)     
    # loop through the observations
    if multiprocessing == True:
        #$ TODO implement multiprocessing
        print('Multi processing not implemented yet')
        raise ValueError
    else:
        for ns in range(n_sources):
            if np.mod(ns, 100) == 0:
                print(ns, 'out of', n_sources)
            line = df_sources.iloc[ns]
            # build in something for nearest 4degrees all round?
            # TODO make it depend on lifetime. Longer lifetime == more obs to include
            selection_near = ((np.abs(df_obs[lon_var].values - line['lon']) < 4.0) & (
                    np.abs(df_obs[lat_var].values - line['lat']) < 4.0))
            if len(df_obs[lon_var].values[selection_near]) == 0:
                continue
            rotated_obs = np.array(
                rotate_plume_around_point(line['lon'], 
                                          line['lat'], 
                                          df_obs[lon_var].values[selection_near], 
                                          df_obs[lat_var].values[selection_near],df_obs['winddirection'].values[selection_near]))
            # TODO maybe return rotated obs?
            x_rotated[ns, selection_near] = rotated_obs[0, :]
            y_rotated[ns, selection_near] = rotated_obs[1, :]
            if len(linear_array[selection_near, ns]) > 1:  # [selection_near2]) > 1:
                indexi = np.arange(n_obs)[selection_near]  # [selection_near2]
                # chose 1 for E and 0. for B to calc without strengths etc
                linear_array[indexi, ns] = constant_flowfuntion(
                    x_rotated[ns, indexi], y_rotated[ns, indexi], wind_obs[indexi],
                    decay, plumewidth)  
                # TODO maybe max flow value to only allow "significant" values
                linear_array[(linear_array[:, ns] < minflow), ns] = 0.0
    return linear_array
    
# multi source helper --> if multisourcing operations
def multi_helper(args):
    return calc_entry_linear_system(*args)

# flatten lists --> little helper to correct obsession with lists
def flatten_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

# create basic emission fields from a inventory for comparison?
def read_subset_data(region: MultiPolygon, filelist: list, add_region_offset = [None,None]):
    # TODO Make this work with regions wrapping around to long < -180 or long > 180?
    if add_region_offset[1] is None:
        min_lat, max_lat = region.bounds[1], region.bounds[3]
    else:
        min_lat, max_lat = region.bounds[1]-add_region_offset[1], region.bounds[3]+add_region_offset[1]
    if add_region_offset[0] is None:
        min_long, max_long = region.bounds[0], region.bounds[2] # or region +- 5degrees
    else:
        min_long, max_long = region.bounds[0]-add_region_offset[0], region.bounds[2]+add_region_offset[1] # or region +- 5degrees

    datap = pd.DataFrame()
    # turn into xarray concate?
    for fil in filelist:
        nc = netCDF4.Dataset(fil)
        print(nc.variables.keys())
        # ensure datap is available even when file empty
        datap_tmp = pd.DataFrame()
        for idx,vari in enumerate(nc.variables.keys()):
            if idx==0:
                datap_tmp = pd.DataFrame(nc[vari][:],columns=[vari])
            else:
                try:
                    datap_tmp[vari] = nc[vari][:]
                except:
                    # 2d and more cases
                    datap_tmp[vari] = [uu for uu in nc[vari][:]]
        # becomes slow, better with xarray
        datap = datap.append(datap_tmp[((datap_tmp[lon_var]>=min_long)&
                                       (datap_tmp[lon_var]<max_long)&
                                       (datap_tmp[lat_var]>=min_lat)&
                                       (datap_tmp[lat_var]<max_lat))])
    return datap


# read data
def assure_data_availability(region,day: date,force_rebuild = False, force_pass = False,satellite_name = 'Tropomi') -> list:
    # check lon_min,lon_max,lat_min,lat_max
    # (5.872058868408317, 47.26990127563522, 15.028479576110897, 55.05652618408209)
    # basic patterns
    lon_min,lon_max = region.bounds[0], region.bounds[2] #lons
    lat_min,lat_max = region.bounds[1], region.bounds[3] #lats
    print('region_bounds',region.bounds)
    # TODO propose to save all files in 20 longitudex15latitude blocks... 
    # removes the need for a lot of redoing files, creates a regularized setup
    # 
    # check if subset is available, if not create
    # find all
    subset_files = glob.glob(LOCAL_DATA_FOLDER + 'subsets/*.nc')
    # select files within period
    subset_files = [fil for fil in subset_files if f'{day:%Y%m}' in fil]
    
    # filter files by latlon   
    subset_files = filter_files_by_latlon(subset_files,[lat_min,lat_max],[lon_min,lon_max])
    # TODO check what number of files is expected:
    lon0 = int(lon_min / 20)
    lon1 = int(lon_max / 20) +1
    lat0 = int(lat_max / 15)
    lat1 = int(lat_max / 15) +1
    files_tot = (lon1-lon0)*(lat1-lat0)
    # expected files
    expected_files = []
    for ilo in range(lon0,lon1):
        for ila in range(lat0,lat1):
            # test
            lonp_0 = ('p%2.2f'%(lon0*interval_lon)).replace('.','_').replace('p-','n')
            lonp_1 = ('p%2.2f'%((lon0+1)*interval_lon)).replace('.','_').replace('p-','n')
            latp_0 = ('p%2.2f'%(lat0*interval_lat)).replace('.','_').replace('p-','n')
            latp_1 = ('p%2.2f'%((lat0+1)*interval_lat)).replace('.','_').replace('p-','n')
            latlonpatter = '%s_%s_%s_%s'%(lonp_0,lonp_1,latp_0,latp_1)
            # pattern should be like p000_0_p020_0_p045_0_p060_0 with p postiive and n negative
            expected_files.append(LOCAL_SUBSET_FOLDER + '%s_coor_%s_date_'%(satellite_name,latlonpatter) + f'{day:%Y%m}.nc')

    # find what missing?
    files_missing = list(set(expected_files) - set(subset_files))

    if force_rebuild is True:
        files_missing = expected_files
    for fil in files_missing:
        [[dminlon, dmaxlon], [dminlat, dmaxlat]] = latlon_fromfile(fil)
        # what does this do? check if its not open in another thread?
        # with threading.Lock():
        status = create_subset(fil,dminlon, dmaxlon,dminlat, dmaxlat,day)
        if status == 0:
            # check that file is there
            if os.path.isfile(fil) is not True:
                print('faulty file check status',fil)
                raise FileNotFoundError

    # TODO pass remaining files? or expected?
    # file_name = '%s/subset/no2_coor_pattern_date_{day:%Y%m}.nc'%(LOCAL_DATA_FOLDER,lon_min_f,lon_max_f,lat_min_f,lat_max_f,resolution[0],resolution[1])
    

    return expected_files

def filter_files_by_latlon(files, lat_range, lon_range):
    '''
    from CDF_tools.py @ CrIS dev package ECCC
    Function that filters through lists of files by lat/lon
    '''
    lat_range = lat_range if lat_range[0] is not None else [-90, 90]
    lon_range = lon_range if lon_range[0] is not None else [-180, 180]

    # Lat and Lon ranges
    minlat, maxlat = lat_range
    minlon, maxlon = lon_range

    # Initialize list
    filtdirs = []

    # Loop over directories
    for directory in files:
        # Get range using function from retv_functions
        [[dminlon, dmaxlon], [dminlat, dmaxlat]] = latlon_fromfile(directory)

        # Check to see if it is OUTSIDE range
        if ((dminlat <= minlat and dmaxlat <= minlat) or
                (dminlon <= minlon and dmaxlon <= minlon) or
                (dminlat >= maxlat and dmaxlat >= maxlat) or
                (dminlon >= maxlon and dmaxlon >= maxlon)):
            # SKIP -- Outside range
            continue
        else:
            # Add to final list
            filtdirs.append(directory)
    # TODO make it smart enough to accept multiple pieces of old files?
    return filtdirs

def latlon_fromfile(directory):
    '''
    from CDF_tools.py @ CrIS dev package ECCC
    Makes a list of the lat range and lon range from parsing directory path
    '''
    import re
    # splitind = -6 if "cdf" in directory[-5:] else -5
    latlon_str = directory.split('coor_')[-1].split('_date_')[0]#re.split("/", directory)[splitind]
    # pattern should be like p000_0_p020_0_p045_0_p060_0 with p postiive and n negative
    # West,east,south,north
    latlon_regex = "[p|n]_*_*_*_*_*_*_*"
    if re.search(latlon_regex, latlon_str):
        empty, minlon, maxlon, minlat, maxlat = re.split(".p|.n|p|n", latlon_str.replace("_", ".").replace("n", "n-"))
        lat_range, lon_range = [[float(minlat), float(maxlat)], [float(minlon), float(maxlon)]]
    else:
        print('faulty pattern',)
        raise ValueError
        # lat_range, lon_range = [[-90, 90], [-180, 180]]
    return lon_range, lat_range

# create subset
def create_subset(filename_out,west, east,south, north,month_date):
    """
    # TODO add nice text
    """
    # TODO add test catch all for input 
    print('Create subset.., step: Reading Datafiles....')
    # TropomiOFFLovp_NO2_None_01_Europe_201805_v.nc
    print('region',west,east,south,north,'%2.4i/%2.2i/'%(month_date.year,month_date.month))
    # weird ass format for directories
    start = datetime.datetime(month_date.year,month_date.month,1)
    month = month_date.month+1
    year = month_date.year
    if month == 13:
        month = 1
        year = month_date.year + 1
    end = datetime.datetime(year,month,1)
    print('search pattern',LOCAL_S5P_FOLDER + '/' +  satellite_name + '/' +  satellite_product + '/' + f'{month_date:%Y/%m}/*/*/*nc')
    # files_to_read = glob.glob(LOCAL_S5P_FOLDER + '/' +  satellite_name + '/' +  satellite_product + '/' + f'{month_date:%Y/%m}/??/S5P*/*nc')
    files_to_read = glob.glob(LOCAL_S5P_FOLDER + '/' +  satellite_name + '/' +  satellite_product + '/' + f'{month_date:%Y/%m}/*/S5P*/*nc')
    if len(files_to_read) == 0:
        print('missing files, check path')
        raise FileNotFoundError
    new_df = pd.DataFrame()
    print('files to read:', len(files_to_read))
    for idx, filename in enumerate(files_to_read):
        print('reading ',idx,'out of',len(files_to_read), filename)
        nc = netCDF4.Dataset(filename)
        # variab = nc.variables.keys()
        # TODO make variable list defined somewhere in main code?
        variab_lib = {lon_var:'PRODUCT/longitude',
                       lat_var:'PRODUCT/latitude',
                    #    'footprint_lon':'PRODUCT/SUPPORT_DATA/GEOLOCATIONS/longitude_bounds',
                    #    'footprint_lat':'PRODUCT/SUPPORT_DATA/GEOLOCATIONS/latitude_bounds',
                       'vcd':'PRODUCT/nitrogendioxide_tropospheric_column',
                       'vcd_err':'PRODUCT/nitrogendioxide_tropospheric_column_precision_kernel',
                       'surface_pressure':'PRODUCT/SUPPORT_DATA/INPUT_DATA/surface_pressure',
                       'quality_value':'PRODUCT/qa_value',
                       'cloud_fraction':'PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/cloud_fraction_crb_nitrogendioxide_window',
                       'time':'PRODUCT/delta_time'}
        
        for key_ind,key in enumerate(variab_lib.keys()):
            print('Reading variable: %s' % key)
            # key_ind = variab.index(key)
            if key_ind == 0:
                dat_read = nc[variab_lib[key]][:]
                dat_shape = dat_read.shape
                # print(key,dat_read.shape)
                if (len(dat_shape) == 3) and (dat_shape[0]==1):
                    datap = pd.DataFrame(dat_read.ravel(), columns=[key])
                elif (len(dat_shape) == 4) and (dat_shape[0]==1):
                    datap = pd.DataFrame(dat_read.ravel(), columns=[key])
                # datap = pd.DataFrame(nc.variables[variab_lib[key]][:], columns=[key])
                else:
                    print('unexpected dimension',dat_shape,key)
                    raise DataError
                
            else:
                if key == 'footprint_lon' or key == 'footprint_lat':
                    dat_read = nc[variab_lib[key]][:]
                    dat_shape = dat_read.shape
                    # print(key,dat_shape)
                    if (len(dat_shape) == 4) and (dat_shape[0]==1):
                        to_pass_df = [uu for uu in dat_read.reshape(dat_shape[0]*dat_shape[1]*dat_shape[2],dat_shape[3])]
                        # print(np.shape(to_pass_df))
                        datap[key] = to_pass_df
                    # datap = pd.DataFrame(nc.variables[variab_lib[key]][:], columns=[key])
                    else:
                        print('unexpected dimension',dat_shape,key)
                        raise DataError
                    # datap[key] = [uu for uu in nc.variables[variab_lib[key]][:].T]
                elif key == 'time':
                    dat_read = nc[variab_lib[key]][:]
                    shape_help = nc[variab_lib[lon_var]].shape[2]
                    dat_shape = dat_read.shape
                    stime = datetime.datetime.strptime(nc[variab_lib[key]].getncattr('units')[19:],'%Y-%m-%d 00:00:00')
                    # print(list(dat_shape) + [shape_help])
                    # stime = datetime.datetime.strptime(nc.variables[variab_lib[key]].getncattr('units')[14:],'%Y-%m-%d 00:00:00')
                    dt = np.rollaxis(np.full([shape_help] + list(dat_shape), nc[variab_lib[key]][:]),0,3).ravel()
                    # dt = nc.variables[variab_lib[key]][:]
                    datap[key] = [stime + timedelta(seconds =float(uu)/1000.) for uu in dt]
                    # print(datap[key].values[0],datap[key].values[-1])
                else:
                    dat_read = nc[variab_lib[key]][:]
                    dat_shape = dat_read.shape
                    # print(key,dat_read.shape)
                    if (len(dat_shape) == 3) and (dat_shape[0]==1):
                        datap[key] = dat_read.ravel()
                    # elif (len(dat_shape) == 4) and (dat_shape[0]==1):
                    #     datap[key] = dat_read.ravel()
                    # datap = pd.DataFrame(nc.variables[variab_lib[key]][:], columns=[key])
                    else:
                        print('unexpected dimension',dat_shape,key)
                        raise DataError
                    # datap[key] = [uu for uu in nc[variab_lib[key]][:]]
                    # datap[key] = [uu for uu in nc.variables[variab_lib[key]][:]]
        # cap to sides of domain
        new_df_tmp = datap[
            ((datap[lon_var] >= west) & (datap[lon_var] < east) & (datap[lat_var] >= south) & (
                    datap[lat_var] < north)&(datap['quality_value']>=0.75)&(datap['cloud_fraction']<=0.3))]
        # ensure observations fall within designated time (UTC)
        new_df_tmp_fin = new_df_tmp[((new_df_tmp.time >= start) & (new_df_tmp.time < end))]
        # append to final array
        if len(new_df_tmp_fin) > 0:
            new_df = new_df.append(new_df_tmp_fin)
            # print(new_df_tmp_fin.shape, filename, 'done', start, end, new_df_tmp_fin['time'].min(), new_df_tmp_fin[
            #     'time'].max(), new_df_tmp_fin['time'].iloc[0])
        # else:
        #     ''
        #     #print(new_df_tmp_fin.shape, filename, 'done')
        # keep last file open to copy paste dimensions and TODO attributes from
        if idx != len(files_to_read) - 1:
            nc.close()
    #endfor filename loop
    print(new_df.shape, filename, 'all files done', new_df['time'].min(), new_df['time'].max())
    if not ('u' in variab_lib.keys() or 'v' in variab_lib.keys()):
        # add meteo
        new_df = add_u_v_data(LOCAL_ERA5_FOLDER, start, end, new_df, lat_var, lon_var)
        print('example u', new_df.u.values[0:10])
        print('example v', new_df.v.values[0:10])
    # create new file
    print('Creating subset....')
    nc_new = netCDF4.Dataset(filename_out, 'w')
    # TODO add attributes
    dimensions_out = {'observations':len(new_df)}
                    #   'corners':4}
                    #   'meteolevels':10}
    for dim in dimensions_out:
        nc_new.createDimension(dim, dimensions_out[dim])
    # for vari in nc.variables:
    for vari in list(new_df.keys()):
        try:
            # TODO add dtypes from frame, pandas doesnt always go well though
            var_tmp = nc_new.createVariable(vari, float, 'observations')
        except:
            print('dimension not yet included',np.array(new_df[vari]).shape)
            raise ValueError
            # adding the new variables, with fixed obs length, drag in from lon_var
            # TODO add attributes
            # var_tmp = nc_new.createVariable(vari, nc.variables[lon_var].dtype, nc[variab_lib[vari]].dimensions)
        if vari != 'time':
            # TODO add attributes
            var_tmp[:] = np.array([uu for uu in new_df[vari]])
        else:
            # TODO add attributes
            var_tmp[:] = dates.date2num(np.array([uu for uu in new_df[vari]]))
        if vari in variab_lib:
            for attri in nc[variab_lib[vari]].ncattrs():
                if ('FillValue' not in attri):
                    # TODO add attributes other variables, cleanup
                    var_tmp.setncattr(attri,nc[variab_lib[vari]].getncattr(attri))
    nc_new.close()
    nc.close()
    status = 0
    return status

def add_u_v_data(era_path, start, end, datas, lat_var_name, lon_var_name):
    """
    # Based on add_meteo @ dev package ECCC
    
    """
    print('Adding ERA5 u,v...')
    ndays = (end - start).days
    date_inter = start
    datas.loc[:, 'u'] = 0.0
    datas.loc[:, 'v'] = 0.0
    datas.loc[:, 'windspeed'] = 0.0
    datas.loc[:, 'winddirection'] = 0.0
    datas.loc[:, 'hh'] = [tt.hour for tt in datas.time]
    datas.loc[:, 'minmin'] = [tt.minute for tt in datas.time]
    datas.loc[:, 'hh_int'] = np.rint(datas['hh']).astype(int)
    # print(datas.iloc[0])
    s_t = time.time()
    for dd in range(ndays):
        print('matching', date_inter)
        # dates def for use
        next_date = date_inter + datetime.timedelta(1)
        date_today = '%2.4i%2.2i%2.2i' % (date_inter.year, date_inter.month, date_inter.day)
        era_file_to_read = era_path + date_today[0:4] + '/' + 'ECMWF_ERA5_uv_%s.nc'%date_today
        if not os.path.isfile(era_file_to_read):
            print('file missing',era_file_to_read)
            print('Download the ERA5 data....then restart')
            raise IOError
        else:
            ncera = netCDF4.Dataset(era_file_to_read)
        # calc longitude latitude positions in grid
        lonstep, latstep = np.round(np.abs(np.diff(ncera['longitude'][:2])), 3)[0], \
                           np.round(np.abs(np.diff(ncera['latitude'][:2])), 3)[0]  # 0.25, 0.25 resolution
        # select all obs for this day 
        sel = ((dates.date2num(datas.time) >= dates.date2num(date_inter)) & (dates.date2num(datas.time) < dates.date2num(next_date)))
        print('adding ERA5', era_path + 'ERA5/nc/' + date_today[
                                                     0:4] + '/' + 'ECMWF_ERA5_uv_' + date_today + '.nc', np.shape(
            np.where(sel)[0]), int(time.time() - s_t), 'seconds_passed')
        if len(datas['time'][sel]) != 0:
            # for now quick interpolation
            # TODO later add surface pressure level dependent meteo
            dataout = interpolate_meteo(datas[lon_var_name][sel].values, datas[lat_var_name][sel].values,
                                          datas['hh'][sel].values + datas['minmin'][sel].values / 60., lonstep, latstep,
                                          ncera)#,ncera_v)
            print('test',dataout.shape)
            dataout.loc[:, 'windspeed'] = np.sqrt(dataout['u'].values ** 2 + dataout['v'].values ** 2)
            dataout.loc[:, 'winddirection'] = calc_wind_direction(dataout['u'].values, dataout['v'].values)
            # print('testje1', np.max(datas['u'].values), np.max(datas['v'].values)
            datas.loc[sel, 'u'] = dataout['u'].values.copy()
            datas.loc[sel, 'v'] = dataout['v'].values.copy()
            # print('testje2',np.max(datas['u'].values),np.max(datas['v'].values)
            datas.loc[sel, 'windspeed'] = dataout['windspeed'].values
            datas.loc[sel, 'winddirection'] = dataout['winddirection'].values
        ncera.close()
        # ncera_v.close()
        
        date_inter += datetime.timedelta(1)
    # quick checkup
    print('here era5', dataout.winddirection.min(), dataout.winddirection.max())
    return datas


def interpolate_meteo(pixlon, pixlat, hh, lon_dx, lat_dx, ancdata):
    '''Interpolate a dataset from regular grid to tropomi center positions
    # TODO add interpolation following footprint shape? 
    # TODO add triangulation algorithm Segers?
    # TODO replace for scipy RGI interpolation?
    # Based on NN_regular_multiday.py @ dev package ECCC
    Args
    ----
    pixlon : numpy.ndarray of float
        Numpy array of floats representing the longitudinal coordinates
    pixlat : numpy.ndarray of float
        Numpy array of floats representing the latitudinal coordinates
    hh : numpy.ndarray of float
        Numpy array of floats representing the hour of the day 0-23
    lon_dx : float
        The regular longitudinal stepsize of the dataset
    lat_dx : float
        The regular latitudinal stepsize of the dataset
    ancdata : netCDF instance
        the dataset to be interpolated to the pixel footprints/centerpoints

    Returns
    -------
    data_uv : pandas dataframe 2,N [u,v]
        The interpolated values of the ancillary data, projected onto the
        given tropOMI dataset.


    '''
    # s_t_t = time.time()
    # ensure float
    pixlon = pixlon.astype(float)
    pixlat = pixlat.astype(float)
    print('pix',pixlon.shape)
    # 0-360 domain argh
    pixlon = pixlon % 360
    lon_m = (pixlon % lon_dx)
    lat_m = (pixlat % lat_dx)

    lon_w = np.where(2 * lon_m <= lon_dx, pixlon, pixlon + lon_dx)
    lat_w = np.where(2 * lat_m <= lat_dx, pixlat, pixlat + lat_dx)

    lon_r = (lon_w - lon_m)  # era is from 0-360, tropomi is from -180 to 180
    lat_r = (lat_w - lat_m)
    
    print('reading u/v')
    # downlaoded in steps of 50hpa.
    #  0:7 is 1000hpa to 700 
    ancdatau_zero = ancdata.variables['u'][:]  
    ancdatav_zero = ancdata.variables['v'][:]  
    print('done reading u/v')
    # get nlat/nlon, domain
    nlat = len(ancdata.variables['latitude'][:])
    nlon = len(ancdata.variables['longitude'][:])
    lon_ind_1 = np.round(lon_r / lon_dx).astype(int)
    lat_ind_1 = np.round(-lat_r / lat_dx + (nlat / 2)).astype(int)
    # get indices.
    lat_ind = np.maximum(np.minimum(lat_ind_1, nlat - 1), 0)
    lon_ind = np.maximum(np.minimum(lon_ind_1, nlon - 1), 0)

    closest = np.round(hh).astype(int)
    closest = np.minimum(np.array(closest), 23)
    closest2 = np.minimum(np.array(closest) + 1, 23)
    # nearest
    # TODO replace for rgi.interpolation?
    closestmin = (hh - closest) * 60
    # TODO We take the lowest 3 layers for now... change to surface pressure based 
    print('interpolating...')
    # data_to_frame = np.array(
    #     [[np.mean(((60 - np.array(closestmin_tmp)) / 60. * ancdatau_zero[closest_tmp, :3, lat_ind_tmp, lon_ind_tmp]) + (
    #             (np.array(closestmin_tmp)) / 60. * ancdatau_zero[closest_tmp2, :3, lat_ind_tmp, lon_ind_tmp])) * 3.6,
    #       np.mean(((60 - np.array(closestmin_tmp)) / 60. * ancdatav_zero[closest_tmp, :3, lat_ind_tmp, lon_ind_tmp]) + (
    #               (np.array(closestmin_tmp)) / 60. * ancdatav_zero[closest_tmp2, :3, lat_ind_tmp, lon_ind_tmp])) * 3.6]
    #      for
    #      closestmin_tmp, closest_tmp, closest_tmp2, lat_ind_tmp, lon_ind_tmp in
    #      zip(closestmin, closest, closest2, lat_ind, lon_ind)])
    data_to_frame = np.array(
        [np.mean(((60 - np.array(closestmin)[:,np.newaxis]) / 60. * ancdatau_zero[closest, :3, lat_ind, lon_ind]) + (
                (np.array(closestmin)[:,np.newaxis]) / 60. * ancdatau_zero[closest2, :3, lat_ind, lon_ind]),1) * 3.6,
          np.mean(((60 - np.array(closestmin)[:,np.newaxis]) / 60. * ancdatav_zero[closest, :3, lat_ind, lon_ind]) + (
                  (np.array(closestmin)[:,np.newaxis]) / 60. * ancdatav_zero[closest2, :3, lat_ind, lon_ind]),1) * 3.6]
         )
    datap = pd.DataFrame(data_to_frame.astype(float).T, columns=['u', 'v'])
    return datap

def chunking_dot(big_matrix, small_matrix, chunk_size=100):
    # quick solve memory error
    # https://stackoverflow.com/questions/27668462/numpy-dot-memoryerror-my-dot-very-slow-but-works-why
    # Make a copy if the array is not already contiguous
    print(big_matrix.shape,small_matrix.shape)
    small_matrix = np.ascontiguousarray(small_matrix)
    print(big_matrix.shape[0], small_matrix.shape[1])
    R = np.empty((big_matrix.shape[0], small_matrix.shape[1]))
    for i in range(0, R.shape[0], chunk_size):
        end = i + chunk_size
        R[i:end] = np.dot(big_matrix[i:end,:], small_matrix)
    return R

if __name__ == "__main__":
    # %%
    # test operations?
    print('test globals',LOCAL_DATA_FOLDER)


# %%
