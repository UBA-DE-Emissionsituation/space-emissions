# -*- coding: utf-8 -*-
"""
Random emission calculator
"""
import random
from pandas import DataFrame

from .base import EOEmissionCalculator, Pollutant

class RandomEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def supports(self, pollutant: Pollutant) -> bool:
        return True
    
    def run(self, area, timespan, pollutant: Pollutant) -> dict:
        results = {}
                
        data = {"": ["A_PublicPower", "Total"],
                f"{pollutant.name} [kt]": [random.random()*100, random.random()*1000],
                "Umin [%]": [3, 4],
                "Umax [%]": [2, 3]}
        results[EOEmissionCalculator.TOTAL_EMISSIONS_KEY] = DataFrame(data)
        results[EOEmissionCalculator.GRIDDED_EMISSIONS_KEY] = 'white noise.png'
                
        return results
    