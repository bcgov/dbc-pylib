'''
Created on Nov 9, 2018

@author: kjnether
'''


import pytest
import FMEUtil.PyFMEServerV3


@pytest.fixture()
def FMEServerDev(FMEServer_ConnectParams_dev):
    url = FMEServer_ConnectParams_dev['url']
    token = FMEServer_ConnectParams_dev['token']
    fme = FMEUtil.PyFMEServerV3.FMEServer(url, token)
    yield fme
    