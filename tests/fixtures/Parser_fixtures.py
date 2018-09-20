'''
Created on Aug 7, 2018

@author: kjnether
'''

import pytest
import FMEUtil.FMWParser
import os.path


@pytest.fixture()
def attributeRenamerFixture():
    '''
    returns a fmw file as a FMWParser
    object that contains a attribute renamer
    transformer:

    fish_aquatic_invasive_spcs_sp_staging_gdb_idwprod1.fmw
    fwa_waterbodies_20k_50k_staging_gdb_bcgw.fmw

    '''
    fileName = 'fish_aquatic_invasive_spcs_sp_staging_gdb_idwprod1.fmw'
    filePath = os.path.join(os.path.dirname(__file__), '..', 'test_Data')
    fileNameFullPath = os.path.join(filePath, fileName)
    parsr = FMEUtil.FMWParser.FMWParser(fileNameFullPath)
    yield parsr


@pytest.fixture()
def counterFixture():
    '''
    returns a fmw file as a FMWParser
    object that contains a counter transformer:
    '''
    fileName = 'fn_land_use_sites_line_staging_gdb_bcgw.fmw'
    filePath = os.path.join(os.path.dirname(__file__), '..', 'test_Data')
    fileNameFullPath = os.path.join(filePath, fileName)
    parsr = FMEUtil.FMWParser.FMWParser(fileNameFullPath)
    yield parsr


@pytest.fixture()
def transParserFixture():
    # returns a parser object useful for testing transfomers
    # only one:     fwa_waterbodies_20k_50k_staging_gdb_bcgw.fmw
    fileName = 'fwa_waterbodies_20k_50k_staging_gdb_bcgw.fmw'
    filePath = os.path.join(os.path.dirname(__file__), '..', 'test_Data')
    fileNameFullPath = os.path.join(filePath, fileName)
    parsr = FMEUtil.FMWParser.FMWParser(fileNameFullPath)
    yield parsr
