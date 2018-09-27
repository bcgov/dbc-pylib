from enum import Enum


class KirkApiPaths():
    '''
    Used to declare the various end points defined in the kirk api
    '''
    Jobs = 'jobs'
    Sources = 'sources'
    Destinations = 'destinations'
    FieldMaps = 'fieldmaps'
    Transformers = 'transformers'


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
    sourceProjection = 10


class FieldmapProperties(Enum):
    fieldMapId = 1
    jobid = 2
    sourceColumnName = 3
    destColumnName = 4
    fmeColumnType = 5
    whoCreated = 6
    whenCreated = 7
    whoUpdated = 8


class TransformerProperties(Enum):
    transformer_id = 1
    jobid = 2
    transformer_type = 3
    ts1_name = 4
    ts1_value = 5
    ts2_name = 6
    ts2_value = 7
    ts3_name = 8
    ts3_value = 9
    ts4_name = 10
    ts4_value = 11
    ts5_name = 12
    ts5_value = 13
    ts6_name = 14
    ts6_value = 15


class TransformerTypes(Enum):
    '''
    supported transformer types
    '''
    counter = 1


class TransformerCoreAttributes(Enum):
    '''
    All transformers will have these attributes
    '''
    transformer_id = 1
    jobid = 2
    transformer_type = 3


class CounterTransformerMap(Enum):
    '''
    These are the dynamic parameter names used for counter transformers
    they are used to populate the various ts_name ts_value parameters
    in the Transformers end points.
    '''
    counterName = 1
    counterAttribute = 2
    counterScope = 3
    counterStartNumber = 4


class SourceTypes():
    '''
    Used to keep track of the different types of sources, initially there
    is only going to be one
    '''
    file_geo_database = 'FGDB'


# error messages for various api methods
GET_NON_200_ERROR_MSG = \
    r'GET request to {0} has a status_code of {1}, returned data is: {2}'
POST_NON_200_ERROR_MSG = \
    r'POST request to {0} has a status_code of {1}, returned data is: {2}'
DELETE_NON_200_ERROR_MSG = \
    r'DELETE request to {0} has a status_code of {1}, returned data is: {2}'

# file name templates
FIELDMAP_CSV = 'fieldmaps_{0}.csv'

# name for counter transformers types
# replace with the enumerated value in TransformerTypes
# COUNTER_TRANSFORMER_NAME = 'counter'

TRANSFORMER_NAME_TMPLT = 'ts{0}_name'
TRANSFORMER_VALUE_TMPLT = 'ts{0}_value'
TRANSFORMERS_DYNAMICFIELDS_LENGTH = 6
