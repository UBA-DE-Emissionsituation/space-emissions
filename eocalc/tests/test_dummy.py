# -*- coding: utf-8 -*-
import pytest

from eocalc.context import Pollutant
from eocalc.methods.dummy import DummyEOEmissionCalculator

from eocalc.tests.test_base import region_sample_north, region_sample_south, region_sample_span_equator


@pytest.fixture
def calc():
    return DummyEOEmissionCalculator()


class TestDummyMethods:

    def test_minimum_area(self, calc):
        assert 0 == calc.minimum_area_size()

    def test_covers(self, calc, region_sample_south, region_sample_north, region_sample_span_equator):
        assert calc.covers(region_sample_north)
        assert calc.covers(region_sample_south)
        assert calc.covers(region_sample_span_equator)

    def test_minimum_period(self, calc):
        assert 0 == calc.minimum_period_length()

    def test_supports(self, calc):
        for p in Pollutant:
            assert calc.supports(p)

    def test_run(self, calc):
        assert 42 == calc.run()
