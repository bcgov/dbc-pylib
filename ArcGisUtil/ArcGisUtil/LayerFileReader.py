'''
Created on Aug 15, 2014

@author: kjnether

Some simple code used to read information from esri layer files.  Primarily
used to populate GWIP tables used by the custom layer tool.

'''
import logging
import os
import platform
import archook

# setup for arcpro paths
archook.get_arcpy(pro=True)
import arcpy

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
        self.layerPropertyList = [
            'dataSource', 'connectionProperties', 'name', 'longName',
            'CREDITS', 'definitionQuery', 'maxThreshold',
            'minThreshold', 'transparency', 'contrast', 'brightness']

    def createSDEConnection(self, database_platform, instance):
        '''
        :param database_platform: Specifies the database management system platform to which the connection will be made. The following are valid options: BIGQUERY, DAMENG, DB2, ORACLE, POSTGRESQL, REDSHIFT, SAP HANA, SNOWFLAKE, SQL_SERVER, TERADATA
        :type: str

        :param instance: The database server or instance to which the connection will be made.
        :type: str

        Creates a arc sde connection file in the data directory named
        TempConnection.sde if the file already exists it will be deleted.
        '''
        connFile = os.path.join(self.dataDir, 'TempConnection' + '.sde')
        if os.path.exists(connFile):
            self.logger.debug("deleting and recreating the connection file")
            os.remove(connFile)
        self.logger.debug("Creating the connection file...")
        arcpy.management.CreateDatabaseConnection(
            self.dataDir, "TempConnection", database_platform, instance,
            "DATABASE_AUTH", self.user, self.passwd, "SAVE_USERNAME")
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
        table_name     - Name of the table that the layer file hits in
                         the schema
                        (from parsing the feature_class from lyr.datasetName)
        description    - Comes from the sub directory that the .lyr files
                         are found in. for example:
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
        self.logger.info(u'Layer Object (lyrObj) Created: %s', lyrObj)
        lyrs = lyrObj.listLayers()
        lyrInfo = []

        for lyr in lyrs:
            if lyr.isGroupLayer:
                # basically if its a group layer skip it
                for prop in self.layerPropertyList:
                    if lyr.supports(prop.upper()):
                        val = eval('lyr.' + prop)
                        self.logger.debug(u'GROUPLAYER: {0}:{1}'.format(prop,
                                                                        val))
            else:
                self.logger.info(f"adding layer : {lyr.name}")
                retData = self.reportLyer(lyr)
                retData['LayerFullFilePath'] = srcLyrFile
                lyrInfo.append(retData)
        return lyrInfo

    def reportLyer(self, inLayer):
        '''
        :param inLayer: the input layer containing information in a layer file.

        Reads pertinent properties from the layer file and adds the information
        to the log.
        '''
        retData = {}
        for prop in self.layerPropertyList:
            retData[prop] = ''
            if inLayer.supports(prop.upper()):
                val = eval('inLayer.' + prop)
                self.logger.debug(u"    {0}:{1}".format(prop, val))
                retData[prop] = val
            else:
                self.logger.debug(u"    {0}:{1}".format(prop, u'None'))
                retData[prop] = None
        return retData
