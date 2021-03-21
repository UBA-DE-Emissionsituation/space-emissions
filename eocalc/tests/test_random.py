# -*- coding: utf-8 -*-
import unittest

import pandas

from eocalc.context import Pollutant
from eocalc.methods.random import RandomEOEmissionCalculator

class TestRandomMethods(unittest.TestCase):

    def test_minimum_area(self):
        self.assertEqual(0, RandomEOEmissionCalculator().minimum_area_size())
        
    def test_minimum_period(self):
        self.assertEqual(0, RandomEOEmissionCalculator().minimum_period_length())

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(RandomEOEmissionCalculator().supports(p))

    def test_run(self):
        period = pandas.date_range('2025-01-01', '2025-12-31')
        for p in Pollutant:
            results = RandomEOEmissionCalculator().run(None, period, p)
            self.assertIsNotNone(results[RandomEOEmissionCalculator.TOTAL_EMISSIONS_KEY])
            self.assertIsNotNone(results[RandomEOEmissionCalculator.GRIDDED_EMISSIONS_KEY])

if __name__ == '__main__':
    unittest.main()