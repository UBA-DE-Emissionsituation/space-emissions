# -*- coding: utf-8 -*-
import pytest
from datetime import date

import numpy
from pandas import Series
from shapely.geometry import MultiPolygon, shape

from eocalc.context import Pollutant, GNFR
from eocalc.methods.base import DateRange, EOEmissionCalculator


@pytest.fixture
def year_2019_from_strs():
    return DateRange("2019-01-01", "2019-12-31")


@pytest.fixture
def year_2019_from_dates():
    return DateRange(date.fromisoformat("2019-01-01"), date.fromisoformat("2019-12-31"))


@pytest.fixture
def year_2020():
    return DateRange("2020-01-01", "2020-12-31")


@pytest.fixture
def year_2020_other():
    return DateRange("2020-01-01", "2020-12-31")


@pytest.fixture
def august_2018():
    return DateRange("2018-08-01", "2018-08-31")


@pytest.fixture
def one_day():
    return DateRange("2018-08-01", "2018-08-01")


class TestDataRange:

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


@pytest.fixture
def calc():
    class MyEOEmissionCalculator(EOEmissionCalculator):

        @staticmethod
        def minimum_area_size() -> int:
            return 42

        @staticmethod
        def coverage() -> MultiPolygon:
            return shape({"type": "MultiPolygon",
                          "coordinates": [[[[-180., -90.], [180., -90.], [180., 0.], [-180., 0.], [-180., -90.]]]]})

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

        def run(self, region=None, period=None, pollutant=None):
            return 42

    return MyEOEmissionCalculator()


@pytest.fixture
def region_sample_south():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-110., -20.], [140., -20.], [180., -40.], [-180., -30.], [-110., -20.]]]]})


@pytest.fixture
def region_sample_north():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-110., 20.], [140., 20.], [180., 40.], [-180., 30.], [-110., 20.]]]]})


@pytest.fixture
def region_sample_span_equator():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-110., 20.], [140., -20.], [180., -40.], [-180., -30.], [-110., 20.]]]]})


@pytest.fixture
def region_clone_coverage():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-180., -90.], [180., -90.], [180., 0.], [-180., 0.], [-180., -90.]]]]})


@pytest.fixture
def region_other_covered():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[0., 0.], [0., -1.], [-1., -1.], [-1., 0.], [0., 0.]]]]})


@pytest.fixture
def region_other_not_covered():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[0., 0.], [0., 1.], [1., 1.], [1., 0.], [0., 0.]]]]})


@pytest.fixture
def region_too_small_but_covered():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[0., 0.], [0., -.001], [-.001, -.001], [-.001, 0.], [0., 0.]]]]})


@pytest.fixture
def region_box_north_of_equator():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[0., 0.], [0., 1.], [1., 1.], [1., 0.], [0., 0.]]]]})


@pytest.fixture
def region_box_span_equator():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]]]]})


@pytest.fixture
def region_far_out_at_the_date_line():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-202, -90], [-202, 22], [301, 22], [301, -90], [-202, -90]]]]})


@pytest.fixture
def region_small_but_well_known():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-122.255, 37.188], [-122.255, 37.438], [-122.38, 37.438]]]]})


@pytest.fixture
def period_supported():
    return DateRange("2019-01-01", "2019-12-31")


@pytest.fixture
def period_not_supported():
    return DateRange("0001-01-01", "2019-12-31")


@pytest.fixture
def period_not_supported_other():
    return DateRange("2000-01-01", "9999-12-31")


@pytest.fixture
def period_too_short():
    return DateRange("2100-01-01", "2100-01-31")


@pytest.fixture
def pollutant_supported():
    return Pollutant.NH3


@pytest.fixture
def pollutant_not_supported():
    return Pollutant.NO2


class TestCalcMethods:

    def test_covers(self, calc, region_sample_south, region_sample_north, region_sample_span_equator,
                    region_clone_coverage, region_other_covered, region_other_not_covered,
                    region_too_small_but_covered):
        assert not calc.covers(region_sample_north)
        assert not calc.covers(region_sample_span_equator)
        assert not calc.covers(region_other_not_covered)
        assert calc.covers(region_sample_south)
        assert calc.covers(region_clone_coverage)
        assert calc.covers(region_other_covered)
        assert calc.covers(region_too_small_but_covered)

    def test_validate_no_problem(self, calc, region_other_covered, period_supported, pollutant_supported):
        calc._validate(region_other_covered, period_supported, pollutant_supported)

    def test_validate_bad_region(self, calc, region_other_not_covered, region_too_small_but_covered,
                                 period_supported, pollutant_supported):
        with pytest.raises(ValueError):
            calc._validate(region_other_not_covered, period_supported, pollutant_supported)
        with pytest.raises(ValueError):
            calc._validate(region_too_small_but_covered, period_supported, pollutant_supported)

    def test_validate_bad_period(self, calc, region_other_covered, period_not_supported,
                                 period_not_supported_other, period_too_short, pollutant_supported):
        with pytest.raises(ValueError):
            calc._validate(region_other_covered, period_not_supported, pollutant_supported)
        with pytest.raises(ValueError):
            calc._validate(region_other_covered, period_not_supported_other, pollutant_supported)
        with pytest.raises(ValueError):
            calc._validate(region_other_covered, period_too_short, pollutant_supported)

    def test_validate_bad_pollutants(self, calc, region_other_covered, period_supported, pollutant_not_supported):
        with pytest.raises(ValueError):
            calc._validate(region_other_covered, period_supported, pollutant_not_supported)

    def test_validate_all_wrong(self, calc, region_other_not_covered, period_not_supported, pollutant_not_supported):
        with pytest.raises(ValueError):
            calc._validate(region_other_not_covered, period_not_supported, pollutant_not_supported)

    def test_create_gnfr_frame(self, calc):
        for pollutant in Pollutant:
            frame = calc._create_gnfr_table(pollutant)
            assert len(GNFR) + 1 == len(frame)
            assert 3 == len(frame.columns)
            assert "A_PublicPower" == frame.iloc[0].name.name
            assert "Totals" == frame.iloc[-1].name
            assert frame.iloc[:, 0].name.startswith(pollutant.name)
            assert frame.iloc[:, 1].name.startswith("Umin")
            assert frame.iloc[:, 2].name.startswith("Umax")

    def test_combine_uncertainties_simple(self, calc):
        assert 2 == calc._combine_uncertainties(Series([10]), Series([2]))
        assert 0 == calc._combine_uncertainties(Series([42, 15]), Series([0, 0]))
        assert ((10 * 2) ** 2 + (10 * 4) ** 2) ** 0.5 / 20 == \
               calc._combine_uncertainties(Series([10, 10]), Series([2, 4]))
        assert ((10 * 2) ** 2 + (10 * 4) ** 2) ** 0.5 / 20 == \
               calc._combine_uncertainties(Series([10, -10]), Series([-2, 4]))
        assert ((10 * 2) ** 2 + (5 * 4) ** 2) ** 0.5 / 15 == \
               calc._combine_uncertainties(Series([-10, -5]), Series([-2, -4]))
        assert ((10 * 3) ** 2 + (5 * 3) ** 2) ** 0.5 / 15 == \
               calc._combine_uncertainties(Series([-10, -5]), Series(3 for _ in range(2)))

    def test_combine_uncertainties_drop_index(self, calc):
        assert 2 == calc._combine_uncertainties(Series([10], index=['A']), Series([2], index=['A']))
        assert 2 == calc._combine_uncertainties(Series([10], index=['A']), Series([2], index=['B']))

    def test_combine_uncertainties_partly_nan(self, calc):
        assert ((10 * 2) ** 2 + (10 * 4) ** 2) ** 0.5 / 20 == \
               calc._combine_uncertainties(Series([10, numpy.nan, 10]), Series([2, 3, 4]))
        assert ((10 * 2) ** 2) ** 0.5 / 10 == \
               calc._combine_uncertainties(Series([10, numpy.nan, numpy.nan]), Series([2, 3, 4]))
        assert 0 == calc._combine_uncertainties(Series([numpy.nan, numpy.nan, numpy.nan]), Series([2, 3, 4]))

    def test_combine_uncertainties_partly_empty(self, calc):
        assert 0 == calc._combine_uncertainties(Series([]), Series([]))
        assert 0 == calc._combine_uncertainties(Series([]), Series([2]))

    def test_combine_uncertainties_series_lengths_do_not_match(self, calc):
        assert ((10 * 2) ** 2 + (20 * 3) ** 2) ** 0.5 / 30 == \
               calc._combine_uncertainties(Series([10, 20]), Series([2, 3, 4]))
        with pytest.raises(ValueError):
            calc._combine_uncertainties(Series([10, 20]), Series([2]))

    def test_combine_uncertainties_bad_uncertainties(self, calc):
        with pytest.raises(ValueError):
            calc._combine_uncertainties(Series([10, 20]), Series([2, numpy.nan]))

    def test_create_grid_simple(self, calc, region_box_north_of_equator):
        assert 1 == len(calc._create_grid(region_box_north_of_equator, 10, 10, snap=False))
        assert 1 == len(calc._create_grid(region_box_north_of_equator, 2, 2, snap=False))
        assert 1 == len(calc._create_grid(region_box_north_of_equator, 1, 1, snap=False))
        assert 1 == len(calc._create_grid(region_box_north_of_equator, 1, 1, snap=True))
        assert 2 == len(calc._create_grid(region_box_north_of_equator, 0.5, 1, snap=False))
        assert 2 == len(calc._create_grid(region_box_north_of_equator, 1, 0.5, snap=True))
        assert 4 == len(calc._create_grid(region_box_north_of_equator, 0.5, 0.5, snap=False))
        assert 4 == len(calc._create_grid(region_box_north_of_equator, 0.5, 0.5, snap=True))
        assert 16 == len(calc._create_grid(region_box_north_of_equator, 0.3, 0.3, snap=True))
        assert 16 == len(calc._create_grid(region_box_north_of_equator, 0.3, 0.3, snap=False))

    def test_create_grid_span_equator(self, calc, region_box_span_equator):
        assert 1 == len(calc._create_grid(region_box_span_equator, 10, 10, snap=False))
        assert 4 == len(calc._create_grid(region_box_span_equator, 10, 10, snap=True))
        assert 1 == len(calc._create_grid(region_box_span_equator, 2, 2, snap=False))
        assert 1 == len(calc._create_grid(region_box_span_equator, 1, 1, snap=False))
        assert 4 == len(calc._create_grid(region_box_span_equator, 1, 1, snap=True))
        assert 2 == len(calc._create_grid(region_box_span_equator, 0.5, 1, snap=False))
        assert 4 == len(calc._create_grid(region_box_span_equator, 1, 0.5, snap=True))
        assert 4 == len(calc._create_grid(region_box_span_equator, 0.5, 0.5, snap=False))
        assert 4 == len(calc._create_grid(region_box_span_equator, 0.5, 0.5, snap=True))
        assert 16 == len(calc._create_grid(region_box_span_equator, 0.3, 0.3, snap=True))
        assert 16 == len(calc._create_grid(region_box_span_equator, 0.3, 0.3, snap=False))

    def test_create_beyond_minus_180_degrees(self, calc, region_far_out_at_the_date_line):
        assert 51 * 12 == len(calc._create_grid(region_far_out_at_the_date_line, 10, 10, snap=False))
        assert 52 * 12 == len(calc._create_grid(region_far_out_at_the_date_line, 10, 10, snap=True))
        assert 11 * 12 == len(calc._create_grid(region_far_out_at_the_date_line, 50, 10, snap=False))
        assert 12 * 12 == len(calc._create_grid(region_far_out_at_the_date_line, 50, 10, snap=True))

    def test_create_grid_well_known(self, calc, region_small_but_well_known):
        assert 2 == len(calc._create_grid(region_small_but_well_known, 0.125, 0.125, snap=False))
        assert 6 == len(calc._create_grid(region_small_but_well_known, 0.125, 0.125, snap=True))
