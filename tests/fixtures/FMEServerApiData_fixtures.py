'''
Created on Oct 18, 2018

@author: kjnether
'''
import pytest
import os.path
import json

import FMEUtil.FMEServerApiData


@pytest.fixture()
def BasicSchedule_fixture(KirkConnectInfo):
    dataFile = os.path.join(os.path.dirname(__file__),
                        '..',
                        'secrets',
                        'schedules4Testing.json')
    with open(dataFile) as f:
        data = json.load(f)
    yield data


@pytest.fixture()
def FMEServerAPISchedules_fixture(BasicSchedule_fixture):
    sched = FMEUtil.FMEServerApiData.Schedules(BasicSchedule_fixture)
    yield sched
