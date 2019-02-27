'''
Created on Nov 9, 2018

@author: kjnether
'''

import pytest
import FMEUtil.PyFMEServerV3


def test_getSchedules(FMEServerDev):
    schedules = FMEServerDev.getSchedules()
    sched = schedules.getSchedule()
    # 176
    categoryName = 'kirk_scheduled'
    scheduleName = 'abms_counties_sp_staging_gdb_bcgw.KIRK'
    newParams = {'KIRK_JOBID': '5000'}
    sched.updateParameters(scheduleName, categoryName, newParams)

    newParams = {'KIRK_JOBID': '176'}
    sched.updateParameters(scheduleName, categoryName, newParams)
