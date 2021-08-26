# -*- coding: utf-8 -*-
# this toolbox contains functions for downloading data required for space based emission estimation
import os
import inspect
from typing import List, Tuple
import json

import datetime
import sentinelsat
from cdsapi import Client as cdsClient
from shapely.geometry import Polygon
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange

def _input_check_period(period:DateRange):  
    """ 
    Function to check if the provided period for the downloadtool is daterange/datetime object or a YYY-MM-DD string.
    """
    if isinstance(period, str):
        try:
            datetime.datetime.strptime(str(period), "%Y-%m-%d")
        except ValueError:
            raise ValueError("incorrect format for datestring, should be YYYY-MM-DD")
    else: 
        try:   
            for day in period:
                datetime.datetime.strptime(str(day), "%Y-%m-%d")
        except TypeError:
            raise TypeError("wrong input, should be daterange/datetime object or string")
    return 

def _input_check_path(data_dir) -> bool: 
    """ 
    Function to check if the provided path for the downloadtool is correct
    """
    status = False
    # if data_dir is not provided we make one in the data directory, called downloadYYYYMM
    if data_dir is None:
        dir_1up = os.path.dirname(os.path.abspath(inspect.getfile(_input_check_path)))
        data_dir = os.path.join(dir_1up,"data", "download%s"%datetime.datetime.today().strftime("%Y%m"))
    try:                   
        # make the folder if it is not there
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            status = True
        else:
            status = True
    except TypeError:
        raise TypeError( "please provide a valid path, not %s" % data_dir)
    return status

def _input_check_era_lvl(levels)->List: 
    """ 
    Function to check if the provided levels for which ERA5 data is downloaded are correct.
    """
    if levels is not None:
        # levels are given
        numericflag = False
        if isinstance(levels,float) or isinstance(levels,int):numericflag = True
                   
        stringflag = False
        if isinstance(levels,str):
            stringflag = True
            try: 
                float(levels)
            except:
                raise TypeError("wrong input: %s" % levels)

        # if a single level was given it should be within the vertical coverage, i.e. between 1000 to 1hPa  
        if numericflag == True or stringflag == True or len(levels) == 1:  
            #change 1x1 list into string or numeric
            if isinstance(levels,list):levels =levels[0]
            
            try:
                if 1 <= float(levels) <= 1000:  # correct
                    levels = [str(float(levels))]
                else:
                    # outside bounds of ERA data
                    raise ValueError("pressure level outside range [1-1000] hPa: %s" %levels)
            except TypeError:
                raise TypeError("wrong input: %s" % levels)

        elif isinstance(levels, list):  # an array/list of levels is given
            # convert to correct array of strings in case floats or ints are given
            try:
                levels = [str(float(lvl)) for lvl in levels]
            except TypeError:
                raise TypeError("wrong input: %s" %levels)
            except ValueError:
                raise ValueError("wrong input: %s" %levels)
            #check if no level is too high or low
            for lvl in levels: 
                if not (1 <= float(lvl) <= 1000):raise ValueError("pressure level outside range [1-1000] hPa: %s" %levels)

        elif len(levels.shape()) > 2:
            # wrong format
            raise TypeError("please provide a valid array of levels, not %s" %levels)
    else:  # levels is None or not provided -> choose defaults
        levels = ["1000.0", "950.0"]
    return levels

def _input_check_times(times)->List: 
    """ 
    Function to check if the provided times for which ERA5 data is downloaded are correct
    """
    if times is not None:
        if isinstance(times, str):
            try:
                time = datetime.datetime.strptime(str(times), "%H:%M")
                times = [time]
            except ValueError:
                raise ValueError("%s is the incorrect date string format. It should be YYYY-MM-DD"%times)
        else: 
            #loop of the time instances and check if they have the correct form
            for time in times:
                try:
                    datetime.datetime.strptime(time, "%H:%M")
                except ValueError:
                    raise ValueError("%s is the incorrect list of date strings. They should be YYYY-MM-DD"%time)
            pass
    else:
        #nothing was provided so we use the default time
        times = ["12:00"]
    return times

def _input_check_resolution(res)->bool: 
    """ 
    Function to check if the provided resolution for which ERA5 data is downloaded is correct
    """
    status = False
    if res is None:
        #set grid to default value
        res =[0.25, 0.25]
        status = True
    else:
        # a (potentially) non-default) grid is provided. Default grids for ERA5 online CDS are 0.25°x0.25° (atmosphere) and
        # 0.5°x0.5° (ocean waves)
        if len(res) == 1:  # longitude resolution is equal to latitude resolution
            res = [float(res), float(res)]
            status = True
        elif len(res) == 2:  # resolution [dlon, dlat] is given.
            # convert to float if necessary
            res = [float(i) for i in res]
            status = True
        elif len(res) < 2:
            # wrong format
            raise TypeError("please provide a valid resolution, not %s\n" % res)
    return status

def _setup_for_s5pdownload(species_name="no2", satellite = "s5p", producttype = "L2", user="s5pguest", password="s5pguest")->Tuple[SentinelAPI, str, list]:
    """ 
    Function to check if satellite product provided to the downloadtools is correct/available and setup the api connection for the download
    """
    # initialize
    producttype_opts = []
    api = []
    platformname = ""

    # select sentinel satellite and products. Setup API accordingly:
    if satellite == "s5p":  # TROPOMI
        platformname = "Sentinel-5 Precursor"

        producttype_opts = ["L1B_IR_SIR", "L1B_IR_UVN", "L1B_RA_BD1", "L1B_RA_BD2", "L1B_RA_BD3", "L1B_RA_BD4",
                            "L1B_RA_BD5", "L1B_RA_BD6", "L1B_RA_BD7", "L1B_RA_BD8", "L2__AER_AI", "L2__AER_LH",
                            "L2__CO____", "L2__HCHO__", "L2__CH4", "L2__CLOUD_", "L2__NO2___", "L2__NP_BD3",
                            "L2__NP_BD6", "L2__NP_BD7", "L2__O3_TCL", "L2__O3____", "L2__SO2___"]
        # try to connect for 100 seconds then timeout
        api = SentinelAPI(user, password, "https://s5phub.copernicus.eu/dhus/", show_progressbars=False,timeout=100)
        print( "Satellite set to  %s" % satellite)
    else: 
        #later "user" and "password" can be used to download other satellite data, e.g. sentinel-2 data
        return ValueError("satellite %s not recognized. Please select from [s5p]" % satellite)

    # select product based on product type
    corr_producttype = [pt for pt in producttype_opts if producttype in pt]
    if len(corr_producttype) == 0:
        return ValueError("product type should be in %s. Not %s" % (producttype_opts, producttype))

    # select product based on species
    corr_speciesproduct = [pt for pt in corr_producttype if species_name.upper() in pt]
    if len(corr_speciesproduct) == 0:
        return ValueError("species type should be one of [no2,o3,so2,co,cloud,ch4,aer,hcho,np,ir,ra]. Not %s"%species_name)
    products = corr_speciesproduct
    return api, platformname, products

def _geojson_to_footprint(geojson_path)->str:
    """ 
    Function to check if path to geojson file provided to the downloadtools is correct and create a footprint as wkt from it
    """
    # initialize. Will contain wkt (Well-Known Text) string to represent the area of interest
    footprint = ""
    if geojson_path is None:
        # bounding box for germany:
        polygon = Polygon([(1.00, 46.00), (15.00, 46.00), (15.00, 55.00), (1.00, 55.00), (1.00, 46.00)])
        footprint = Polygon.to_wkt(polygon)
    else:
        try:
            footprint = geojson_to_wkt(read_geojson(geojson_path))
        except TypeError:
            return TypeError(str(geojson_path) + "is not a path to a valid geojson polygon")
    return footprint

def _s5p_file_rename(data_dir):
    """ 
    Renaming file extensions of TROPOMI downloads (TROPOMI files are downloaded as zips but are actually netCDF files). Only changing the extension is
    required.
    """
    for filename in os.listdir(data_dir):
        if filename[-4:] == ".zip" and filename[:3] == "S5P":
            os.rename(os.path.join(data_dir, filename), os.path.join(data_dir, filename[:-4] + ".nc"))
    return

def satellite_download(
    period, data_dir, geojson_path, satellite="s5p", species=Pollutant.NO2, producttype="L2__NO2___",user="s5pguest",password= "s5pguest", replace=False):
    """ 
    Function for downloading satellite data using the sentinelsat API. By default, the L2 NO2 OFFL data  products is
    downloaded. Currently only downloads of TROPOMI data are implemented

    inputs:
       period      - daterange object specifying the download period \n   
       data_dir    - directory where the data will get stored \n
       species     - pollutant for which the satellite data is downloaded  \n
       producttype - string that specifies the level of the tropomi data that is to be downloaded, i.e. L1B, L2 etc \n
       geojson_path- path to a geojson file that contains the region for which data should be downloaded \n
       satellite   - will in the future allow extensions to other satellites, for now it should be set to s5p \n
       user        - username at the copernicus data hub \n
       password    - corresponding password at copernicus data hub \n
       replace     - boolean, replace previously downloaded data, yes or no? True means data will be replaced \n
    
    outputs:
       no function output. Data will be downloaded in specified data dir

    """
    # check if the provided period and data_dir are correct:
    _input_check_period(period)
    _input_check_path(data_dir)    
    
    #make the footprint
    footprint = _geojson_to_footprint(geojson_path)

    #make API connection
    if satellite =="s5p":
        api, platformname, products = _setup_for_s5pdownload(species.name,satellite,producttype,user,password)
        ver = "REPRO"  # or "NRTI or OFFL"
    else:
        raise ValueError("satellite %s not implemented"%satellite)

    # query products for one day
    for day in period:
        # make the year subdir if it is not there.
        if not os.path.exists("{dir}/{d:%Y}/".format(dir=data_dir, d=day)):
            os.makedirs("{dir}/{d:%Y}/".format(dir=data_dir, d=day))

        print("searching products at: " + day.strftime("%m/%d/%Y") + "...")
        print("               within: " + footprint + ".")

        s5p_products = api.query(footprint,
                             date=(day, day + datetime.timedelta(days=1)),
                             platformname=platformname, producttype=products[0]
                             )

        message = f"{len(s5p_products)} products found \n product IDs are:\n"

        for s5p_product in s5p_products:
            message += "  %s\n" % s5p_product
            info = api.get_product_odata(s5p_product)

            # check version
            if info["title"].split("_")[1] in ver:

                message  += "product title:           %s" % info["title"]
                message  += "product md5:             %s" % info["md5"]
                print(message)

                # TODO: check if product is there already (mostly it will be for hyperspec) and only download it if
                #  it is not
                if replace:
                    print(" the tropomi files will be downloaded again")

                # individual product download:
                try:
                    api.download(info["id"], directory_path=data_dir, checksum=True)
                    print("sucesfully downloaded:   %s\n" % info["title"])
                except sentinelsat.InvalidChecksumError:
                    # throw checksum error when encountered but continue
                    print("checksum error for %s\n" % info["title"])
                    continue
    #rename tropomi files only
    _s5p_file_rename(data_dir)
    return

def era5_download(
        period, data_dir, res, levels, times, region="global",apikey = "[PLACEHOLDER:https://cds.climate.copernicus.eu/api/v2 apikey]",
                  replace=False):
    """ 
    Function for downloading wind data using the CDSapi. By default, global ERA5 uv wind products are downloaded
    from ECMWF and stored.

     inputs:
       period   - daterange object specifying the download period
       data_dir - directory where the data needs to get stored
       res      - resolution of the data in ° [lat, lon] or ° as homogenous
       levels   - string or array of strings with pressure levels in hPa, default is 1000 and 950
       times    - times of the data as array of strings ["hh:mm","hh:mm"], default is "12:00"
       region   - [North, West, South, East], e.g.  [5, 47, 16, 55] for Germany. Default: global.
       TODO: region should also accept shapes
       replace  - boolean, replace previously downloaded data, yes or no? True means data will be replaced
    """
    # check if the provided period and data_dir are correct:
    _input_check_period(period)
    _input_check_path(data_dir) 
    _input_check_resolution(res) 
    levels = _input_check_era_lvl(levels)
    times = _input_check_times(times)

    # check if cds cdsapirc file exist with uid and API key. If it does not exist make the file.
    home_dir = os.path.expanduser("~")
    cdsapirc_file = os.path.join(home_dir, ".cdsapirc")
    if not os.path.isfile(cdsapirc_file):
        f = open(cdsapirc_file, "w")
        f.write("url: https://cds.climate.copernicus.eu/api/v2\n")
        f.write(apikey)
        f.close()

    # make contact
    server = cdsClient()

    # download per day:
    for day in period:
        # make the year subdir if it is not there.
        if not os.path.exists("{dir}/{d:%Y}/".format(dir=data_dir, d=day)):
            os.makedirs("{dir}/{d:%Y}/".format(dir=data_dir, d=day))

        filename = "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day)

        print("checking..." + filename)
        # download only if the file was not downloaded before or replace it if requested:
        if (replace is False and not os.path.exists(filename)) or (replace):
            print("attempt to collect..." + filename)
            try:
                server.retrieve(
                    "reanalysis-era5-pressure-levels",
                    {
                        "product_type": "reanalysis",
                        "format": "netcdf",
                        "variable": ["u_component_of_wind", "v_component_of_wind"],
                        "pressure_level": levels,
                        "year": day.strftime("%Y"),
                        "month": day.strftime("%m"),
                        "day": day.strftime("%d"),
                        "time": times,
                        "grid": res
                    },
                    "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day))
            except Exception as ex:
                print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                raise ex 
        else:
            # file was downloaded before and no replacement is requested:
            print(filename + " exists and \"replace\" is set to \"%s\"" % replace)
            print("data %s is already there. Skipped the download\n" % filename)

    print("done with ERA5 download")
    return
