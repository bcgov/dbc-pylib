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
    secretFile = os.path.join(os.path.dirname(__file__), '..', 'secrets', 'secrets.json')
    creds = DBCSecrets.GetSecrets.CredentialRetriever(secretFileName=secretFile)
    secrets = creds.getSecretsByLabel(secretLbl)
    password = secrets.getPassword()
    schema = secrets.getUserName()
    yield [schema, password]


@pytest.fixture()
def readlayerfiles_Fixture(getSecrets_Fixture):
    lyrLib = 'lyrlib'
    #delDirFP = os.path.join(os.path.dirname(__file__), 'deleteme')
    lyrLibFP = os.path.join(os.path.dirname(__file__),
                                             '..',
                                             'test_data',
                                             lyrLib)
    delDirFP = os.path.join(lyrLibFP, '..', 'deleteme')
    if not os.path.exists(delDirFP):
        os.mkdir(delDirFP)
    lyrFileFP = os.path.join(lyrLibFP, lyrLib)
    lyrFileFP = os.path.realpath(lyrFileFP)
    delDirFP = os.path.realpath(delDirFP)
    
    lyrReader = ArcGisUtil.LayerFileReader.ReadLayerFiles(lyrLibFP, delDirFP, getSecrets_Fixture[0], getSecrets_Fixture[1])
    yield lyrReader
    #if os.path.exists(delDirFP):
    #    shutil.rmtree(delDirFP)

