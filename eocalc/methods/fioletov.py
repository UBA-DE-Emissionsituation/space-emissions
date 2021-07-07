# -*- coding: utf-8 -*-
"""Fioletov functions"""
from datetime import date, timedelta
from re import template
from urllib.request import urlretrieve

import numpy
import pandas as pd
from shapely.geometry import MultiPolygon, shape,Polygon
from geopandas import GeoDataFrame, overlay
from scipy import sparse
import scipy.sparse
import scipy
import scipy.sparse.linalg
import time
import eocalc.methods.binas as binas
from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator, DateRange, Status
import eocalc.methods.tools as tools
# temporary
import matplotlib.pyplot as plt
import scipy.linalg.blas
# from cartopy import config
# import cartopy.crs as ccrs
# from mpl_toolkits.basemap import Basemap


# Local directory we use to store downloaded and decompressed data
# TODO move to more logical place
global LOCAL_DATA_FOLDER
LOCAL_DATA_FOLDER = "/media/uba_emis/space_emissions/enrico/"
# Local directory we use to store downloaded and decompressed data
global LOCAL_ERA5_FOLDER 
LOCAL_ERA5_FOLDER = "/media/uba_emis/space_emissions/enrico/ERA5/"
# Local directory we use to store downloaded and decompressed data
global LOCAL_S5P_FOLDER 
LOCAL_S5P_FOLDER = "/codede/Sentinel-5P/"
# Local directory we use to store subsets
global LOCAL_SUBSET_FOLDER 
LOCAL_SUBSET_FOLDER = "/media/uba_emis/space_emissions/enrico/subsets/"
# Satellite Name
global satellite_name 
satellite_name = "TROPOMI"
# TODO replace as choice, for now fixed
global satellite_product
satellite_product = "L2__NO2___"
global lon_var
lon_var = 'Longitude'
global lat_var
lat_var = 'Latitude'
global vcd_var
vcd_var = 'vcd'
# Online resource used to download TEMIS data on demand
# TODO! implement download tool from Janot
# Scitools.sh/python version
global resolution_lat
global resolution_lon
resolution_lon, resolution_lat = 0.2,0.2
class MultiSourceCalculator(EOEmissionCalculator):

    @staticmethod
    def minimum_area_size() -> int:
        return 10**4

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -60.], [180., -60.], [180., 60.], [-180., 60.], [-180., -60.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 1

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat('2019-06-01') # hardcapped for initial tests

    @staticmethod
    def latest_end_date() -> date:
        return date.fromisoformat('2019-07-01') # hardcapped for initial tests
        #return (date.today().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant == Pollutant.NO2


    # TODO add plumewidth and decay to parameter pollutant/satellite instrument
    def run(self, region= MultiPolygon, period= DateRange, pollutant= Pollutant, plumewidth = 7, decay = 1/3.,  resolution=(resolution_lon,resolution_lat),add_region_offset=[None,None]) -> dict:
        self._validate(region, period, pollutant)
        self._state = Status.RUNNING
        self._progress = 0  # TODO Update progress below!
        s_t_0 = time.time()
        # 1. Create a field of sources
        # TODO allow for domain of higher resolution within a coarser set. For example germany at 0.1 with surroundings at 0.2
        # grid = self._create_grid(region, resolution[0], resolution[1], snap=True, include_center_cols=True)
        # TODO if memory becomes an issue... maybe divide in even smaller areas? or zoom in after fits broader region?
        min_lat, max_lat = region.bounds[1], region.bounds[3]
        min_long, max_long = region.bounds[0], region.bounds[2] # or region +- 5degree
        if add_region_offset[1] is None:
            min_lat, max_lat = region.bounds[1], region.bounds[3]
        else:
            min_lat, max_lat = region.bounds[1]-add_region_offset[1], region.bounds[3]+add_region_offset[1]
        if add_region_offset[0] is None:
            min_long, max_long = region.bounds[0], region.bounds[2] # or region +- 5degrees
        else:
            min_long, max_long = region.bounds[0]-add_region_offset[0], region.bounds[2]+add_region_offset[1] # or region +- 5degrees
        lons = numpy.arange(min_long,max_long,resolution_lon)
        lats = numpy.arange(min_lat,max_lat,resolution_lat)
        meshed = numpy.meshgrid(lons,lats)
        #!TODO switch to Grid module, check if we can share
        grid_lon = meshed[0]
        grid_lat = meshed[1]
        wgrid,egrid=grid_lon.ravel()-resolution_lon*0.5,grid_lon.ravel()+resolution_lon*0.5
        sgrid,ngrid=grid_lat.ravel()-resolution_lat*0.5,grid_lat.ravel()+resolution_lat*0.5
        grid_polygons = [Polygon(zip([w1,e1,e1,w1,w1],[s1,s1,n1,n1,s1])) for w1,e1,s1,n1 in zip(wgrid,egrid,sgrid,ngrid)]
        gp_sources = GeoDataFrame(geometry=grid_polygons)
        # geopandas frame?

        # TODO add original emissions for analysis?
        source_df = pd.DataFrame(numpy.array([grid_lon.ravel(),grid_lat.ravel()]).T,columns=['lon','lat'])
        # 2. Read TROPOMI data into the grid, use cache to avoid re-reading the file for each day individually
        cache = []
        df_obs = pd.DataFrame()
        for day in period:
            month_cache_key = f"{day:%Y-%m}"
            if month_cache_key not in cache:
                df_mon_obs = tools.read_subset_data(region, tools.assure_data_availability(region,day),add_region_offset=add_region_offset)#period))
                cache.append(month_cache_key)
                df_obs = df_obs.append(df_mon_obs)
        # 3. Perform operations multi-source
        # 3.1 create matrix
        linear_system_A = tools.multisource_emission_fit(source_df, df_obs, lon_var, lat_var, plumewidth, decay, min_long, max_long,min_lat,max_lat)

        # 3.2 Create B, subtract bias
        # to find bias, we grid all obs and take the lowest 5% of each cell
        # TODO add higher resolution gridding. Arjos triangle?
        df_obs['iy'] = (numpy.floor((df_obs[lat_var]-min_lat)/resolution_lat)).values.astype(int)
        print('done,  iy')
        df_obs['ix'] = (numpy.floor((df_obs[lon_var]-min_long)/resolution_lon)).values.astype(int)
        print('done,  ix')
        df_obs['iy_ix']=['%i_%i'%(int(numpy.floor((la-min_lat)/resolution_lat)),int(numpy.floor((lo-min_long)/resolution_lon))) for la,lo in zip(df_obs[lat_var],df_obs[lon_var])]   
        print('done,  iy_ix')                                      
        vcd_mean = df_obs.groupby('iy_ix').mean() 
        bias_grouped = df_obs.groupby('iy_ix')[[vcd_var,lat_var,lon_var]].quantile(.05) 
        # maybe count for later?
        dfg2c = df_obs.groupby('iy_ix').count() 
        bias_grid = numpy.zeros((len(lats),len(lons)),float)
        bias_grid[:]= numpy.nan
        for idx in range(len(vcd_mean.index.values)):
            bias_grid[int(vcd_mean['iy'][idx]),int(vcd_mean['ix'][idx])] = bias_grouped[vcd_var][idx]
        bias_per_obs = bias_grid[df_obs['iy'],df_obs['ix']]
        linear_system_B = df_obs.copy()
        linear_system_B[vcd_var] = linear_system_B[vcd_var] - bias_per_obs
        print('shapetest',linear_system_A.shape,linear_system_B.shape)
        # 
        # Damped least squares  --    solve  (   A    )*x = ( b )
                                    # ( damp*I )     ( 0 )
        dampening_factor = 0.007 # test value depends on size domain and number of obs
        # assume matrix is pretty sparse
        print('Turn into sparse system for calculation speed')
        s_t = time.time()
        sA = sparse.csr_matrix(linear_system_A) 
        print('Turning into sparse array took' '%3.3i:%2.2i' % ( int((time.time() - s_t) / 60), int(numpy.mod((time.time() - s_t), 60))), 'Min:Sec') 
        # TODO add loop for multiple fits with different settings
        s_t = time.time()
        print('finding solution...',decay,plumewidth)
        solution = scipy.sparse.linalg.lsqr(sA, linear_system_B[vcd_var].values,damp=dampening_factor)
        print('Fit took' '%3.3i:%2.2i' % ( int((time.time() - s_t) / 60), int(numpy.mod((time.time() - s_t), 60))), 'Min:Sec')                
        print('Found solution',decay,plumewidth)

        # test quickplot
        # conversion  mol  * m-2 * km2 -> kg/yr =* 1/hr * m2/km2 * kg / mol  * days/year * hours/day =  (kg*m2)/(km2*yr*mol)
        source_conversion = (decay * 1e6) * (binas.xm_NO2) * 365. * 24.
        print('solution max',numpy.max(solution[0].reshape(grid_lon.shape) * source_conversion))
        print('solution min',numpy.min(solution[0].reshape(grid_lon.shape) * source_conversion))
        # 1e-6 for kt
        emissions = source_conversion * solution[0]
        gp_sources['fitted_emissions'] = emissions*1e-6
        gp_sources.plot('fitted_emissions',vmin=0,vmax=3,legend=True)
        plt.ion()
        plt.show()
        # calculate reconstruction
        # print('Loop took' '%3.3i:%2.2i' % ( int((time.time() - s_t_0) / 60), int(numpy.mod((time.time() - s_t_0), 60))), 'Min:Sec')                
        # s_t_3 = time.time()
        # reconstructed_obs = tools.chunking_dot(linear_system_A,numpy.array(solution[0])[:,numpy.newaxis]) + bias_per_obs
        # print('Chunking took' '%3.3i:%2.2i' % ( int((time.time() - s_t_3) / 60), int(numpy.mod((time.time() - s_t_3), 60))), 'Min:Sec')                
        # s_t_3 = time.time()
        # reconstructed_obs = scipy.linalg.blas.dgemm(alpha=1.0, a=sA, b=numpy.array(solution[0])[:], trans_b=True) + bias_per_obs
        # print('SPBLAS took' '%3.3i:%2.2i' % ( int((time.time() - s_t_3) / 60), int(numpy.mod((time.time() - s_t_3), 60))), 'Min:Sec')                
        # s_t_3 = time.time()
        # reconstructed_obs = scipy.linalg.blas.dgemm(alpha=1.0, a=sA.T, b=numpy.array(solution[0])[:,numpy.newaxis].T, trans_b=True) + bias_per_obs
        # print('SPBLAS.T took' '%3.3i:%2.2i' % ( int((time.time() - s_t_3) / 60), int(numpy.mod((time.time() - s_t_3), 60))), 'Min:Sec')                
        # reconstructed_obs = numpy.dot(sA,solution[0]) + bias_per_obs
        # add bias back?
        tmp_return = {}
        tmp_return['solution'] = solution
        tmp_return['emissions'] = emissions
        tmp_return['gpd'] = gp_sources
        # tmp_return['reconstructed_obs'] = reconstructed_obs
        # tmp_return['df_obs'] = df_obs
        print('Loop took' '%3.3i:%2.2i' % ( int((time.time() - s_t_0) / 60), int(numpy.mod((time.time() - s_t_0), 60))), 'Min:Sec')                

        # 3. Clip to actual region and add a data frame column with each cell's size
        # grid = overlay(grid, GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')
        # grid.insert(0, "Area [km²]", grid.to_crs(epsg=8857).area / 10 ** 6)  # Equal earth projection
        
        # # 4. Update emission columns by multiplying with the area value and sum it all up
        # grid.iloc[:, -(len(period)+3):-3] = grid.iloc[:, -(len(period)+3):-3].mul(grid["Area [km²]"], axis=0)
        # grid.insert(1, f"Total {pollutant.name} emissions [kg]", grid.iloc[:, -(len(period)+3):-3].sum(axis=1))
        # grid.insert(2, "Umin [%]", numpy.NaN)
        # grid.insert(3, "Umax [%]", numpy.NaN)
        # grid.insert(4, "Number of values [1]", len(period))
        # grid.insert(5, "Missing values [1]", grid.iloc[:, -(len(period)+3):-3].isna().sum(axis=1))
        # self._calculate_row_uncertainties(grid, period)  # Replace NaNs in Umin/Umax cols with actual values

        # # 5. Add GNFR table incl. uncertainties
        # table = self._create_gnfr_table(pollutant)
        # total_uncertainty = self._combine_uncertainties(grid.iloc[:, 1], grid.iloc[:, 2])
        # table.iloc[-1] = [grid.iloc[:, 1].sum() / 10**6, total_uncertainty, total_uncertainty]

        # self._state = Status.READY
        return tmp_return #{self.TOTAL_EMISSIONS_KEY: table, self.GRIDDED_EMISSIONS_KEY: grid}


    # operations for class / or functions to fit emissions using fioletov approach

    #__some__basic__operation__


    #__get_all_plume_functions_


    #add_bias


    #fit_for_domain


    #errors_uncertainties_estimator


    #posteriori_adjustments