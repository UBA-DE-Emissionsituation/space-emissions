# -*- coding: utf-8 -*-
import unittest
import json
from datetime import date, timedelta

from shapely.geometry import shape

from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.naive import TropomiMonthlyMeanAggregator


class TestTropomiMonthlyMeanAggregatorMethods(unittest.TestCase):

    def test_covers(self):
        calc = TropomiMonthlyMeanAggregator()
        north = shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-110., 20.], [140., 20.], [180., 40.], [-180., 30.], [-110., 20.]]]]})
        south = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., -20.], [140., -20.], [180., -40.], [-180., -30.], [-110., -20.]]]]})
        both = shape({'type': 'MultiPolygon',
                       'coordinates': [[[[-110., 20.], [140., -20.], [180., -40.], [-180., -30.], [-110., 20.]]]]})
        self.assertTrue(calc.covers(north))
        self.assertTrue(calc.covers(south))
        self.assertTrue(calc.covers(both))

        with open("data/regions/adak-left.geo.json", 'r') as geojson_file:
            self.assertFalse(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/adak-right.geo.json", 'r') as geojson_file:
            self.assertFalse(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/alps_and_po_valley.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/europe.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/germany.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/guinea_and_gabon.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/portugal_envelope.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))
        with open("data/regions/roughly_saxonia.geo.json", 'r') as geojson_file:
            self.assertTrue(calc.covers(shape(json.load(geojson_file)["geometry"])))

    def test_end_date(self):
        test = date.fromisoformat("2021-04-19")
        self.assertEqual(date.fromisoformat("2021-02-28"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

        test = date.fromisoformat("2021-01-01")
        self.assertEqual(date.fromisoformat("2020-11-30"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

        test = date.fromisoformat("2021-05-31")
        self.assertEqual(date.fromisoformat("2021-03-31"), (test.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(TropomiMonthlyMeanAggregator.supports(p)) if p == Pollutant.NO2 else \
                        self.assertFalse(TropomiMonthlyMeanAggregator.supports(p))
        self.assertFalse(TropomiMonthlyMeanAggregator.supports(None))

    def test_run(self):
        with open("data/regions/germany.geo.json", 'r') as geojson_file:
            germany = shape(json.load(geojson_file)["geometry"])

        result = TropomiMonthlyMeanAggregator().run(germany, DateRange(start='2018-08-01', end='2018-08-31'), Pollutant.NO2)
        self.assertTrue(22.5 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 22.6)
        self.assertTrue(3.49 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 3.5)
        self.assertTrue(3.49 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 3.5)

        with open("data/regions/europe.geo.json", 'r') as geojson_file:
            europe = shape(json.load(geojson_file)["geometry"])

        result = TropomiMonthlyMeanAggregator().run(europe, DateRange(start='2020-02-10', end='2020-02-25'), Pollutant.NO2)
        self.assertTrue(187 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 0] <= 188)
        self.assertTrue(1 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 1] <= 1.1)
        self.assertTrue(1 <= result[TropomiMonthlyMeanAggregator.TOTAL_EMISSIONS_KEY].iloc[-1, 2] <= 1.1)

    def test_read_toms_data(self):
        region = shape(dict(type='MultiPolygon',
                            coordinates=[[[[-122.245, 37.188], [-122.245, 37.438], [-122.12, 37.438]]]]))
        file = "data/methods/temis/tropomi/no2/monthly_mean/no2_201808_clipped.asc"

        self.assertEqual([133, 186, 189, 304, 272, 294], TropomiMonthlyMeanAggregator._read_toms_data(region, file))

        other = shape(dict(type='MultiPolygon',
                            coordinates=[[[[-179.99, 37.188], [-179.995, 37.188], [-179.995, 37.187]]]]))
        self.assertEqual([30], TropomiMonthlyMeanAggregator._read_toms_data(other, file))

        third = shape(dict(type='MultiPolygon',
                           coordinates=[[[[179.79, 47.188], [179.995, 47.188], [179.995, 47.187]]]]))
        self.assertEqual([69, 60], TropomiMonthlyMeanAggregator._read_toms_data(third, file))


if __name__ == '__main__':
    unittest.main()
