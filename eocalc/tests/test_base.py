# -*- coding: utf-8 -*-
import unittest
import pytest
from datetime import date

import numpy
from pandas import Series
from shapely.geometry import MultiPolygon, shape

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import DateRange, EOEmissionCalculator


class TestDataRange:

    @pytest.fixture
    def year_2019_from_strs(self):
        return DateRange("2019-01-01", "2019-12-31")

    @pytest.fixture
    def year_2019_from_dates(self):
        return DateRange(date.fromisoformat("2019-01-01"), date.fromisoformat("2019-12-31"))

    @pytest.fixture
    def year_2020(self):
        return DateRange("2020-01-01", "2020-12-31")

    @pytest.fixture
    def year_2020_other(self):
        return DateRange("2020-01-01", "2020-12-31")

    @pytest.fixture
    def august_2018(self):
        return DateRange("2018-08-01", "2018-08-31")

    @pytest.fixture
    def one_day(self):
        return DateRange("2018-08-01", "2018-08-01")

    def test_equals(self, year_2019_from_strs, year_2019_from_dates, year_2020, year_2020_other):
        assert year_2019_from_strs == DateRange(end="2019-12-31", start="2019-01-01")
        assert year_2019_from_dates == DateRange(end="2019-12-31", start="2019-01-01")
        assert year_2020 != DateRange(end="2019-12-31", start="2019-01-01")
        assert year_2020 != year_2019_from_dates
        assert year_2020 != year_2019_from_strs
        assert year_2020 == year_2020_other

    def test_period_length(self, year_2019_from_dates, year_2020, august_2018, one_day):
        assert 365 == len(year_2019_from_dates)
        assert 366 == len(year_2020)
        assert 31 == len(august_2018)
        assert 1 == len(one_day)

    def test_to_string(self, year_2019_from_strs):
        assert str(year_2019_from_strs) == "[2019-01-01 to 2019-12-31, 365 days]"

    def test_hash(self, year_2019_from_dates, year_2020, year_2020_other):
        assert hash(year_2019_from_dates) != hash(year_2020)
        assert hash(year_2020) == hash(year_2020_other)

    def test_iter(self, august_2018):
        count = 0
        for _ in august_2018:
            count += 1

        assert 31 == count

    def test_invalid_init_input(self):
        with pytest.raises(TypeError):
            DateRange()
        with pytest.raises(TypeError):
            DateRange(1, "")
        with pytest.raises(ValueError):
            DateRange(end="alice", start="bob")

    def test_bad_period(self):
        with pytest.raises(ValueError):
            DateRange(start="2019-01-01", end="2018-12-31")
        with pytest.raises(ValueError):
            DateRange(start="2019-01-01", end="2019-12-31").end = "2018-12-31"
        with pytest.raises(ValueError):
            DateRange(start="2019-01-01", end="2019-12-31").start = "2020-12-31"


class TestBaseMethods(unittest.TestCase):

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

    def test_validate(self):
        calc = TestEOEmissionCalculator()
        region_covered = shape({'type': 'MultiPolygon', 'coordinates': [[[[0., 0.], [0., -1.], [-1., -1.], [-1., 0.], [0., 0.]]]]})
        valid_period = DateRange("2019-01-01", "2019-12-31")
        valid_pollutant = Pollutant.NH3

        calc._validate(region_covered, valid_period, valid_pollutant)

        # Validate region
        region_not_covered = shape({'type': 'MultiPolygon', 'coordinates': [[[[0., 0.], [0., 1.], [1., 1.], [1., 0.], [0., 0.]]]]})
        region_too_small = shape({'type': 'MultiPolygon', 'coordinates': [[[[0., 0.], [0., -.001], [-.001, -.001], [-.001, 0.], [0., 0.]]]]})

        with self.assertRaises(ValueError):
            calc._validate(region_not_covered, valid_period, valid_pollutant)
        with self.assertRaises(ValueError):
            calc._validate(region_too_small, valid_period, valid_pollutant)

        # Validate region
        with self.assertRaises(ValueError):
            calc._validate(region_covered, DateRange("0000-01-01", "2019-12-31"), valid_pollutant)
        with self.assertRaises(ValueError):
            calc._validate(region_covered, DateRange("2000-01-01", "9999-12-31"), valid_pollutant)
        with self.assertRaises(ValueError):
            calc._validate(region_covered, DateRange("0000-01-01", "9999-12-31"), valid_pollutant)
        with self.assertRaises(ValueError):
            calc._validate(region_covered, DateRange("2100-01-01", "2100-01-31"), valid_pollutant)

        # Validate pollutant
        with self.assertRaises(ValueError):
            calc._validate(region_covered, valid_period, Pollutant.NO2)

    def test_create_gnfr_frame(self):
        for p in Pollutant:
            frame = EOEmissionCalculator._create_gnfr_table(p)
            self.assertEqual(len(GNFR) + 1, len(frame))
            self.assertEqual(3, len(frame.columns))
            self.assertEqual("A_PublicPower", frame.iloc[0].name.name)
            self.assertEqual("Totals", frame.iloc[-1].name)
            self.assertTrue(frame.iloc[:, 0].name.startswith(p.name))
            self.assertTrue(frame.iloc[:, 1].name.startswith("Umin"))
            self.assertTrue(frame.iloc[:, 2].name.startswith("Umax"))

    def test_combine_uncertainties(self):
        self.assertEqual(2, EOEmissionCalculator._combine_uncertainties(Series([10]), Series([2])))
        self.assertEqual(((10*2)**2+(10*4)**2)**0.5/20, EOEmissionCalculator._combine_uncertainties(Series([10, 10]), Series([2, 4])))
        self.assertEqual(((10*2)**2+(10*4)**2)**0.5/20, EOEmissionCalculator._combine_uncertainties(Series([10, -10]), Series([-2, 4])))
        self.assertEqual(((10*2)**2+(5*4)**2)**0.5/15, EOEmissionCalculator._combine_uncertainties(Series([-10, -5]), Series([-2, -4])))
        self.assertEqual(((10*3)**2+(5*3)**2)**0.5/15,
                         EOEmissionCalculator._combine_uncertainties(Series([-10, -5]), Series(3 for _ in range(2))))

        self.assertEqual(2, EOEmissionCalculator._combine_uncertainties(Series([10], index=['A']), Series([2], index=['A'])))
        self.assertEqual(2, EOEmissionCalculator._combine_uncertainties(Series([10], index=['A']), Series([2], index=['B'])))

        self.assertEqual(((10 * 2) ** 2 + (10 * 4) ** 2) ** 0.5 / 20,
                         EOEmissionCalculator._combine_uncertainties(Series([10, numpy.nan, 10]), Series([2, 3, 4])))
        self.assertEqual(((10 * 2) ** 2) ** 0.5 / 10,
                         EOEmissionCalculator._combine_uncertainties(Series([10, numpy.nan, numpy.nan]), Series([2, 3, 4])))
        self.assertEqual(0, EOEmissionCalculator._combine_uncertainties(Series([numpy.nan, numpy.nan, numpy.nan]), Series([2, 3, 4])))

        self.assertEqual(0, EOEmissionCalculator._combine_uncertainties(Series([]), Series([])))
        self.assertEqual(0, EOEmissionCalculator._combine_uncertainties(Series([]), Series([2])))
        self.assertEqual(((10 * 2) ** 2 + (20 * 3) ** 2) ** 0.5 / 30,
                         EOEmissionCalculator._combine_uncertainties(Series([10, 20]), Series([2, 3, 4])))
        with self.assertRaises(ValueError):
            EOEmissionCalculator._combine_uncertainties(Series([10, 20]), Series([2]))
        with self.assertRaises(ValueError):
            EOEmissionCalculator._combine_uncertainties(Series([10, 20]), Series([2, numpy.nan]))

    def test_create_grid(self):
        box = shape(dict(type='MultiPolygon', coordinates=[[[[0., 0.], [0., 1.], [1., 1.], [1., 0.], [0., 0.]]]]))

        self.assertEqual(1, len(EOEmissionCalculator._create_grid(box, 10, 10, snap=False)))
        self.assertEqual(1, len(EOEmissionCalculator._create_grid(box, 2, 2, snap=False)))
        self.assertEqual(1, len(EOEmissionCalculator._create_grid(box, 1, 1, snap=False)))
        self.assertEqual(1, len(EOEmissionCalculator._create_grid(box, 1, 1, snap=True)))
        self.assertEqual(2, len(EOEmissionCalculator._create_grid(box, 0.5, 1, snap=False)))
        self.assertEqual(2, len(EOEmissionCalculator._create_grid(box, 1, 0.5, snap=True)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(box, 0.5, 0.5, snap=False)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(box, 0.5, 0.5, snap=True)))
        self.assertEqual(16, len(EOEmissionCalculator._create_grid(box, 0.3, 0.3, snap=True)))
        self.assertEqual(16, len(EOEmissionCalculator._create_grid(box, 0.3, 0.3, snap=False)))

        other = shape(dict(type='MultiPolygon',
                           coordinates=[[[[-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]]]]))

        self.assertEqual(1, len(EOEmissionCalculator._create_grid(other, 10, 10, snap=False)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(other, 10, 10, snap=True)))
        self.assertEqual(1, len(EOEmissionCalculator._create_grid(other, 2, 2, snap=False)))
        self.assertEqual(1, len(EOEmissionCalculator._create_grid(other, 1, 1, snap=False)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(other, 1, 1, snap=True)))
        self.assertEqual(2, len(EOEmissionCalculator._create_grid(other, 0.5, 1, snap=False)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(other, 1, 0.5, snap=True)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(other, 0.5, 0.5, snap=False)))
        self.assertEqual(4, len(EOEmissionCalculator._create_grid(other, 0.5, 0.5, snap=True)))
        self.assertEqual(16, len(EOEmissionCalculator._create_grid(other, 0.3, 0.3, snap=True)))
        self.assertEqual(16, len(EOEmissionCalculator._create_grid(other, 0.3, 0.3, snap=False)))

        third = shape(dict(type='MultiPolygon',
                           coordinates=[[[[-202, -90], [-202, 22], [301, 22], [301, -90], [-202, -90]]]]))

        self.assertEqual(51*12, len(EOEmissionCalculator._create_grid(third, 10, 10, snap=False)))
        self.assertEqual(52*12, len(EOEmissionCalculator._create_grid(third, 10, 10, snap=True)))
        self.assertEqual(11*12, len(EOEmissionCalculator._create_grid(third, 50, 10, snap=False)))
        self.assertEqual(12*12, len(EOEmissionCalculator._create_grid(third, 50, 10, snap=True)))

        fourth = shape(dict(type='MultiPolygon',
                           coordinates=[[[[-122.255, 37.188], [-122.255, 37.438], [-122.38, 37.438]]]]))
        self.assertEqual(2, len(EOEmissionCalculator._create_grid(fourth, 0.125, 0.125, snap=False)))
        self.assertEqual(6, len(EOEmissionCalculator._create_grid(fourth, 0.125, 0.125, snap=True)))


class TestEOEmissionCalculator(EOEmissionCalculator):

    def __init__(self):
        super().__init__()

    @staticmethod
    def minimum_area_size() -> int:
        return 42

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -90.], [180., -90.], [180., 0.], [-180., 0.], [-180., -90.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 42

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat("1000-01-01")

    @staticmethod
    def latest_end_date() -> date:
        return date.fromisoformat("2999-12-31")

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant == Pollutant.NH3

    def run(self, region=None, period=None, pollutant=None) -> dict:
        return 42


if __name__ == '__main__':
    unittest.main()
