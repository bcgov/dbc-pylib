'''
Created on Mar 23, 2018

@author: kjnether
'''
import logging
import pprint
import re

import pytest

import FMEUtil.FMWParser as FMWParser
import FMEUtil.FMWParser.FMWParserConstants as Constants


def test_getDestinationHost(FMWParserInstanceParsed):
    # could put a mock in here for the log config to prevent that from running
    # params =  DataBCFMWTemplate.CalcParamsBase(FileBasedFMWMacros)
    # host = params.getDestinationHost()
    featureTypes = FMWParserInstanceParsed.getFeatureTypes()

    logging.info("featureTypes: %s", featureTypes)
    logging.info("featureTypes length: %s", len(featureTypes))

    assert len(featureTypes) == 2


def test_getDestinationFeatureClass(FMWParserInstanceParsed,
                                    FMWParserInstanceParsedProblemDestFeature):
    wrkspcObj = FMWParserInstanceParsed.getFMEWorkspace()
    featureClasses = wrkspcObj.getFeatureClasses()
    dests = featureClasses.getDestinations()
    fcName = dests[0].getFeatureClassName()
    logging.debug("fc name: %s", fcName)
    assert fcName == 'WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_COUNTIES_SP'
    dataset = dests[0].getDataSet()
    dataSetName = dataset.getDataSetName()
    assert dataSetName == 'idwprod1.bcgov'
    dsFormat = dataset.getDataSetFormat()
    assert dsFormat == 'SDE30'
    logging.info('datasetname: %s', dataSetName)
    logging.info("datasetformat: %s", dsFormat)

    wrkspcObj = FMWParserInstanceParsedProblemDestFeature.getFMEWorkspace()
    featureClasses = wrkspcObj.getFeatureClasses()
    dests = featureClasses.getDestinations()
    fcName = dests[0].getFeatureClassName()
    logging.debug("fc name: %s", fcName)
    assert len(fcName) <= 30


def test_getDestinationSchema(FMWParserInstanceParsedProblemDestSchema):
    parser = FMWParserInstanceParsedProblemDestSchema

    schema = parser.getDestinationSchema('AMA_SNOWMOBILE_MGMT_AREAS_SP')
    logging.debug("returned schema: %s", schema)
    assert schema.upper() == 'WHSE_WILDLIFE_INVENTORY'


def test_addPublishedParameters_1(FMWParserMockedPubParams):
    testDataOnlyFeatureName = {'SomeParam': "$(DEST_FEATURE_1)"}
    featureTypes = FMWParserMockedPubParams.addPublishedParameters(
        testDataOnlyFeatureName)
    print 'featureTypes1:', featureTypes
    assert featureTypes == {'SomeParam': 'SOMEFC'}

    testSchemaParam = {'NODE_NAME': '$(DEST_SCHEMA).ABMS_COUNTIES_SP'}
    expected = {'NODE_NAME': 'SOMESCHEMA.ABMS_COUNTIES_SP'}
    featureTypes = FMWParserMockedPubParams.addPublishedParameters(
        testSchemaParam)
    print 'featureTypes2:', featureTypes
    assert featureTypes == expected

    testFeatClsParam = {'NODE_NAME': 'SOMESCHEMA.$(DEST_FEATURE_1)'}
    expected = {'NODE_NAME': 'SOMESCHEMA.SOMEFC'}
    featureTypes = FMWParserMockedPubParams.addPublishedParameters(
        testFeatClsParam)
    print 'featureTypes2:', featureTypes
    assert featureTypes == expected


def test_regexs():
    '''
    Verifies the regex's capture the correct text
    '''
    # assert host == expected
    justParam = '$(DEST_FEATURE_1)'
    schemaParam = '$(DEST_SCHEMA_1).SOMEFEATURENAME'
    featClsParam = 'WHSE_CORP.$(DEST_FEATURE_1)'
    allParameterized = '$(DEST_SCHEMA).$(DEST_FEATURE_2)'
    pubParamRegex = re.compile(Constants.PUBPARAM_ONLY_REGEX, re.IGNORECASE)
    srch = pubParamRegex.search(justParam)
    assert srch
    srch = pubParamRegex.search(schemaParam)
    assert not srch
    srch = pubParamRegex.search(featClsParam)
    assert not srch

    # testing for the $(PARAM).value
    pubParamRegex = re.compile(Constants.PUBPARAM_SCHEMA_REGEX, re.IGNORECASE)
    srch = pubParamRegex.search(schemaParam)
    assert srch
    srch = pubParamRegex.search(justParam)
    assert not srch
    srch = pubParamRegex.search(featClsParam)
    assert not srch

    # testing for a dest_feature pattern
    pubParamRegex = re.compile(Constants.PUBPARAM_FEATURE_REGEX, re.IGNORECASE)
    srch = pubParamRegex.search(featClsParam)
    assert srch
    srch = pubParamRegex.search(schemaParam)
    assert not srch
    srch = pubParamRegex.search(justParam)
    assert not srch

    # testing for presence of a published parameter
    pubParam = re.compile(Constants.PUBPARAM_ANY, re.IGNORECASE)
    match = pubParam.match(allParameterized)
    assert match


def test_stripVariableNotations():
    var = '$(DEST_FEATURE_1)'
    util = FMWParser.FMWUtil.Util()
    # util = FMWParser.Util()
    strippedVar = util.stripVariableNotations(var)
    print 'var'
    assert strippedVar == 'DEST_FEATURE_1'


def test_getWorkspaceJson(FMWParserInstance):
    # FMWParserInstance.

    FMEWrkspc = FMWParserInstance.getFMEWorkspace()
    fc = FMEWrkspc.getFeatureClasses()
    print 'fc:', fc
    # json is getting generated for now, but needs review.  In the end
    # its not being used and therefore haven't reviewed or revised
    json = fc.getJson()

#     pp = pprint.PrettyPrinter(indent=4)
#     pp.pprint(json)
#
#      json = FMWParserInstance.getJson()
#      pp = pprint.PrettyPrinter(indent=4)
#      pp.pprint(json)
    pass


def test_pubParam_subPubParams(FMWParserMockedPubParams):
    parser = FMWParserMockedPubParams
    fmeWrkspc = parser.getFMEWorkspace()
    pubParams = fmeWrkspc.getPublishedParameters()
    inputStr = '$(DEST_SCHEMA).$(DEST_FEATURE_1)'
    retStr = pubParams.deReference(inputStr)
    print 'retStr', retStr


def test_getDataSetProjection(FMWParserInstance):
    FMEWrkspc = FMWParserInstance.getFMEWorkspace()
    featClses = FMEWrkspc.getFeatureClasses()
    expectedData = {'\\\\data.bcgov\\data_staging_ro\\BCGW\\administrative_boundaries\\GBA_Administrative_Boundaries.gdb': '', 'idwprod1.bcgov': 'BCALB-83'}
    returnedData = {}
    for featCls in featClses:
        dataSet = featCls.getDataSet()
        proj = dataSet.getProjection()
        dataSetName = dataSet.getDataSetName()
        logging.info("dataset/projection: %s / %s", dataSetName, proj)
        returnedData[dataSetName] = proj
    logging.info("expected: %s", expectedData)
    logging.info("returnedData: %s", returnedData)
    assert returnedData == expectedData
