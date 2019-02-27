'''
Created on Feb 26, 2019

@author: kjnether
'''
import pytest
import os.path

def test_singleLayerReader(readlayerfiles_Fixture):
    lyrFile = 'ABMS_Counties.lyr'
    lyrFileFp = os.path.join(readlayerfiles_Fixture.dataDir, lyrFile)
    readlayerfiles_Fixture.readLyrFile(lyrFileFp)
