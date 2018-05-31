'''
Created on Dec 8, 2017

@author: kjnether
'''
import cx_Oracle
import logging


class Iterator(object):
    '''
    This class allows you to define a database connection and a database
    query.  The class will allow you to iterate over the results of that
    query using a builtin python iterator.

    '''

    def __init__(self, connection, sql):
        # self.connection = DbConnection(user, pswd, host, servicename, port)
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        self.sql = sql
        self.results = None
        self.recordCnt = 0

    def __iter__(self):
        return self

    def next(self):
        '''
        returns the next row associated with the query.

        '''
        retVal = None
        if not self.results:
            self.runQuery()
        if self.recordCnt >= len(self.results):
            raise StopIteration
        else:
            retVal = self.results[self.recordCnt]
            self.recordCnt += 1
        return retVal

    def runQuery(self):
        '''
        run's the query that was set up, making the results available as an
        iterator
        '''
        self.logger.info("running the query: %s", self.sql)
        dbConn = self.connection.getConnection()
        cur = dbConn.cursor()
        cur.execute(self.sql)
        self.results = cur.fetchall()
        cur.close()
        self.recordCnt = 0

class DbConnection(object):
    '''
    used to create a database connection,
    '''

    def __init__(self, user, pswd, host, sn, port, pmpLabel):
        self.logger = logging.getLogger(__name__)
        self.user = user
        self.pswd = pswd
        self.host = host
        self.port = port
        self.pmpLabel = pmpLabel
        self.service_name = sn
        self.conn = None
        self.dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
        self.createConn()

    def getLabel(self):
        return self.pmpLabel

    def getHost(self):
        return self.host

    def getPort(self):
        return self.port

    def getServiceName(self):
        return self.service_name

    def createConn(self):
        self.close()
        self.conn = cx_Oracle.connect(self.user, self.pswd, self.dsn)
        self.logger.info("created a connection using schema %s", self.user)

    def getConnection(self):
        if not self.conn:
            self.createConn()
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
