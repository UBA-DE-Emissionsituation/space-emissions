# -*- coding: utf-8 -*-
"""
Random emission calculator
"""
import random

import pandas
from pandas import DataFrame

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import EOEmissionCalculator

class RandomEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def minimum_area_size(self) -> int:
        return 0
    
    def minimum_period_length(self) -> int:
        return 0
    
    def supports(self, pollutant: Pollutant) -> bool:
        return True
    
    def run(self, area, period: pandas.DatetimeIndex, pollutant: Pollutant) -> dict:
        assert(self.supports(pollutant))
        assert(len(period) >= self.minimum_period_length())
        
        results = {}
        
        # Generate data frame with random emission values per GNFR sector
        data = DataFrame(index=GNFR,
            columns=[f"{pollutant.name} [kt]", "Umin [%]", "Umax [%]"])
        for sector in GNFR:
            data.loc[sector] = [random.random()*100, random.random()*18, random.random()*22]
        # Add totals row at the bottom
        data.loc["Totals"] = data.sum(axis=0)
                        
        results[EOEmissionCalculator.TOTAL_EMISSIONS_KEY] = data
        results[EOEmissionCalculator.GRIDDED_EMISSIONS_KEY] = 'white noise.png'
                
        return results
    