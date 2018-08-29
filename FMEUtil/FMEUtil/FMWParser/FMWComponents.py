'''
Created on Jul 24, 2018

@author: kjnether

When a FMW gets parsed it gets broken up into the various components 
described in this module.
'''
import logging
import FMWParser
import FMWParserConstants
import re
import pprint
import warnings

print 'FMWCOMPONENTS: ', __name__

class FMEWorkspace(object):
    '''
    Provides an api to extract information about the workspace
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
        # TODO: not working at the moment 7-24-2018
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
        
        This method should be able detect both of these approaches.
        
        '''
        # TODO: write code to do this.


class FMETransformers(object):
    '''
    a wrapper to the transformer data struct that should hopefully make it
    easy to extract information about transformers.
    '''

    def __init__(self, transformerStruct, publishedParams):
        self.logger = logging.getLogger(__name__)
        self.transfomerStruct = transformerStruct
        self.logger.debug('transformer struct: {0}'.format(self.transfomerStruct))
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
    
    def __extractAttributeRenamerFieldMaps(self, fldMapStr, version):
        '''
        :param fldMapStr: the field map string, form: oldfld, newfld, default, <repeat>...
        :param version: different versions of the attribute renamer will have 
                        different fldmapstr formats.  
                        version 1: uses pairs of values
                        version 3: triplets with default values.
        :return: a list of lists where the inner list is made up of: 
                 [old column name, new column name]
        '''
        fldMapList = fldMapStr.split(',')
        self.logger.debug("fldMapList: {0}".format(fldMapList))
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
                msg = 'Warning found a default value defined for the field {0}/{1} {2}'
                msg = msg.format(oldValue, newValue, defaultValue)
                self.logger.warning(msg)
                warnings.warn(msg)
            fldMap.append([oldValue, newValue])
        if version not in ['1', '3', '2']:
            print fldMapStr
            raise
        return fldMap
    
    def getAttributeRenamerFieldMap(self):
        fldMaps = []
        transNames = self.getTransformerNames()
        for trans in transNames:
            if trans.lower() == 'AttributeRenamer'.lower():
                # need to extract the struct for this one
                for transformer in self.transfomerStruct:
                    if transformer['TYPE'].lower() == 'AttributeRenamer'.lower():
                        transVersion = transformer['VERSION']
                        #pp = pprint.PrettyPrinter(indent=4)
                        #pp.pprint(transformer)
                        # need to iterate over the CHILD element
                        # list and extract the entry where 
                        # PARM_NAME = ATTR_LIST
                        # then extract the PARM_VALUE for that entry
                        # the values are organized into triplets, where
                        # OLDCOLUMN, NEWCOLUMN, DEFAULTVALUE
                        # default should be blank
                        for child in transformer['CHILD']:
                            if 'PARM_NAME' in child:
                                if child['PARM_NAME'] == 'ATTR_LIST':
                                    if child['PARM_VALUE']:
                                        print 'fldmapstr', child['PARM_VALUE']
                                        fldMap = self.__extractAttributeRenamerFieldMaps(child['PARM_VALUE'], transVersion)
                                        fldMaps.append(fldMap)
        return fldMaps

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
        self.logger.debug("featureClassesStruct: {0}".format(featureClassesStruct))
        self.featClassesList = []
        self.pubParms = publishedParams
        self.logger.debug("publishedParams: {0}".format(publishedParams))
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
        self.logger = logging.getLogger(__name__)
        self.logger.debug("fc: {0}".format(fc))
        self.pubParams = publishedParameters
        self.logger.debug("pubparams: {0}".format(self.pubParams))
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
