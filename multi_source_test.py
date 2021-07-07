# -*- coding: utf-8 -*-
# %%
"""Fioletov Multi-source emission calculator"""
import os
import json
import time
# from datetime import datetime
import datetime
import pandas
import geopandas
from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.tools import *
from eocalc.methods.fioletov import *
import time
### %%
# time test
s_t = time.time()
# select region for test
directory = "/home/enrico/dammerse_tno/space-emissions/data/regions/"
regions = {}

for filename in os.listdir(directory):
    if ((filename.endswith(".geo.json") or filename.endswith(".geojson")) and ('germany.geo.json' in filename)):
        with open(f"{directory}/{filename}", 'r') as geojson_file:
            regions[filename] = shape(json.load(geojson_file)["geometry"])

# first region test
region = regions[next(iter(regions))]
bounds = region.bounds
## %%
# results test
results = {} # results will be put here as results[<filename>][<data>]
start = datetime.datetime.now()

for filename, region in regions.items():
    results[filename] = MultiSourceCalculator().run(region, DateRange(start='2019-06-01', end='2019-06-30'), Pollutant.NO2)
    print(f"Done with region represented by file '{filename}'")

print(f"All finished in {datetime.datetime.now()-start}.")

# # %%
# # Remove regions not covered
# regions = {filename: region for filename, region in regions.items() if MultiSourceCalculator.covers(region)}
quicktestplot = overlay(results[filename]['gpd'], GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')
quicktestplot.plot(f"Total {Pollutant.NO2.name} emissions [kg]", figsize=(20, 20), legend=True, legend_kwds={'label': f"Emissions in {filename} [kg]", 'orientation': "horizontal"})
# %%


# %%