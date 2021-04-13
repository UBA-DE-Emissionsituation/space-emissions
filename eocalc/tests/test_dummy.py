# -*- coding: utf-8 -*-
import unittest

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.dummy import DummyEOEmissionCalculator


class TestDummyMethods(unittest.TestCase):

    def test_minimum_area(self):
        self.assertEqual(0, DummyEOEmissionCalculator.minimum_area_size())

    def test_covers(self):
        calc = DummyEOEmissionCalculator()
        north = shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-110., 20.], [140., 20.], [180., 40.], [-180., 30.], [-110., 20.]]]]})
        south = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., -20.], [140., -20.], [180., -40.], [-180., -30.], [-110., -20.]]]]})
        both = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., 20.], [140., -20.], [180., -40.], [-180., -30.], [-110., 20.]]]]})
        self.assertTrue(calc.covers(north))
        self.assertTrue(calc.covers(south))
        self.assertTrue(calc.covers(both))

    def test_minimum_period(self):
        self.assertEqual(0, DummyEOEmissionCalculator.minimum_period_length())

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(DummyEOEmissionCalculator.supports(p))

    def test_run(self):
        self.assertEqual(42, DummyEOEmissionCalculator().run())


if __name__ == '__main__':
    unittest.main()
