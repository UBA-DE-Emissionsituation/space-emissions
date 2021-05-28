# -*- coding: utf-8 -*-
import pytest
import json
from datetime import date, timedelta

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.naive import TropomiMonthlyMeanAggregator

from eocalc.tests.test_base import region_sample_north, region_sample_south, region_sample_span_equator


@pytest.fixture
def calc():
    return TropomiMonthlyMeanAggregator()


@pytest.fixture
def region_germany():
    with open("data/regions/germany.geo.json", 'r') as geojson_file:
        return shape(json.load(geojson_file)["geometry"])


@pytest.fixture
def region_europe():
    with open("data/regions/europe.geo.json", 'r') as geojson_file:
        return shape(json.load(geojson_file)["geometry"])


@pytest.fixture
def clipped_data_file_name():
    return "data/methods/temis/tropomi/no2/monthly_mean/no2_201808_clipped.asc"


@pytest.fixture
def region_small_but_well_known():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-122.245, 37.188], [-122.245, 37.438], [-122.12, 37.438]]]]})


@pytest.fixture
def region_small_but_well_known_other():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[-179.99, 37.188], [-179.995, 37.188], [-179.995, 37.187]]]]})


@pytest.fixture
def region_small_but_well_known_third():
    return shape({"type": "MultiPolygon",
                  "coordinates": [[[[179.79, 47.188], [179.995, 47.188], [179.995, 47.187]]]]})


class TestTropomiMonthlyMeanAggregatorMethods:

    def test_covers_simple(self, calc, region_sample_north, region_sample_south, region_sample_span_equator):
        assert calc.covers(region_sample_north)
        assert calc.covers(region_sample_south)
        assert calc.covers(region_sample_span_equator)

    def test_covers_sample_region_from_json(self, calc):
        with open("data/regions/adak-left.geo.json", 'r') as geojson_file:
            assert not calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/adak-right.geo.json", 'r') as geojson_file:
            assert not calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/alps_and_po_valley.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/europe.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/germany.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/guinea_and_gabon.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/portugal_envelope.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))
        with open("data/regions/roughly_saxonia.geo.json", 'r') as geojson_file:
            assert calc.covers(shape(json.load(geojson_file)["geometry"]))

    def test_end_date(self):
        def go_to_end_of_previous_month(day):
            return (day.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1)

        assert date.fromisoformat("2021-02-28") == go_to_end_of_previous_month(date.fromisoformat("2021-04-19"))
        assert date.fromisoformat("2020-11-30") == go_to_end_of_previous_month(date.fromisoformat("2021-01-01"))
        assert date.fromisoformat("2021-03-31") == go_to_end_of_previous_month(date.fromisoformat("2021-05-31"))

    def test_supports(self, calc):
        for p in Pollutant:
            assert calc.supports(p) if p == Pollutant.NO2 else not calc.supports(p)

        assert not calc.supports(None)

    def test_run(self, calc, region_germany, region_europe):
        result = calc.run(region_germany, DateRange(start='2018-08-01', end='2018-08-31'), Pollutant.NO2)
        assert 22.5 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 22.6
        assert 3.49 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 3.5
        assert 3.49 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 3.5

        result = calc.run(region_europe, DateRange(start='2020-02-10', end='2020-02-25'), Pollutant.NO2)
        assert 187 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 188
        assert 1 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 1.1
        assert 1 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 1.1

    def test_read_toms_data(self, calc, clipped_data_file_name, region_small_but_well_known,
                            region_small_but_well_known_other, region_small_but_well_known_third):
        assert [133, 186, 189, 304, 272, 294] == \
               calc._read_toms_data(region_small_but_well_known, clipped_data_file_name)
        assert [30] == calc._read_toms_data(region_small_but_well_known_other, clipped_data_file_name)
        assert [69, 60] == calc._read_toms_data(region_small_but_well_known_third, clipped_data_file_name)
