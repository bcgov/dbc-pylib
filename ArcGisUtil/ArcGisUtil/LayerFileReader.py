'''
Created on Aug 15, 2014

@author: kjnether

Some simple code used to read information from esri layer files.  Primarily
used to populate GWIP tables used by the custom layer tool.

'''
import logging
import os

import arcpy  # @UnresolvedImport


class ReadLayerFiles(object):
    '''
    class used to support reading information from esri layer files.

    functionality included to help with creation of connections to SDE
    '''

    def __init__(self, lyrLib, scrtchSpc, user, passwd):
        self.logger = logging.getLogger(__name__)
        self.version = "9.3"  # other values: "10.0", "10.1", "10.2"
        self.lyrFileRootDir = lyrLib
        self.dataDir = scrtchSpc
        self.user = user
        self.passwd = passwd

    def createSDEConnection(self, sdeServer, sdePort):
        '''
        :param sdeServer: the sde host to connect to
        :type sdeServer: str

        :param sdePort: the sde port that the application server is listening on
        :type str:

        Creates a arc sde connection file in the data directory named
        TempConnection.sde if the file already exists it will be deleted.
        '''
        connFile = os.path.join(self.dataDir, 'TempConnection' + '.sde')
        if os.path.exists(connFile):
            # print u'deleting and recreating the connection file'
            self.logger.debug("deleting and recreating the connection file")
            os.remove(connFile)
        self.logger.debug("Creating the connection file...")
        arcpy.CreateArcSDEConnectionFile_management(
            self.dataDir, "TempConnection", sdeServer, sdePort, "", "DATABASE_AUTH", \
            self.user, self.passwd, "SAVE_USERNAME", "SDE.DEFAULT", "SAVE_VERSION")
        self.logger.debug("Connection file successfully created...")

    def readLyrFile(self, srcLyrFile):
        '''
        Going into the layer file and extracting the following information
        to put into the GWIP database.

        layer file name - the name of the .lyr file with out the suffix (.lyr)
        layer_name     - Name of the layer in the file.
                         from the lyr.name
        schema         - Name of the schema the layer file hits
                         (from parsing the schema off of lyr.datasetName)
        table_name     - Name of the table that the layer file hits in the schema
                        (from parsing the feature_class from lyr.datasetName)
        description    - Comes from the sub directory that the .lyr files are found in.
                         for example:
                         $(LAYERLIBDIR)/Administrative Boundaries/
                              First_Nation_Traditional_Use_Sites_All.lyr
                         the description would be 'Administrative Boundaries'
        dataset_type   - ???
                         (get from serviceProperties.ServiceType)

        :param  srcLyrFile: a string describing the input layer file that is to
                            be read.
        :type srcLyrFile: str
        '''
        self.logger.info(u'inlayer file is: %s', srcLyrFile)
        lyrObj = arcpy.mp.LayerFile(srcLyrFile)
        
        
        
        
        #if lyrObj.supports('description'):
        #    self.logger.debug(u'DESCRIPTION: %s', lyrObj.description)
        lyrInfo = []
        if lyrObj.isGroupLayer:
            propertyList = ['workspacePath', 'description', 'serviceProperties', \
                            'datasetName', 'dataSource', 'name', 'longName']
            for prop in propertyList:
                if lyrObj.supports(prop):
                    val = eval('lyrObj.' + prop)
                    self.logger.debug(u'GROUPLAYER: {0}:{1}'.format(prop, val))
            lyrList = arcpy.mp.ListLayers(lyrObj)

            for lyr in lyrList:
                retData = self.reportLyer(lyr)
                retData['LayerFullFilePath'] = srcLyrFile
                lyrInfo.append(retData)
        else:
            retData = self.reportLyer(lyrObj)
            retData['LayerFullFilePath'] = srcLyrFile
            lyrInfo.append(retData)
        return lyrInfo

    def reportLyer(self, inLayer):
        '''
        :param inLayer: the input layer containing information in a layer file.

        Reads pertinent properties from the layer file and adds the information
        to the log.
        '''

        propertyList = ['workspacePath', 'description', 'serviceProperties',
                        'datasetName', 'dataSource', 'name', 'longName']
        retData = {}
        for prop in propertyList:
            retData[prop] = ''
            if inLayer.supports(prop):
                val = eval('inLayer.' + prop)
                self.logger.info(u"    {0}:{1}".format(prop, val))
                retData[prop] = val
            else:
                self.logger.info(u"    {0}:{1}".format(prop, u'None'))
                retData[prop] = None
        return retData
