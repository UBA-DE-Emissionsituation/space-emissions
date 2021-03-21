# -*- coding: utf-8 -*-
"""
Dummy emission calculator
"""

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator

class DummyEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def minimum_area_size(self) -> int:
        return 0
    
    def minimum_period_length(self) -> int:
        return 0
        
    def supports(self, pollutant: Pollutant) -> bool:
        return True
    
    def run(self, area = None, period = None, pollutant: Pollutant = None) -> dict:
        return 42
