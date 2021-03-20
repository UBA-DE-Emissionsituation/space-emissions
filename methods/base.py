# -*- coding: utf-8 -*-
"""
Space emission calculator base classes and definitions
"""

from enum import Enum, auto
from abc import ABC, abstractmethod

class Pollutant(Enum):
    NOx = auto()
    SO2 = auto()
    NH3 = auto()
    PM2_5 = auto()

class EOEmissionCalculator(ABC):
    TOTAL_EMISSIONS_KEY = "totals"
    GRIDDED_EMISSIONS_KEY = "grid"
    
    def __init__(self):
        super().__init__()
    
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
    def run(self, area, timespan, pollutant: Pollutant) -> dict:
        pass
    