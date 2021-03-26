# -*- coding: utf-8 -*-
import unittest

from eocalc.tests.test_base import TestBaseMethods
from eocalc.tests.test_dummy import TestDummyMethods
from eocalc.tests.test_random import TestRandomMethods


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestBaseMethods))
    test_suite.addTest(unittest.makeSuite(TestDummyMethods))
    test_suite.addTest(unittest.makeSuite(TestRandomMethods))
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
