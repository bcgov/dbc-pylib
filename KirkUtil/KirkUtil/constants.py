from enum import Enum

class KirkApiPaths():
    '''
    Used to declare the various end points defined in the kirk api
    '''
    Jobs = 'jobs'
    Sources = 'sources'
    Destinations = 'destinations'
    FieldMaps = 'fieldmaps'
    
    
class JobProperties(Enum):
    date_modified = 1
    destField = 2
    jobStatus = 3
    jobid = 4
    jobLabel = 5
    sources = 6
    owner = 7
    date_created = 8
    cronStr = 9
    destTableName = 10
    destSchema = 11
    
class SourceProperties(Enum):
    sourceid = 1
    jobid = 2
    sourceTable = 3
    sourceType = 4
    sourceDBSchema = 5
    sourceDBName = 6
    sourceDBHost = 7
    sourceDBPort = 8
    sourceFilePath = 9
    
class FieldmapProps(Enum):
    fieldMapId = 1
    jobid = 2
    sourceColumnName = 3
    destColumnName = 4
    fmeColumnType = 5
    whoCreated = 6
    whenCreated = 7
    whoUpdated = 8
    
class SourceTypes():
    '''
    Used to keep track of the different types of sources, initially there is only 
    going to be one
    '''
    file_geo_database = 'FGDB'

# error messages for various api methods
GET_NON_200_ERROR_MSG = r'GET request to {0} has a status_code of {1}, returned data is: {2}'
POST_NON_200_ERROR_MSG = r'POST request to {0} has a status_code of {1}, returned data is: {2}'
DELETE_NON_200_ERROR_MSG = r'DELETE request to {0} has a status_code of {1}, returned data is: {2}'

# file name templates
FIELDMAP_CSV = 'fieldmaps_{0}.csv'
