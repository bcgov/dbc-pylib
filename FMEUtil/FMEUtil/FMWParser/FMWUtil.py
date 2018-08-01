'''
Created on Jul 24, 2018

@author: kjnether
'''
import logging
from . import FMWParserConstants
import re

class Util():
    '''
    simple methods that may be used by this modules
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def stripVariableNotations(self, varName):
        '''
        Takes a variable name like $(DEST_FEATURE_1) and strips off the
        '$(' from the start and ')' from the end
        '''
        regex = re.compile(FMWParserConstants.PUBPARAM_STIPNOTATION, re.IGNORECASE)
        srch = regex.search(varName)
        if not srch:
            msg = 'unable to extract a variable from the text %s, expecting ' + \
                  'test in the format of \'$(SOMEVAR)\'. '
            self.logger.error(msg, varName)
            raise ValueError, msg, varName
        pubParmName = srch.group(1)
        return pubParmName

