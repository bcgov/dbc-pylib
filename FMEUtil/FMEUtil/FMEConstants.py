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
    workspacePath = 11
    workspace = 12
    
class FMEFrameworkPublishedParameters(Enum):
    DEST_SCHEMA = 1
    DEST_FEATURE = 2
    KIRK_JOBID = 3
    KIRK_JOBLABEL = 4
    
    
class Workspace(Enum):
    lastSaveDate = 1
    lastPublishDate = 2
    name = 3
    description = 4
    repositoryName = 5
    title = 6
    type = 7
    userName = 8
    
class WorkspaceInfo(Enum):
    '''
    sample data 
    u'buildNumber': 17539,
    u'category': u'DataBC Warehouse Replication',
    u'name': u'OBJECTID',
    u'datasets': {   u'destination': [   {   u'featuretypes': [   {   u'attributes': [   {   u'decimals': 0,

    '''
    buildNumber = 1
    category = 2
    datasets = 3
    description = 4
    enabled = 5
    fileSize = 6
    history = 7
    isVersioned = 8
    lastPublishDate = 9
    lastSaveBuild = 10
    lastSaveDate = 11
    legalTermsConditions = 12
    name = 13
    parameters = 14
    properties = 15
    requirements = 16
    requirementsKeyword = 17
    resources = 18
    services = 19
    title = 20
    type = 21
    usage = 22
    userName = 23
    
class Properties(Enum):
    attributes = 1
    category = 2
    name = 3
    value = 4
   
class Parameters(Enum):
    '''
    example data:
{   u'defaultValue': u'PROXY_FADM_WHSE',
                           u'description': u'Source schema used to login to the database (upper case only please)',
                           u'model': u'string',
                           u'name': u'SRC_ORA_PROXY_SCHEMA',
                           u'type': u'TEXT'},
                       {   u'defaultValue': u'DLV',
                           u'description': u'Destination Database Keyword (DLV|TST|PRD)',
                           u'listOptions': [   {   u'caption': u'DLV',
                                                   u'value': u'DLV'},
                                               {   u'caption': u'TST',
                                                   u'value': u'TST'},
                                               {   u'caption': u'PRD',
                                                   u'value': u'PRD'},
                                               {   u'caption': u'DEV',
                                                   u'value': u'DEV'}],
    '''
    defaultValue = 1
    description = 2
    model = 3
    name = 4
    type = 5
    listOptions = 6
    
class DataSets(Enum):
    # both of these properties are tied to lists
    destination = 1
    source = 2
    
class DataSet(Enum):
    '''
    example of data:
    u'format': u'SDE30',
    u'location': u'random.bcgov',
    u'name': u'SDE30_1',
    u'properties': [   {   u'attributes': {   }, ...
    u'source': True}

    '''
    featuretypes = 1
    format = 2
    location = 3
    properties = 4
    source = 5
