# -*- coding: utf-8 -*-
"""Dummy emission calculator."""

from datetime import date

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator


class DummyEOEmissionCalculator(EOEmissionCalculator):

    def __init__(self):
        super().__init__()

    def minimum_area_size(self) -> int:
        return 0

    def minimum_period_length(self) -> int:
        return 0

    def earliest_start_date(self) -> date:
        return date.fromisoformat('0001-01-01')

    def latest_end_date(self) -> date:
        return date.fromisoformat('9999-12-31')

    def supports(self, pollutant: Pollutant) -> bool:
        return True

    def run(self, area=None, period=None, pollutant=None) -> dict:
        return 42
