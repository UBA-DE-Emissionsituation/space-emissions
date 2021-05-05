# -*- coding: utf-8 -*-
"""Emission calculators based on TEMIS data (temis.nl)"""
import os.path
import shutil
import gzip
import threading
from datetime import date, timedelta
from urllib.request import urlretrieve

import numpy
from pandas import Series
from shapely.geometry import MultiPolygon, shape
from geopandas import GeoDataFrame, overlay

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator, DateRange

# Local directory we use to store downloaded and decompressed data
LOCAL_DATA_FOLDER = "data/methods/temis/tropomi/no2/monthly_mean"
# Online resource used to download TEMIS data on demand
TEMIS_DOWNLOAD_URL = "https://d1qb6yzwaaq4he.cloudfront.net/tropomi/no2/%s/%s/no2_%s.asc.gz"
# TEMIS TOMS file format cell width and height [degrees]
TEMIS_BIN_WIDTH = 0.125
# TEMIS TOMS file format number of four digit values per line [1]
TEMIS_VALUES_PER_ROW = 20
# Uncertainty value assumed per cell (TODO find a real value here!)
TEMIS_CELL_UNCERTAINTY = 1000


class TropomiMonthlyMeanAggregator(EOEmissionCalculator):

    @staticmethod
    def minimum_area_size() -> int:
        return 10**5

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -60.], [180., -60.], [180., 60.], [-180., 60.], [-180., -60.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 1

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat('2018-02-01')

    @staticmethod
    def latest_end_date() -> date:
        return (date.today().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant == Pollutant.NO2

    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict:
        # TODO Update status and progress on the way!

        # 1. Overlay area given with cell matching the TEMIS data set
        grid = self._create_grid(region, TEMIS_BIN_WIDTH, TEMIS_BIN_WIDTH, snap=True, include_center_cols=True)

        # 2. Read TEMIS data into the grid, use cache to avoid re-reading the file for each day individually
        cache = {}
        for day in period:
            month_cache_key = f"{day:%Y-%m}"
            if month_cache_key not in cache.keys():
                concentrations = self._read_toms_data(region, self._assure_data_availability(day))
                # value [1/cm²] * TEMIS scale [1] / Avogadro constant [1] * NO2 molecule weight [g] / to [kg] * to [km²]
                cache[month_cache_key] = [x * 10**13 / (6.022 * 10**23) * 46.01 / 1000 * 10**10 for x in concentrations]
                # TODO Correct for pollutant atmosphere lifetime and diurnal variation: pollutant.atmo_lifetime(day, latitude) * pollutant.diurnal_variation(day, instrument)

            # Here, values are actually [kg/km²], but the area [km²] cancels out below
            grid.insert(0, f"{day} {pollutant.name} emissions [kg]", cache[month_cache_key])

        # 3. Clip to actual region and add a data frame column with each cell's size
        grid = overlay(grid, GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')
        grid.insert(0, "Area [km²]", grid.to_crs(epsg=5243).area / 10 ** 6)

        # 4. Update emission columns by multiplying with the area value and sum it all up
        grid.iloc[:, -(len(period)+3):-3] = grid.iloc[:, -(len(period)+3):-3].mul(grid["Area [km²]"], axis=0)
        grid.insert(1, f"Total {pollutant.name} emissions [kg]", grid.iloc[:, -(len(period)+3):-3].sum(axis=1))
        cell_uncertainties = [self._combine_uncertainties(grid.iloc[row, -(len(period)+3):-3],
                                                          Series(TEMIS_CELL_UNCERTAINTY).repeat(len(period))) for row in range(len(grid))]
        grid.insert(2, "Umin [%]", cell_uncertainties)
        grid.insert(3, "Umax [%]", cell_uncertainties)
        grid.insert(4, "Number of values [1]", len(period))
        grid.insert(5, "Missing values [1]", grid.iloc[:, -(len(period)+3):-3].isna().sum(axis=1))

        # 5. Add GNFR table incl. uncertainties
        table = self._create_gnfr_table(pollutant)
        total_uncertainty = self._combine_uncertainties(grid.iloc[:, 1], grid.iloc[:, 2])
        table.iloc[-1] = [grid.iloc[:, 1].sum() / 10**6, total_uncertainty, total_uncertainty]

        return {self.__class__.TOTAL_EMISSIONS_KEY: table, self.__class__.GRIDDED_EMISSIONS_KEY: grid}

    @staticmethod
    def _read_toms_data(region: MultiPolygon, file: str) -> ():
        # TODO Do we need to make this work with regions wrapping around to long < -180 or long > 180?
        min_lat = region.bounds[1] - region.bounds[1] % TEMIS_BIN_WIDTH
        max_lat = region.bounds[3] + region.bounds[3] % TEMIS_BIN_WIDTH
        min_long = region.bounds[0] - region.bounds[0] % TEMIS_BIN_WIDTH
        max_long = region.bounds[2] + region.bounds[2] % TEMIS_BIN_WIDTH

        result = []

        with open(file, 'r') as data:
            lat = -91
            for line in data:
                if line.startswith("lat="):
                    lat = float(line.split('=')[1]) - TEMIS_BIN_WIDTH / 2
                    offset = -180  # We need to go from -180° to +180° for each latitude
                elif min_lat <= lat <= max_lat and line[:4].strip().lstrip('-').isdigit():
                    for count, long in enumerate(offset + x * TEMIS_BIN_WIDTH for x in range(TEMIS_VALUES_PER_ROW)):
                        if min_long <= long <= max_long:
                            emission = int(line[count * 4:count * 4 + 4])  # All emission values are four digits wide
                            result += [emission] if emission >= 0 else [numpy.NaN]
                    offset += TEMIS_VALUES_PER_ROW * TEMIS_BIN_WIDTH

        return result

    @staticmethod
    def _assure_data_availability(day: date) -> str:
        def is_gz_file(filepath):
            with open(filepath, 'rb') as testfile:
                return testfile.read(2) == b'\x1f\x8b'  # gzip 'magic number'

        file = f"{LOCAL_DATA_FOLDER}/no2_{day:%Y%m}.asc"

        with threading.Lock():
            if not os.path.isfile(f"{file}"):
                if not os.path.isfile(f"{file}.original.gz"):
                    # TODO Handle HTTP errors
                    urlretrieve(TEMIS_DOWNLOAD_URL % (f"{day:%Y}", f"{day:%m}", f"{day:%Y%m}"), f"{file}.original.gz")

                # TODO Test this on different platforms, behaviours seem to differ!
                with gzip.open(f"{file}.original.gz", 'rb') as compressed:
                    with open(f"{file}.gz", 'wb') as uncompressed:
                        shutil.copyfileobj(compressed, uncompressed)
                if is_gz_file(f"{file}.gz"):
                    with gzip.open(f"{file}.gz", 'rb') as compressed:
                        with open(f"{file}", 'wb') as uncompressed:
                            shutil.copyfileobj(compressed, uncompressed)
                else:
                    shutil.move(f"{file}.gz", f"{file}")

                # TODO Remove downloaded/intermediate files?

        return file
