# -*- coding: utf-8 -*-
"""Space emission calculator base classes and definitions."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from datetime import date, timedelta
import math

import numpy as np
from pandas import DataFrame, Series
from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon

from eocalc.context import Pollutant, GNFR


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

    @staticmethod
    def _create_gnfr_table(pollutant: Pollutant) -> DataFrame:
        """
        Generate empty result data frame. Has one row per GNFR sector, plus a row named "Totals".
        Also comes with three columns for the emission values and min/max uncertainties.
        All rows are pre-filled with n/a.

        Parameters
        ----------
        pollutant : Pollutant
            Pollutant name to include in first column name.

        Returns
        -------
        DataFrame
            Table to be filled by calculation methods.
        """
        cols = [f"{pollutant.name} emissions [kt]", "Umin [%]", "Umax [%]"]
        return DataFrame(index=GNFR, columns=cols, data=np.nan).append(
                    DataFrame(index=["Totals"], columns=cols, data=np.nan))

    @staticmethod
    def _combine_uncertainties(values: Series, uncertainties: Series) -> float:
        """
        Calculate combined uncertainty using simple error propagation. Uses IPCC
        Guidelines formula 6.3 to aggregate and weight given values and uncertainties.
        U = sqrt((x1 * u1)^2 + ... + (xn * un)^2) / x1 + ... + xn

        Parameters
        ----------
        values: Series
            List of values to combine uncertainties for.
        uncertainties: Series
            List of uncertainties for values given.

        Returns
        -------
        float
            Combined uncertainty.
        """
        if len(values) == 0 or len(uncertainties) == 0:
            raise ValueError("Neither values nor uncertainties may be empty.")
        elif len(values) != len(uncertainties):
            raise ValueError("List of values need to have the same length as the list of uncertainties.")
        elif (uncertainties.values < 0).any() or uncertainties.isnull().values.any():
            raise ValueError("All uncertainties need to be positive real numbers.")
        elif values.sum() == 0:
            return 0
        else:
            values = values.reset_index(drop=True)
            uncertainties = uncertainties.reset_index(drop=True)
            return ((values.multiply(uncertainties, fill_value=0)) ** 2).sum() ** 0.5 / values.sum()

    @staticmethod
    def _create_grid(region: MultiPolygon, width: float, height: float, snap: bool = False,
                     include_center_col: bool = False, crs: str = "EPSG:4326") -> GeoDataFrame:
        """
        Overlay given region with grid data frame. Each cell will be created as a row, starting
        at the bottom left and then moving up row by row. Thus, the last row will represent the
        top right corner cell of the grid.

        Parameters
        ----------
        region: MultiPolygon
            Area to cover.
        width: float
            Cell width [degrees].
        height: float
            Cell height [degrees].
        snap: bool
            Make grid corners snap. If true, the lower left corner of the lower left cell
            will have long % width == 0 and lat % height == 0. If false, region bounds will
            be used. Defaults to False.
        include_center_col: bool
            Add column to data frame with cell center coordinates. Defaults to False.
        crs: str
            CRS to set on the data frame. Defaults to "EPSG:4326" (WGS84)

        Returns
        -------
        GeoDataFrame
            Data frame with cell features spanning the full region. Will contain at least one row.
        """
        grid = {"type": "FeatureCollection", "features": []}

        min_lat = region.bounds[1] - region.bounds[1] % height if snap else region.bounds[1]
        max_lat = region.bounds[3] + region.bounds[3] % height if snap else region.bounds[3]
        min_long = region.bounds[0] - region.bounds[0] % width if snap else region.bounds[0]
        max_long = region.bounds[2] + region.bounds[2] % width if snap else region.bounds[2]

        for lat in (min_lat + y * height for y in range(math.ceil((max_lat - min_lat) / height))):
            for long in (min_long + x * width for x in range(math.ceil((max_long - min_long) / width))):
                grid["features"].append({
                    "type": "Feature",
                    "properties": {"center": f"{lat + height / 2}/{long + width / 2}"} if include_center_col else {},
                    "geometry": {"type": "Polygon", "coordinates": [
                        [(long, lat),
                         (long + width, lat),
                         (long + width, lat + height),
                         (long, lat + height),
                         (long, lat)]]}
                })

        return GeoDataFrame.from_features(grid, crs=crs)
