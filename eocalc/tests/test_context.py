# -*- coding: utf-8 -*-
from eocalc.context import GNFR


class TestGNFREnum:
    def test_gnfr(self):
        for gnfr in GNFR:
            assert str(GNFR.L_AgriOther) == "L_AgriOther"
            assert str(gnfr) == gnfr.name
