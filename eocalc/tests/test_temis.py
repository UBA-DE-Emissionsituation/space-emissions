# -*- coding: utf-8 -*-
import unittest
from datetime import date, timedelta

from eocalc.context import Pollutant
from eocalc.methods.temis import TEMISTropomiMonthlyMeanNOxEmissionCalculator


class TestTEMISTropomiMonthlyMeanNOxMethods(unittest.TestCase):

    def test_end_date(self):
        now = date.fromisoformat("2021-04-19")
        end = date.fromisoformat("2021-02-28")

        self.assertEqual(end, (now.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1))

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(p)) if p == Pollutant.NOx else \
                        self.assertFalse(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(p))
        self.assertFalse(TEMISTropomiMonthlyMeanNOxEmissionCalculator.supports(None))
