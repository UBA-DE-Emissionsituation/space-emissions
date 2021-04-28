# -*- coding: utf-8 -*-
import unittest

from eocalc.tests.test_base import TestBaseMethods
from eocalc.tests.test_dummy import TestDummyMethods
from eocalc.tests.test_fluky import TestRandomMethods
from eocalc.tests.test_temis import TestTropomiMonthlyMeanAggregatorMethods


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestBaseMethods))
    test_suite.addTest(unittest.makeSuite(TestDummyMethods))
    test_suite.addTest(unittest.makeSuite(TestRandomMethods))
    test_suite.addTest(unittest.makeSuite(TestTropomiMonthlyMeanAggregatorMethods))
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
