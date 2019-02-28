'''
Created on Feb 26, 2019

@author: kjnether

contains functionality to identify what the install dir is for python 3
for arcgis pro, and then add those paths to PATH and PYTHONPATH so that
the libraries can be properly imported.
'''

import winreg
import logging
import os
import sys


class RegistryReader(object):
    '''
    Simplifies access to registry keys and items, keys are the hierarchical
    names that values are organized under.  Items are the actual values that
    are associated with the various keys
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def getKeyValues(self, keys):
        self.logger.debug("keys: %s", keys)
        keyStr = '\\'.join(str(e) for e in keys)
        self.logger.debug('keyStr: %s', keyStr)
        explorer = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, keyStr, 0,
                                  winreg.KEY_READ)
        subKeys = []
        try:
            i = 0
            while 1:
                asubkey = winreg.EnumKey(explorer, i)
                subKeys.append(asubkey)
                i += 1
        except WindowsError:
            self.logger.debug('Iteration is now complete')
        return subKeys

    def getKeyItems(self, keys):
        keyStr = '\\'.join(str(e) for e in keys)
        self.logger.debug('keyStr: %s', keyStr)
        explorer = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, keyStr, 0,
                                  winreg.KEY_READ)
        values = []
        try:
            cnt = 0
            while True:
                t = (winreg.EnumValue(explorer, cnt))
                values.append(t)
                cnt += 1
        except WindowsError:
            self.logger.debug('Iteration is now complete')
        return values


class Py3PathRegistry(RegistryReader):
    '''
    Methods to extract the python 3 install location from the arcgis pro
    installation.
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.startKeys = ['SOFTWARE']
        self.esriKey = 'ESRI'

    def getKeys(self, keys, srchKey, errorMsg):
        '''
        queries the regirstry for the path defined in the list keys,
        then triggers an error if the srchKey is not found
        :param keys: a list of the keys in the registry to find
        :param srchKey: the key that we are looking for in the defined
                        path provided in the param keys
        :param errorMsg: the text string to include if the path cannot
                         be found

        '''
        self.logger.debug(f"keys: {keys}")
        currentKeys = self.getKeyValues(keys)
        self.logger.debug(f"found the keys: {keys} in {currentKeys}")
        if srchKey not in currentKeys:
            self.logger.error(errorMsg)
            raise ArcProRegistryPathNotFound(errorMsg)
        self.logger.debug(f"{keys}  {srchKey}  {currentKeys}")

    def getArcProItems(self):
        '''
        :return: the root path in the registry to arcpro
        '''
        # sw has esri
        keys = self.startKeys[0:]
        srchKey = self.esriKey
        errMsg = f"Cannot find: {srchKey} key in {keys}"
        self.getKeys(keys, srchKey, errMsg)

        # esri has arcpro
        keys.append(srchKey)
        srchKey = 'ArcGISPro'
        errMsg = f"Cannot find: {srchKey} key in {keys}"
        self.getKeys(keys, srchKey, errMsg)

        # get the arcpro tags
        keys.append(srchKey)
        regloc = '->'.join(keys)
        self.logger.info("getting install info from the registry location:" + \
                         f" {regloc}")
        items = self.getKeyItems(keys)
        return items

    def extractFromItems(self, inputItems, extractItems):
        '''
        :param inputItems: items extracted from registry keys, has a format
                           like [('InstallDir', 'E:\\sw_nt\\ArcGIS\\Pro\\', 1),
                           ('ProFlexNetService', '11.14.1.3', 1),
                           ('BuildNumber', '10257', 1), ... ]
        :param extractItems: a list of the item names that you want to
                             extract and return as a dictionary
        '''
        itemDict = {}
        for item in inputItems:
            if item[0] in extractItems:
                itemDict[item[0]] = item[1]
        self.logger.debug(f'itemDict: {itemDict}')
        return itemDict
        # root pro install is in InstallDir

    def getArcProRootPath(self):
        '''
        :return: the root directory for the python arc pro install
        '''
        items = self.getArcProItems()
        # looking to get the keys: PythonCondaEnv and PythonCondaRoot
        self.logger.debug(f'items: {items}')
        searchItems = ['InstallDir']
        itemDict = self.extractFromItems(items, searchItems)
        # root pro install is in InstallDir
        self.logger.debug(f"arcpro root install dir: {itemDict['InstallDir']}")
        return itemDict['InstallDir']

    def getArcProPythonPath(self):
        '''
        :return: the root directory for the python arc pro install
        '''
        items = self.getArcProItems()
        # looking to get the keys: PythonCondaEnv and PythonCondaRoot
        self.logger.debug(f'items: {items}')
        searchItems = ['PythonCondaEnv', 'PythonCondaRoot', 'InstallDir']
        itemDict = self.extractFromItems(items, searchItems)

        # root pro install is in InstallDir
        installPath = os.path.join(itemDict['PythonCondaRoot'], 'envs',
                                   itemDict['PythonCondaEnv'])
        self.logger.debug(f"installPath: {installPath}")
        return installPath

    def getPaths2Add(self):
        '''
        gets the root install for arcpro
        '''
        # creating the paths that are built off of the root arcpro
        # installation
        paths2Add = []
        proRootPath = self.getArcProRootPath()
        subDirs2Add = ['bin', 'Resources/ArcPy', 'Resources/ArcToolBox',
                       'Resources/ArcToolBox/Scripts']
        for subdir in subDirs2Add:
            subDirPath = os.path.join(proRootPath, subdir)
            paths2Add.append(subDirPath)

        # creating the paths that are built off of the root python 3
        # pro installation
        pyPathRoot = self.getArcProPythonPath()
        pyPaths2Add = ['Library/bin', 'Library/lib', 'DLLs', 'Lib',
                       'Lib/site-packages']
        for pyPathStub in pyPaths2Add:
            subDirPath = os.path.join(pyPathRoot, pyPathStub)
            paths2Add.append(subDirPath)
        return paths2Add

    def addToPythonPath(self):
        '''
        retrieves the arcpro install directories from the registry then
        uses that information to create the paths necessary to successfully
        import arcpy and adds them to PATH env var
        '''
        self.logger.info("updating the PYTHONPATH to find python3 / arcpy")

        proPaths = self.getPaths2Add()
        for i in proPaths:
            if i not in sys.path:
                sys.path.append(i)
                self.logger.info(f"adding path: {i}")

    def addToPATHEnvVar(self):
        self.logger.info("updating the PATH env var to find python3 / arcpy")
        proPaths = self.getPaths2Add()
        pthList = os.environ['PATH'].split(';')
        for i in proPaths:
            if i not in pthList:
                pthList.append(i)
                self.logger.info(f"adding path: {i}")
        os.environ['PATH'] = ';'.join(pthList)


class ArcProRegistryPathNotFound(Exception):
    """creating a new exception type for when the expected path to arcgis
    pro cannot be found in the registry"""
    pass
