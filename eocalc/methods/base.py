# -*- coding: utf-8 -*-
"""
Space emission calculator base classes and definitions
"""

from abc import ABC, abstractmethod

import pandas

from eocalc.context import Pollutant

class EOEmissionCalculator(ABC):
    
    # Key to use for the total emission breakdown in result dict
    TOTAL_EMISSIONS_KEY = "totals"
    # Key to use for the spatial gridded emissions in result dict
    GRIDDED_EMISSIONS_KEY = "grid"
    
    def __init__(self):
        super().__init__()
    
    @property
    @abstractmethod
    def minimum_area_size(self) -> int:
        """
        The minimum region size this method can reliably work on.

        Returns
        -------
        Minimum region size in km² (square kilometers).

        """
        pass
    
    @property
    @abstractmethod
    def minimum_period_length(self) -> int:
        """
        The minimum time span this method can reliably work on.

        Returns
        -------
        Minimum period in number of days.

        """
        pass
    
    @abstractmethod
    def supports(self, pollutant: Pollutant) -> bool:
        """
        Check for the calculation method's applicability to given pollutant.

        Parameters
        ----------
        pollutant: Pollutant
            Pollutant to check.

        Returns
        -------
        If this method support estimation of given pollutant.

        """
        pass
    
    @abstractmethod
    def run(self, area, period: pandas.DatetimeIndex, pollutant: Pollutant) -> dict:
        """
        Run method for given input and return the derived emission values. 

        Parameters
        ----------
        area : TYPE (TODO)
            Area to calculate emissions for.
        period : pandas.DatetimeIndex
            Time span to cover. Use pandas.date_range to create.
        pollutant : Pollutant
            Air pollutant to calculate emissions for.

        Returns
        -------
        dict
            The emission values, both as total numbers and as a grid.

        """
        pass
    