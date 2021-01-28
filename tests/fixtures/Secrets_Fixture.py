'''
Created on Aug 28, 2018

@author: kjnether

Fixture that provides the url and the tokens required to communicate with
Kirk API
'''
import pytest
import DBCSecrets.GetSecrets
import os
import logging

@pytest.fixture()
def FMEServer_ConnectParams_dev():
    secretsFile = os.path.join(os.path.dirname(__file__), '..', 'secrets',
                               'secrets.json')
    secretsFile = os.path.realpath(secretsFile)
    print 'secretsFile', secretsFile
    creds = DBCSecrets.GetSecrets.CredentialRetriever(secretsFile)
    secrets = creds.getSecretsByLabel('fmetst')
    host = secrets.getHost()
    token = secrets.getAPI()
    baseUrl = 'http://{0}/'.format(host)
    return {'url':baseUrl, 'token':token}

@pytest.fixture()
def KirkConnectInfo_local():
    secretsFile = os.path.join(os.path.dirname(__file__), '..', 'secrets',
                               'secrets.json')
    secretsFile = os.path.realpath(secretsFile)
    print 'secretsFile', secretsFile
    creds = DBCSecrets.GetSecrets.CredentialRetriever(secretsFile)
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
    creds = DBCSecrets.GetSecrets.CredentialRetriever(secretsFile)
    credsMisc = creds.getMiscParams()
    url = credsMisc.getParam('appkirkhost_os_dev')
    token = credsMisc.getParam('appkirktoken_os_dev')
    obj = type('obj', (object, ), {'url': url, 'token': token})
    yield obj

@pytest.fixture()
def KirkConnectInfo(KirkConnectInfo_openShift_dev):
    # KirkConnectInfo_local
    yield KirkConnectInfo_openShift_dev
    