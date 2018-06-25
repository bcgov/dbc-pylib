'''
Created on May 2, 2018

@author: kjnether
'''
import Reporters.Report_abc
import logging
import Constants


class Report_md(Reporters.Report_abc.ReporterBase):

    def __init__(self, outputFile):
        self.logger = logging.getLogger(__name__)
        self.outputFile = outputFile
        self.fh = open(self.outputFile, u'w')
        self.data = []
        self.headerLength = None
        self.header = None

    def render(self):
        self.fh.write(self.header)
        sepList = [u'----'] * len(self.data[0])
        separator = u'| {0} |\n'.format(' | '.join(sepList))
        self.fh.write(separator)
        for row in self.data:
            rowStr = u'| {0} |\n'.format(u' | '.join(row))
            self.fh.write(rowStr)
        self.fh.flush()
        self.fh.close()
        self.logger.debug(u"report %s should now exist!", self.outputFile)

    def setHeader(self, header):
        '''
        sets the header for the report, 
        :param header: the header for the report
        :type param: list
        '''
        if not isinstance(header, list):
            msg = u'expecting the header to be sent as a list.  You provided a ' + \
                  u'%s type'
            self.logger.error(msg, type(header))
            raise TypeError, msg
        self.headerLength = len(header)
        headerStr = '| {0} |\n'.format(' | '.join(header))
        self.header = headerStr

    def addNewFMW(self, parser):
        '''
        Gets an FMW parser to write to the report file
        :param parser: a parser object that was derived from an FMW file.
        :type parser:
        '''
        wrkspcObj = parser.getFMEWorkspace()
        wrkspaceName = wrkspcObj.getWorkspaceName()

        # now get the feature classes
        featCls = wrkspcObj.getFeatureClasses()
        sources = featCls.getSources()
        srcNamesList = []
        for src in sources:
            srcNamesList.append(src.getFeatureClassDescriptiveName())

        dests = featCls.getDestinations()
        destNamesList = []
        for dest in dests:
            destNamesList.append(dest.getFeatureClassDescriptiveName())

        trans = wrkspcObj.getTransformers()
        transformerNames = trans.getTransformerNames()

        # params = wrkspcObj.getPublishedParameters()
        # paramNames = params.getPublishedParameterNames()
        sourcesStr = u','.join(srcNamesList)
        destStr = u','.join(destNamesList)
        transStr = u','.join(transformerNames)
        transLenStr = str(len(transformerNames))

        row = [wrkspaceName, sourcesStr, destStr, transStr, transLenStr]

        # rowStr = self.getRow(wrkspaceName, srcNamesList, destNamesList, transformerNames)
        if len(row) <> self.headerLength:
            msg = u'Tried to create a row with a different number of elements as ' + \
                  u'defined in the header.  Elems in row: %s elems in header: %s'
            self.logger.error(msg, len(row), self.headerLength)
            raise ValueError, msg
        self.data.append(row)
        
    def addHeaderMap(self, headerDataMap):
        '''
        This object is used to identify what the various headers actually
        contain, This allows the addNewFMW method to know what column to
        put the data into.

        contains a list:
          - same number of items in the header
          - order maps the column names to the data they contain
          - use the const.reportColumns as the map

        example:
          if the header has the values:
             - fme workspace name
             - fme workspace sources
             - fme workspace destinations
             - transformer list

           then the map would look like:
             [reportColumns.fmwWorkspaceName,
             reportColumns.sources
             reportColumns.destinations
             reportColumns.transformerList]

        '''
        if len(headerDataMap) <> len(self.header):
            msg = 'you provided a header map with a different number of values ' + \
                  'than the header, header map has {0} values while the header ' + \
                  'contains {1} valures'
            msg = msg.format(len(headerDataMap), len(self.header))
            self.logger.error(msg)
            raise ValueError, msg

        # take the list and create a dictionary to allow
        # mapping back and forth easily between these values
        columnEnum = Constants.reportColumns

        enumToColumns = {}
        columnsToEnum = {}
        for colCnt in range(0, len(self.header)):
            enumToColumns[self.header[colCnt]] = headerDataMap[colCnt]
            columnsToEnum[headerDataMap[colCnt]] = self.header[colCnt]
            if not columnEnum.has_value(headerDataMap[colCnt]):
                msg = 'your map contains a value that is not defined in the enumeration' + \
                      'Constants.reportColumns'
                self.logger.error(msg)
                raise ValueError, msg

        self.headerEnumToColumnNames = enumToColumns
        self.headerColumnsToEnum = columnsToEnum
