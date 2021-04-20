# -*- coding: utf-8 -*-
"""Emission calculators based on TEMIS data (temis.nl)"""

from datetime import date, timedelta

from shapely.geometry import MultiPolygon, shape
import geopandas

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator, DateRange


class TEMISTropomiMonthlyMeanNOxEmissionCalculator(EOEmissionCalculator):

    @staticmethod
    def minimum_area_size() -> int:
        return 10**5

    @staticmethod
    def coverage() -> MultiPolygon:
        return shape({'type': 'MultiPolygon',
                      'coordinates': [[[[-180., -60.], [180., -60.], [180., 60.], [-180., 60.], [-180., -60.]]]]})

    @staticmethod
    def minimum_period_length() -> int:
        return 1

    @staticmethod
    def earliest_start_date() -> date:
        return date.fromisoformat('2018-02-01')

    @staticmethod
    def latest_end_date() -> date:
        return (date.today().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def supports(pollutant: Pollutant) -> bool:
        return pollutant == Pollutant.NOx

    def run(self, region: MultiPolygon, period: DateRange, pollutant: Pollutant) -> dict:

        grid = {
            "type": "FeatureCollection",
            "features": []
        }

        bin_width = 0.125
        min_long = region.bounds[0] - region.bounds[0] % bin_width
        min_lat = region.bounds[1] - region.bounds[1] % bin_width
        max_long = region.bounds[2] + bin_width - (region.bounds[2] % bin_width)
        max_lat = region.bounds[3] + bin_width - (region.bounds[3] % bin_width)
        for long in (min_long + x * bin_width for x in range(int((max_long - min_long) / bin_width) + 1)):
            for lat in (min_lat + y * bin_width for y in range(int((max_lat - min_lat) / bin_width) + 1)):
                grid["features"].append({
                    "type": "Feature",
                    "properties": {"center": f"{lat + bin_width / 2}/{long + bin_width / 2}"},
                    "geometry": {"type": "Polygon", "coordinates": [
                        [(long, lat), (long + bin_width, lat), (long + bin_width, lat + bin_width),
                         (long, lat + bin_width), (long, lat)]]},
                })

        grid_result = geopandas.GeoDataFrame.from_features(grid, crs="EPSG:4326")

        for day in range((period.end - period.start).days + 1):
            grid_result[f"{period.start + timedelta(days=day)}"] = day

        grid_result["SUM"] = grid_result.sum(axis=1, numeric_only=True)
        grid_result = geopandas.overlay(grid_result, geopandas.GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')

        return {
            EOEmissionCalculator.TOTAL_EMISSIONS_KEY: grid_result["SUM"].sum(),
            EOEmissionCalculator.GRIDDED_EMISSIONS_KEY: grid_result
        }
