'''
Created on Aug 7, 2018

@author: kjnether
'''
import logging

import pytest  # @UnusedImport


def test_getFieldMaps(attributeRenamerFixture):
    # could put a mock in here for the log config to prevent that from running
    # params =  DataBCFMWTemplate.CalcParamsBase(FileBasedFMWMacros)
    # host = params.getDestinationHost()

    # trans = attributeRenamerFixture.getTransformers()
    # transNames = trans.getTransformerNames()\
    wrkSpc = attributeRenamerFixture.getFMEWorkspace()
    trans = wrkSpc.getTransformers()
    transNames = trans.getTransformerNames()
    logging.info('transformers: %s', transNames)
    atribNameTransformers = trans.getAttributeRenamerTransformers()
    expectedTrans = ['AttributeRenamer', 'File Change Detector v2']
    assert expectedTrans == atribNameTransformers
    # there should be at least one atribNameTransformers in  the
    # returned list
    assert atribNameTransformers
    atribNameTransformer = atribNameTransformers[0]

    fieldMap = atribNameTransformer.getAttributeRenamerFieldMap()
    logging.debug('fieldMap: %s', fieldMap)
    assert len(fieldMap) == 22
