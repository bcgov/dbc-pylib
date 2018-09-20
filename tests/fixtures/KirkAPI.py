'''
Created on Sep 4, 2018

@author: kjnether

used to create KirkUtil.PyKirk fixtures
'''
import pytest
import KirkUtil.PyKirk


@pytest.fixture()
def PyKirk_Fixture(KirkConnectInfo):
    kirkapi = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    yield kirkapi


@pytest.fixture()
def PyKirk_Fixture_broken(KirkConnectInfo):
    kirkapi = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, 'BADTOKEN1234')
    yield kirkapi


@pytest.fixture()
def PyKirk_addedJob_Fixture(KirkConnectInfo):
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()

    jobDescr = {'label': 'deletemejob',
                'status': 'DELETE',
                'cronStr': '0 0 0 0 0',
                'destEnv': 'DLV',
                'schema': 'TESTSCHEMA',
                'fcName': 'TESTFCNAME'}

    # create dummy job if it doesnt exist
    if not kirkJobs.jobLabelExists(jobDescr['label']):
        kirkJobs.postJobs(status=jobDescr['status'],
                          cronStr=jobDescr['cronStr'],
                          destEnv=jobDescr['destEnv'],
                          jobLabel=jobDescr['label'],
                          schema=jobDescr['schema'],
                          fcName=jobDescr['fcName'])

    yield [kirk, jobDescr]
