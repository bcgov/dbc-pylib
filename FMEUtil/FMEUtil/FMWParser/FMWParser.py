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
import itertools
import warnings

import lxml.objectify  # @UnresolvedImport
from . import FMWParserConstants
from . import FMWComponents
from . import FMWUtil
from . import FMWTCLParser


class FMWParser(object):
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
        self.tclObj = None
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
        if self.fmwReader is None:
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

    def parseTCL(self):
        if self.tclObj is None:
            if self.fmwReader is None:
                self.separateFMWComponents()
            tclList = self.fmwReader.getFMEScript()
            self.tclObj = FMWTCLParser(tclList)

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
        util = FMWUtil.Util()
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

    def getTransformers(self, enabledOnly=True):
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
                transfrmrDict = self.recurse(transfrmr)
                proceed = True
                if enabledOnly:
                    if transfrmrDict['ENABLED'] <> 'true':
                        proceed = False
                if proceed:
                    transList.append(transfrmrDict)

#                 proceed = True
#                 if enabledOnly:
#                     if transfrmr.attrib['ENABLED'] <> 'true':
#                         proceed = False
#                 if proceed:
#                     transDict = {}
#                     for transAtrib in transfrmr.attrib:
#                         transDict[transAtrib] = transfrmr.attrib[transAtrib]
#                         self.logger.debug("at: %s, %s ", transAtrib, transfrmr.attrib[transAtrib])
#                         print 'at:', transAtrib, transfrmr.attrib[transAtrib]
#                     transList.append(transDict)
#                     self.logger.debug(transDict)
#
#                     # children
#                     for child in transfrmr.getchildren():
#                         print 'chld', child.tag
#
        return transList

    def recurse(self, xmlObj, chldTag='CHILD', nameTag='ELEMENTNAME', textTag='ELEMENTTEXT'):
        '''
        :param xmlObj: an xml element
        :type xmlObj: lxml.objectify element
        :param chldTag: the name of the tag that children elements will be stored
                        in
        :param nameTag: the name of the tag used to store the child element tag 
                        names.
                        
        using defaults takes:
        <TRANSFORMER
             IDENTIFIER="26"
             TYPE="AttributeRenamer"
             VERSION="3"
             POSITION="727.232 -209"
             BOUNDING_RECT="727.232 -209 -1 -1"
             ORDER="5e+014"
             PARMS_EDITED="true"
             ENABLED="true"
             LAST_PARM_EDIT="15538"
             >
             <OUTPUT_FEAT NAME="OUTPUT"/>
             <XFORM_ATTR ATTR_NAME="geodb_oid" IS_USER_CREATED="false" FEAT_INDEX="0" />
             <XFORM_ATTR ATTR_NAME="OBJECTID" IS_USER_CREATED="false" FEAT_INDEX="0" />
        </TRANSFORMER>
        
        and converts to:
        [   
            {'BOUNDING_RECT': '727.232 -209 -1 -1',
            'ENABLED': 'true',
            'IDENTIFIER': '26',
            'LAST_PARM_EDIT': '15538',
            'ORDER': '5e+014',
            'PARMS_EDITED': 'true',
            'POSITION': '727.232 -209',
            'TYPE': 'AttributeRenamer',
            'VERSION': '3'},
            'CHILD': [   {   'ELEMENTNAME': 'OUTPUT_FEAT', 'NAME': 'OUTPUT'},
                         {   'ATTR_NAME': 'geodb_oid',
                             'ELEMENTNAME': 'XFORM_ATTR',
                             'FEAT_INDEX': '0',
                             'IS_USER_CREATED': 'false'},
                         {   'ATTR_NAME': 'OBJECTID',
                             'ELEMENTNAME': 'XFORM_ATTR',
                             'FEAT_INDEX': '0',
                             'IS_USER_CREATED': 'false'}
                    ]
            }
        ]
    
        '''
        transDict = {}
        chldrn = []
        # get all the attributes
        for objAtribName in xmlObj.attrib:
            #print '{0} = {1}'.format(objAtribName, xmlObj.attrib[objAtribName])
            transDict[objAtribName] = xmlObj.attrib[objAtribName]
        transDict[nameTag] = xmlObj.tag
        if xmlObj.text:
            transDict[textTag] = xmlObj.text
        # now get all the children
        for chld in xmlObj.getchildren():
            chldAsDict = self.recurse(chld)
            if chld.tag:
                chldAsDict[nameTag] = chld.tag
            chldrn.append(chldAsDict)
        if chldrn:
            transDict[chldTag] = chldrn
        return transDict

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

        FMEWrkspc = FMWComponents.FMEWorkspace(fmwFile, transformers, featureClassStruct, pubParams)
        return FMEWrkspc

    def getJson(self):
        FMEWrkspc = self.getFMEWorkspace()
        jsonableStruct = FMEWrkspc.getTreedJSON()
        return jsonableStruct

    def getFMWFieldmaps(self):
        self.parseTCL()
        # gets the field maps defined by drawing lines between columns
        fldMaps = self.tclObj.getFieldMaps()
        
        # get the field maps defined by attributeRenamers
        wrkSpc = self.getFMEWorkspace()
        trans = wrkSpc.getTransformers()
        fldMapAtrib = trans.getAttributeRenamerFieldMap()
        
        if fldMaps and fldMapAtrib:
            msg = 'Field maps are defined using attributeRenamers as well as' + \
                  'by dragging columns.  This field map cannot be extracted'
            #raise ConflictingFieldMaps, msg
            self.logger.warning(msg)
            warnings.warn(msg)
            # combining the lists, so [[[1,2],[2,3]]] and [[['a',b'],['c','d']]] 
            # become [[[1,2],[2,3]], [['a',b'],['c','d']]]
            newList = []
            for fldMapList in fldMaps:
                newList.append(fldMapList)
            for fldMapList in fldMapAtrib:
                newList.append(fldMapList)
#             pp = pprint.PrettyPrinter(indent=4)
#             print 'list 1'
#             pp.pprint(fldMaps)
#             print 'list 2'
#             pp.pprint(fldMapAtrib)
#             print 'combined'
#             pp.pprint(newList)
#             raise ConflictingFieldMaps, msg
            
            fldMaps = newList
        elif not fldMaps:
            fldMaps = fldMapAtrib
        return fldMaps

    def getAttributeRenamerFieldMaps(self):
        '''
        There are two ways that you can map column relationships between source
        data and destination data.  They are:
          - by drawing relatinships between columns, for these field maps retrieve
            using getFMWFieldmaps
          - by adding an AttributeRenamer transformer.  This method will retrieve
            the field maps defined in this way.

        AttributeRenamer transformers are used to define fieldmaps as:

        a) start by determining if the transofmer has an AttributeRenamer
           transformer in it.
        '''
        transformers = self.getTransformers()
        if 'attributeRenamer' in transformers:
            print 'heloo'

    def getDestinationSchema(self, fcName):
        '''
        :param fcName: name of the feature class / feature type who's schema you 
                       are trying to retrieve.
        
        destination schema's can be defined in a number of different locations.  the 
        method will search in the following order in an attempt to extract the destination 
        schema from this dataset.
          - First finds destination feature classes for the FMW, Then searches the following 
           parameters for the feature classes looking for destination schema:
             - FEATURE_TYPE_NAME_QUALIFIER - if this is filled in assumes that this 
                                             is the schema name, if blank caries on...
             - NODE_NAME - loooks at the node name, if it can be split on a '.' character
                           then assumes the format is schema.featureclassname and 
                           pulls the schema from the start of this name, otherwise...
          - next if none of the above attempts to find the destination schema are
            successful then reads the published parameters and gets it from 
            DEST_SCHEMA
        '''
        destschemas = []
        wrkspcObj = self.getFMEWorkspace()
        featureClasses = wrkspcObj.getFeatureClasses()
        dests = featureClasses.getDestinations()
        pubParams = wrkspcObj.getPublishedParameters()
        schema = None
        self.logger.debug("pubparams: %s", pubParams.getJson())
        for dest in dests:
            curFcName = dest.getFeatureClassName()
            self.logger.debug("curFcName: %s", curFcName)
            if curFcName.lower().strip() == fcName.lower().strip():
                schema = dest.getParamName('FEATURE_TYPE_NAME_QUALIFIER')
                self.logger.debug("FEATURE_TYPE_NAME_QUALIFIER: %s", schema)
                if not schema:
                    fullFcName =  dest.getParamName('NODE_NAME')
                    self.logger.debug("node name: %s", fullFcName)
                    fullFcNameSplit = fullFcName.split('.')
                    if len(fullFcNameSplit) == 2:
                        schema = fullFcNameSplit[0]
                    if not schema:
                        # TODO: should really create a FMEUTIL constants file where these
                        # types of parameters are stored
                        self.logger.debug('Looking for DEST_SCHEMA in dest params...')
                        schema = pubParams.getPublishedParameterValue('DEST_SCHEMA')
                        self.logger.debug("schema: %s", schema)
                    if schema is None:
                        # TODO: should really create a FMEUTIL constants file where these
                        # types of parameters are stored
                        if pubParams.hasPubParams('DEST_SCHEMA_1'):
                            schema = pubParams.getPublishedParameterValue('DEST_SCHEMA_1')
            if schema: 
                break
        return schema

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


