# -*- coding: utf-8 -*-
import unittest

from eocalc.context import Pollutant
from eocalc.methods.dummy import DummyEOEmissionCalculator

class TestDummyMethods(unittest.TestCase):

    def test_supports(self):
        for p in Pollutant:
            self.assertTrue(DummyEOEmissionCalculator().supports(p))

    def test_run(self):
        self.assertEqual(42, DummyEOEmissionCalculator().run())

if __name__ == '__main__':
    unittest.main()