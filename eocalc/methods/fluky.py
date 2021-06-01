# -*- coding: utf-8 -*-
"""Random emission calculator."""

import random
from datetime import date

from shapely.geometry import MultiPolygon, shape
from pandas import DataFrame
from geopandas import GeoDataFrame, overlay

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import DateRange
from eocalc.methods.base import Status, EOEmissionCalculator


class RandomEOEmissionCalculator(EOEmissionCalculator):
    """Implement the emission calculator returning random non-sense."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def minimum_area_size() -> int:
        return 1

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -90.], [180., -90.], [180., 90.], [-180., 90.], [-180., -90.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 1

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat('0001-01-01')

    @staticmethod
    def latest_end_date() -> date:
        return date.fromisoformat('9999-12-31')

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant is not None

    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict[str, DataFrame]:
        self._validate(region, period, pollutant)
        self._state = Status.RUNNING
        self._progress = 0

        # Generate data frame with random emission values per GNFR sector
        data = self._create_gnfr_table(pollutant)
        for sector in GNFR:
            data.loc[sector] = [random.random()*100, random.random()*18, random.random()*22]
        # Add totals row at the bottom
        data.loc["Totals"] = data.sum(axis=0)

        self._progress = 50

        # Generate bogus grid with random emission values
        geo_data = self._create_grid(region, .1, .1, snap=False)
        geo_data = overlay(geo_data, GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')
        geo_data.insert(0, "Area [km²]", geo_data.to_crs(epsg=8857).area / 10 ** 6)  # Equal earth projection
        geo_data.insert(1, f"Total {pollutant.name} emissions [kg]", [random.random()*100 for _ in range(len(geo_data))])
        geo_data.insert(2, "Umin [%]", 42)
        geo_data.insert(3, "Umax [%]", 42)
        geo_data.insert(4, "Number of values [1]", len(period))
        geo_data.insert(5, "Missing values [1]", 0)

        self._progress = 100
        self._state = Status.READY
        return {self.TOTAL_EMISSIONS_KEY: data, self.GRIDDED_EMISSIONS_KEY: geo_data}
