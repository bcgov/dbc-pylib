'''
Created on Feb 26, 2019

@author: kjnether
'''
import ArcGisUtil.ConfigurePy3Paths
import pytest

@pytest.fixture()
def getRegistryReader():
    reader = ArcGisUtil.ConfigurePy3Paths.Py3PathRegistry()
    yield reader
    
@pytest.fixture()
def getArcPyEnvs(getRegistryReader):
    getRegistryReader.addToPATHEnvVar()
    getRegistryReader.addToPythonPath()