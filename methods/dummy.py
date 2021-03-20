# -*- coding: utf-8 -*-
"""
Dummy emission calculator
"""

from .base import EOEmissionCalculator

class DummyEOEmissionCalculator(EOEmissionCalculator):
    
    def __init__(self):
        super().__init__()
        
    def supports():
        return True
    
    def run(self):
        return 42
    