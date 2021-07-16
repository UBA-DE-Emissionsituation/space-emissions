# -*- coding: utf-8 -*-
import json
import os

import geopandas as gpd
from bokeh.layouts import row
from bokeh.models import GeoJSONDataSource, LogColorMapper
from bokeh.palettes import RdYlGn11
from bokeh.plotting import figure, curdoc
from bokeh.tile_providers import OSM, get_provider
from shapely.geometry import shape

from controls import ControlPanel
from eocalc.context import Pollutant
from eocalc.methods.base import DateRange
from eocalc.methods.fluky import RandomEOEmissionCalculator


def region_selection_handler(event):
    global selected_region, controls

    selected_region = os.path.join(os.path.dirname(__file__), "regions", f"{event.item}.geo.json")
    region = gpd.read_file(selected_region).to_crs(epsg='3857')
    controls.label_region.text = f"<p>{event.item}</p>"  # TODO Use proper label
    map_control.patches('xs', 'ys', source=GeoJSONDataSource(geojson=region.to_json()), color='black', alpha=0.3)

    map_control.x_range.start = region.total_bounds[0]
    map_control.x_range.end = region.total_bounds[2]
    map_control.y_range.start = region.total_bounds[1]
    map_control.y_range.end = region.total_bounds[3]


def pollutant_selection_handler(event):
    global selected_pollutant, controls

    controls.label_pollutant.text = f"<p>{event.item}</p>"  # TODO Use proper label


def run_method_handler(event):
    global controls

    with open(selected_region, 'r') as geojson_file:
        region = shape(json.load(geojson_file)["geometry"])
    period = DateRange("2020-01-01", "2020-12-31")
    pollutant = Pollutant.NO2
    results = RandomEOEmissionCalculator().run(region, period, pollutant)

    grid = results[RandomEOEmissionCalculator.GRIDDED_EMISSIONS_KEY].to_crs(epsg='3857')
    map_control.patches('xs', 'ys', source=GeoJSONDataSource(geojson=grid.to_json()),
                        fill_color={'field': 'Total NO2 emissions [kg]', 'transform': LogColorMapper(palette=RdYlGn11)},
                        color='black', alpha=0.3)

    controls.result.text = results[RandomEOEmissionCalculator.TOTAL_EMISSIONS_KEY].to_html()


selected_region: str = None
selected_pollutant: Pollutant = None

map_control = figure(x_range=(-9_000_000, 9_000_000), y_range=(-9_000_000, 9_000_000),
                     x_axis_type="mercator", y_axis_type="mercator", sizing_mode="stretch_both")
map_control.add_tile(get_provider(OSM))

controls = ControlPanel(region_selection_handler, pollutant_selection_handler, run_method_handler)

curdoc().add_root(row(controls.layout(), map_control, sizing_mode="stretch_height"))
