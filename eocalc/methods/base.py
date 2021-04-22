# -*- coding: utf-8 -*-
"""Space emission calculator base classes and definitions."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from datetime import date, timedelta

from shapely.geometry import MultiPolygon

from eocalc.context import Pollutant


class Status(Enum):
    """Represent state of calculator."""

    READY = auto()
    RUNNING = auto()


class DateRange:
    """Represent a time span between two dates. Includes both start and end date."""

    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f"[{self.start} to {self.end}, {len(self)} days]"

    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __len__(self) -> int:
        return (self.end - self.start).days + 1

    def __iter__(self):
        yield from [self.start + timedelta(days=count) for count in range(len(self))]

    def __setattr__(self, key, value):
        super.__setattr__(self, key, date.fromisoformat(value))

        if hasattr(self, "start") and hasattr(self, "end") and self.end < self.start:
            raise ValueError(f"Invalid date range, end ({self.end}) cannot be before start ({self.start})!")


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
    def coverage() -> MultiPolygon:
        """
        Get spatial extend the calculation method can cover.

        Returns
        -------
        MultiPolygon
            Representation of the area the method can be applied to.
        """
        pass

    @classmethod
    def covers(cls, region: MultiPolygon) -> bool:
        """
        Check for the calculation method's applicability to given region.

        Parameters
        ----------
        region: MultiPolygon
            Area to check.

        Returns
        -------
        bool
            If this method support emission estimation for given area.

        """
        return cls.coverage().contains(region)

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
    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict:
        """
        Run method for given input and return the derived emission values.

        Parameters
        ----------
        region : MultiPolygon
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
