'''
Created on Dec 12, 2018

@author: kjnether

Used to test communication with PMP
'''
import pytest
import os.path
import json
import PMP.PMPRestConnect


@pytest.fixture()
def PMP_Secrets():
    pmpConst = PMP.PMPRestConnect.PMPConst()
    secretsFile = os.path.join(os.path.dirname(__file__), '..', 'secrets', 'secrets.json')
    with open(secretsFile) as json_data:
        secretsData = json.load(json_data)
    yield secretsData


@pytest.fixture()
def PMP_ConfigDict(PMP_Secrets):
    pmpConst = PMP.PMPRestConnect.PMPConst()

    pmpApiKey = PMP_Secrets['pmptoken']
    pmpHost = PMP_Secrets['pmphost']
    pmpRestDir = PMP_Secrets['pmprestapidir']

    pmp = {pmpConst.connectKey_token :pmpApiKey,
           pmpConst.connectKey_baseurl: pmpHost,
           pmpConst.connectKey_restdir: pmpRestDir }
    yield pmp


@pytest.fixture()
def PMP_Resource_prd(PMP_Secrets):
    resourceName = None
    for secretConfig in PMP_Secrets['secrets2get']:
        if secretConfig['label'] == 'whse_prd':
            resourceName = secretConfig['PMPResource']
            break
    yield resourceName


@pytest.fixture()
def PMP_Resource_dlv(PMP_Secrets):
    resourceName = None
    for secretConfig in PMP_Secrets['secrets2get']:
        if secretConfig['label'] == 'whse_dlv':
            resourceName = secretConfig['PMPResource']
            break
    yield resourceName

