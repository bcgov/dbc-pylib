'''
Created on Apr 17, 2018

@author: kjnether

This is another attempt at a simple parser that allows us to read the content
of an FMW file.
'''
import logging
import os.path
import pprint
import re

import FMWParserConstants
import lxml.objectify  # @UnresolvedImport


class FMWParser():
    '''
    This class is a high level class to the fmw document.  This
    class goes through the following pre-processing steps necessary to parse
    an fmw document:
        - reads through the document and separates the
          command line script, the xml and the map script
          portions of the file.
        - when the xml is separated it removes the preceding comment '#!' characters
          from the text
        - when reading the command line it separates the text that is just
          decoration from the text that actually defines the command line
          paramater.

    Once the various sections are separated the class then generates
    different objects for each portion of the document.  In doing this the
    interface for all three portions is to:

      a) send the text to parser, the parser rips through the text and
         creates the appropriate data object which has an interface
         that can be used to extract paramaters from that portion of
         the document.


    :ivar FMWFile: Describe the variable here!
    :ivar fmwReader: Describe the variable here!
    :ivar xmlElemTree: Describe the variable here!
    '''

    xmlElemTree = None
    fmwReader = None

    def __init__(self, fmwFile):
        self.logger = logging.getLogger(__name__)
        self.FMWFile = fmwFile
        self.xmlObj = None
        self.fmwReader = None

    def separateFMWComponents(self):
        '''
        FMW documents are made of three sets of information:
          a) The command line parameters (how to run the script from the
             command line
          b) XML
          c) FME specific lines (usually at the end of the doc following the
             tag that closes the WORKSPACE definition)

        This method will read through the doc, putting all these components
        into different in memory objects.
          a) self.xmlDoc - contains the xml components
          b) self.fmeCommand - contains the command line parameters.
          c) self.fmeScript - contains the fme specific information that
                              follows the closing of the root xml tag.

        _IN_SDE3MINX _IN_SDE3MINY _IN_SDE3MAXX _IN_SDE3MAXY _IN_SDE3WhereClause _IN_SDE3CLIP _IN_SDE3SEARCH_ENVELOPE_COORDINATE_SYSTEM _IN_SDE3SearchMethod _IN_SDE3RemoveTableQualifier _IN_SDE3SearchOrder _IN_SDE3SearchMethodFilter _IN_SDE3PersistentConnection _IN_SDE3SearchFeature _IN_SDE3ChildVersionName _TRANSACTION_INTERVAL _ADD_LAYERS_TO_EXISTING_TABLES _WRITER_MODE _TRANSACTION _REJECTED_PIPELINE_DIRECTORY _CONTINUE_TRANSLATION_BAD_DATA _MAX_OPEN_TABLES _INTEGER_OVERRIDE_DEFINITION _STRICT_LOAD _FORCE_IN_AGGREGATES _DEFAULT_Z_VALUE _LEAVE_LAYER_EXTENTS _SPLIT_DONUTS SDE30_OUT_RECONCILE_AND_POST SDE30_OUT_TABLES_TO_RECONCILE SDE30_OUT_WRITE_TO_CURRENT_STATE SDE30_OUT_DELETE_CHILD_AFTER_RECONCILE_AND_POST
        '''
        self.fmwReader = FMWRestruct(self.FMWFile)
        self.fmwReader.read()

    def parseXML(self):
        '''
        creates an 'objectified' object of the xml that was
        extracted from the FMW if it hasn't already been
        done

        '''
        if self.xmlObj is None:
            if self.fmwReader is None:
                self.separateFMWComponents()
            xmlList = self.fmwReader.getXML()
            xmlStr = '\n'.join(xmlList)
            self.xmlObj = lxml.objectify.fromstring(xmlStr)

    def readEverything(self):
        '''
        a debugging method that helps with debugging the xml
        parser
        '''
        self.parseXML()
        for appt in self.xmlObj.getchildren():
            self.logger.debug('attribs: %s', appt.attrib)
            self.logger.debug("%s => %s", appt.tag, appt.text)
            for e in appt.getchildren():
                self.logger.debug("  %s => %s", e.tag, e.text)
                for at in e.attrib:
                    self.logger.debug('   %s %s', at, e.attrib[at])
                for f in e.getchildren():
                    self.logger.debug("      %s => %s", f.tag, f.text)

    def getSourceDataSets(self):
        self.parseXML()
        dataSets = self.getDataSets()
        srcDataSets = []
        for dataset in dataSets:
            if dataset['IS_SOURCE'] == 'true':
                srcDataSets.append(dataset)
        return srcDataSets

    def getDataSets(self):
        self.parseXML()
        datasets = []
        children = self.xmlObj.DATASETS.countchildren()
        if children:
            for dataset in self.xmlObj.DATASETS.DATASET:
                dataSetPy = {}
                for attrib in dataset.attrib:
                    dataSetPy[attrib] = dataset.attrib[attrib]
                datasets.append(dataSetPy)
        return datasets

    def getDestDataSets(self):
        self.parseXML()
        dataSets = self.getDataSets()
        destDataSet = []
        for dataset in dataSets:
            if dataset['IS_SOURCE'] <> 'true':
                destDataSet.append(dataset)
        return destDataSet

    def addPublishedParameters(self, InParamSet):
        '''
        will rip through all the values in a 'InParamSet' searching for
        published parameters.  If pub params found the values for the
        pub params are substituted in, in place of the parameter name.
        '''
        # regex to search for pub params
        # moved the regex definitions to the constants to make it easier to
        # test them.
        # pubParamRegex = re.compile(r'^\s*\$\(([A-Za-z0-9_-]+)\)\s*$', re.IGNORECASE)
        # pubParamSchema = re.compile(r'^\s*\$\(([A-Za-z0-9_-]+)\)\.[A-Za-z0-9_-]\s*$', re.IGNORECASE)

        pubParamOnlyRegex = re.compile(FMWParserConstants.PUBPARAM_ONLY_REGEX, re.I)
        schemaOnlyRegex = re.compile(FMWParserConstants.PUBPARAM_SCHEMA_REGEX, re.I)
        featClsOnlyRegex = re.compile(FMWParserConstants.PUBPARAM_FEATURE_REGEX, re.I)

        params = self.getPublishedParams()
        self.logger.debug("params: {0}".format(params))
        for curEntry in InParamSet.keys():
            self.logger.debug("curEntry: {0}".format(curEntry))
            curValue = InParamSet[curEntry]

            # setting up the regex searches
            srchParamOnly = pubParamOnlyRegex.search(curValue)
            srchSchemaOnly = schemaOnlyRegex.search(curValue)
            srchFeatClsOnly = featClsOnlyRegex.search(curValue)

            self.logger.debug('curEntry: {0}'.format(curEntry))
            self.logger.debug('curValue: {0}'.format(curValue))

            # logic applied to the various searches
            if srchParamOnly:
                paramValue = self.extractAndReplaceParam(srchParamOnly, params)
                InParamSet[curEntry] = paramValue
                self.logger.info("substituting the value: %s with %s for the param %s",
                                  curValue, paramValue, curEntry)
            elif srchSchemaOnly:
                paramValue = self.extractAndReplaceParam(srchSchemaOnly, params)
                pubParmName = srchSchemaOnly.group(1)
                self.logger.debug("substituting (SchemaOnly) pubParmName: %s with %s", pubParmName, paramValue)
                # print 'pubParmName:', pubParmName
                InParamSet[curEntry] = InParamSet[curEntry].replace(pubParmName,
                                                                    paramValue)
            elif srchFeatClsOnly:
                paramValue = self.extractAndReplaceParam(srchFeatClsOnly, params)
                pubParmName = srchFeatClsOnly.group(1)
                self.logger.debug("substituting (FeatureOnly) pubParmName: %s with %s", pubParmName, paramValue)
                # print 'pubParmName:', pubParmName
                InParamSet[curEntry] = InParamSet[curEntry].replace(pubParmName,
                                                                    paramValue)

        return  InParamSet

    def extractAndReplaceParam(self, regex, params):
        '''
        :param regex: the re/search object that will be used to
                      extract the published parameter.
        :param params: The published parameters which are a list
                       of dictionaries with the keys DEFAULT_VALUE and
                       TYPE
                       
        DEST_DATASET_FGDB_1
        {'DEST_GEODATABASE': {'DEFAULT_VALUE': '\\\\data.bcgov\\wwwroot\\datasets\\4cf233c2-f020-4f7a-9b87-1923252fbc24\\ParcelMapBCExtract.zip\\ParcelMapBCExtract.gdb', 'TYPE': 'DEST_DATASET_FGDB_1 Destination Geodatabase:'}, 'DEST_DB_ENV_KEY': {'DEFAULT_VALUE': 'OTHR', 'TYPE': 'DLV%TST%PRD%DEV%OTHR Destination Database Keyword (DLV|TST|PRD|OTHR):'}, 'SRC_DATASET_FGDB_1': {'DEFAULT_VALUE': '\\\\data.bcgov\\data_staging\\BCGW\\land_ownership_and_status_pmbc_secure\\ParcelMapBCExtract.gdb', 'TYPE': 'Source Geodatabase:'}, 'LOG_FILE': {'DEFAULT_VALUE': 'import<space>DataBCFMWTemplate<lf>params<space>=<space>DataBCFMWTemplate.CalcParams<openparen>FME_MacroValues<closeparen><lf>return<space>params.getFMWLogFileRelativePath<openparen><closeparen><lf>', 'TYPE': 'Python Script:'}, 'SRC_FEATURE_1': {'DEFAULT_VALUE': 'Parcel_Polygon', 'TYPE': 'Source feature class:'}, 'DEST_FEATURE_1': {'DEFAULT_VALUE': 'Parcel_Polygon', 'TYPE': 'Destination feature class:'}}
       {'DEST_GEODATABASE': {'DEFAULT_VALUE': '\\\\data.bcgov\\wwwroot\\datasets\\4cf233c2-f020-4f7a-9b87-1923252fbc24\\ParcelMapBCExtract.zip\\ParcelMapBCExtract.gdb', 'TYPE': 'DEST_DATASET_FGDB_1 Destination Geodatabase:'}, 
        'DEST_DB_ENV_KEY': {'DEFAULT_VALUE': 'OTHR', 'TYPE': 'DLV%TST%PRD%DEV%OTHR Destination Database Keyword (DLV|TST|PRD|OTHR):'}, 
        'SRC_DATASET_FGDB_1': {'DEFAULT_VALUE': '\\\\data.bcgov\\data_staging\\BCGW\\land_ownership_and_status_pmbc_secure\\ParcelMapBCExtract.gdb', 'TYPE': 'Source Geodatabase:'}, 'LOG_FILE': {'DEFAULT_VALUE': 'import<space>DataBCFMWTemplate<lf>params<space>=<space>DataBCFMWTemplate.CalcParams<openparen>FME_MacroValues<closeparen><lf>return<space>params.getFMWLogFileRelativePath<openparen><closeparen><lf>', 'TYPE': 'Python Script:'}, 'SRC_FEATURE_1': {'DEFAULT_VALUE': 'Parcel_Polygon', 'TYPE': 'Source feature class:'}, 'DEST_FEATURE_1': {'DEFAULT_VALUE': 'Parcel_Polygon', 'TYPE': 'Destination feature class:'}}
        '''
        paramValue = None
        pubParmName = regex.group(1)
        self.logger.debug("found pub param and extracted: %s", pubParmName)
        util = Util()
        pubParmName = util.stripVariableNotations(pubParmName)
        # Now sub in the pub param from the pubparam list
        # don't sub in if the pub param is scripted
        self.logger.debug("pub param name: {0}".format(pubParmName))
        
        if pubParmName in params and params[pubParmName]['TYPE'] <> 'Python Script:':
            paramValue = params[pubParmName]['DEFAULT_VALUE']
        elif pubParmName not in params:
            # when fme parameters are linked to datasets they will take on this structure:
            # {'DEST_GEODATABASE': {'DEFAULT_VALUE': '\\\\data.bcgov\\wwwroot\\datasets\\4cf233c2-f020-4f7a-9b87-1923252fbc24\\ParcelMapBCExtract.zip\\ParcelMapBCExtract.gdb', 'TYPE': 'DEST_DATASET_FGDB_1 Destination Geodatabase:'}, 
            # in this case we need to fish this value out of the 'type'
            for iterParamName in params.keys():
                if pubParmName in params[iterParamName]['TYPE']:
                    paramValue = params[iterParamName]['DEFAULT_VALUE']
                    break
            if paramValue is None:
                msg = 'unable to extract the parameter value for the parameter ' + \
                      'name {0}.  variable params: {1}'
                msg = msg.format(pubParmName, params)
                raise ValueError, msg
        else:
            # just leave it as is by returning the parameter name
            # this is what the normal data would look like:
            # 'DEST_DB_ENV_KEY': {'DEFAULT_VALUE': 'OTHR', 'TYPE': 'DLV%TST%PRD%DEV%OTHR Destination Database Keyword (DLV|TST|PRD|OTHR):'}
            paramValue = pubParmName
        return paramValue

    def getFeatureTypes(self):
        '''
        Extracts the dataset and the feature types from the xml
        converts them into a python data strcture and returns them
        into a single data structure.

        Looks for the relationship between the datasets and connects
        them
        '''
        # gets the datasets
        # relationship between dataset and features types is built using
        # KEYWORD (dataset side) to KEYWORD (feature type side)
        datasets = self.getDataSets()

        self.parseXML()
        ftypes = []

        children = self.xmlObj.FEATURE_TYPES.countchildren()
        if children:
            for ftype in self.xmlObj.FEATURE_TYPES.FEATURE_TYPE:
                fypePy = {}
                for attribName in ftype.attrib:
                    fypePy[attribName] = ftype.attrib[attribName]
                    self.logger.debug("{0} - {1}".format(attribName, ftype.attrib[attribName]))
                    # print attribName, ftype.attrib[attribName]

                # deal with the attributes
                pyAtribs = []
                if hasattr(ftype, 'FEAT_ATTRIBUTE'):
                    for column in ftype.FEAT_ATTRIBUTE:
                        colDef = {}
                        for columnAtribName in column.attrib:
                            colDef[columnAtribName] = column.attrib[columnAtribName]
                        pyAtribs.append(colDef)

                    # populating published parameter references with values
                    fypePy = self.addPublishedParameters(fypePy)

                fypePy['COLUMNS'] = pyAtribs

                # connecting the dataset to the feature class
                for dataset in datasets:
                    if dataset['KEYWORD'] == fypePy['KEYWORD']:
                        # replacing variable names with their actual values
                        dataset = self.addPublishedParameters(dataset)
                        fypePy['DATASET'] = dataset
                        self.logger.info("linkage found: dataset/keyword %s ftype/keyword %s",
                                         dataset['KEYWORD'], fypePy['KEYWORD'])
                        break
                    else:
                        self.logger.info("no linkage: dataset/keyword %s ftype/keyword %s",
                                         dataset['KEYWORD'], fypePy['KEYWORD'])
                ftypes.append(fypePy)
        return ftypes

    def getSourceFeatureTypes(self):
        allFtypes = self.getFeatureTypes()
        srcTypes = []
        for ftype in allFtypes:
             # TODO: once the published parameter and the dataset have
             # been linked can continue with this task
            pass

    def getTransformers(self):
        '''
        extracts the portion of the document that starts with the tag:
        TRANSFORMERS,

        currently ignores the extra tag that is a child of the transformer
        ie. XFORM_ATTR, and  OUTPUT_FEAT

        down the road would be super useful to include these parameters as
        they include the table maps for transformers like 'attributerenamer'
        '''

        self.parseXML()
        transList = []

        children = self.xmlObj.TRANSFORMERS.countchildren()
        if children:
            for transfrmr in self.xmlObj.TRANSFORMERS.TRANSFORMER:
                if transfrmr.attrib['ENABLED'] == 'true':
                    transDict = {}
                    for transAtrib in transfrmr.attrib:
                        transDict[transAtrib] = transfrmr.attrib[transAtrib]
                        self.logger.debug("at: %s, %s ", transAtrib, transfrmr.attrib[transAtrib])
                        # print 'at:', transAtrib, transfrmr.attrib[transAtrib]
                    transList.append(transDict)
                    self.logger.debug(transDict)
        return transList

    def getPublishedParams(self):
        '''
        extracts the published parameters from the fmw and returns them with
        the following:
           -

        '''
        paramDict = {}
        for pubParam in self.xmlObj.GLOBAL_PARAMETERS.GLOBAL_PARAMETER:
            # print '', pubParam.attrib['GUI_LINE']
            self.logger.debug('GUI_LINE: %s', pubParam.attrib['GUI_LINE'])
            # extracting from this element based on the assumption
            # that the line has the following structure:
            #  GUI OPTIONAL TEXT SRC_FEATURE_1 The source feature class:
            #  GUI OPTIONAL CHOICE FILE_CHANGE_DETECTION TRUE%FALSE Boolean value used to enable/disable change detection:
            #
            # python params might look like this:
            #  GUI OPTIONAL IGNORE TEXT_EDIT_PYTHON_PARM LOGFILE Python Script:"
            #  GUI SOURCE_GEODATABASE SRC_DATASET_FGDB_1 Source Esri File Geodatabase:"
            # basically the elements are:
            # 0 - GUI
            # 1 - optional or required
            # 2 - type
            # 3 - variable name
            #
            pubParamNameLst = re.split(r'\s+', pubParam.attrib['GUI_LINE'])
            # starting to remove some elements trying to
            # get to the point where the first element in the
            # list is the pub param name
            # elems to delete:
            elems2Delete = ['GUI', 'OPTIONAL', 'IGNORE', 'TEXT', 'STRING_OR_CHOICE', \
                             'TEXT_OR_ATTR', 'TEXT_EDIT_PYTHON_PARM', \
                             'SOURCE_GEODATABASE', 'MULTIFILE', 'DIRNAME', \
                             'STRING_OR_ATTR', 'FILENAME_MUSTEXIST', 'CHOICE', \
                             'DIRNAME_SRC', 'STRING', 'STRING_OR_CHOICE_OR_ATTR', \
                             'FILENAME']
            for elem2Delete in elems2Delete:
                if pubParamNameLst[0].upper() == elem2Delete:
                    del pubParamNameLst[0]
                self.logger.debug("shortened list: %s", pubParamNameLst)
            # trying to detect problems with how the parsing took place.
            if len(pubParamNameLst) >= 2:
                if pubParamNameLst[0].isupper() and pubParamNameLst[1].isupper():
                    msg = "Possible missing type to add to elems2Delete in the " + \
                          'method getPublishedParams() %s'
                    self.logger.warning(msg, pubParamNameLst[0])
                if re.match('^SRC_.*$', pubParamNameLst[1]) or \
                  re.match('^DEST_.*$', pubParamNameLst[1]):
                    msg = "Possible missing type to add to elems2Delete in the " + \
                          'method getPublishedParams() %s  param looks like a SRC ' + \
                          'or a DEST type that was not properly detected'
                    self.logger.warning(msg, pubParamNameLst[0])

            paramDict[pubParamNameLst[0]] = { 'DEFAULT_VALUE': pubParam.attrib['DEFAULT_VALUE'],
                                              'TYPE': ' '.join(pubParamNameLst[1:])}
            self.logger.debug("paramDict: %s", paramDict)
            # self.logger.info("pp {0} = {1}".format(pubParamNameLst[0]), paramDict[pubParamNameLst[0]]['DEFAULT_VALUE'])
        return paramDict

    def getFMWWorkspaceName(self):
        '''
        :return: the fmw workspace name, ie the fmw file name.
        '''
        fmwFile = os.path.basename(self.FMWFile)
        return fmwFile

    def getFMEWorkspace(self):
        '''
        parses the existing document, extracts the:
         - Datasets
         - Columns
         - Feature classes
         - Transformers
         - Published Parameters

        and stores them in an FMEWorkspace object with a simple api for
        extracting information.
        '''
        self.parseXML()
        pubParams = self.getPublishedParams()
        transformers = self.getTransformers()
        featureClassStruct = self.getFeatureTypes()
        #      transformerStruct, featureClassStruct, publishedParams):
        # fmwFile = os.path.basename(self.FMWFile)
        fmwFile = self.getFMWWorkspaceName()

        FMEWrkspc = FMEWorkspace(fmwFile, transformers, featureClassStruct, pubParams)
        return FMEWrkspc

    def getJson(self):
        FMEWrkspc = self.getFMEWorkspace()
        jsonableStruct = FMEWrkspc.getTreedJSON()
        return jsonableStruct


class FMWRestruct():
    '''
    This class is used to read an fmw file in and separate out
    the three components.  Those being:

        - xml
        - command line
        - map script

    :ivar fh: Describe the variable here!
    :ivar fmeCommandlineUsage: Describe the variable here!
    :ivar fmeScript: Describe the variable here!
    :ivar regex_CommentLine: Describe the variable here!
    :ivar regex_FMECommandLineHeader: Describe the variable here!
    :ivar regex_IsXMLTag: Describe the variable here!
    :ivar regex_LeadingCharsRemove: Describe the variable here!
    :ivar regex_XMLDefLine: Describe the variable here!
    :ivar regex_xmlComment: Describe the variable here!
    :ivar srcFMWFilePath: Describe the variable here!
    :ivar xmlList: Describe the variable here!
    '''

    def __init__(self, srcFMWFilePath):
        self.logger = logging.getLogger(__name__)
        self.srcFMWFilePath = srcFMWFilePath
        self.initRegexs()
        self.fh = open(self.srcFMWFilePath, 'r')
        # The xml content will get dumped into this list
        self.xmlList = []
        # the fme command lines get put into this list.
        # These are the lines that describe how to run this
        # script as a command line
        self.fmeCommandlineUsage = []
        # the fme script - the parts that conclude the last tag
        self.fmeScript = []

    def initRegexs(self):
        '''
        compiles the various regex's used by this class
        '''
        # used to detect lines that start with the #!
        self.regex_xmlComment = re.compile('^#!.*')
        # used to remove the leading #! characters
        self.regex_LeadingCharsRemove = re.compile('^#!')
        # comment line used to identify the command line
        # parameters
        self.regex_CommentLine = re.compile('^#.*')

        # used to detect the line in fmw's that starts with
        # Windows command-line to run this workspace:
        self.regex_FMECommandLineHeader = re.compile('^#\s+Windows\s+command-line\s+to\s+run\s+this\s+workspace:\s*$')
        # detect the xml definition line
        self.regex_XMLDefLine = re.compile("^#!\s*<\?xml\s+version=.*\?>$")
        # used to identify a line that starts with an xml tag
        # only reason we need to identify this is so we can find the
        # first tag, which then in turn allows us to identify the last tag
        self.regex_IsXMLTag = re.compile("^#!\s*</{0,1}[a-zA-Z].*$")

    def read(self):
        # steps:
        # A) Any lines that start with #! are assumed to be xml
        # B) Make a note of the first tag encountered after the xml definition line
        #    that looks like this: #! <?xml version="1.0" encoding="iso-8859-1" ?>
        #    its usually the line that immediately follows
        # C) Read through the doc removing leading #! characters and putting those
        #    lines into the xml in memory doc.
        # D) While doing this look for the lines near the start of the doc that
        #    define the fme command line
        #    Once those are found

        lineCnt = 0
        firstXMLTagIndicator = True
        firstXMLTag = None
        prevLine = ''
        for line in self.fh:
#             print 'line:', line
            if self.regex_XMLDefLine.match(line):
                # remove the leading comment characters and
                # add to the xml list
                line = self.removeLeadingChars(line)
                self.xmlList.append(line)
            # matching a tag def!  need to be able to identify this so
            # we can identify the first tag to be encountered, which
            # then enables us to identify the last.
            elif self.regex_IsXMLTag.match(line):
                if firstXMLTagIndicator:
                    firstXMLTagIndicator = False
                    firstXMLTag = self.removeLeadingChars(line)
                    self.xmlList.append(firstXMLTag)
                elif self.isLastTag(line, firstXMLTag):
                    line = self.removeLeadingChars(line)
                    self.xmlList.append(line)
                    # we are done as the rest of the doc is not xml its the
                    # actual code used by the fme engine
                    self.__readFMEScript(self.fh)
                    break
                else:
                    line = self.removeLeadingChars(line)
                    self.xmlList.append(line)
            elif self.regex_xmlComment.match(line):
                line = self.removeLeadingChars(line)
                self.xmlList.append(line)
            elif self.isCommentLine(line):
                lineCleaned = line.replace('#', '').strip()
                if lineCleaned:
                    self.fmeCommandlineUsage.append(lineCleaned)
            elif self.isCommentLine(prevLine) and line.count('#') == 0:
                # add the line to previous command line
                # can have the situation where the command line paramaters look something like this:
                '''
                #          --Dest_Server
                 bcgw.bcgov
                #          --Dest_Instance_Connect
                port:5153
                #          --Dest_Password
                ********
                '''
                self.fmeCommandlineUsage[len(self.fmeCommandlineUsage) - 1] = self.fmeCommandlineUsage[len(self.fmeCommandlineUsage) - 1] + line
            else:
                print 'problem problem!'
                self.logger.error('PROBLEM!  %s', line)
                msg = 'PROBLEM WITH THIS LINE:\n' + line
                raise ValueError, msg
            # First thing is to remove the leading #! characters
            # line = self.removeLeadingChars(line)
            # is the line the xml definition line
            prevLine = line
            lineCnt += 1

    def __readFMEScript(self, iterable):
        '''
        Receives an iterable object that is currently pointing at the
        last line of XML (the closing tag for WORKSPACE).  The iterator
        then continues on and pulls the data from the
        '''
        #
        #
        for i in iterable:
            i = i.replace("\n", '')
            self.fmeScript.append(i)

    def isCommentLine(self, line):
        # will only
        retVal = False
        if self.regex_CommentLine.match(line) and not self.regex_xmlComment.match(line):
            # if line.replace('#', '').strip():
            retVal = True
        return retVal

    def isXML(self, line):
        # should be any line that is prefaced by #!
        pass

    def isLastTag(self, line, firstXMLTag):
        retVal = False
        firstXMLTag = firstXMLTag.replace("<", '').replace(">", '')
        mtch = re.match('^#!\s*</' + firstXMLTag + '>.*$', line)
        if mtch:
            retVal = True
        return retVal

    def removeLeadingChars(self, line):
        newLine = line
        if self.regex_xmlComment.match(line):
            newLine = self.regex_LeadingCharsRemove.sub('', line)
            newLine = newLine.strip()
            newLine = newLine.replace('\n', ' ')
        return newLine

    def getCommandLineArgs(self):
        return self.fmeCommandlineUsage

    def getFMEScript(self):
        return self.fmeScript

    def getXML(self):
        return self.xmlList

# Deprecated!  Next time working on this lib determine if can delete this.
#              Left over from older attempt to parse these files.


class FMWXML():

    def __init__(self, xmlTree, commandLineArgs):
        self.logger = logging.getLogger(__name__)
        self.xmlTree = xmlTree
        self.rootElem = xmlTree.getroot()
        self.commandLineArgs = commandLineArgs
        self.extractFromXml()

    def extractFromXml(self):
        '''
        reads through the xml document and separates the contents of
        the various tags into python data structures (lists).  Check
        code below, but at the time of writing this comment it grabs
        all the information for the following tags:

           - WORKSPACE
           - DATASETS
               - DATASET
           - FEATURE_TYPES
               - FEATURE_TYPE
           - TRANSFORMERS
               - TRANSFORMER
           - FEAT_LINKS
               - FEAT_LINK
           - ATTR_LINKS
               - ATTR_LINK

        The data structure that is created is then used to create a
        FMWData object that wraps methods around this data structure
        that make it easier to query / extract info from this structure.
        '''
        workspace = []
        dataSets = []
        featTypes = []
        transformers = []
        featLinks = []
        attlinks = []
        globParams = []
        if self.rootElem.tag == 'WORKSPACE':
            # print self.rootElem.tag
            # print self.rootElem.attrib
            workspace.append(self.rootElem.attrib)

        for elem in self.rootElem:
            if elem.tag == 'DATASETS':
                for dataset in elem:
                    if dataset.tag == 'DATASET':
                        # print '-------- datasets --------'
                        # self.printDict(dataset.attrib)
                        dataSets.append(dataset.attrib)
            elif elem.tag == 'FEATURE_TYPES':
                for featType in elem:
                    if featType.tag == 'FEATURE_TYPE':
                        # print '-------- featTypes --------'
                        # self.printDict(featType.attrib)
                        featTypes.append(featType.attrib)
            elif elem.tag == 'TRANSFORMERS':
                for trnsFormer in elem:
                    if trnsFormer.tag == 'TRANSFORMER':
                        # print '-------- transformer man --------'
                        # self.printDict(trnsFormer.attrib)
                        transformers.append(trnsFormer.attrib)
            elif elem.tag == 'FEAT_LINKS':
                for featLnk in elem:
                    if featLnk.tag == 'FEAT_LINK':
                        # print '-------- FEAT_LINK --------'
                        # self.printDict(featLnk.attrib)
                        featLinks.append(featLnk.attrib)
            elif elem.tag == 'ATTR_LINKS':
                for attr in elem:
                    if attr.tag == 'ATTR_LINK':
                        # print '--------- ATTR LINK --------'
                        # self.printDict(attr.attrib)
                        attlinks.append(attr.attrib)
            elif elem.tag == 'GLOBAL_PARAMETERS':
                for globParam in elem:
                    if globParam.tag == 'GLOBAL_PARAMETER':
                        globParams.append(globParam.attrib)

        retDict = {}
        retDict['DATASETS'] = dataSets
        retDict['FEATURE_TYPES'] = featTypes
        retDict['TRANSFORMERS'] = transformers
        retDict['FEAT_LINKS'] = featLinks
        retDict['ATTR_LINKS'] = attlinks
        retDict['WORKSPACE'] = workspace
        retDict['GLOBAL_PARAMETERS'] = globParams

    def getEtreeObj(self):
        '''
        Returns the etree xml object of the xml part of the fmw file.

        :returns: etree xml object
        :rtype: xml.etree.ElementTree
        '''
        return self.xmlTree

    def getFMWDataObject(self):
        '''
        Returns a FMWData object that contains the information that this
        class has extracted from the fmw file.

        :returns: fmw data object with the subset of data extracted from the
                  xml part of the fmw
        :rtype: FMWData
        '''
        return self.fmwData


class Util():
    '''
    simple methods that may be used by this modules
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def stripVariableNotations(self, varName):
        '''
        Takes a variable name like $(DEST_FEATURE_1) and strips off the
        '$(' from the start and ')' from the end
        '''
        regex = re.compile(FMWParserConstants.PUBPARAM_STIPNOTATION, re.IGNORECASE)
        srch = regex.search(varName)
        if not srch:
            msg = 'unable to extract a variable from the text %s, expecting ' + \
                  'test in the format of \'$(SOMEVAR)\'. '
            self.logger.error(msg, varName)
            raise ValueError, msg, varName
        pubParmName = srch.group(1)
        return pubParmName


class FMEWorkspace(object):
    '''
    Provides an easy to use api to extract information about the workspace
    '''

    def __init__(self, fmwFileName, transformerStruct, featureClassStruct, publishedParams):
        self.publishedParams = FMEPublishedParameters(publishedParams)
        self.featureClasses = FMEFeatureClasses(featureClassStruct, self.publishedParams)
        self.transformers = FMETransformers(transformerStruct, self.publishedParams)
        self.fmwFileName = fmwFileName

    def getTreedJSON(self):
        '''
          - End structure will be:
             FME Server
                FME Repository
                    FME Workspace
                        Sources
                            columns
                        Destinations
                            columns
                        Transformers
                            names
                        Published Parameters
                            name / value pairs
        '''
        pubParamsJson = self.publishedParams.getJson()
        featureClassesJson = self.featureClasses.getJson()
        transformersJson = self.transformers.getJson()

        # info about workspace now exists ready to put into a unified structure
        newEntry = {'name': self.fmwFileName,
                    'children': [featureClassesJson, transformersJson, pubParamsJson]}
        return newEntry

    def getFeatureClasses(self):
        return self.featureClasses

    def getTransformers(self):
        return self.transformers

    def getWorkspaceName(self):
        '''
        returns the name of the FMW file that this object is wrapping
        '''
        return self.fmwFileName

    def getPublishedParameters(self):
        '''
        :return: returns the published parameter object
        :rtype: FMEPublishedParameters
        '''
        return self.publishedParams

    def hasFieldMap(self):
        '''
        fieldmaps can be defined in two different ways, one way is to 
        use an "AttributeRenamer" transformer.  At DataBC this is the 
        "preferred" way of doing this.  The other way is to drag
        connecting lines from either the reader or the last transformer
        to the writers feature class.
        
        This method should be able detect both of these appoaches.
        
        '''


class FMETransformers(object):
    '''
    a wrapper to the transformer data struct that should hopefully make it
    easy to extract information about transformers.
    '''

    def __init__(self, transformerStruct, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.transfomerStruct = transformerStruct
        self.transformerNameAttribute = 'TYPE'

    def getJson(self):
        transformerList = []
        for transformer in self.transfomerStruct:
            # transformer is a dict descrbing a transformer
            curTransformerList = []
            for transformerAtrib in transformer.keys():
                self.logger.debug('transformerAtrib: %s', transformerAtrib)
                if transformerAtrib <> self.transformerNameAttribute:
                    node = {'name': transformerAtrib,
                            'value': transformer[transformerAtrib]}
                    curTransformerList.append(node)

            newTransformer = {'name': transformer[self.transformerNameAttribute],
                              'children': curTransformerList}
            transformerList.append(newTransformer)
        transformers = {'name': 'tranformers',
                        'children': transformerList}
        return transformers

    def getTransformerNames(self):
        '''
        :return: returns a list of strings that describe the transformers found
                 in the fmw workspace.
        :rtype: list

        transformer name is extracted from the TYPE parameter
        '''
        transList = []
        for transformer in self.transfomerStruct:
            transName = transformer['TYPE']
            transList.append(transName)
        return transList


class FMEPublishedParameters(object):
    '''
    wrapper to published parameters
    '''

    def __init__(self, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.publishedParams = publishedParams
        self.hasPubParamRegex = re.compile(FMWParserConstants.PUBPARAM_ANY, re.IGNORECASE)

    def getJson(self):
        '''
        paramDict[pubParamNameLst[0]] = { 'DEFAULT_VALUE': pubParam.attrib['DEFAULT_VALUE'],
                                          'TYPE': ' '.join(pubParamNameLst[1:])}
        return paramDict
        '''
        struct = []
        for pubParam in self.publishedParams.keys():
            param = {'name': pubParam,
                     'value': self.publishedParams[pubParam]['DEFAULT_VALUE']}
            struct.append(param)
        return struct

    def hasPubParams(self, inStr):
        '''
        :param inStr: input string that will be searched for $(some text)
                      published parameter signature.  Returns True if it
                      is found.
        :return: bool indicating if the inStr contains published parameters.
        :rtype: bool
        '''
        retVal = False
        if self.hasPubParamRegex.match(inStr):
            retVal = True
        return retVal

    def deReference(self, inStr):
        '''
        :param inputString: the input string that you want to have published
                            parameters replaced with their values.
        :return: same string but with the actual published parameter values
        '''
        outStr = inStr
        if self.hasPubParams(inStr):
            findParamRegex = re.compile(FMWParserConstants.PUBPARAM_SINGLE, re.IGNORECASE)
            for pubParamRegex in findParamRegex.finditer(inStr):
                paramName = inStr[pubParamRegex.start():pubParamRegex.end()]
                if paramName in self.publishedParams:
                    self.logger.debug("matched published parameter! %s", paramName)
                    type = self.publishedParams[paramName]['TYPE']
                    if type.lower() <> 'Python Script:' and \
                       type.lower() <> 'Python Script':
                        msg = "replacing the variable reference %s with its value %s"
                        paramValue = self.publishedParams[paramName]['DEFAULT_VALUE']
                        self.logger.info(msg, paramName, paramValue)
                        outStr = outStr.replace(paramName, paramValue)
                    else:
                        msg = "parameter %s is a python script so not replacing" + \
                              'with its value'
                        self.logger.info(msg, paramName)


class FMEFeatureClasses(object):
    '''
    Parser will extract all the feature class records from the fmw that was read.
    This class provides an API to help extract specific Feature classes from the
    total number of feature classes defined in the FMW
    '''

    def __init__(self, featureClassesStruct, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.featClassesList = []
        self.pubParms = publishedParams
        self.addFeatureClasses(featureClassesStruct)

    def addFeatureClasses(self, featureClassesStruct):
        '''
        Iterates through the featureClassesStruct which is a list of feature classes
        and uses them to create feature class objects.
        '''
        for featCls in featureClassesStruct:
            fc = FMEFeatureClass(featCls, self.pubParms)
            self.featClassesList.append(fc)

    def getSources(self):
        sources = []
        for fc in self.featClassesList:
            if fc.isSource():
                sources.append(fc)
        return sources

    def getDestinations(self):
        dests = []
        for fc in self.featClassesList:
            if not fc.isSource():
                dests.append(fc)
        return dests

    def getJson(self):
        '''
        returns a treed data structure for each feature class with the following
        hierarchical structure:
        dataset
           feature class
               columns
                   column defs
               properties

        name: Datasets,
        children: [
            name: sources,
            children: [
                name: DatasetName,
                children [
                    name: DatasetProperties,
                    children: [
                        name: property,
                        value: value
                        ...]
                    ],
                    name: Feature Classes,
                    children: [
                        name: feature class name,
                        children: [
                            name: properties,
                            children: [
                                name: property name,
                                value: property value
                                ...
                            ],
                            name: columns,
                            children: [
                                name: property name,
                                value: property value]


        '''
        # TODO: 6-25-2018 - Not working correctly
        datasetDict = {'name': 'datasets',
                       'children': []}
        # simple dictionary used to collect the datasets,
        # at the end of the loop they are written to
        # datasetDict, as the children.
        tmpDataSetDict = {}
        self.logger.debug("exporting the feature classes to a data struct that" + \
                          " can be jsonified")
        for featCls in self.featClassesList:
            dataSet = featCls.getDataSet()
            datasetName = dataSet.getDataSetName()
            self.logger.debug("datasetName: %s", datasetName)
            if datasetName in tmpDataSetDict:
                curDataSet = tmpDataSetDict[datasetName]
                self.logger.debug("creating new dataset entry for: %s", datasetName)
            else:
                dataSetProps = {'name': 'properties',
                                'children': dataSet.getJson()}
                featureClasses = {'name': 'featureclasses',
                                  'children': []}
                # later on will add the individual feature class entries to the
                # children list.
                curDataSet = {'name': datasetName,
                              'children': [dataSetProps, featureClasses]}

            # now build the feature class and column parts.
            featClsName = featCls.getFeatureClassName()
            featClsProperties = []
            properties = featCls.getFeatureClassPropertiesAsNameChild()
            self.logger.debug("fc: %s properties %s", featClsName, properties)
            propertiesRecord = {'name': 'properties',
                                'children': properties}
            featClsProperties.append(propertiesRecord)
            # list of name / children property objs.
            columns = featCls.getColumnsAsNameChild()
            self.logger.debug("columns: %s", columns)
            columnsRecord = {'name': 'columns',
                             'children': columns}
            featClsProperties.append(columnsRecord)

            featureClassJS = {'name': featClsName,
                              'children': featClsProperties}
            # now add the featureClassJS to the current datasets feature class
            # child
            cnt = 0
            for node in curDataSet['children']:
                if node['name'] == 'featureclasses':
                    break
                cnt += 1
            self.logger.debug('cnt: %s', cnt)
            self.logger.debug("featureClassJS: %s", featureClassJS)
            curDataSet['children'][cnt]['children'].append(featureClassJS)
            tmpDataSetDict[datasetName] = curDataSet

        for dataSet in tmpDataSetDict.keys():
            newEntry = {'name': dataSet,
                        'children': tmpDataSetDict[dataSet]}
            # datasetDict['children'].append(newEntry)
            datasetDict['children'].append(tmpDataSetDict[dataSet])
        return datasetDict


class FMEFeatureClass(object):
    '''
    The parser will extract info from the FMW and puts them into a python data
    structure.  The data structure is derived from what the attributes defined
    in the FMW. The parser also joins the column information and dataset
    information to the feature class record.

    This class provides an API to the Feature class record WITH the joined column
    information, hopefully making it easy to read.
    '''

    def __init__(self, fc, publishedParameters):
        self.pubParams = publishedParameters
        self.featClsStruct = fc
        self.fcNameField = 'NODE_NAME'

    def isSource(self):
        retVal = True
        if self.featClsStruct['DATASET']['IS_SOURCE'] == 'false':
            retVal = False
        return retVal

    def getDataSet(self):
        dataset = FMEDataSet(self.featClsStruct['DATASET'])
        return dataset

    def getFeatureClassName(self):
        return self.featClsStruct[self.fcNameField]

    def getFeatureClassPropertiesAsNameChild(self):
        '''
        returns the properties of the feature class as the following structure
            ...
            { name: propertyName,
              value: propertyValue },
              etc...

        Omits datasets and omits columns
        '''
        omitList = ['DATASET', 'COLUMNS']
        returnList = []
        for fcProperty in self.featClsStruct.keys():
            if fcProperty not in omitList:
                propertySet = {'name': fcProperty,
                               'value': self.featClsStruct[fcProperty]}
                returnList.append(propertySet)
        return returnList

    def getColumnsAsNameChild(self):
        '''
        returns the columns information as a hierarchical name child
        property set
        '''
        returnStruct = []
        for column in self.featClsStruct['COLUMNS']:
            columnName = column['ATTR_NAME']
            columnProperties = []
            for columnProperty in column.keys():
                if columnProperty <> 'ATTR_NAME':
                    propertyStruct = {'name': columnProperty,
                                      'value': column[columnProperty]}
                    columnProperties.append(propertyStruct)
            propertySet = {'name': columnName,
                           'children': columnProperties}
            returnStruct.append(propertySet)
        return returnStruct

    def getFeatureClassDescriptiveName(self):
        datasetObj = self.getDataSet()
        dataSetName = datasetObj.getDataSetName()
        fcName = self.getFeatureClassName()
        fcName = self.subPubParams(fcName)
        srcName = u'{0}/{1}'.format(dataSetName, fcName)
        return srcName

    def subPubParams(self, inputString):
        '''
        :param inputString: input strign that you want to have published parameters
                            dereferenced if possible.
        :return: same string but variable references de-referenced
        '''
        outStr = inputString
        if self.pubParams.hasPubParams(inputString):
            outStr = self.pubParams.deReference(inputString)
        return outStr


class FMEDataSet(object):

    def __init__(self, datasetStruct):
        self.datasetStruct = datasetStruct
        self.fcDataSetRelationshipField = 'KEYWORD'
        self.datasetNameField = 'DATASET'
        self.datasetFormatField = 'FORMAT'

    def getJson(self):
        dataSetList = []
        for propertyName in self.datasetStruct:
            param = {'name': propertyName,
                     'value': self.datasetStruct[propertyName] }
            dataSetList.append(param)
        # dataSetEntry = {'name': }
        return dataSetList

    def getFeatureClassDatasetRelationshipField(self):
        return self.fcDataSetRelationshipField

    def getDataSetName(self):
        return self.datasetStruct[self.datasetNameField]
    
    def getDataSetFormat(self):
        '''
        :return: The dataset format / type
        '''
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(self.datasetStruct)
        return self.datasetStruct[self.datasetFormatField]


# if __name__ == '__main__':
#     logger = logging.getLogger(__name__)
#     logger.addHandler(logging.StreamHandler())
#     logger.setLevel(logging.DEBUG)
# 
#     pp = pprint.PrettyPrinter(indent=4)
# 
#     inFMW = 'testFME.fmw'
#     parsr = FMWParser(inFMW)
#     parsr.separateFMWComponents()
#     # parsr.readEverything()
# 
#     # trans = parsr.getTransformers()
# 
#     # dest = parsr.getDestDataSets()
#     # pp.pprint(dest)
# 
#     dest = parsr.getFeatureTypes()
#     pp.pprint(dest)
#     # dest = parsr.addPublishedParameters(dest)
#     # pp.pprint(dest)
# 
#     # pp  = pprint.PrettyPrinter(indent=4)
#     # pp.pprint(dest[0])
#     # print 'dest', dest[0].attrib
#     # parsr.getSourceDataSets()
#     # parsr.parseXML()
#     # parsr.getPublishedParams()

'''
 currently trying to figure out how to extract fieldmaps.
 FACTORY_DEF * RoutingFactory FACTORY_NAME "Destination Feature Type Routing Correlator"
        
        
'''