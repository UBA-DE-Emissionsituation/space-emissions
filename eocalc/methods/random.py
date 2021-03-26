# -*- coding: utf-8 -*-
"""Random emission calculator."""

import random
from datetime import date

from pandas import DataFrame

import pyproj
import shapely
from shapely.geometry import MultiPolygon
# from geopandas import GeoDataFrame

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import DateRange
from eocalc.methods.base import Status, EOEmissionCalculator


class RandomEOEmissionCalculator(EOEmissionCalculator):
    """Implement the emission calculator returning random non-sense."""

    def __init__(self):
        super().__init__()

    def minimum_area_size() -> int:
        return 1

    def minimum_period_length() -> int:
        return 1

    def earliest_start_date() -> date:
        return date.fromisoformat('0001-01-01')

    def latest_end_date() -> date:
        return date.fromisoformat('9999-12-31')

    def supports(pollutant: Pollutant) -> bool:
        return pollutant is not None

    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict:
        assert self.__class__.supports(pollutant), f"Pollutant {pollutant} not supported!"
        assert (period.end-period.start).days >= self.__class__.minimum_period_length(), "Time span too short!"
        assert period.start >= self.__class__.earliest_start_date(), f"Method cannot be used for period starting on {period.start}!"
        assert period.end <= self.__class__.latest_end_date(), f"Method cannot be used for period ending on {period.end}!"

        projection = pyproj.Transformer.from_crs(pyproj.CRS('EPSG:4326'), pyproj.CRS('EPSG:8857'), always_xy=True).transform
        assert shapely.ops.transform(projection, region).area / 10**6 >= self.__class__.minimum_area_size(), "Region too small!"

        self._state = Status.RUNNING
        results = {}

        # Generate data frame with random emission values per GNFR sector
        data = DataFrame(index=GNFR,
                         columns=[f"{pollutant.name} [kt]", "Umin [%]", "Umax [%]"])
        for sector in GNFR:
            data.loc[sector] = [random.random()*100, random.random()*18, random.random()*22]
        # Add totals row at the bottom
        data.loc["Totals"] = data.sum(axis=0)

        results[self.__class__.TOTAL_EMISSIONS_KEY] = data
        results[self.__class__.GRIDDED_EMISSIONS_KEY] = region

        self._state = Status.READY
        return results
