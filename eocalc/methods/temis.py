# -*- coding: utf-8 -*-
"""Emission calculators based on TEMIS data (temis.nl)"""

from datetime import date, timedelta

from shapely.geometry import MultiPolygon, shape

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator, DateRange


class TEMISTropomiMonthlyMeanNOxEmissionCalculator(EOEmissionCalculator):

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
        return pollutant == Pollutant.NOx

    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict:
        return {}
