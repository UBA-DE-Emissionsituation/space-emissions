# -*- coding: utf-8 -*-
import unittest
from datetime import date

from shapely.geometry import MultiPolygon, shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange, Status, EOEmissionCalculator


class TestBaseMethods(unittest.TestCase):

    def test_date_range(self):
        with self.assertRaises(TypeError):
            DateRange()
        with self.assertRaises(TypeError):
            DateRange(1, "")
        with self.assertRaises(ValueError):
            DateRange(end="alice", start="bob")

        year2019 = DateRange("2019-01-01", "2019-12-31")
        self.assertEqual(year2019, DateRange(end="2019-12-31", start="2019-01-01"))
        self.assertEqual(365, len(year2019))
        self.assertEqual(year2019.__str__(), "[2019-01-01 to 2019-12-31, 365 days]")

        year2020 = DateRange("2020-01-01", "2020-12-31")
        self.assertNotEqual(year2019, year2020)
        self.assertEqual(366, len(year2020))

        august = DateRange("2018-08-01", "2018-08-31")
        self.assertEqual(31, len(august))

        count = 0
        for _ in august:
            count += 1
        self.assertEqual(31, count)

        with self.assertRaises(ValueError):
            DateRange(start="2019-01-01", end="2018-12-31")
        with self.assertRaises(ValueError):
            DateRange(start="2019-01-01", end="2019-12-31").end = "2018-12-31"
        with self.assertRaises(ValueError):
            DateRange(start="2019-01-01", end="2019-12-31").start = "2020-12-31"

    def test_covers(self):
        calc = TestEOEmissionCalculator()
        north = shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-110., 20.], [140., 20.], [180., 40.], [-180., 30.], [-110., 20.]]]]})
        south = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., -20.], [140., -20.], [180., -40.], [-180., -30.], [-110., -20.]]]]})
        both = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., 20.], [140., -20.], [180., -40.], [-180., -30.], [-110., 20.]]]]})
        self.assertFalse(calc.covers(north))
        self.assertTrue(calc.covers(south))
        self.assertFalse(calc.covers(both))

        identical = shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -90.], [180., -90.], [180., 0.], [-180., 0.], [-180., -90.]]]]})
        self.assertTrue(calc.covers(identical))


class TestEOEmissionCalculator(EOEmissionCalculator):

    def __init__(self):
        super().__init__()

    @staticmethod
    def minimum_area_size() -> int:
        return 0

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -90.], [180., -90.], [180., 0.], [-180., 0.], [-180., -90.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 0

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat("0001-01-01")

    @staticmethod
    def latest_end_date() -> date:
        return date.fromisoformat("9999-12-31")

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant is not None

    def run(self, region=None, period=None, pollutant=None) -> dict:
        return 42


if __name__ == '__main__':
    unittest.main()
