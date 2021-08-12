# -*- coding: utf-8 -*-
import os
import pytest
import inspect

from requests import HTTPError

from eocalc.methods.base import DateRange
from eocalc.tools.downloadtools import input_check_period,input_check_path,input_check_era_lvl,era5_download

class TestInputs:
    def test_invalid_period(self):
        with pytest.raises(TypeError):
            input_check_period()
        with pytest.raises(TypeError):
            input_check_period(None)
        with pytest.raises(ValueError):
            input_check_period([1,2,3])

    def test_valid_period(self):
            assert None == input_check_period(DateRange(end="2016-01-03", start="2016-01-02"))
            assert None == input_check_period(["2016-01-02","2016-01-03"])

    def test_invalid_path(self):
        with pytest.raises(TypeError):
            input_check_path([1,2,3])

    def test_valid_path(self):
        assert os.path.join(os.path.split(inspect.getfile(input_check_path))[0],'data') in input_check_path(None, makedir=False)
        assert os.getcwd() in input_check_path(os.getcwd(), makedir=False)
        assert 'my/test/path' in input_check_path('my/test/path', makedir=False)

    def test_invalid_era_lvl(self):
        with pytest.raises(ValueError):
            input_check_era_lvl('-10')
        with pytest.raises(ValueError):
            input_check_era_lvl(-10)
        with pytest.raises(ValueError):
            input_check_era_lvl([-10, 100, 800])
        with pytest.raises(ValueError):
            input_check_era_lvl(['-10', '100', 800])
        with pytest.raises(ValueError):
            input_check_era_lvl([1e8])
        with pytest.raises(ValueError):
            input_check_era_lvl(1e8)
        with pytest.raises(TypeError):
            input_check_era_lvl("Alice")
        with pytest.raises(ValueError):
            input_check_era_lvl([100,"Alice"])

    def test_valid_input_era_lvl(self):
        assert '100.0' == input_check_era_lvl(100)[0]
        assert '100.0' == input_check_era_lvl('100')[0]
        assert ['100.0','200.0'] == input_check_era_lvl([100,200])
        assert ["1000.0", "950.0"] == input_check_era_lvl()
        assert ["1000.0", "950.0"] == input_check_era_lvl([1000,950])
        assert ["123.45"] == input_check_era_lvl(123.45)
        assert ["123.45"] == input_check_era_lvl('123.45')
        assert ["123.45"] == input_check_era_lvl(['123.45'])
        assert ["123.45"] == input_check_era_lvl([123.45])

class TestDownload:
    def bad_connect_s5p_download(self):
        with pytest.raises(Exception):
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"),apikey = '123', replace=False)
        with pytest.raises(Exception) as excinfo:
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"),apikey = '123', replace=False)
        assert "401" in str(excinfo.value) #bad api

    def bad_connect_era_download(self):
        with pytest.raises(Exception):
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"),apikey = '123', replace=False)
        with pytest.raises(Exception) as excinfo:
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"),apikey = '123', replace=False)
        assert "401" in str(excinfo.value) #bad api


    def succesful_test_era_download(self):
        assert None == era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"), replace=False)
