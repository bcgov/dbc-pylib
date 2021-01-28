'''
Created on Apr 16, 2018

@author: kjnether
'''
import enum

FMESERVER_SECRET_LABEL = u'fme_prod'

FMESERVER_REPOSITORIES_TO_INVENTORY = [u'BCGW_SCHEDULED']

TMPDIR = u'tmp'
DATADIR = u'data'

PUBPARAM_ANY = r'^.*\$\([A-Za-z0-9_-]+\).*$'
PUBPARAM_SINGLE = '\$\([A-Za-z0-9_-]+\)'

PUBPARAM_ONLY_REGEX = r'^\s*(\$\([A-Za-z0-9_-]+\))\s*$'
PUBPARAM_SCHEMA_REGEX = r'^\s*(\$\([A-Za-z0-9_-]+\))\.[A-Za-z0-9_-]+\s*$'
PUBPARAM_FEATURE_REGEX = r'^\s*[A-Za-z0-9_-]+\.(\$\([A-Za-z0-9_-]+\))\s*$'

PUBPARAM_STIPNOTATION = r'^\s*\$\(([A-Za-z0-9_-]+)\)\s*$'


class reportColumns(enum.Enum):
    '''
    These are the possible columns that the report can extract from the
    parser.  They are used also to map column names to what data they
    contain
    '''
    fmwWorkspaceName = 1
    sources = 2
    destinations = 3
    transformerCount = 4
    transformerList = 5

    @classmethod
    def has_value(cls, value):
        print(f'value: {value}')
        return any(value == item.value for item in cls)
