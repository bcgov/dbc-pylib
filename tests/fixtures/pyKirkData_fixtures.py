'''
Created on Nov 9, 2018

@author: kjnether
'''
import pytest
import os.path
import json

@pytest.fixture()
def Kirk_Destinations():
    destsFileJson = os.path.join(os.path.dirname(__file__), '..', 'test_data',
                               'destinations.json')
    destsFileJson = os.path.realpath(destsFileJson)
    with open(destsFileJson) as f:
        dataStruct = json.load(f)
    yield dataStruct
    
    
    
