'''
Created on Apr 23, 2018

@author: kjnether
'''
import pytest
from helpers import TestingUtilities  # @UnresolvedImport
import FMEUtil.FMWParser
import logging
import os.path


@pytest.fixture()
def logFixture():
    logger = logging.getLogger()
    formatStr = '%(asctime)s - %(name)s - %(levelname)s - %(lineno)d ' + \
                '- %(message)s'
    formatter = logging.Formatter(formatStr)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


@pytest.fixture()
def FMWParserInstance(logFixture):
    util = TestingUtilities.Utils()
    fullFMWPath = util.getABMSJob()
    fmwParser = FMEUtil.FMWParser.FMWParser(fullFMWPath)

    yield fmwParser
    print('fixture finished')


@pytest.fixture()
def FMWFieldMapData(logFixture):
    # util = TestingUtilities.Utils()
    fldMapDataFile = os.path.join(os.path.dirname(__file__),
                                  'fieldMapData.txt')
    fh = open(fldMapDataFile, 'r')
    data = fh.readlines()

    yield data


@pytest.fixture()
def FMWParserInstanceParsedProblemDestSchema(logFixture):
    util = TestingUtilities.Utils()
    fullFMWPath = util.getAMASnowmobile()
    fmwParser = FMEUtil.FMWParser.FMWParser(fullFMWPath)
    # FMWParser.FMWParser(fullFMWPath)

    # fmwParser = FMWParser.FMWParser(fullFMWPath)
    fmwParser.separateFMWComponents()
    yield fmwParser


@pytest.fixture()
def FMWParserInstanceParsedProblemDestFeature(logFixture):
    util = TestingUtilities.Utils()
    fullFMWPath = util.getFishForeshore()
    fmwParser = FMEUtil.FMWParser.FMWParser(fullFMWPath)
    # FMWParser.FMWParser(fullFMWPath)

    # fmwParser = FMWParser.FMWParser(fullFMWPath)
    fmwParser.separateFMWComponents()
    yield fmwParser


@pytest.fixture()
def FMWParserInstanceParsed(logFixture):
    util = TestingUtilities.Utils()
    fullFMWPath = util.getABMSJob()
    fmwParser = FMEUtil.FMWParser.FMWParser(fullFMWPath)

    # FMWParser.FMWParser(fullFMWPath)

    # fmwParser = FMWParser.FMWParser(fullFMWPath)
    fmwParser.separateFMWComponents()
    yield fmwParser


@pytest.fixture()
def FMWParserMockedPubParams(logFixture, monkeypatch):
    util = TestingUtilities.Utils()
    fullFMWPath = util.getABMSJob()
    monkeypatch.setattr('FMEUtil.FMWParser.FMWParser.getPublishedParams',
                        getPublishedParams)
    fmwParser = FMEUtil.FMWParser.FMWParser(fullFMWPath)
    # fmwParser = FMWParser.FMWParser(fullFMWPath)
    fmwParser.separateFMWComponents()
    yield fmwParser


def getPublishedParams(self):
    paramDict = {}
    paramDict['DEST_FEATURE_1'] = {'DEFAULT_VALUE': 'SOMEFC',
                                   'TYPE': 'TEXT'}
    paramDict['DEST_SCHEMA'] = {'DEFAULT_VALUE': 'SOMESCHEMA',
                                'TYPE': 'TEXT'}

    paramDict['SRC_FEATURE_1'] = {'DEFAULT_VALUE': 'SOURCESCHEMA',
                                  'TYPE': 'TEXT'}
    paramDict['SRC_DATASET_FGDB_1'] = {'DEFAULT_VALUE': 'SRCFGDB',
                                       'TYPE': 'TEXT'}
    # paramDict['DEST_FEATURE_1'] = { 'DEFAULT_VALUE': 'SOMEFEATCLS',
    #                                'TYPE': 'TEXT'}
    return paramDict
