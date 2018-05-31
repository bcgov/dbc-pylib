'''
Created on Sep 8, 2014

@author: kjnether
'''

import logging
import os.path
import sys

import cx_Oracle

import DbLib


class LRDW():
    '''
    Various commonly used queries bundled up into a python class
    '''

    def __init__(self, configDict, credsFileDir=None):
        self.logger = logging.getLogger(__name__)
        self.db = LRDWDbLib(configDict, credsFileDir)

    def getSchema(self, tableName):
        '''
        :param tableName: name of the table.
        Returns a list of schemas that contain the given table name
        '''
        sql = 'SELECT ' + \
              ' owner from all_tables where table_name = \'' + \
              str(tableName.upper()) + "'"
        cur = self.db.executeOracleSql(sql)
        schemas = []
        for i in cur:
            schemas.append(i[0])
        return schemas


class LRDWDbLib(DbLib.DbMethods):

    def __init__(self, configDict, credsFileDir=None):
        self.logger = logging.getLogger(__name__)
        DbLib.DbMethods.__init__(self)
        self.connParamsFile = configDict['securitycredsfile']
        self.instanceName = configDict['instancename']
        self.server = configDict['server']
        self.port = configDict['port']
        self.connect2(credsFileDir)

    def connect(self):
        # this method gets called by the inherited class.  Needs
        # to be overridden.  Later will call connect2 that does
        # the acutal connection to the database.
        pass

    def connect2(self, credsFileDir=None):
        '''
        populates the class variables that are used to connect
        to the database.  Going to create our own dsn in memory
        and then use it.  Allows us to define a connection with
        server / port / instance name
        '''
        if credsFileDir:
            fileName = os.path.join(credsFileDir, self.connParamsFile)
        else:
            fileName = os.path.join(os.path.dirname(__file__), self.connParamsFile)
        fh = open(fileName, 'r')
        usr = fh.readline()
        passwd = fh.readline()
        fh.close()
        usr = usr.strip()
        passwd = passwd.strip()
        dsn = cx_Oracle.makedsn(self.server, self.port, service_name=self.instanceName)
        self.connObj = cx_Oracle.connect(usr, passwd, dsn)
