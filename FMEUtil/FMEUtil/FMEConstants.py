'''
Created on Oct 18, 2018

@author: kjnether

used to keep track of property names used by fme rest api.
'''
from enum import Enum


class Schedule(Enum):
    name = 1
    request = 2
    publishedParameters = 3
    begin = 4
    category = 5
    cron = 6
    description = 7
    enabled = 8
    recurrence = 9
    repository = 10
    request = 11
    publishedParameters = 12
    workspacePath = 13
    workspace = 14
    
class FMEFrameworkPublishedParameters(Enum):
    DEST_SCHEMA = 1
    DEST_FEATURE = 2
    KIRK_JOBID = 3
    KIRK_JOBLABEL = 4
    
    
    