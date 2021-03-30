# -*- coding: utf-8 -*-
"""Dummy emission calculator."""

import time
from datetime import date

from eocalc.context import Pollutant
from eocalc.methods.base import Status, EOEmissionCalculator


class DummyEOEmissionCalculator(EOEmissionCalculator):
    """Implement an emission calculator in the laziest way possible."""

    def __init__(self):
        super().__init__()

    @staticmethod
    def minimum_area_size() -> int:
        return 0

    @staticmethod
    def minimum_period_length() -> int:
        return 0

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat("0001-01-01")

    @staticmethod
    def latest_end_date() -> date:
        return date.fromisoformat("9999-12-31")

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant is not None

    def run(self, region=None, period=None, pollutant=None) -> dict:
        self._state = Status.RUNNING
        self._progress = 20
        time.sleep(1)
        self._progress = 50
        time.sleep(1)
        self._progress = 80
        time.sleep(1)
        self._progress = 0
        self._state = Status.READY
        return 42
