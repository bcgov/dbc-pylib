"""

About
=========
:synopsis:     Quick and dirty database abstraction layer
:moduleauthor: Kevin Netherton
:date:         5-21-2014
:description:  Yes could have used something like sqlalchemy.  This is
               just a simple poller app so don't see the need for a
               full on database abstraction layer and the extra time
               involved with re-writing queries to use sqlalchemy.


Dependencies:
-------------------
Relies on the excellent cx_Oracle module.
http://cx-oracle.sourceforge.net/

Also relies on the AppConfigs module and that modules dependant
config file to get the database connection parameters file and
other database specific parameters.




API DOC:
===============
"""
import logging
import os

import cx_Oracle


class DbMethods(object):
    '''
    Just database methods.  No code in here that is specific to entering
    info into the esri stats database.

    :ivar confObj: the AppConfigs object, used to retrieve parameters
                   that are stored in the app. config file.
    :ivar connObj: The cx_Oracle connection object
    :ivar dbParams: Contains the database connection parameters.
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Logging set up in the module: %s" , os.path.basename(__file__))
        self.logger.debug("using this version of dblib")
        self.connObj = None  # the db connection object
        # a hash that will be populated with database connection
        # parameters by the method __getDbParams
        self.dbParams = {}


    def connectParams(self, user=None, pswd=None, instance=None):
        '''
        :param user: The user/schema that will be used to establish a connection
                     to the database
        :param pswd: The password for the schema above
        :param instance: The database instance to connect to

        '''
        if user:
            self.dbParams['username'] = user
        if pswd:
            self.dbParams['password'] = pswd
        if instance:
            self.dbParams['instance'] = instance
        try:
            self.connObj = cx_Oracle.connect(self.dbParams['username'],  # pylint: disable=no-member
                                             self.dbParams['password'],
                                             self.dbParams['instance'])
        except cx_Oracle.DatabaseError as e:
            msg = "problem encountered when trying to connect " + \
                  "to the database instance ({0}) using the " + \
                  'id ({1}), password {2}.  Database error is {3}'
            passwd = '*' * len(self.dbParams['password'])
            msg = msg.format(self.dbParams['instance'], self.dbParams['username'], passwd, e)
            self.logger.error(msg)
            msg = 'username type: {0}, pass type: {1}, instance type: {2}'
            msg = msg.format(type(self.dbParams['username']),
                             type(self.dbParams['password']),
                             type(self.dbParams['instance']))
            self.logger.info(msg)
            raise ConnectionError(self.dbParams['username'], self.dbParams['instance'])

    def connectNoDSN(self, user, pswd, serviceName, host, port=1521):
        '''
        Allows for the creation of a database connection when the
        client does not have a valid TNS file.  Allows you to connect
        using port and host name.

        :param  user: schema that you are using to connnect to the database
        :type user: str
        :param  pswd: password that goes with the schema
        :type pswd: str
        :param  serviceName: The database serviceName (service_name) that is being connected to.
        :type serviceName: str
        :param  host: The host that the serviceName resides on
        :type host: str
        :param  port: the port that the database listener is attached to.
        :type port: int
        '''
        try:
            clientVer = cx_Oracle.clientversion()
            self.logger.debug("client version: %s", clientVer)

            cxOraPath = os.path.abspath(cx_Oracle.__file__)
            self.logger.debug("cx_oracle path is: %s", cxOraPath)

            # dsn = cx_Oracle.makedsn(host, port, service_name=serviceName)
            dsn = cx_Oracle.makedsn(host, port, service_name=serviceName)  # pylint: disable=no-member
            self.logger.info("successfully connected to host/sn %s/%s", host, serviceName)
        except Exception as e:  # pylint: disable=broad-except
            msg = u'Got an error trying to create the dsn using the ' + \
                  u'service_name keyword.  Trying with no keywords'
            self.logger.debug(msg)
            self.logger.debug(repr(e))
            msg = u'input params are, host: {0}, port: {1}, inst {2}'
            msg = msg.format(host, port, serviceName)
            dsn = cx_Oracle.makedsn(host, port, serviceName).replace(u'SID', u'SERVICE_NAME')  # pylint: disable=no-member
            self.logger.debug(u'dsn returned is: %s', dsn)
        self.connectParams(user, pswd, dsn)

    def commit(self):
        '''
        commits the current connection
        '''
        self.connObj.commit()

    def rollback(self):
        '''
        Rolls back any transactions that have not previously been committed
        '''
        self.connObj.rollback()

    def executeOracleSqlNoReturn(self, sqlToExecute, values=None):
        '''
        Executes a sql statement then closes the cursor and cleans it up
        does not return anything.  The sql statement is also committed.

        This is the way to send DML or DDL statements to the database.

        :param  sqlToExecute: sql statement to be executed
        :type sqlToExecute: string
        '''
        curObj = self.connObj.cursor()
        if values:
            curObj.execute(sqlToExecute, values)
        else:
            curObj.execute(sqlToExecute)
        curObj.close()
        del curObj

    def executeOracleSql(self, sqlToExecute, values=None, outputsize=None):
        '''
        Executes sql and returns the cursor object which will contain the
        result set.

        :param  sqlToExecute: sql statement to execute
        :type sqlToExecute: string

        :returns: database cursor object that contains the results of the sql
                  statement
        :rtype: database connection object.
        '''
        curObj = self.connObj.cursor()
        if outputsize:
            curObj.setoutputsize(outputsize)
        if values:
            curObj.execute(sqlToExecute, values)
        else:
            curObj.execute(sqlToExecute)
        return curObj

    def executeProcedure(self, command, args):
        self.logger.debug("trying to execute procedure: %s", command)
        if not isinstance(args, list):
            msg = 'To run a procedure the arguments need to be provided as a ' + \
                  'list.  YOu provided the args: {0} which has a type: {1}'
            msg = msg.format(args, type(args))
            self.logger.error(msg)
            raise ValueError(msg)
        # creating cursor...
        curObj = self.connObj.cursor()
        # curObj.callproc('DBMS_MVIEW.REFRESH', [schemaMview, 'c'])
        curObj.callproc(command, args)
        self.logger.debug("ran procedure: %s with args %s ", command, args)
        return curObj

    def getCursor(self):
        '''
        Returns a database cursor object

        :returns: cx_Oracle cursor
        :rtype: cx_Oracle cursor
        '''
        curObj = self.connObj.cursor()
        return curObj

    def objExists(self, schema, objType, objName, connObj=None):  # pylint: disable=too-many-branches
        '''
        Receives a schema name, database object type, database object
        name and a connection object.  Returns a boolean value indicating
        whether there is an object with that name and type in the
        database

        :param  schema: schema name
        :type schema: string
        :param  objType: object type, example 'TABLE', 'VIEW', 'INDEX' etc.
        :type objType: string
        :param  objName: name of the database object.
        :type objName: string
        :param  connObj: database connection object that implements the
                         python database api 2.0.
        :type connObj: database connection object

        :returns: Describe the return value
        :rtype: boolean
        '''
        curObj = None
        if connObj is None:
            connObj = self.connObj

        schema = schema.upper()
        objType = objType.upper()
        objName = objName.upper()

        if objType.upper() == 'TABLES' or objType.upper() == 'TABLE':
            if schema != None:
                sql = 'select * from all_tables where table_name = \'' + \
                      objName.upper() + '\' and ' + \
                      'owner = \'' + schema.upper() + '\''
                curObj = self.executeOracleSql(sql)
            else:
                sql = 'select * from all_tables where table_name = \'' + \
                      objName.upper() + '\''
                curObj = self.executeOracleSql(sql)

        elif objType.upper() == 'INDEX' or objType.upper() == 'INDEXES':
            whereClause = ' where index_name = \'' + objName.upper() + '\''
            if schema:
                whereClause = whereClause + ' and  owner = \'' + schema.upper() + '\''
            sql = 'select index_name from all_indexes ' + whereClause
            curObj = connObj.cursor()
            curObj.execute(sql)
        elif objType.upper() == 'VIEW' or objType.upper() == 'VIEWS':
            whereClause = ' where view_name = \'' + objName.upper() + '\''
            if schema:
                whereClause = whereClause + ' and  owner = \'' + schema.upper() + '\''
            sql = 'select view_name from all_views ' + whereClause
            curObj = connObj.cursor()
            curObj.execute(sql)
        elif objType.upper() == 'MATERIALIZEDVIEW' or objType.upper() == 'MV' or \
             objType.upper() == 'MVIEW' or objType.upper() == 'MATERIALIZED VIEW':
            # all_mviews
            whereClause = ' where MVIEW_NAME = \'' + objName.upper() + '\''
            if schema:
                whereClause = whereClause + ' and  owner = \'' + schema.upper() + '\''
            sql = 'select MVIEW_NAME from all_mviews ' + whereClause
            curObj = connObj.cursor()
            curObj.execute(sql)
        elif objType.upper() == 'DB_LINK' or objType.upper() == 'DBLINK':
            whereClause = ' where DB_LINK = \'' + objName.upper() + '\''
            # table = 'DBA_DB_LINKS'
            table = 'ALL_DB_LINKS'
            if schema:
                whereClause = whereClause + ' and  owner = \'' + schema.upper() + '\''
            sql = 'select DB_LINK from {0} {1} '.format(table, whereClause)
            self.logger.debug("sql: %s", sql)
            curObj = connObj.cursor()
            curObj.execute(sql)
        else:
            raise 'FunctionalityNotDefinedError'( 'Functionality for the object type ' + objType + \
                  ' is not yet defined!')
        row = curObj.fetchone()
        retval = bool(row)
        curObj.close()
        del curObj
        return retval

    def getDbLinks(self, schema):
        '''
        ??? not sure why this is here, leaving in case its required for now.
        '''
        msg = 'Deprecated!  dont use this method.  schema you sent is: {0}'
        msg = msg.format(schema)
        self.logger.error(msg)

    def getFromDb(self, dataList, dbTable, dbCodeCol, dbValuesCol):
        '''
        This is generic method for extracting information from the
        database.  Creating a generic method so that I don't have to
        create a separate method to extract product, user, and org
        information from the database.  Data needs to be extracted
        from the db to enter it, as the extraction process provides
        us the code values for various data values.  These codes
        are necessary for the normalization of the information in
        the database

        :param  dataList: a list of the values that are to be entered
                          into the database.
        :type dataList: list
        :param  dbTable: The name of the lookup table that must contain
                         entries for all the values in the previous list
                         dataList
        :type dbTable: string
        :param  dbCodeCol: This is the column in the previous table that
                           contains the database codes.  This is the column
                           that establishes the relationship between the
                           lookup table and the actual data table.
        :type dbCodeCol: string
        :param  dbValues: The column in the database that contains the
                          names / descriptions for the values that need to
                          be enteered.  This is where the values described in
                          the parameter dataList exist.
        :type dbValues: string
        '''
        def xrange(x):
            return iter(range(x))

        in_clause = ', '.join([':id%d' % x for x in xrange(len(dataList))])
        # dbFormattedList = self.quoteStrings(dataList)
        sql = 'SELECT ' + \
              dbCodeCol + ' codes, ' + \
              dbValuesCol + ' vals ' + \
              ' FROM ' + \
               dbTable + \
               ' WHERE ' + \
               ' ' + dbValuesCol + '  in ( %s )' % in_clause

        self.logger.debug("sql: " + str(sql))

        # if type(dataList) is not list:
        if not isinstance(dataList, list):
            dataList = list(dataList)
            # print 'list dataList:', dataList

        cur = self.executeOracleSql(sql, dataList)
        retList = []
        for line in cur:
            inList = [line[0], line[1]]
            retList.append(inList)
        return retList

    def closeDbConnection(self):
        '''
        closes the database connection
        '''
        self.connObj.close()


class ConnectionError(cx_Oracle.DatabaseError):  # pylint: disable=too-few-public-methods, no-member
    '''
    A custom error, to help define and provide more useful information back when
    problems encountered trying to connect to a database

    '''

    def __init__(self, schema, servicename, msg=None):  # pylint: disable=invalid-name
        if msg is None:
            # Set some default useful error message
            msg = "Unable to connect to the database: {0} using the account: " + \
                  "{1} and the password provided"
            msg = msg.format(servicename, schema)
        super(ConnectionError, self).__init__(msg)


