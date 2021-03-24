# -*- coding: utf-8 -*-
import unittest

from eocalc.methods.base import DateRange


class TestBaseMethods(unittest.TestCase):

    def test_date_range(self):
        year2019 = DateRange("2019-01-01", "2019-12-31")
        year2020 = DateRange("2020-01-01", "2020-12-31")
        self.assertEqual(365, (year2019.end-year2019.start).days)
        self.assertEqual(366, (year2020.end-year2020.start).days)
        with self.assertRaises(AssertionError):
            DateRange("2019-01-01", "2018-12-31")


if __name__ == '__main__':
    unittest.main()
