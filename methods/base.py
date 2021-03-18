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
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def run(self, area, timespan, Pollutant):
        pass

class DummyEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
    
    def run(self, area=None, timespan=None, Pollutant=None):
        return 42
    