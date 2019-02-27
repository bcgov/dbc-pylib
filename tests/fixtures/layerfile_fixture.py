'''
Created on Feb 26, 2019

@author: kjnether
'''
import pytest
import os
import ArcGisUtil.LayerFileReader
import shutil
import DBCSecrets.GetSecrets 

@pytest.fixture()
def getSecrets_Fixture():
    secretLbl = 'whse_dlv'
    creds = DBCSecrets.GetSecrets.CredentialRetriever()
    secrets = creds.getSecretsByLabel(secretLbl)
    password = secrets.getPassword()
    schema = secrets.getUserName()
    yield [schema, password]


@pytest.fixture()
def readlayerfiles_Fixture(getSecrets_Fixture):
    lyrLib = 'lyrlib'
    delDirFP = os.path.join(os.path.dirname(__file__), 'deleteme')
    if not os.path.exists(delDirFP):
        os.mkdir(delDirFP)
    lyrLibFP = os.path.join(os.path.dirname(__file__,
                                             '..',
                                             'test_data',
                                             lyrLib))
    lyrFileFP = os.path.join(lyrLibFP, lyrLib)
    
    
    lyrReader = ArcGisUtil.LayerFileReader(lyrLibFP, delDirFP, *getSecrets_Fixture)
    yield lyrReader
    if os.path.exists(delDirFP):
        shutil.rmtree(delDirFP)

