# -*- coding: utf-8 -*-
# Script:     downloadtools.py
# Author(s):  Enrico Dammers / Janot Tokaya
# Last Edit:  2021-03-11
# Contact:    enrico.dammers@tno.nl, janot.tokaya@tno.nl

# INFO: this toolbox contains functions for gathering data required for space based emission estimation

# %%
# importing modules and tools
import os
import os.path

import datetime
import logging

import sentinelsat
from cdsapi import Client as cdsClient
from geojson import Polygon
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

from eocalc.context import Pollutant


# %% Download functions
def tropomi_download(period=None, data_dir=None,
                     species=Pollutant.NO2, producttype='L2__NO2___', geojson_path=None, satellite='s5p',
                     user='[PLACEHOLDER:https://scihub.copernicus.eu/dhus UN]',
                     password='[PLACEHOLDER:https://scihub.copernicus.eu/dhus PW]', replace=False, makelog=True):
    """" Function for downloading TROPOMI data using the sentinelsat API. By default, the L2 NO2 OFFL data  products is
    downloaded """

    # inputs:
    #   period      - daterange object specifying the download period    
    #   data_dir    - directory where the data needs to get stored
    #   species     - pollutant for which the tropomi data is downloaded 
    #   producttype - string that specifies the level of the tropomi data that is to be downloaded, i.e. L1B, L2 etc
    #   geojson_path- path to a geojson file that contains the region for which data should be downloaded
    #   satellite   - will in the future allow extensions to other satellites, for now it should be set to s5p
    #   user        - username at the copernicus data hub
    #   user        - corresponding password at copernicus data hub
    #   replace     - boolean, replace previously downloaded data, yes or no? True means data will be replaced
    #   makelog     - boolean, make a log file yes or no? 

    # -------------------------------------------------------------------------
    # configure logging
    # -------------------------------------------------------------------------

    if makelog:
        logfilename = "tropomi_download_%s.log" % datetime.datetime.today().strftime("%Y%m%d")

        if data_dir is None:
            if not os.path.exists(os.path.join(os.getcwd(), 'log')):
                os.makedirs(os.path.join(os.getcwd(), 'log'))
            logfile = os.path.join(os.getcwd(), 'log', logfilename)
        else:
            if not os.path.exists(os.path.join(data_dir, 'log')):
                os.makedirs(os.path.join(data_dir, 'log'))
            logfile = os.path.join(data_dir, 'log', logfilename)

        # if the log file exists we make it empty
        if os.path.isfile(logfile):
            file = open(logfile, "r+")
            file.truncate(0)

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(filename=logfile, encoding="utf-8", filemode='w', level=logging.DEBUG)

    # -------------------------------------------------------------------------
    # check if the provided inputs are correct:
    # -------------------------------------------------------------------------

    # period:
    # should be provided and should be DateRange instance
    if period is None or len(period) == 0:
        message = "Period is empty.\n"
        logging.error(message)

    # check species and product selection
    # initialize
    producttype_opts = []
    api = []
    platformname = []
    ver = []

    # select sentinel satellite and products. Setup API accordingly:
    if satellite == 's5p':  # TROPOMI
        platformname = 'Sentinel-5 Precursor'

        producttype_opts = ['L1B_IR_SIR', 'L1B_IR_UVN', 'L1B_RA_BD1', 'L1B_RA_BD2', 'L1B_RA_BD3', 'L1B_RA_BD4',
                            'L1B_RA_BD5', 'L1B_RA_BD6', 'L1B_RA_BD7', 'L1B_RA_BD8', 'L2__AER_AI', 'L2__AER_LH',
                            'L2__CO____', 'L2__HCHO__', 'L2__CH4', 'L2__CLOUD_', 'L2__NO2___', 'L2__NP_BD3',
                            'L2__NP_BD6', 'L2__NP_BD7', 'L2__O3_TCL', 'L2__O3____', 'L2__SO2___']
        #  set up sentinel 5p api
        s5p_user = 's5pguest'
        s5p_password = 's5pguest'
        api = SentinelAPI(s5p_user, s5p_password, 'https://s5phub.copernicus.eu/dhus/', show_progressbars=False)
        message = "Satellite set to  %s\n" % satellite
        logging.info(message)
        ver = 'OFFL'  # or "NRTI or REPRO"

    else:  # error
        message = 'satellite %s not recognized. Please select from [s5p]' % satellite
        print(message)
        logging.error(message)

    # select product based on product type
    corr_producttype = [pt for pt in producttype_opts if producttype in pt]
    if len(corr_producttype) == 0:
        logging.error("product type should be in %s. Not %s" % (producttype_opts, producttype))

    # select product based on species
    corr_speciesproduct = [pt for pt in corr_producttype if species.name.upper() in pt]
    if len(corr_speciesproduct) == 0:
        logging.error(f"species type should be one of [no2,o3,so2,co,cloud,ch4,aer,hcho,np,ir,ra]. Not {species.name}")

    # path:
    # if data_dir is not provided we make one in the current directory
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), 'sentinel', satellite)
        logging.warning("No path was provided: data will be stored in %s" % data_dir)

    # try to make the folder
    if not os.path.exists(data_dir):
        # try to make the path
        try:
            message = "making a new directory to store data: %s\n" % data_dir
            print(message)
            logging.info(message)
            os.makedirs(data_dir)
        # data_dir is not a valid path
        except ValueError:
            message = "please provide a valid path, not %s\n" % data_dir
            print(message)
            logging.error(message)
            return ValueError("wrong input: %s" % data_dir)

    # -------------------------------------------------------------------------
    # collect products per day
    # -------------------------------------------------------------------------
    # initialize
    footprint = []
    if geojson_path is None:
        # bounding box for germany:
        polygon = Polygon([[(1.00, 46.00), (15.00, 46.00), (15.00, 55.00), (1.00, 55.00), (1.00, 46.00)]])
        footprint = geojson_to_wkt(polygon)
    else:
        try:
            footprint = geojson_to_wkt(read_geojson(geojson_path))
        except ValueError:
            message = geojson_path + 'is not a path to a valid geojson polygon'
            print(message)
            logging.error(message)
    message = 'QUERY API for regions : %s' % footprint
    logging.info(message)

    # query products for one day
    for idx_day, date in enumerate(period):
        message = 'QUERY API for dates : %s till %s' % (date, date + datetime.timedelta(days=1))
        logging.info(message)

        # make terminal output for Enrico:
        print('searching products at: ' + date.strftime('%m/%d/%Y') + '...')
        print('               within: ' + footprint + '.')

        products = api.query(footprint,
                             date=(date, date + datetime.timedelta(days=1)),
                             platformname=platformname, producttype=corr_speciesproduct[0]
                             )

        message = f'{len(products)} products found \n product IDs are:\n'

        for product in products:
            message += '  %s\n' % product
            info = api.get_product_odata(product)

            # check version
            if info['title'].split('_')[1] in ver:

                # more terminal output for Enrico:
                message = 'product title:           %s' % info['title']
                print(message)
                logging.info(message)
                message = 'product md5:             %s' % info['md5']
                print(message)
                logging.info(message)

                # TODO: check if product is there already (mostly it will be for hyperspec) and only download it if
                #  it is not
                if replace is True:
                    print(' the tropomi files will be downloaded again')

                # individual product download:
                try:
                    api.download(info['id'], directory_path=data_dir, checksum=True)
                    message = 'sucesfully downloaded:   %s\n' % info['title']
                    print(message)
                    logging.info(message)
                except sentinelsat.InvalidChecksumError:
                    # throw checksum error when encountered but continue
                    message = 'checksum error for %s\n' % info['title']
                    print(message)
                    logging.error(message)
                    continue

        logging.info(message)

    # renaming files (TROPOMI files are dowloaded as zips but are actually netCDF files). Only extension change is
    # required.
    for filename in os.listdir(data_dir):
        if filename[-4:] == '.zip' and filename[:3] == 'S5P':
            os.rename(os.path.join(data_dir, filename), os.path.join(data_dir, filename[:-4] + '.nc'))
            print('renaming zips to ncs')
    return print('done.')


# %%
def era5_download(period=None, data_dir=None, res=None, levels=None, times=None, region="global",
                  replace=False, makelog=False):
    """" Function for downloading wind data using the CDSapi. By default, global ERA5 uv wind products are downloaded
    from ECMWF and stored. """

    # inputs:
    #   period   - daterange object specifying the download period
    #   data_dir - directory where the data needs to get stored
    #   res      - resolution of the data in ° [lat, lon] or ° as homogenous
    #   levels   - string or array of strings with pressure levels in hPa, default is 1000 and 950
    #   times    - times of the data as array of strings ["hh:mm","hh:mm"], default is "12:00"
    #   region   - [North, West, South, East], e.g.  [5, 47, 16, 55] for Germany. Default: global.
    #   TODO: region should also accept shapes
    #   replace  - boolean, replace previously downloaded data, yes or no? True means data will be replaced
    #   makelog  - boolean, make a log file yes or no? 

    # -------------------------------------------------------------------------
    # configure logging
    # -------------------------------------------------------------------------
    if makelog:
        logfilename = "era5_download_%s.log" % datetime.datetime.today().strftime("%Y%m%d")

        if data_dir is None:
            if not os.path.exists(os.path.join(os.getcwd(), 'log')):
                os.makedirs(os.path.join(os.getcwd(), 'log'))
            logfile = os.path.join(os.getcwd(), 'log', logfilename)
        else:
            if not os.path.exists(os.path.join(data_dir, 'log')):
                os.makedirs(os.path.join(data_dir, 'log'))
            logfile = os.path.join(data_dir, 'log', logfilename)

        # if the log file exists we make it empty
        if os.path.isfile(logfile):
            file = open(logfile, "r+")
            file.truncate(0)

        # reset and reconfigure
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(filename=logfile, encoding="utf-8", filemode='w', level=logging.DEBUG)

    # -------------------------------------------------------------------------
    # check if the provided inputs are correct and set defaults:
    # -------------------------------------------------------------------------

    # period:
    # should be provided and should be DateRange instance
    if period is None or len(period) == 0:
        message = "Period is empty.\n"
        logging.error(message)

    # path:
    # when the data_dir is not provided we make one in the current directory
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), 'ERA5')
        logging.warning("No path was provided: data will be stored in %s" % data_dir)
    else:
        pass

    if not os.path.exists(data_dir):
        # try to make the path
        try:
            message = "making a new directory to store data: %s\n" % data_dir
            print(message)
            logging.info(message)
            os.makedirs(data_dir)
        # data_dir is not a valid path
        except ValueError:
            message = "please provide a valid path, not %s\n" % data_dir
            print(message)
            logging.error(message)
            return ValueError("wrong input: %s" % data_dir)

    # resolution:
    if res is None:
        pass
    else:
        # a none default grid is provided. Default grids for ERA5 online CDS is 0.25°x0.25° (atmosphere) and
        # 0.5°x0.5° (ocean waves)
        if len(res) == 1:  # longitude resolution is equal to latitude resolution
            res = [float(res), float(res)]
            message = "resolution set to  %s\n" % res
            logging.info(message)
        elif len(res) == 2:  # resolution [lon, lat] is given.
            # convert to float
            res = [float(i) for i in res]
            message = "resolution set to  %s\n" % res
            logging.info(message)
        elif len(res) < 2:
            # wrong format
            message = 'please provide a valid resolution, not %s\n' % res
            print(message)
            logging.error(message)
            return ValueError("wrong input: %s" % res)

    # levels:
    if levels is not None:
        # levels are given
        if len(levels) == 1:  # one level was given it should be within vertical coverage, i.e. between 1000 to 1hPa
            if 1 <= int(levels[0]) <= 1000:  # correct
                levels = [str(levels)]
            else:
                # outside bounds
                message = 'please request levels within ERA limits, between [1hPa, 1000hPa], not %s \n' % levels
                print(message)
                logging.error(message)
                return ValueError("wrong input: %s" % levels)

        elif isinstance(levels, list):  # an array or list of levels is given
            # convert to correct array of string in case floats or ints are given
            try:
                levels = [str(lvl) for lvl in levels]
            except ValueError:
                # wrong format
                message = 'please provide a valid array of levels, %s is not convertible to correct format \n' % levels
                print(message)
                logging.error(message)
                return ValueError("wrong input: %s" % levels)
        elif len(levels.shape()) > 2:
            # wrong format
            message = 'please provide a valid array of levels, not %s\n' % levels
            print(message)
            logging.error(message)
            return ValueError("wrong input: %s" % levels)
    else:  # levels is None/not given -> set them to defaults
        levels = ["1000", "950"]

    # set default time
    if times is not None:
        pass
    else:
        times = ["12:00"]
    # -------------------------------------------------------------------------
    # Downloading using CDS api
    # -------------------------------------------------------------------------

    # check if cds cdsapirc file exist with uid and API key. If it does not exist make the file.
    home_dir = os.path.expanduser("~")
    cdsapirc_file = os.path.join(home_dir, ".cdsapirc")
    if not os.path.isfile(cdsapirc_file):
        f = open(cdsapirc_file, "w")
        # f.write("url: https://ads.atmosphere.copernicus.eu/api/v2\n")
        f.write("url: https://cds.climate.copernicus.eu/api/v2\n")
        f.write("key: [PLACEHOLDER:https://cds.climate.copernicus.eu/api/v2 apikey]")
        f.close()

    # make contact
    server = cdsClient()

    # download per day:
    for idx_day, day in enumerate(period):
        # make the year subdir if it is not there.
        if not os.path.exists("{dir}/{d:%Y}/".format(dir=data_dir, d=day)):
            os.makedirs("{dir}/{d:%Y}/".format(dir=data_dir, d=day))

        filename = "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day)

        print('checking...' + filename)
        # download only if the file was not downloaded before or replace it if requested:
        if (replace is False and not os.path.exists(filename)) or (replace is True):
            print('saving...' + filename)
            server.retrieve(
                'reanalysis-era5-pressure-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': ['u_component_of_wind', 'v_component_of_wind'],
                    'pressure_level': levels,
                    'year': day.strftime("%Y"),
                    'month': day.strftime("%m"),
                    'day': day.strftime("%d"),
                    'time': times,
                    'grid': res
                },
                "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day))
        else:
            # file was downloaded before and no replacement is requested:
            print(filename + ' exists and \'replace\' is set to \'%s\'' % replace)
            message = 'data %s is already there. Skipped the download\n' % filename
            print(message)
            logging.warning(message)

    message = 'done with ERA5 download'
    print(message)
    logging.info(message)
    return
