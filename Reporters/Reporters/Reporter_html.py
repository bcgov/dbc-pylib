'''
Created on May 2, 2018

@author: kjnether
'''
import logging
import os.path

import Constants
import Reporters.Report_abc
import jinja2


class Report_html(Reporters.Report_abc.ReporterBase):

    def __init__(self, outputFile):
        self.logger = logging.getLogger(__name__)
        self.outputFile = outputFile

        self.htmlTemplateFile = u'page_tableTemplate.html'
        htmlTemplateFullPath = os.path.join(os.path.dirname(__file__))
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader([htmlTemplateFullPath]))

        self.data = []
        self.headerLength = None
        self.header = None

        self.Rows = []

        self.pageTitle = u'FMW Source / Destinations'

    def render(self):
        tmplate = self.env.get_template(self.htmlTemplateFile)
        rendered = tmplate.render(title=u'FME Transformer Report',
                                  Columns=self.header,
                                  rows=self.Rows,
                                  pageTitle=self.pageTitle)
        fh = open(self.outputFile, 'w')
        fh.write(rendered)
        fh.close()

    def setHeader(self, header):
        if isinstance(header, basestring):
            msg = u'expecting the header to be a list / iterable type object, you ' + \
                  u'provided an object of type: {0}'
            msg = msg.format(type(header))
            self.logger = logging.getLogger(__name__)
            raise TypeError, msg
        self.header = header

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
            msg = u'you provided a header map with a different number of values ' + \
                  u'than the header, header map has {0} values while the header ' + \
                  u'contains {1} valures'
            msg = msg.format(len(headerDataMap), len(self.header))
            self.logger.error(msg)
            raise ValueError, msg

        # take the list and create a dictionary to allow
        # mapping back and forth easily between these values
        columnEnum = Constants.reportColumns
        self.logger.debug(u"column enum: {0}".format(columnEnum))

        enumToColumns = {}
        columnsToEnum = {}
        for colCnt in range(0, len(self.header)):
            enumToColumns[self.header[colCnt]] = headerDataMap[colCnt]
            columnsToEnum[headerDataMap[colCnt]] = self.header[colCnt]

            if not columnEnum.has_value(headerDataMap[colCnt].value):
            # if not headerDataMap[colCnt] in columnEnum.__members__:
                self.logger.debug(u"headerDataMap[colCnt] = {0}".format(headerDataMap[colCnt]))
                msg = u'your map contains a value that is not defined in the enumeration' + \
                      u'Constants.reportColumns'

                self.logger.error(msg)
                raise ValueError, msg

        # self.headerEnumToColumnNames = enumToColumns
        # self.headerColumnsToEnum = columnsToEnum
        self.headerEnumToColumnNames = columnsToEnum
        self.headerColumnsToEnum = enumToColumns

    def addNewFMW(self, parser):
        '''
        :param parser: a parser object that can be used to easily retrieve
                       information from an FMW file.
        :type parser: FMWParser.FMWParser
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

        colEnm = Constants.reportColumns

        # going to first write the data to a structure using enumerations
        data = {}
        data[colEnm.fmwWorkspaceName] = wrkspaceName
        data[colEnm.sources] = u','.join(srcNamesList)
        data[colEnm.destinations] = u','.join(destNamesList)
        data[colEnm.transformerCount] = str(len(transformerNames))
        data[colEnm.transformerList] = u','.join(transformerNames)

        # now going to map the data to the columns that are in the report
        row = {}
        for enumVal in self.headerEnumToColumnNames.keys():
            self.logger.debug(u"enumVal: {0}".format(enumVal))
            self.logger.debug(u"self.headerEnumToColumnNames[enumVal]: {0}".format(self.headerEnumToColumnNames[enumVal]))
            columnName = self.headerEnumToColumnNames[enumVal]
            row[columnName] = data[enumVal]

        self.Rows.append(row)
