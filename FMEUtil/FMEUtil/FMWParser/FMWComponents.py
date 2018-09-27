'''
Created on Jul 24, 2018

@author: kjnether

When a FMW gets parsed it gets broken up into the various components
described in this module.
'''
import logging
import pprint
import re
import warnings

# import FMWParser
import FMWParserConstants

# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation


class FMEWorkspace(object):
    '''
    Provides an api to extract information about the workspace
    '''

    def __init__(self, fmwFileName, transformerStruct, featureClassStruct,
                 publishedParams):
        self.publishedParams = FMEPublishedParameters(publishedParams)
        self.featureClasses = FMEFeatureClasses(featureClassStruct,
                                                self.publishedParams)
        self.transformers = FMETransformers(transformerStruct,
                                            self.publishedParams)
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
        # TODO: not working at the moment 7-24-2018
        pubParamsJson = self.publishedParams.getJson()
        featureClassesJson = self.featureClasses.getJson()
        transformersJson = self.transformers.getJson()

        # info about workspace now exists ready to put into a unified structure
        newEntry = {'name': self.fmwFileName,
                    'children': [featureClassesJson, transformersJson,
                                 pubParamsJson]}
        return newEntry

    def getFeatureClasses(self):
        '''
        :return: a feature classes object
        '''
        return self.featureClasses

    def getTransformers(self):
        '''
        :return: transformers object
        '''
        return self.transformers

    def getWorkspaceName(self):
        '''
        :returns: the name of the FMW file that this object is wrapping
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

        This method should be able detect both of these approaches.

        '''
        # TODO: write code to do this.
        pass


class FMETransformers(object):
    '''
    a wrapper to the transformer data struct that should hopefully make it
    easy to extract information about transformers,

    functionality for dealing with collections of transformers, Puts
    individual transformer information into 'Transforer' objects
    '''

    def __init__(self, transformerStruct, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.transformerNameAttribute = 'TYPE'
        self.transfomerStruct = transformerStruct
        self.pubParams = publishedParams
        self.logger.debug('transformer struct: {0}'.format(
            self.transfomerStruct))
        self.transformerList = None
        self.parseTransformers()

    def parseTransformers(self):
        '''
        rips through the transformers data sturct extracting indvidual
        transformers and storing in 'Transforer' objects
        '''
        self.transformerList = []
        for trans in self.transfomerStruct:
            self.logger.debug("trans: %s", trans)
            print "trans: %s", trans
            transformer = Transformer(trans)
            self.transformerList.append(transformer)

    def getJson(self):
        transformerList = []
        for transformer in self.transfomerStruct:
            # transformer is a dict descrbing a transformer
            curTransformerList = []
            for transformerAtrib in transformer.keys():
                self.logger.debug('transformerAtrib: %s', transformerAtrib)
                if transformerAtrib != self.transformerNameAttribute:
                    node = {'name': transformerAtrib,
                            'value': transformer[transformerAtrib]}
                    curTransformerList.append(node)

            newTransformer = {'name':
                              transformer[self.transformerNameAttribute],
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
        transNameList = []
        for transformer in self.transformerList:
            transName = transformer.getType()
            transNameList.append(transName)
        return transNameList

    def _getInst(self, instType):
        transList = []
        for transformer in self.transformerList:
            if isinstance(transformer, instType):
                transList.append(transformer)
        return transList

    def _hasInst(self, instType):
        retVal = False
        for transformer in self.transformerList:
            if isinstance(transformer, instType):
                retVal = True
                break
        return retVal

    def hasAttributeRenamer(self):
        return self._hasInst(AttributeRenamerTransformer)

    def getAttributeRenamerTransformers(self):
        '''
        Returns a list of AttributeRenamerTransformers
        '''
        return self._getInst(AttributeRenamerTransformer)

    def hasCounter(self):
        return self._hasInst(CounterTransformer)

    def getCounterTransformers(self):
        return self._getInst(CounterTransformer)


class Transformer(object):
    '''
    wraps the transformer data structure
    '''

    def __new__(cls, struct):
        if struct['TYPE'].lower() == 'counter':
            return CounterTransformer(struct)
        elif struct['TYPE'].lower() == 'attributerenamer':
            return AttributeRenamerTransformer(struct)
        else:
            return TransfomerBase(struct)


class TransfomerBase(object):

    def __init__(self, struct):
        self.logger = logging.getLogger(__name__)
        self.struct = struct
        self.transformerNameAttribute = 'TYPE'

    def getType(self):
        transName = self.struct['TYPE']
        return transName

    def isCounter(self):
        '''
        queries the transformer to determine if it is a 'counter'
        transformer, the type of transformer is extracted from the
        property 'TYPE' of the transformer
        '''
        retVal = False
        if self.transformerNameAttribute.lower() == 'counter':
            retVal = True
        return retVal

    def _searchChildElems(self, types, searchList, returnKey):
        '''
        Most transformers have a 'CHILD' section that describes the output
        attributes and the parameters that are sent to the transformer.

        This will look as follows in the self.struct...

        {...
          'CHILD': [{   'ELEMENTNAME': 'OUTPUT_FEAT', 'NAME': 'OUTPUT'},
                     ...
                    {   'ATTR_NAME': 'CLTRL_HERITAGE_SITE_ID',
                     'ELEMENTNAME': 'XFORM_ATTR',
                     'FEAT_INDEX': '0',
                     'IS_USER_CREATED': 'false'},
                     ...
                    {   'ELEMENTNAME': 'XFORM_PARM',
                     'PARM_NAME': 'XFORMER_NAME',
                     'PARM_VALUE': 'Counter'},
                     ...

        The following parameter descriptions will use the struct above as
        a reference to help explain what they do.

        :param types: child record types are idenfied by the presence of
                      attribute names, this parameter identifies a list
                      of attributes that the CHILD element will have to have,
                      examples:

                      ['PARM_NAME'] would select out entries
                      that describe parameters to the transformer, ie
                      parameters that get filled in when you create or
                      edit the transformer

                      ['ATTR_NAME'] would select out entries that describe
                      the output attributes that are comming out of this
                      transformer

        :param searchList: The first parameter would identify the record
                     recordType, this attribute will identify a selection
                     criteria for records of that recordType,

                     This parameter is a list of lists, where each inner
                     list is made up of:
                        0 - Property name
                        1 - Property value

                    So using the example above, would return 'Counter'
                    if I provided the list:
                    ['PARM_NAME', 'XFORMER_NAME']

        :param returnKey: having identified a child key you want to return
                    this value identifies the parameter for the child
                    element that you want to return

        Putting it together if the method was called with the following
        parameter values, given the data described above...

           types = ['ELEMENTNAME']
           searchList = [['PARM_NAME','XFORMER_NAME']]
           returnKey = 'PARM_VALUE'

        It would return the value: 'Counter'

        '''
        retVal = False
        for elem in self.struct['CHILD']:
            matches = True
            for recordType in types:
                if recordType not in elem:
                    matches = False
            if matches:
                # matches indicates all the element types requires are
                # present, now to evalue to the key=value list
                for searchPair in searchList:
                    searchKey = searchPair[0]
                    searchValue = searchPair[1]

                    if (searchKey in elem) and elem[searchKey] != searchValue:
                        matches = False
                        break
            if matches:
                retVal = elem[returnKey]
                break
        return retVal

    def __str__(self):
        transName = self.getType()
        self.logger.debug("default string value is the name of the" +
                          'of the transformer: %s', transName)
        return transName


class CounterTransformer(TransfomerBase):
    '''
    a class created to make it easier to extract required parameters from
    counter transformers
    '''

    def __init__(self, struct):
        TransfomerBase.__init__(self, struct)

    def getUserAssignedTransformerName(self):
        '''
        When a counter transformer is added to an FMW one of the things that
        gets added to it is a transformer name.  This method will return
        the name that was assigned to this transformer.

        If you double click on a transformer, this method will return the
        value that corresponds with 'Transformer Name'

        :return: the user supplied name for the transformer
        '''
        return self._searchChildElems(['ELEMENTNAME'],
                                      [['PARM_NAME', 'XFORMER_NAME'],
                                       ['ELEMENTNAME', 'XFORM_PARM']],
                                      'PARM_VALUE')

    def getCounterOutputAttributeName(self):
        '''
        If you double click on a transformer, this method will return the
        value that corresponds with 'Count Output Attribute'

        :return: the output attribute that is going to be populated by the
                 counter transformer

        '''
        return self._searchChildElems(['ELEMENTNAME'],
                                      [['PARM_NAME', 'CNT_ATTR'],
                                       ['ELEMENTNAME', 'XFORM_PARM']],
                                      'PARM_VALUE')

    def getCounterStartNumber(self):
        '''
        If you double click on a transformer, this method will return the
        value that corresponds with 'Count Start'

        :return: the number that the first iteration of the counter will
                 start with
        '''
        return self._searchChildElems(['ELEMENTNAME'],
                                      [['PARM_NAME', 'START'],
                                       ['ELEMENTNAME', 'XFORM_PARM']],
                                      'PARM_VALUE')

    def getCounterName(self):
        '''
        If you double click on a transformer, this method will return the
        value that corresponds with 'Counter Name'

        :return: the name of the counter, not sure what this attribute does
        '''
        return self._searchChildElems(['ELEMENTNAME'],
                                      [['PARM_NAME', 'DOMAIN'],
                                       ['ELEMENTNAME', 'XFORM_PARM']],
                                      'PARM_VALUE')

    def getCounterScope(self):
        '''
        If you double click on a transformer, this method will return the
        value that corresponds with 'Counter Scope'

        :return: the scope of the counter, see fme help on 'counter'
                 transformer for more info on this.

        '''
        return self._searchChildElems(['ELEMENTNAME'],
                                      [['PARM_NAME', 'SCOPE'],
                                       ['ELEMENTNAME', 'XFORM_PARM']],
                                      'PARM_VALUE')


class AttributeRenamerTransformer(TransfomerBase):

    def __init__(self, struct):
        TransfomerBase.__init__(self, struct)

    def getAttributeRenamerFieldMap(self):
        fldMaps = []
        transVersion = self.struct['VERSION']
        self.logger.debug("child elems: %s", self.struct['CHILD'])
        for child in self.struct['CHILD']:
            if 'PARM_NAME' in child:
                if child['PARM_NAME'] == 'ATTR_LIST':
                    if child['PARM_VALUE']:
                        self.logger.debug('fldmapstr: %s', child['PARM_VALUE'])
                        fldMaps = self.__extractAttributeRenamerFieldMaps(
                            child['PARM_VALUE'], transVersion)
                        # fldMaps.append(fldMap)
        self.logger.debug("fldMaps: {0}".format(fldMaps))
        return fldMaps

    def __extractAttributeRenamerFieldMaps(self, fldMapStr, version):
        '''
        :param fldMapStr: the field map string, form: oldfld, newfld,
                          default, <repeat>...
        :param version: different versions of the attribute renamer will have
                        different fldmapstr formats.
                        version 1: uses pairs of values
                        version 3: triplets with default values.
        :return: a list of lists where the inner list is made up of:
                 [old column name, new column name]
        '''
        fldMapList = fldMapStr.split(',')
        self.logger.debug("fldMapList: {0}".format(fldMapList))
        self.logger.debug("version: %s", version)
        fldMap = []
        increment = 3
        if version == '1':
            increment = 2

        for cntr in range(0, len(fldMapList), increment):
            if cntr + 2 > len(fldMapList):
                break
            defaultValue = None
            oldValue = fldMapList[cntr]
            newValue = fldMapList[cntr + 1]
            if increment == 3:
                defaultValue = fldMapList[cntr + 2]
            if defaultValue:
                msg = 'Warning found a default value defined for the field ' + \
                      '{0}/{1} {2}'
                msg = msg.format(oldValue, newValue, defaultValue)
                self.logger.warning(msg)
                warnings.warn(msg)
            fldMap.append([oldValue, newValue])
        if version not in ['1', '3', '2']:
            print fldMapStr
            msg = 'Unknown attribute renamer version, uncertain how to' + \
                  ' parse attribute renamers of this type: {0}'
            raise UnknownAttributeRenamerVersion(msg.format(version))
        return fldMap


class FMEPublishedParameters(object):
    '''
    wrapper to published parameters
    '''

    def __init__(self, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.publishedParams = publishedParams
        self.hasPubParamRegex = re.compile(
            FMWParserConstants.PUBPARAM_ANY, re.IGNORECASE)

    def getJson(self):
        '''
        paramDict[pubParamNameLst[0]] = { 'DEFAULT_VALUE':
                                            pubParam.attrib['DEFAULT_VALUE'],
                                          'TYPE':
                                            ' '.join(pubParamNameLst[1:])}
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
        self.logger.debug("self.publishedParams: %s", self.publishedParams)
        if self.hasPubParamRegex.match(inStr):
            retVal = True
        return retVal

    def getPublishedParameterValue(self, publishedParameterName):
        '''
        :param publishedParameterName: the name of a published parameter
                                       variable name.  Returns the value
                                       if the parameter exists and None if
                                       it does not
        '''
        retVal = None
        for param in self.publishedParams:
            if param == publishedParameterName:
                retVal = self.publishedParams[param]['DEFAULT_VALUE']
        return retVal

    def deReference(self, inStr):
        '''
        :param inputString: the input string that you want to have published
                            parameters replaced with their values.
        :return: same string but with the actual published parameter values
        '''
        outStr = inStr
        if self.hasPubParams(inStr):
            findParamRegex = re.compile(FMWParserConstants.PUBPARAM_SINGLE,
                                        re.IGNORECASE)
            for pubParamRegex in findParamRegex.finditer(inStr):
                paramName = inStr[pubParamRegex.start():pubParamRegex.end()]
                if paramName in self.publishedParams:
                    self.logger.debug("matched published parameter! %s",
                                      paramName)
                    paramType = self.publishedParams[paramName]['TYPE']
                    if paramType.lower() != 'Python Script:' and \
                       paramType.lower() != 'Python Script':
                        msg = "replacing the variable reference %s with its" + \
                              " value %s"
                        paramValue = \
                            self.publishedParams[paramName]['DEFAULT_VALUE']
                        self.logger.info(msg, paramName, paramValue)
                        outStr = outStr.replace(paramName, paramValue)
                    else:
                        msg = "parameter %s is a python script so not " + \
                              "replacing with its value"
                        self.logger.info(msg, paramName)


class FMEFeatureClasses(object):
    '''
    Parser will extract all the feature class records from the fmw that was
    read. This class provides an API to help extract specific Feature
    classes from the total number of feature classes defined in the FMW
    '''

    def __init__(self, featureClassesStruct, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("featureClassesStruct: {0}".format(
            featureClassesStruct))
        self.featClassesList = []
        self.pubParms = publishedParams
        self.logger.debug("publishedParams: {0}".format(
            publishedParams))
        self.addFeatureClasses(featureClassesStruct)
        self.iterCnter = 0  # keeps track of where the iterator is

    def addFeatureClasses(self, featureClassesStruct):
        '''
        Iterates through the featureClassesStruct which is a list of
        feature classes and uses them to create feature class objects.
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
        returns a treed data structure for each feature class with the
        following hierarchical structure:
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
        self.logger.debug("exporting the feature classes to a data struct" +
                          " that can be jsonified")
        for featCls in self.featClassesList:
            dataSet = featCls.getDataSet()
            datasetName = dataSet.getDataSetName()
            self.logger.debug("datasetName: %s", datasetName)
            if datasetName in tmpDataSetDict:
                curDataSet = tmpDataSetDict[datasetName]
                self.logger.debug("creating new dataset entry for: %s",
                                  datasetName)
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
            # newEntry = {'name': dataSet,
            #            'children': tmpDataSetDict[dataSet]}
            # datasetDict['children'].append(newEntry)
            datasetDict['children'].append(tmpDataSetDict[dataSet])
        return datasetDict

    def __iter__(self):
        return self

    def reset(self):
        '''
        resets the iterator back to the start, any current iterators will
        get pointed back to the first element.
        '''
        self.iterCnter = 0

    def next(self):
        '''
        required method for iterators
        '''
        retVal = None
        if self.iterCnter >= len(self.featClassesList):
            raise StopIteration
        else:
            retVal = self.featClassesList[self.iterCnter]
            self.iterCnter += 1
        return retVal


class FMEFeatureClass(object):
    '''
    The parser will extract info from the FMW and puts them into a python data
    structure.  The data structure is derived from what the attributes defined
    in the FMW. The parser also joins the column information and dataset
    information to the feature class record.

    This class provides an API to the Feature class record WITH the joined
    column information, hopefully making it easy to read.
    '''

    def __init__(self, fc, publishedParameters):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("fc: {0}".format(fc))
        self.pubParams = publishedParameters
        self.logger.debug("pubparams: {0}".format(self.pubParams))
        self.featClsStruct = fc
        self.fcNameField = 'NODE_NAME'
        self.featureTypeName = 'FEATURE_TYPE_NAME'

    def isSource(self):
        retVal = True
        if self.featClsStruct['DATASET']['IS_SOURCE'] == 'false':
            retVal = False
        return retVal

    def getParamName(self, paramName):
        '''
        Used to get parameters from the xml for the feature class that
        don't have methods associated with them.  Example, this is a
        list of parameters associated with a feature type.  To get the
        value of any of them simply include as an arguement to this
        method.

        id to get IS_SOURCE say ...getParamName(paramName='IS_SOURCE')
        will return "false"

             <FEATURE_TYPE
                 IS_SOURCE="false"
                 NODE_NAME="AMA_SNOWMOBILE_MGMT_AREAS_SP"
                 FEATURE_TYPE_NAME=""
                 FEATURE_TYPE_NAME_QUALIFIER=""
                 IS_EDITABLE="true"
                 IDENTIFIER="32"
                 FEAT_GEOMTYPE="sde30_area"
                 POSITION="1221 -385.69"
                 BOUNDING_RECT="1221 -385.69 0 0"
                 ORDER="35"
                 COLLAPSED="false"
                 KEYWORD="SDE30_1"
                 PARMS_EDITED="true"
                 ENABLED="true"
                 SCHEMA_ATTRIBUTE_SOURCE="1"
             >

        :param paramName : the name of the feature type property who's
                           corresponding value you are trying to retrieve.

        '''
        if paramName not in self.featClsStruct:
            msg = 'The parameter {0} does not exist as a property of this feature ' + \
                  'type.  Possible values include: {1}'
            msg = msg.format(paramName, self.featClsStruct.keys())
            self.logger.error(msg)
            raise ValueError(msg)
        return self.featClsStruct[paramName]

    def getDataSet(self):
        dataset = FMEDataSet(self.featClsStruct['DATASET'])
        return dataset

    def getFeatureClassName(self):
        '''
        starts by getting the NODE_NAME described for the feature type.
        This should be the fully qualified name with the schema in front of
        it.  Then to make sure this entry looks correct a bit of sanity
        checking takes place by comparing this value with the value in the
        property FEATURE_TYPE_NAME, it the names align then the assumption
        is that everything is ok.  If not then will get the name from the
        published parameter DEST_FEATURE_1
        '''
        nodeName = self.featClsStruct[self.fcNameField]
        featureType = self.featClsStruct[self.featureTypeName]
        nodeNameList = nodeName.split('.')

        if self.isSource():
            pubParamName = 'SRC_FEATURE_1'
        else:
            pubParamName = 'DEST_FEATURE_1'

        if len(nodeNameList) > 1:
            nodeNameFeatureClass = nodeNameList[1]
        else:
            nodeNameFeatureClass = nodeName
        if nodeNameFeatureClass.lower().strip() == featureType.lower().strip():
            retVal = nodeName
        else:
            # now hunting down the published parameters for the DEST_FEATURE_1
            # parameter then return whatever that value is.
            ppfc = self.pubParams.getPublishedParameterValue(pubParamName)
            if ppfc:
                if ppfc.lower().strip() == nodeNameFeatureClass.lower().strip() or \
                   ppfc.lower().strip() == featureType.lower().strip():
                    retVal = ppfc
                else:
                    msg = 'not sure what the destination feature class is for this fmw ' + \
                          'NODE_NAME = {0} FEATURE_TYPE_NAME = {1} and the published ' + \
                          'parameter $({3}) = {2}'
                    msg = msg.format(nodeName, featureType, ppfc, pubParamName)
                    self.logger.warning(msg)

        return retVal

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
                if columnProperty != 'ATTR_NAME':
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
        :param inputString: input strign that you want to have published
                            parameters dereferenced if possible.
        :return: same string but variable references de-referenced
        '''
        outStr = inputString
        if self.pubParams.hasPubParams(inputString):
            outStr = self.pubParams.deReference(inputString)
        return outStr

    def __str__(self):
        '''
        string representation, joins dataset name and feature class name
        '''
        dataSet = self.getDataSet()
        fcName = self.getFeatureClassName()
        return '{0}/{1}'.format(dataSet, fcName)


class FMEDataSet(object):

    def __init__(self, datasetStruct):
        self.datasetStruct = datasetStruct
        self.fcDataSetRelationshipField = 'KEYWORD'
        self.datasetNameField = 'DATASET'
        self.datasetFormatField = 'FORMAT'
        self.projectionField = 'COORDSYS'

    def getJson(self):
        dataSetList = []
        for propertyName in self.datasetStruct:
            param = {'name': propertyName,
                     'value': self.datasetStruct[propertyName]}
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
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.datasetStruct)
        return self.datasetStruct[self.datasetFormatField]

    def getProjection(self):
        '''
        :returns: the projection that has been defined for the dataset
        '''
        return self.datasetStruct[self.projectionField]

    def __str__(self):
        return self.getDataSetName()

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


class UnknownAttributeRenamerVersion(Exception):
    '''
    Error / exception for non 200 responses.
    '''

    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(UnknownAttributeRenamerVersion, self).__init__(message)
