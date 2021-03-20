# -*- coding: utf-8 -*-
"""
Dummy emission calculator
"""

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator

class DummyEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def supports(self, pollutant: Pollutant) -> bool:
        return True
    
    def run(self, area = None, timespan = None, pollutant: Pollutant = None) -> dict:
        return 42
