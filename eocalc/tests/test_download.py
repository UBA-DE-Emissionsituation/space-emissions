# -*- coding: utf-8 -*-
import os
import pytest
import inspect

from requests import HTTPError

from eocalc.methods.base import DateRange, Pollutant
from eocalc.tools.download import _input_check_period, _input_check_path, _input_check_era_lvl, era5_download, satellite_download

class TestInputs:
    def test_invalid_period(self):
        with pytest.raises(TypeError):
            _input_check_period()
        with pytest.raises(ValueError):
            _input_check_period(None)
        with pytest.raises(ValueError):
            _input_check_period([1,2,3])

    def test_valid_period(self):
            assert True == _input_check_period(DateRange(end="2016-01-03", start="2016-01-02"))
            assert True == _input_check_period(["2016-01-02","2016-01-03"])
            #assert None == input_check_period("2016-01-02")

    def test_invalid_path(self):
        with pytest.raises(TypeError):
            _input_check_path([1,2,3])

    def test_valid_path(self):
        assert os.path.join(os.path.split(inspect.getfile(_input_check_path))[0],'data') in _input_check_path(None, makedir=False)
        assert os.getcwd() in _input_check_path(os.getcwd(), makedir=False)
        assert 'my/test/path' in _input_check_path('my/test/path', makedir=False)

    def test_invalid_era_lvl(self):
        with pytest.raises(ValueError):
            _input_check_era_lvl('-10')
        with pytest.raises(ValueError):
            _input_check_era_lvl(-10)
        with pytest.raises(ValueError):
            _input_check_era_lvl([-10, 100, 800])
        with pytest.raises(ValueError):
            _input_check_era_lvl(['-10', '100', 800])
        with pytest.raises(ValueError):
            _input_check_era_lvl([1e8])
        with pytest.raises(ValueError):
            _input_check_era_lvl(1e8)
        with pytest.raises(TypeError):
            _input_check_era_lvl("Alice")
        with pytest.raises(ValueError):
            _input_check_era_lvl([100,"Alice"])

    def test_valid_input_era_lvl(self):
        assert '100.0' == _input_check_era_lvl(100)[0]
        assert '100.0' == _input_check_era_lvl('100')[0]
        assert ['100.0','200.0'] == _input_check_era_lvl([100,200])
        assert ["1000.0", "950.0"] == _input_check_era_lvl()
        assert ["1000.0", "950.0"] == _input_check_era_lvl([1000,950])
        assert ["123.45"] == _input_check_era_lvl(123.45)
        assert ["123.45"] == _input_check_era_lvl('123.45')
        assert ["123.45"] == _input_check_era_lvl(['123.45'])
        assert ["123.45"] == _input_check_era_lvl([123.45])

    def test_invalid_input_satellite(self):
        with pytest.raises(ValueError):
            satellite_download(period = DateRange(end="2100-01-03", start="2100-01-02"), species = Pollutant.NO2, producttype = "L2__NO2___", satellite = "s2",replace =False)

class TestDownload:
    def bad_connect_era_download(self):
        with pytest.raises(Exception):
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"), replace=False)
        with pytest.raises(Exception) as excinfo:
            era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"),apikey = '123', replace=False)
        assert "401" in str(excinfo.value) #bad api connection

    def bad_request_s5p_download(self):
        with pytest.raises(Exception) as excinfo:
            satellite_download(period = DateRange(end="2100-01-03", start="2100-01-02"), species = Pollutant.NO2, producttype = "L2__NO2___", satellite = "s5p",replace =False)
        assert "SentinelAPIError" in str(excinfo.value)

    def succesful_test_era_download(self):
        assert None == era5_download(period = DateRange(end="2016-01-03", start="2016-01-02"), replace=False)

    def succesful_test_s5p_download(self):
        assert None == satellite_download(period = DateRange(end="2016-01-03", start="2016-01-02"), species = Pollutant.NO2, producttype = "L2__NO2___", satellite = "s5p",replace =False)