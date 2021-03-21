# -*- coding: utf-8 -*-
import unittest

from eocalc.context import Pollutant
from eocalc.methods.dummy import DummyEOEmissionCalculator

class TestDummyMethods(unittest.TestCase):

    def test_minimum_area(self):
        self.assertEqual(0, DummyEOEmissionCalculator().minimum_area_size())
        
    def test_minimum_period(self):
        self.assertEqual(0, DummyEOEmissionCalculator().minimum_period_length())

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(DummyEOEmissionCalculator().supports(p))

    def test_run(self):
        self.assertEqual(42, DummyEOEmissionCalculator().run())

if __name__ == '__main__':
    unittest.main()