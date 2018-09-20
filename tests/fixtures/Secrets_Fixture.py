'''
Created on Aug 28, 2018

@author: kjnether

Fixture that provides the url and the tokens required to communicate with
Kirk API
'''
import pytest
import Secrets.GetSecrets
import os
import logging


@pytest.fixture()
def KirkConnectInfo_local():
    secretsFile = os.path.join(os.path.dirname(__file__), '..', 'secrets',
                               'secrets.json')
    secretsFile = os.path.realpath(secretsFile)
    print 'secretsFile', secretsFile
    creds = Secrets.GetSecrets.CredentialRetriever(secretsFile)
    credsMisc = creds.getMiscParams()
    url = credsMisc.getParam('appkirkhost_local')
    token = credsMisc.getParam('appkirktoken_local')
    obj = type('obj', (object,), {'url': url, 'token': token})
    yield obj


@pytest.fixture()
def KirkConnectInfo_openShift_dev():
    secretsFile = os.path.join(os.path.dirname(__file__), '..', 'secrets',
                               'secrets.json')
    secretsFile = os.path.realpath(secretsFile)
    logging.debug('secretsFile: %s', secretsFile)
    creds = Secrets.GetSecrets.CredentialRetriever(secretsFile)
    credsMisc = creds.getMiscParams()
    url = credsMisc.getParam('appkirkhost_os_dev')
    token = credsMisc.getParam('appkirktoken_os_dev')
    obj = type('obj', (object, ), {'url': url, 'token': token})
    yield obj


@pytest.fixture()
def KirkConnectInfo(KirkConnectInfo_openShift_dev):
    # KirkConnectInfo_local
    yield KirkConnectInfo_openShift_dev
