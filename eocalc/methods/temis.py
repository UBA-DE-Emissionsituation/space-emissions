# -*- coding: utf-8 -*-
"""Emission calculators based on TEMIS data (temis.nl)"""

from datetime import date, timedelta

from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon, shape
import geopandas

from eocalc.context import Pollutant
from eocalc.methods.base import EOEmissionCalculator, DateRange

bin_width = 0.125
values_per_row = 20


class TEMISTropomiMonthlyMeanNOxEmissionCalculator(EOEmissionCalculator):

    cache = {}

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

        grid = self._create_grid(region, 0.125, 0.125, snap=True, include_center_col=True)

        for day in range((period.end - period.start).days):
            grid[f"{period.start + timedelta(days=day)}"] = self.read_temis_data(region, period.start + timedelta(days=day))

        grid["total"] = grid.sum(axis=1, numeric_only=True)
        grid = geopandas.overlay(grid, GeoDataFrame({'geometry': [region]}, crs="EPSG:4326"), how='intersection')

        grid.insert(0, "area [km²]", grid.to_crs(epsg=5243).area / 10 ** 6)

        return {
            EOEmissionCalculator.TOTAL_EMISSIONS_KEY: grid["total"].sum(),
            EOEmissionCalculator.GRIDDED_EMISSIONS_KEY: grid
        }

    def read_temis_data(self, region: MultiPolygon, day: date) -> ():
        month = f"{day:%Y-%m}"
        if month not in self.cache.keys():
            self.cache[month] = self.read_temis_data_from_file(region, f"data/temis/no2_{day:%Y%m}.asc")

        return self.cache[month]

    @staticmethod
    def read_temis_data_from_file(region: MultiPolygon, filename: str) -> ():
        min_lat = region.bounds[1] - region.bounds[1] % bin_width
        max_lat = region.bounds[3] + bin_width - (region.bounds[3] % bin_width)
        min_long = region.bounds[0] - region.bounds[0] % bin_width
        max_long = region.bounds[2] + bin_width - (region.bounds[2] % bin_width)

        result = []

        with open(filename) as data:
            lat = -91
            for line in data:
                if line.startswith("lat="):
                    lat = float(line.split('=')[1]) - bin_width / 2
                    offset = -180  # We need to go from -180° to +180° for each latitude
                elif min_lat <= lat <= max_lat and line[:4].strip().lstrip('-').isdigit():
                    for count, long in enumerate(offset + x * bin_width for x in range(values_per_row)):
                        if min_long <= long <= max_long:
                            emission = int(line[count * 4:count * 4 + 4])  # All emission values are four digits wide
                            result += [emission] if emission >= 0 else [0]
                    offset += values_per_row * bin_width

        return result

    @staticmethod
    def _create_grid(region: MultiPolygon, width: float, height: float, snap: bool = False,
                     include_center_col: bool = False, crs: str = "EPSG:4326") -> GeoDataFrame:
        """
        Overlay given region with grid data frame. Each cell will be created as a row, starting
        at the bottom left and then moving up row by row. Thus, the last row will represent the
        top right corner cell of the grid.

        Parameters
        ----------
        region: MultiPolygon
            Area to cover.
        width: float
            Cell width [degrees].
        height: float
            Cell height [degrees].
        snap: bool
            Make grid corners snap. If true, the lower left corner of the lower left cell
            will have long % width == 0 and lat % height == 0. If false, region bounds will
            be used.
        include_center_col: bool
            Add column to data frame with cell center coordinates.
        crs: str
            CRS to set on the data frame.

        Returns
        -------
        GeoDataFrame
            Data frame with cell features spanning the full region. Will contain at least one row.
        """

        grid = {"type": "FeatureCollection", "features": []}
        # TODO Test this with region that spans the longitude -180/180
        min_lat = region.bounds[1] - region.bounds[1] % height if snap else region.bounds[1]
        max_lat = region.bounds[3] + height - (region.bounds[3] % height) if snap else region.bounds[3]
        min_long = region.bounds[0] - region.bounds[0] % width if snap else region.bounds[0]
        max_long = region.bounds[2] + width - (region.bounds[2] % width) if snap else region.bounds[2]
        for lat in (min_lat + y * height for y in range(int((max_lat - min_lat) / height) + 1)):
            for long in (min_long + x * width for x in range(int((max_long - min_long) / width) + 1)):
                grid["features"].append({
                    "type": "Feature",
                    "properties": {"center": f"{lat + height / 2}/{long + width / 2}"} if include_center_col else {},
                    "geometry": {"type": "Polygon", "coordinates": [
                        [(long, lat),
                         (long + width, lat),
                         (long + width, lat + height),
                         (long, lat + height),
                         (long, lat)]]}
                    })

        return geopandas.GeoDataFrame.from_features(grid, crs=crs)
