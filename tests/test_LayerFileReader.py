'''
Created on Feb 26, 2019

@author: kjnether
'''
import pytest
import os.path

def test_singleLayerReader(getArcPyEnvs, readlayerfiles_Fixture):
    #getRegistryReader.addToPATHEnvVar()
    #getRegistryReader.addToPythonPath()
    lyrFile = 'ABMS_Counties.lyr'
    lyrFileFp = os.path.join(readlayerfiles_Fixture.lyrFileRootDir, lyrFile)
    readlayerfiles_Fixture.readLyrFile(lyrFileFp)
    
