'''
Created on Aug 7, 2018

@author: kjnether
'''

import FMEUtil.FMWParser.FMWComponents
import logging


def test_getFieldMaps(transParserFixture):
    # attributeRenamerFixture i

    transStruct = transParserFixture.getTransformers()

    wrkspc = transParserFixture.getFMEWorkspace()
    transformers = wrkspc.getTransformers()
    transNames = transformers.getTransformerNames()
    expected = ['File Change Detector v2']
    logging.debug("transNames: %s", transNames)
    assert set(expected) == set(transNames)


def test_parseAttributeRenamer(attributeRenamerFixture):
    parsr = attributeRenamerFixture
    wrkspc = parsr.getFMEWorkspace()
    transformers = wrkspc.getTransformers()
    hasAttribTrans = transformers.hasAttributeRenamer()
    assert hasAttribTrans

    atribTransformers = transformers.getAttributeRenamerTransformers()
    assert len(atribTransformers) >= 1

    for atribTrans in atribTransformers:
        assert isinstance(atribTrans,
                          FMEUtil.FMWParser.FMWComponents.AttributeRenamerTransformer)  # @IgnorePep8
        fldMap = atribTrans.getAttributeRenamerFieldMap()
        logging.info('fieldmap: %s', fldMap)
        assert len(fldMap[0]) > 0


def test_getCounterTransformerParameters(counterFixture):
    transParserFixture = counterFixture
    transStruct = transParserFixture.getTransformers()
    wrkspc = transParserFixture.getFMEWorkspace()
    transformers = wrkspc.getTransformers()
    transNames = transformers.getTransformerNames()
    logging.info('transNames: %s', transNames)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(transStruct)

    hasCnter = transformers.hasCounter()
    assert hasCnter is True

    cnter = transformers.getCounterTransformers()
    assert cnter

    cnter = cnter[0]

    userNamedFld = cnter.getUserAssignedTransformerName()
    assert userNamedFld == 'Counter'

    outputAtributeName = cnter.getCounterOutputAttributeName()
    assert outputAtributeName == 'LAND_USE_SITE_ID'

    counterStartNumber = cnter.getCounterStartNumber()
    assert int(counterStartNumber) == 1

    counterName = cnter.getCounterName()
    assert counterName == 'counter'

    counterScope = cnter.getCounterScope()
    assert counterScope == 'Global'
