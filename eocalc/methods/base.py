# -*- coding: utf-8 -*-
"""Space emission calculator base classes and definitions."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from datetime import date

# from shapely.geometry import MultiPolygon

from eocalc.context import Pollutant


class Status(Enum):
    """Represent state of calculator."""

    READY = auto()
    RUNNING = auto()


class DateRange:
    """Represent a time span between two dates."""

    def __init__(self, start, end):
        self.start = date.fromisoformat(start)
        self.end = date.fromisoformat(end)


class EOEmissionCalculator(ABC):
    """Base class for all emission calculation methods to implement."""

    # Key to use for the total emission breakdown in result dict
    TOTAL_EMISSIONS_KEY = "totals"
    # Key to use for the spatial gridded emissions in result dict
    GRIDDED_EMISSIONS_KEY = "grid"

    def __init__(self):
        super().__init__()
        self._state = Status.READY
        self._progress = 0

    @property
    def state(self) -> Status:
        """
        Check on the status of the calculator.

        Returns
        -------
        Status
            Current state of the calculation method.

        """
        return self._state

    @property
    def progress(self) -> int:
        """
        Check on the progress of the calculator after calling run().

        Returns
        -------
        int
            Progress in percent.

        """
        return self._progress

    @staticmethod
    @abstractmethod
    def minimum_area_size() -> int:
        """
        Check minimum region size this method can reliably work on.

        Returns
        -------
        int
            Minimum region size in km² (square kilometers).

        """
        pass

    @staticmethod
    @abstractmethod
    def minimum_period_length() -> int:
        """
        Check minimum time span this method can reliably work on.

        Returns
        -------
        int
            Minimum period in number of days.

        """
        pass

    @staticmethod
    @abstractmethod
    def earliest_start_date() -> date:
        """
        Check if the method can be used for given period.

        Returns
        -------
        date
            Specific day the method becomes available.

        """
        pass

    @staticmethod
    @abstractmethod
    def latest_end_date() -> date:
        """
        Check if the method can be used for given period.

        Returns
        -------
        date
            Specific day the method becomes unavailable.

        """
        pass

    @staticmethod
    @abstractmethod
    def supports(pollutant: Pollutant) -> bool:
        """
        Check for the calculation method's applicability to given pollutant.

        Parameters
        ----------
        pollutant: Pollutant
            Pollutant to check.

        Returns
        -------
        bool
            If this method support estimation of given pollutant.

        """
        pass

    @abstractmethod
    def run(self, area, period: DateRange, pollutant: Pollutant) -> dict:
        """
        Run method for given input and return the derived emission values.

        Parameters
        ----------
        area : MultiPolygon (TODO)
            Area to calculate emissions for.
        period : DateRange
            Time span to cover.
        pollutant : Pollutant
            Air pollutant to calculate emissions for.

        Returns
        -------
        dict
            The emission values, both as total numbers and as a grid.

        """
        pass
