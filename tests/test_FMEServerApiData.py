'''
Created on Oct 18, 2018

@author: kjnether
'''
import pprint
import KirkUtil.constants

import pytest


def test_getScheduleName(FMEServerAPISchedules_fixture):
    scheds = FMEServerAPISchedules_fixture
    testSchedName = 'rec_features_inventory_recprd_sde_bcgw.PROD'
    pp = pprint.PrettyPrinter(indent=4)
    assert scheds.exists(testSchedName)


def test_getCategory(FMEServerAPISchedules_fixture):
    scheds = FMEServerAPISchedules_fixture
    testSchedName = 'rec_features_inventory_recprd_sde_bcgw.PROD'
    sched = scheds.getSchedule(testSchedName)
    category = sched.getCategory()
    expectedCategory = 'SDGW - nightly'
    assert expectedCategory == category


def test_getDestinationSchema(FMEServerAPISchedules_fixture):
    scheds = FMEServerAPISchedules_fixture
    testSchedName = 'rec_features_inventory_recprd_sde_bcgw.PROD'
    sched = scheds.getSchedule(testSchedName)
    pubparams = sched.getPublishedParameters()
    destSchema = pubparams.getDestinationSchema()
    assert destSchema == 'WHSE_FOREST_VEGETATION'


def test_getDestinationFeature(FMEServerAPISchedules_fixture):
    scheds = FMEServerAPISchedules_fixture
    testSchedName = 'rec_features_inventory_recprd_ssde_bcgw.PROD'
    sched = scheds.getSchedule(testSchedName)
    pubparams = sched.getPublishedParameters()
    destFeature = pubparams.getDestinationFeature()
    assert destFeature == 'REC_FEATURES_INVENTORY'


def test_kirkJobRetrieval(FMEServerAPISchedules_fixture):
    scheds = FMEServerAPISchedules_fixture
    testJobid = 159
    exists = scheds.kirkScheduleExists(testJobid, KirkUtil.constants.KirkFMWs.APP_KIRK__FGDB)
    print('exists: {exists}')
    assert exists
