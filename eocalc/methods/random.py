# -*- coding: utf-8 -*-
"""Random emission calculator."""

from datetime import date
import random

from pandas import DataFrame

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import DateRange
from eocalc.methods.base import Status, EOEmissionCalculator


class RandomEOEmissionCalculator(EOEmissionCalculator):
    """Implement the emission calculator returning random non-sense."""

    def __init__(self):
        super().__init__()

    def minimum_area_size() -> int:
        return 0

    def minimum_period_length() -> int:
        return 0

    def earliest_start_date() -> date:
        return date.fromisoformat('0001-01-01')

    def latest_end_date() -> date:
        return date.fromisoformat('9999-12-31')

    def supports(pollutant: Pollutant) -> bool:
        return True

    def run(self, area, period: DateRange, pollutant: Pollutant) -> dict:
        assert(self.__class__.supports(pollutant))
        assert((period.end-period.start).days >=
               self.__class__.minimum_period_length())

        self._state = Status.RUNNING
        results = {}

        # Generate data frame with random emission values per GNFR sector
        data = DataFrame(index=GNFR,
                         columns=[f"{pollutant.name} [kt]", "Umin [%]", "Umax [%]"])
        for sector in GNFR:
            data.loc[sector] = [random.random()*100, random.random()*18, random.random()*22]
        # Add totals row at the bottom
        data.loc["Totals"] = data.sum(axis=0)

        results[EOEmissionCalculator.TOTAL_EMISSIONS_KEY] = data
        results[EOEmissionCalculator.GRIDDED_EMISSIONS_KEY] = 'white noise.png'

        self._state = Status.READY
        return results
