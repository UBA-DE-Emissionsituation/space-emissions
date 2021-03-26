# -*- coding: utf-8 -*-
import unittest

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.random import RandomEOEmissionCalculator


class TestRandomMethods(unittest.TestCase):

    def test_minimum_area(self):
        self.assertEqual(1, RandomEOEmissionCalculator.minimum_area_size())

    def test_minimum_period(self):
        self.assertEqual(1, RandomEOEmissionCalculator.minimum_period_length())

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(RandomEOEmissionCalculator.supports(p))
        self.assertFalse(RandomEOEmissionCalculator.supports(None))

    def test_run(self):
        region = shape({'type': 'Polygon', 'coordinates': [[[-122., 37.], [-125., 37.], [-125., 38.], [-122., 38.], [-122., 37.]]]})
        period = DateRange('2025-01-01', '2025-12-31')

        for p in Pollutant:
            results = RandomEOEmissionCalculator().run(region, period, p)
            self.assertIsNotNone(results[RandomEOEmissionCalculator.TOTAL_EMISSIONS_KEY])
            self.assertIsNotNone(results[RandomEOEmissionCalculator.GRIDDED_EMISSIONS_KEY])
        with self.assertRaises(AssertionError):
            RandomEOEmissionCalculator().run(region, period, None)


if __name__ == '__main__':
    unittest.main()
