# -*- coding: utf-8 -*-
import pytest

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.fluky import RandomEOEmissionCalculator

from eocalc.tests.test_base import region_sample_north, region_sample_south, region_sample_span_equator


@pytest.fixture
def calc():
    return RandomEOEmissionCalculator()


@pytest.fixture
def region():
    return shape({"type": "Polygon",
                  "coordinates": [[[-122., 37.], [-125., 37.], [-125., 38.], [-122., 38.], [-122., 37.]]]})


@pytest.fixture
def period():
    return DateRange("2020-01-01", "2020-12-31")


class TestRandomMethods:

    def test_minimum_area(self, calc):
        assert 1 == calc.minimum_area_size()

    def test_covers(self, calc, region_sample_north, region_sample_south, region_sample_span_equator):
        assert calc.covers(region_sample_north)
        assert calc.covers(region_sample_south)
        assert calc.covers(region_sample_span_equator)

    def test_minimum_period(self, calc):
        assert 1 == calc.minimum_period_length()

    def test_supports(self, calc):
        for p in Pollutant:
            assert calc.supports(p)

        assert not calc.supports(None)

    def test_run(self, calc, region, period):
        for p in Pollutant:
            results = calc.run(region, period, p)
            assert results[calc.TOTAL_EMISSIONS_KEY] is not None
            assert results[calc.GRIDDED_EMISSIONS_KEY] is not None

        with pytest.raises(AttributeError):
            calc.run(region, period, None)
