'''
Created on Nov 25, 2015

@author: kjnether


'''

import platform
import json
import os.path


class DBEnvInfo(object):

    def __init__(self, secretsFile=None):
        # if you edit this dict make sure you also
        # edit the first value of the corresponding key
        # in self.sameKeys
        secrets = None
        if not secretsFile:
            secretsFile = os.path.join(os.path.dirname(__file__), 'secrets.json')
        if os.path.exists(secretsFile):
            fh = open(secretsFile, 'r')
            secrets = json.load(fh)
            fh.close()

        self.dbInfo = secrets['DBPARAMS']

        # these need to be populated by the inheriting class
        self.pmpTokens = { }
        self.pmpConfig = secrets['PMPPARAMS']

    def getPMPToken(self):
        computerName = platform.node()
        computerName = computerName.lower()
        computerNameList = computerName.split('.')
        computerName = computerNameList[0]
        if not self.pmpTokens.has_key(computerName):
            msg = 'you tried to get a pmp key for the computer {0}' + \
                  'however there is no key described for that machine ' + \
                  '.  You need to populate the pmpTokens dictionary ' + \
                  ' with the key for this machine.'
            msg = msg.formatSql(computerName)
            raise ValueError, msg
        return self.pmpTokens[computerName]

    def getPMPConfig(self):
        self.pmpConfig['token'] = self.getPMPToken()
        return self.pmpConfig

    def getValidKeys(self):
        return self.dbInfo.keys()

    def getDbInfo(self, key):
        '''
        checks to see if the key lines up with one of the keys
        defined in self.dbInfo.  If not then checks to see if the
        the key is defined as a valid alias.  If it can find the
        key it returns the corresponding database dictionary


        :param  key: the database key that should be used to
                     retrieve database info.
        :type key: string
        :returns: a dictionary with the following keys:
                   server - server hosting the db
                   port - port that the sde listener is hooked up to
                   name - instance name / service name
                   keyAliases - other keys that can be used
                                to refer to this struct
        :rtype: dict
        '''
        key = key.upper()
        retVal = None
        curKeys = self.dbInfo.keys()
        if key in curKeys:
            retVal = self.dbInfo[key]
        else:
            # check aliases
            for curKey in curKeys:
                aliases = self.dbInfo[curKey]['keyAliases']
                if key in aliases:
                    retVal = self.dbInfo[curKey]
                    break
        return retVal

    def isValidKey(self, key):
        '''
        Looks at the keys in the struct self.dbInfo for
        the key provided as an arg.  Also checks the
        keyAliases for the self.dbInfo for keys with
        the provided value.  Returns True if the
        key can be resolved to a defined set of db
        params, false if not.

        :param  key: string containing the key to check for
        :type key: str

        :returns: boolean indicating whether they provided key
                  has corresponding db info set up for it.
        :rtype: boolean
        '''
        valid = False
        key = key.upper()
        validKeys = self.dbInfo.keys()
        if key in validKeys:
            valid = True
        else:
            for curKey in validKeys:
                if curKey in self.dbInfo[curKey]['keyAliases']:
                    valid = True
                    break
        return valid

    def getKey(self, key):
        '''
        If the key provided is an alias will return the key
        that can be used to get directly to the corresponding
        database dict in self.dbInfo
        '''
        key = key.upper()
        retVal = None
        curKeys = self.dbInfo.keys()
        if key in curKeys:
            retVal = key
        else:
            # check aliases
            for curKey in curKeys:
                aliases = self.dbInfo[curKey]['keyAliases']
                if key in aliases:
                    retVal = curKey
                    break
        return retVal

    def getDestinationPmpResource(self, key):
        key = self.getKey(key)
        return self.dbInfo[key]['pmpres']

