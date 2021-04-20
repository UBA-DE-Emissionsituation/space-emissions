# -*- coding: utf-8 -*-
import unittest
from datetime import date, timedelta

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.temis import TEMISTropomiMonthlyMeanNOxEmissionCalculator


class TestTEMISTropomiMonthlyMeanNOxMethods(unittest.TestCase):

    def test_covers(self):
        calc = TEMISTropomiMonthlyMeanNOxEmissionCalculator()
        north = shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-110., 20.], [140., 20.], [180., 40.], [-180., 30.], [-110., 20.]]]]})
        south = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., -20.], [140., -20.], [180., -40.], [-180., -30.], [-110., -20.]]]]})
        both = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., 20.], [140., -20.], [180., -40.], [-180., -30.], [-110., 20.]]]]})
        self.assertTrue(calc.covers(north))
        self.assertTrue(calc.covers(south))
        self.assertTrue(calc.covers(both))

    def test_end_date(self):
        test = date.fromisoformat("2021-04-19")
        self.assertEqual(date.fromisoformat("2021-02-28"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

        test = date.fromisoformat("2021-01-01")
        self.assertEqual(date.fromisoformat("2020-11-30"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

        test = date.fromisoformat("2021-05-31")
        self.assertEqual(date.fromisoformat("2021-03-31"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(p)) if p == Pollutant.NOx else \
                        self.assertFalse(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(p))
        self.assertFalse(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(None))
