# -*- coding: utf-8 -*-
#%%
import pytest

from eocalc.context import Pollutant
from eocalc.methods.downloadtools import era5_download, tropomi_download
from eocalc.methods.base import DateRange 
#%%
#@pytest.fixture
#def calc():
#    return era5_download()

#%%
class Test_era5_download:
    def test_invalid_init_era5_input(self):
        with pytest.raises(AssertionError): #too little input
            era5_download()
        with pytest.raises(TypeError): #wrong DateRange
            era5_download(period = DateRange(1, ""))
        with pytest.raises(ValueError): #wrong path
            era5_download(period = DateRange(end="2016-01-02", start="2016-01-03"),sdir ='\/this path will not work' )
        with pytest.raises(ValueError):#level too high 
            era5_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels ='100000' )
        with pytest.raises(ValueError):#level too low
            era5_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels ='0.4' )
        with pytest.raises(ValueError):#level wrong
            era5_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels =['1000', 'hello'] )
# %%
class Test_tropomi_download:
    def test_invalid_init_s5p_input(self):
        with pytest.raises(AssertionError): #too little input
            tropomi_download()
        with pytest.raises(TypeError): #wrong DateRange
            tropomi_download(period = DateRange(1, ""))
        with pytest.raises(ValueError): #wrong path
            tropomi_download(period = DateRange(end="2016-01-02", start="2016-01-03"),sdir ='\/this path will not work' )
        with pytest.raises(ValueError):#level too high 
            tropomi_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels ='100000' )
        with pytest.raises(ValueError):#level too low
            tropomi_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels ='0.4' )
        with pytest.raises(ValueError):#level wrong
            tropomi_download(period = DateRange(end="2016-01-02", start="2016-01-03"),levels =['1000', 'hello'] )
