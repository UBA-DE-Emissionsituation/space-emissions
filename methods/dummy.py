# -*- coding: utf-8 -*-
"""
Dummy emission calculator
"""

from .base import EOEmissionCalculator, Pollutant

class DummyEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def supports(self, pollutant: Pollutant) -> bool:
        return True
    
    def run(self, area, timespan, pollutant: Pollutant) -> dict:
        return 42
