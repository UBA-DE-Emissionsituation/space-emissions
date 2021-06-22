# -*- coding: utf-8 -*-
import pytest
import json
import os
from datetime import date, timedelta

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.naive import TropomiMonthlyMeanAggregator, LOCAL_DATA_FOLDER

from eocalc.tests.test_base import region_sample_north, region_sample_south, region_sample_span_equator


@pytest.fixture
def calc():
    return TropomiMonthlyMeanAggregator()


@pytest.fixture
def region_germany():
    with open("data/regions/germany.geo.json", 'r') as geojson_file:
        return shape(json.load(geojson_file)["geometry"])


@pytest.fixture
def region_saxony():
    with open("data/regions/roughly_saxonia.geo.json", 'r') as geojson_file:
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

    @pytest.mark.parametrize("region", ["region_sample_north", "region_sample_south", "region_sample_span_equator"])
    def test_covers_simple(self, calc, region, request):
        assert calc.covers(request.getfixturevalue(region))

    @pytest.mark.parametrize("json_file, result", [
        ("adak-left.geo.json", False), ("adak-right.geo.json", False),
        ("alps_and_po_valley.geo.json", True), ("europe.geo.json", True),
        ("germany.geo.json", True), ("guinea_and_gabon.geo.json", True),
        ("portugal_envelope.geo.json", True), ("roughly_saxonia.geo.json", True)
    ])
    def test_covers_sample_region_from_json(self, calc, json_file, result):
        with open(f"data/regions/{json_file}", 'r') as geojson_file:
            assert result == calc.covers(shape(json.load(geojson_file)["geometry"]))

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

    def test_run_germany(self, calc, region_germany):
        result = calc.run(region_germany, DateRange(start='2018-08-01', end='2018-08-31'), Pollutant.NO2)
        assert 22.5 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 22.6
        assert 3.49 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 3.5
        assert 3.49 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 3.5

    def test_run_saxony(self, calc, region_saxony):
        result = calc.run(region_saxony, DateRange(start='2020-02-10', end='2020-02-10'), Pollutant.NO2)
        assert 0.04 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 0.05
        assert 71 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 72
        assert 71 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 72

        result = calc.run(region_saxony, DateRange(start='2020-02-29', end='2020-03-01'), Pollutant.NO2)
        assert 0.09 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 0.1
        assert 50 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 51
        assert 50 <= result[calc.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 51

    @pytest.mark.parametrize("file, region, result", [
        ("clipped_data_file_name", "region_small_but_well_known", [133, 186, 189, 304, 272, 294]),
        ("clipped_data_file_name", "region_small_but_well_known_other", [30]),
        ("clipped_data_file_name", "region_small_but_well_known_third", [69, 60])
    ])
    def test_read_toms_data(self, calc, file, region, result, request):
        assert result == calc._read_toms_data(request.getfixturevalue(region), request.getfixturevalue(file))

    def test_assure_data_availability(self, calc):
        day = date.fromisoformat("2018-09-15")
        file = calc._assure_data_availability(day)
        assert f"{LOCAL_DATA_FOLDER}/no2_201809.asc" == file

        os.remove(file)
        assert f"{LOCAL_DATA_FOLDER}/no2_201809.asc" == calc._assure_data_availability(day)
