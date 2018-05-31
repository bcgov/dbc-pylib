"""

About
=========
:synopsis:     an api used to retrieve global application parameters.
:moduleauthor: Kevin Netherton
:date:         6-4-2014
:description:  Retrieves application level parameters from a config
               file.

"""
import os
import ConfigParser


class Config():
    '''
    functionality to retrieve properties / parameters.

    :ivar confPars: The config file parser object
    :ivar configDir: The directory where this class is
                     is expecting to find the config
                     file.  Directory is relative to the
                     application root directory.
    :ivar configFile: Name of the config file, no path
                      in the name.
    '''

    confPars = None  # config parser object
    configDir = 'config'

    def __init__(self, configFile):
        self.configFile = configFile
        configFileFullPath = self.__getConfigFilePath()
        print 'configFileFullPath', configFileFullPath
        # print 'file:', configFileFullPath
        self.confPars = ConfigParser.ConfigParser()
        self.confPars.read(configFileFullPath)

    def __getConfigFilePath(self):
        # can't use the config object to get this as it
        # hasn't been created yet
        dir = os.path.dirname(os.path.dirname(__file__))
        dir = os.path.normpath(os.path.join(dir, '..'))

        fullPath2Config = os.path.join(dir, self.configDir, self.configFile)
        # appDir = self.confPars.get('Global', 'appdir')
        # confDir = self.confPars.get('Global', 'confdir')
        # fullPath2Config = os.path.join(appDir, confDir, self.configFile)
        return fullPath2Config

    def getFullPathToDbParamsFile(self):
        curPath = os.path.dirname(__file__)
        confDir = self.confPars.get('Global', 'configdir')
        dbConfFile = self.confPars.get('Global', 'dbconfigfile')
        path = os.path.normcase(os.path.join(curPath, '..', '..', confDir, dbConfFile))
#         print 'path:', path
        return path

    def getDbInstance(self):
        appDir = self.confPars.get('Global', 'dbinstance')
        return appDir

    def getGlobalParams(self):
        '''
        Returns a dictionary that contains keys that describe
        application global configuration parameters.

        :returns: application level global configuration parameters
        :rtype: string
        '''
        params = self.__getSection("Global")
        return params

    def __getSection(self, section):
        '''
        generic method that makes it easy to grab an entire section
        from the config file and add all the elements from each
        section into a dictionary and return that dictionary.

        :param  section: the name of the section who's parameters
                         you would like returned.
        :type section: string

        :returns: a dictionary with all the parameters in the config
                  file for the section you requested.
        :rtype: dictionary
        '''
        returnDict = {}
        options = self.confPars.options(section)
        for opt in options:
            returnDict[opt] = self.confPars.get(section, opt)
        return returnDict

    def couldBeBool(self, val):
        retVal = False
        if type(val) is str:
            if val.upper() in ('YES', 'TRUE', '1', 'NO', 'FALSE', '0'):
                retVal = True
        return retVal

    def getBool(self, val):
        retVal = val
        if type(val) is str:
            if val.upper() in ('YES', 'TRUE', '1'):
                retVal = True
            elif val.upper() in ('NO', 'FALSE', '0'):
                retVal = False
            elif val.isdigit():
                val = int(val)
                if val:
                    retVal = True
                else:
                    retVal = False
        elif type(val) is int:
            if val:
                retVal = True
            else:
                retVal = False
        return retVal

    def getConfigDict(self, checkForBool=False):
        sections = self.confPars.sections()
        retDict = {}
        for section in sections:
            if not retDict.has_key(section):
                retDict[section] = {}
            items = self.confPars.options(section)
            for item in items:
                retDict[section][item] = self.confPars.get(section, item)
                if checkForBool:
                    if self.couldBeBool(retDict[section][item]):
                        retDict[section][item] = self.getBool(retDict[section][item])
        return retDict

