'''
Created on Jun 15, 2018

@author: kjnether
'''

import pytest
import logging
import KirkUtil.PyKirk


def test_getJobs(PyKirk_Fixture, caplog):
    caplog.set_level(logging.DEBUG)
    # every day at 1 am
    dummyCron = '0 0 1 * * ?'
    jobs = PyKirk_Fixture.getJobs()
    jobList = jobs.getJobs()
    logging.debug('jobList: %s', jobList)
    assert len(jobList) > 0
    assert "jobid" in jobList[0]


# @pytest.mark.xfail(raises=KirkUtil.PyKirk.APIError)
def test_badAuth(PyKirk_Fixture_broken):
    # jobs = KirkLoader.JobLoader.JobLoader(KirkConnectInfo.url, 'BADTOKEN')
    jobs = PyKirk_Fixture_broken.getJobs()
    with pytest.raises(KirkUtil.PyKirk.APIError) as excinfo:  # @UnusedVariable
        jobList = jobs.getJobs()
        logging.debug('jobList bad token: %s', jobList)
        assert jobList['detail'] == 'Invalid token.'
