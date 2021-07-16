# -*- coding: utf-8 -*-
from datetime import date

from bokeh.layouts import layout
from bokeh.models import Div, Dropdown, Button, DateRangeSlider


class ControlPanel:

    def __init__(self, region_selection_handler, pollutant_selection_handler, run_method_handler):
        region_list = [("Germany", "germany"), ("Guinea and Gabon", "guinea_and_gabon"), ("New Zealand", "new_zealand")]

        self.dropdown_region = Dropdown(label="Select region", menu=region_list)
        self.dropdown_region.on_click(region_selection_handler)
        self.label_region = Div(text="<p>None</p>", sizing_mode="stretch_width")

        self.dropdown_pollutant = Dropdown(label="Select pollutant", menu=[("NO2", "no2"), ("SO2", "so2")])
        self.dropdown_pollutant.on_click(pollutant_selection_handler)
        self.label_pollutant = Div(text="<p>None</p>", sizing_mode="stretch_width")

        self.slider_period = DateRangeSlider(value=(date(2020, 1, 1), date(2020, 12, 31)),
                                             start=date(2018, 1, 1), end=date(2021, 12, 31),
                                             sizing_mode="stretch_width")

        self.run = Button(label="Run", button_type="success", sizing_mode="stretch_width")
        self.run.on_click(run_method_handler)

        # TODO Use something like data_table = DataTable(source=source, columns=columns, width=400, height=280)
        self.result = Div(text="<p>No results yet</p>", sizing_mode="stretch_both")

    def layout(self):
        return layout([
            [self.dropdown_region, self.label_region],
            [self.dropdown_pollutant, self.label_pollutant],
            [self.slider_period],
            [self.run],
            [self.result],
        ], width=450)
