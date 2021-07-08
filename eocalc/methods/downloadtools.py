# -*- coding: utf-8 -*-
# downloadtools.py
# Author(s):     Enrico Dammers / Janot Tokaya
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
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from geojson import Polygon
from cdsapi import Client as cdsClient
from datetime import date, timedelta

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange ,EOEmissionCalculator, Status

#%% Download functions
def tropomi_download(period = None, data_dir = None, 
                        species = Pollutant.NO2, producttype = 'L2__NO2___', geojson_path = None, satellite = 's5p',user = '[PLACEHOLDER:https://scihub.copernicus.eu/dhus UN]', password = '[PLACEHOLDER:https://scihub.copernicus.eu/dhus PW]',replace =False, makelog = True):
    """"Function for downloading TROPOMI data using the sentinelsat API. Defaultly, L2 NO2 OFFL data is downloaded """

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
      logfilename = "tropomi_download_%s.log"%datetime.datetime.today().strftime("%Y%m%d")

      if data_dir is None: 
        if not os.path.exists(os.path.join(os.getcwd(),'log')):
          os.makedirs (os.path.join(os.getcwd(),'log'))
        logfile = os.path.join(os.getcwd(),'log',logfilename)
      else:
        if not os.path.exists(os.path.join(data_dir,'log')):
          os.makedirs(os.path.join(data_dir,'log'))
        logfile = os.path.join(data_dir,'log',logfilename)

      #if the log file exists we make it empty
      if os.path.isfile(logfile): 
        file = open(logfile,"r+")
        file. truncate(0)

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
      mssg = "Period is empty.\n" 
      logging.error(mssg)
    
    #check species and product selection
    
    #select sentinel satellite and products. Setup API accordingly:
    if satellite == 's5p': #TROPOMI
      platformname = 'Sentinel-5 Precursor'
       
      producttype_opts = ['L1B_IR_SIR', 'L1B_IR_UVN', 'L1B_RA_BD1', 'L1B_RA_BD2', 'L1B_RA_BD3', 'L1B_RA_BD4', 'L1B_RA_BD5', 'L1B_RA_BD6',
                          'L1B_RA_BD7', 'L1B_RA_BD8', 'L2__AER_AI', 'L2__AER_LH', 'L2__CH4'   , 'L2__CLOUD_', 'L2__CO____', 'L2__HCHO__',
                          'L2__NO2___', 'L2__NP_BD3', 'L2__NP_BD6', 'L2__NP_BD7', 'L2__O3_TCL', 'L2__O3____', 'L2__SO2___']
      #  set up sentinel 5p api
      s5p_user='s5pguest'
      s5p_password='s5pguest'
      api = SentinelAPI(s5p_user, s5p_password, 'https://s5phub.copernicus.eu/dhus/',show_progressbars=False) 
      mssg = "Satellite set to  %s\n"%satellite
      logging.info(mssg)
      ver  =  'OFFL' #or "NRTI or REPRO"
         
    else: #error
      mssg = 'satellite %s not recognized. Please select from [s5p]'%satellite
      print(mssg)
      logging.error(mssg)
            
    #select product based on product type
    corr_producttype = [pt for pt in producttype_opts if producttype in pt ]
    if len(corr_producttype)==0: logging.error("product type should be in %s. Not %s"%(producttype_opts,producttype))
    
    #select product based on species
    corr_speciesproduct = [pt for pt in corr_producttype if species.name.upper() in pt ]
    if len(corr_speciesproduct)==0: logging.error("species type should be one of [no2,o3,so2,co,cloud,ch4,aer,hcho,np,ir,ra]. Not %s"%species.name)
              
    # path:
    # if data_dir is not provided we make one in the current directory
    if data_dir is None: data_dir = os.path.join(os.getcwd(), 'sentinel',satellite);logging.warning("No path was provided: data will be stored in %s"%data_dir)

    #try to make the folder
    if not os.path.exists(data_dir):
      #try to make the path
      try:
        mssg = "making a new directory to store data: %s\n"%data_dir
        print(mssg)
        logging.info(mssg)
        os.makedirs(data_dir)
      #data_dir is not a valid path
      except:
        mssg = "please provide a valid path, not %s\n"%data_dir
        print(mssg)
        logging.error(mssg)
        return ValueError("wrong input: %s"%data_dir)
            
    # -------------------------------------------------------------------------
    # collect products per day
    # -------------------------------------------------------------------------
            
    if geojson_path is None:
       #bounding box for germany:
       P = Polygon([[(1.00, 46.00), (15.00, 46.00), (15.00, 55.00), (1.00, 55.00), (1.00, 46.00)]])
       footprint =  geojson_to_wkt(P)
    else: 
      try:
        footprint = geojson_to_wkt(read_geojson(geojson_path))
      except:
        mssg = geojson_path+ 'is not a path to a valid geojson polygon'
        print(mssg)
        logging.error(mssg)
    mssg = 'QUERY API for regions : %s'%(footprint)
    logging.info(mssg)
          
    #query products for one day
    for idx_day, date in enumerate(period):   
      mssg = 'QUERY API for dates : %s till %s'%(date, date + datetime.timedelta(days=1))
      logging.info(mssg)
      
      #make terminal output for Enrico:
      print('searching products at: ' + date.strftime('%m/%d/%Y') +'...')
      print('               within: ' + footprint + '.')
     
      products = api.query(footprint,
                     date=(date, date + datetime.timedelta(days=1)),
                     platformname=platformname,producttype=corr_speciesproduct[0]
                     )
      
      mssg = '%s products found \n product IDs are:\n'%(len(products))
      
      for product in products:
        mssg += '  %s\n'%product
        info = api.get_product_odata(product)
        
        #check version
        if info['title'].split('_')[1] in ver:
        
           #more terminal output for Enrico:
           mssg = 'product title:           %s'%info['title']
           print(mssg)
           logging.info(mssg)
           mssg = 'product md5:             %s'%info['md5']
           print(mssg)
           logging.info(mssg)
           
          #TODO: check if product is there already (mostly it will be for hyperspec) and only download it if it is not

           #individual product download:
           try:
              api.download(info['id'],  directory_path= data_dir , checksum=True)
              mssg = 'sucesfully downloaded:   %s\n'%info['title']
              print(mssg)
              logging.info(mssg)
           except sentinelsat.InvalidChecksumError:
              # throw checksum error when encountered but continue
              mssg = 'checksum error for %s\n'%info['title']
              print(mssg)
              logging.error(mssg)
              continue
           
      logging.info(mssg)
         
    #renaming files (TROPOMI files are dowloaded as zips but are actually netCDF files). Only extension change is required.
    for filename in os.listdir(data_dir):
      if filename[-4:] == '.zip' and filename[:3] == 'S5P':
        os.rename(os.path.join(data_dir,filename),os.path.join(data_dir,filename[:-4]+'.nc'))
        print('renaming zips to ncs')          
    return print('done.')

#%%
def era5_download(period = None, data_dir = None , res = None, levels = ["1000", "950"], times = ["12:00"], region = "global", replace =False, makelog = False):
    """"Function for downloading wind data using the CDSapi. Defaultly, global ERA5 uv wind products are downloaded from ECMWF and stored. """
    
    # inputs:
    #   period   - daterange object specifying the download period
    #   data_dir - directory where the data needs to get stored
    #   res      - resolution of the data in ° [lat, lon] or ° as homogenous
    #   levels   - string or array of strings with pressure levels in hPa
    #   times    - times of the data as array of strings ["hh:mm","hh:mm"]
    #   region   - [North, West, South, East], e.g.  [5, 47, 16, 55] for Germany. Default: global. TODO should also accept shapes
    #   replace  - boolean, replace previously downloaded data, yes or no? True means data will be replaced
    #   makelog  - boolean, make a log file yes or no? 

    # -------------------------------------------------------------------------
    # configure logging
    # -------------------------------------------------------------------------
    if makelog:
      logfilename = "era5_download_%s.log"%datetime.datetime.today().strftime("%Y%m%d")

      if data_dir is None: 
        if not os.path.exists(os.path.join(os.getcwd(),'log')):
          os.makedirs (os.path.join(os.getcwd(),'log'))
        logfile = os.path.join(os.getcwd(),'log',logfilename)
      else:
        if not os.path.exists(os.path.join(data_dir,'log')):
          os.makedirs(os.path.join(data_dir,'log'))
        logfile = os.path.join(data_dir,'log',logfilename)

      #if the log file exists we make it empty
      if os.path.isfile(logfile): 
        file = open(logfile,"r+")
        file. truncate(0)

      #reset and reconfigure
      for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)      
      logging.basicConfig(filename=logfile, encoding="utf-8", filemode='w', level=logging.DEBUG)
       
    # -------------------------------------------------------------------------
    # check if the provided inputs are correct:
    # -------------------------------------------------------------------------

    # period:
    # should be rpovided and should be DateRange instance
    if period is None or len(period) == 0:
      mssg = "Period is empty.\n" 
      logging.error(mssg)

    # path:
    # if data_dir is not provided we make one in the current directory
    if data_dir is None: data_dir = os.path.join(os.getcwd(), 'ERA5'); logging.warning("No path was provided: data will be stored in %s"%data_dir)

    if not os.path.exists(data_dir):
      #try to make the path
      try:
        mssg = "making a new directory to store data: %s\n"%data_dir
        print(mssg)
        logging.info(mssg)
        os.makedirs(data_dir)
      #data_dir is not a valid path
      except:
        mssg = "please provide a valid path, not %s\n"%data_dir
        print(mssg)
        logging.error(mssg)
        return ValueError("wrong input: %s"%data_dir)

    # resolution:
    if res is not None:
      # a none default grid is provided. Default grids for ERA5 online CDS is 0.25°x0.25° (atmosphere) and 0.5°x0.5° (ocean waves)
      if len(res) == 1: # longitude resolution is equal to latitude resolution 
        res = [float(res), float(res)]
        mssg = "resolution set to  %s\n"%res
        logging.info(mssg)
      elif len(res) == 2: # resolution [lon, lat] is given.
        #convert to float
        res = [float(i) for i in res]
        mssg = "resolution set to  %s\n"%res
        logging.info(mssg)
      elif len(res) <2:
        #wrong format
        mssg = 'please provide a valid resolution, not %s\n'%res
        print(mssg)
        logging.error(mssg)
        return ValueError("wrong input: %s"%res)

    # levels:
    if levels is not None:
      #levels are given
      if len(levels) == 1: #one level was given it should be within vertical coverage, i.e. between 1000 hPa to 1 hPa
        if int(levels)>=1 and int(levels)<=1000: #correct
          levels = [str(levels)]
        else: 
          #outside bounds
          mssg = 'please request levels within ERA limits, between [1hPa, 1000hPa], not %s \n'%levels
          print(mssg)
          logging.error(mssg)
          return ValueError("wrong input: %s"%levels)

      elif isinstance(levels, list): # an array or list of levels is given
        #convert to correct array of string in case floats or ints are given
        try:
          levels = [str(lvl) for lvl in levels]
        except:
          #wrong format
          mssg = 'please provide a valid array of levels, %s is not convertable to correct format \n'%levels
          print(mssg)
          logging.error(mssg)
          return ValueError("wrong input: %s"%levels)
      elif len(levels.shape()) >2:
        #wrong format
        mssg = 'please provide a valid array of levels, not %s\n'%levels
        print(mssg)
        logging.error(mssg)
        return ValueError("wrong input: %s"%levels)

    # -------------------------------------------------------------------------
    # Downloading using CDS api
    # ------------------------------------------------------------------------- 

    # check if cds cdsapirc file exist with uid and API key. If it does not exist make the file.
    homedir =  os.path.expanduser("~") 
    cdsapirc_file = os.path.join(homedir,".cdsapirc")
    if not os.path.isfile(cdsapirc_file): 
      f = open(cdsapirc_file, "w")
      #f.write("url: https://ads.atmosphere.copernicus.eu/api/v2\n")
      f.write("url: https://cds.climate.copernicus.eu/api/v2\n")
      f.write("key: [PLACEHOLDER:https://cds.climate.copernicus.eu/api/v2 apikey]")
      f.close()

    # make contact
    server = cdsClient()
    
    #download per day:
    for idx_day, day in enumerate(period):          
        #make the year subdir if it is not there.
        if not os.path.exists("{dir}/{d:%Y}/".format(dir=data_dir, d=day)): os.makedirs("{dir}/{d:%Y}/".format(dir=data_dir, d=day))
        
        filename = "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day)

        print('checking...'+filename)
        #download only if the file was not downloaded before or replace it if requested:   
        if (replace == False and not os.path.exists(filename)) or (replace == True):
          print('saving...'+filename)
          server.retrieve(
              'reanalysis-era5-pressure-levels',
              {
              'product_type':'reanalysis',
              'format':'netcdf',
              'variable':[ 'u_component_of_wind','v_component_of_wind' ],
              'pressure_level':levels,
              'year': day.strftime("%Y"),
              'month': day.strftime("%m"),
              'day': day.strftime("%d"),
              'time': times,
              'grid': res
              },
              "{dir}/{d:%Y}/ECMWF_ERA5_uv_{d:%Y%m%d}.nc".format(dir=data_dir, d=day))
        else:
          #file was downloaded before and no replacement is requested:   
          print(filename+' exists and \'replace\' is set to \'%s\''%replace)
          mssg = 'data %s is already there. Skipped the download\n'%filename
          print(mssg)
          logging.warning(mssg)

    mssg ='done with ERA5 download'
    print(mssg)
    logging.info(mssg)
    return 


