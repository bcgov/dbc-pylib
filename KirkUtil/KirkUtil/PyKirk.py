'''
Created on Aug 8, 2018

@author: kjnether

A python wrapper around the kirk rest api.

'''
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation

from __future__ import unicode_literals

import logging
import os.path
import urlparse

import requests

from . import constants

class BaseRestCall(object):
    '''
    all kirk api methods will inherit from this class, includes base data
    and functions that relate to all api calls.
    '''

    def __init__(self, baseurl, token, apiVersion=1):
        self.logger = logging.getLogger(__name__)
        self.baseurl = baseurl
        self.restUrl = urlparse.urljoin(self.baseurl,
                                        'api/v{0}/'.format(apiVersion))
        self.authHeader = {'Authorization': 'Token {0}'.format(token)}

    def fixUrlPath(self, url):  # pylint: disable=no-self-use
        '''
        Receives a url path and ensures that it ends with a '/' character
        This is used when constructing urls to make sure the path can have
        another directory added to it using the urljoin method.
        '''
        if url[len(url) - 1] != '/':
            url = url + '/'
        return url


class ParamMatch(object):
    '''
    utility class for comparing parameter sets provided as dictionaries
    against a flexible database parameter schema.

    flexible database parameter schema sees each parameter stored using
    two columns, one that identifies the parameter type and the other
    the actual value.

    Contains methods that make it easy to take a dictionary and compare
    against the flexible schema

    :ivar paramSchema: an enumeration that describes the possible column
                       names that can be stored in the flexible schema
    :ivar schemaNameTemplate: a python format string where a single parameter
                              can be used to identify the position of the
                              element.  identifies the column name.
    :ivar schemaValueTemplate: a python format string where a single parameter
                               can be used to identify the position of the
                               element, this template identifies the value
    :ivar numberOfColumns: the number of columns represented in the flexible
                           schema

    so to provide some examples that will hopefully clarify how this works...

    paramSchema: to an enumeration with the following values, the actual
                  numeric values are unimportant, they are only requried
                  to keep the enumeration unique.  Each of the entries in
                  this enumeration identify a different column name that
                  can be represented in the flexible schema

       - transformerType = 1
       - counterName = 2
       - counterAttribute = 3
       - counterScope = 4
       - counterStartNumber = 5

    schemaNameTemplate: identifies a string that will be used to identify
                        the name of the column in the flexible schema,

                        an example: ts{0}_name

    schemaValueTemplate: identifies a string that will be used to identify
                         the name of a value that corresponds with a column,

                         an example: ts{0}_name


    numberOfColumns: this tells us how many columns will be represented by
                     this schema, thus if I used the examples above, and
                     entered a value of 4 for this value, the class would
                     expect a schema with the following columns:

                     ts1_name
                     ts1_value
                     ts2_name
                     ts2_value
                     ts3_name
                     ts3_value
                     ts4_name
                     ts4_value

    So putting it all together it would expect the schema that it will be
    comparing to have the ts*_name entreis to have one of the following values:
       - transformerType
       - counterName
       - counterAttribute
       - counterScope
       - counterStartNumber

    and the corresponding ts*_value would contain the corresponding values for each,
    thus if
       ts1_name = transformerType

    then the entry
       ts1_value
    would contain the corresponding value for transformerType.
    '''

    def __init__(self, paramSchema, schemaNameTemplate, schemaValueTemplate, numberOfColumns):
        self.logger = logging.getLogger(__name__)
        self.paramSchema = paramSchema
        self.schemaNameTemplate = schemaNameTemplate
        self.schemaValueTemplate = schemaValueTemplate
        self.numberOfColumns = numberOfColumns

    def dictionaryCompliesWithSchema(self, paramDictionary):
        '''
        This method will verify that the dictionary 'keys' are defined
        in the paramSchema.
        '''
        retVal = True
        for paramKey in paramDictionary:
            if paramKey not in self.paramSchema.__members__:
                retVal = False
                break
        return retVal

    def getMatchingSchema(self, flexibleSchema, paramDictionary, check=True):
        '''
        :param flexibleSchema: a list of dictionaries that contain the schema
                               that was described in the constructor
        :param paramDictionary: a dictionary that you would like to determine
                                if its value are represented in the flexible
                                schema list/struct
        :param check: checks that all the keys in the supplied dictionary
                      are described in the enumeration 'paramSchema'
        :return: None if the schema is not represented in the flexible schema
                 If a match is found then returns that actual schema
        '''
        if check:
            if not self.dictionaryCompliesWithSchema(paramDictionary):
                msg = 'The input dictionary keys: {0} do not match the ' + \
                      'expected schema: {1} contained in the property ' + \
                      'paramSchema'
                msg = msg.format(paramDictionary.keys(), self.paramSchema)
                raise SchemaMisMatchError(msg)

        retVal = None
        for schema in flexibleSchema:
            matched = False
            self.logger.debug("transformer id and name match")
            for param_name in paramDictionary:
                param_value = paramDictionary[param_name]
                for paramCnt in range(1, self.numberOfColumns + 1):
                    paramName_name = self.schemaNameTemplate.format(paramCnt)
                    paramValue_name = self.schemaValueTemplate.format(paramCnt)

                    paramName_value = schema[paramName_name]
                    paramValue_value = schema[paramValue_name]

                    if param_name == paramName_value and \
                       param_value == paramValue_value:
                        matched = True
                        break
                if not matched:
                    # have iterated over all the parameters and have
                    # not found a match
                    msg = "cannot find a match for the parameter {0} " + \
                          " = {1}, breaking out of loop"
                    msg = msg.format(param_name, param_value)
                    self.logger.debug(msg)
                    break
                else:
                    msg = "matched the parameter {0} " + \
                          " = {1}"
                    msg = msg.format(param_name, param_value)
                    self.logger.debug(msg)
            if matched:
                retVal = schema
                self.logger.debug("schema that matched: %s", retVal)
                break
        return retVal


class Kirk(BaseRestCall):
    '''
    The base class for all interactions with the KIRK api
    '''

    def __init__(self, baseurl, token):
        BaseRestCall.__init__(self, baseurl, token)

    def getJobs(self):
        '''
        :return:  a 'Jobs' object used to interact with the jobs end point
        '''
        jobs = Jobs(self)
        return jobs

    def getSources(self):
        '''
        :return: a 'Sources' object, used to interact with the source end
                 point.
        '''
        sources = Sources(self)
        return sources

    def getFieldMaps(self):
        '''
        :return: a 'Fieldmap' object, used to interact with the fieldmap
                 end point
        '''
        fldMaps = FieldMaps(self)
        return fldMaps

    def getTransformers(self):
        transformers = Transformers(self)
        return transformers


class FieldMaps(object):
    '''
    functionality relating to interaction with the fieldmap end point

    :ivar baseObj: reference to the object that contains the root path to
                   the api, etc.
    :ivar fldmapUrl: the root fieldmap url
    '''

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        fldmapUrl = urlparse.urljoin(self.baseObj.restUrl,
                                     constants.KirkApiPaths.FieldMaps, True)
        self.fldmapUrl = self.baseObj.fixUrlPath(fldmapUrl)
        self.logger.debug("fieldmaps url: %s", self.fldmapUrl)
        self.fldMaps = None

    def getFieldMaps(self, force=False):
        '''
        Queries the api and retrieves a list of the currently defined
        fieldmaps.  Once this has been done once the results are cached and
        re-used.  If you want to force a refresh of the cached data indicate
        a 'True' value for the 'force' parameter

        :param force: inicates whether you want to force the method to
                      refresh the cache.  In other words force it to igore
                      the cache, make the query to the api, and refresh the
                      data in the cache.
        :type force: bool
        '''

        if self.fldMaps is not None and not force:
            respJson = self.fldMaps
        else:
            response = requests.get(self.fldmapUrl,
                                    headers=self.baseObj.authHeader)
            if response.status_code < 200 or response.status_code >= 300:
                msg = constants.GET_NON_200_ERROR_MSG.format(
                    self.fldmapUrl,
                    response.status_code, response.text)
                raise APIError(msg)
            respJson = response.json()
            self.logger.debug("response json: %s", respJson)
            # print 'response:', respJson
            self.fldMaps = respJson
        return respJson

    def postFieldMaps(self, jobid, sourceColumnName, destColumnName):
        '''
        Adds a new field map based on provided parameters
        :param jobid: the job id that the fieldmap should be associated with
        :type jobid: int/str
        :param sourceColumnName: the name of the source column
        :type sourceColumnName: str
        :param destColumnName: the name of the destination column
        :type destColumnName: str
        '''

        fldmapProps = constants.FieldmapProperties

        struct = {fldmapProps.jobid.name: jobid,
                  fldmapProps.sourceColumnName.name: sourceColumnName,
                  fldmapProps.destColumnName.name: destColumnName}

        resp = requests.post(self.fldmapUrl,
                             data=struct,
                             headers=self.baseObj.authHeader)
        self.logger.debug("response from fieldmap post: %s", resp.json())
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(self.fldmapUrl,
                                                          resp.status_code,
                                                          resp.text)
            raise APIError(msg)
        self.getFieldMaps(force=True)
        return resp.json()

    def fieldMapExists(self, jobid, sourceColumn, destColumnName):
        '''
        look for a field map that matches the input jobid, source column
        name and destination Column name :param jobid: the job id to match
        in the field map

        :param sourceColumn: the source column
        :param destColumnName: the destination column

        :return: boolean value indicating whether a fieldmap record was found
                 that matches the provided input parameters
        '''
        fldMaps = self.getFieldMaps()
        fmProps = constants.FieldmapProperties
        retVal = False
        for fldmap in fldMaps:
            if fldmap[fmProps.jobid.name] == jobid and\
               fldmap[fmProps.sourceColumnName.name] == sourceColumn and\
               fldmap[fmProps.destColumnName.name] == destColumnName:
                retVal = True
                break
        return retVal

    def getFieldMapId(self, jobid, sourceColumn, destColumnName):
        '''
        Using the jobid, source column namd and destination column name
        retrieves the corresponding fieldmap id.

        :param jobid: the input job id, that corresponds with the fieldmap
                      that you want to retrieve
        :type jobid: str/int
        :param sourceColumn: the name of the source column in the fieldmap
                             that you are searching for
        :type sourceColumn: str
        :param destColumnName: the name of the destination column that
                               corresponds with the fieldmap you are trying
                               to retrieve
        :type destColumnName: str
        '''

        fldMaps = self.getFieldMaps()
        fmProps = constants.FieldmapProperties
        retVal = None
        for fldmap in fldMaps:
            if fldmap[fmProps.jobid.name] == jobid and\
               fldmap[fmProps.sourceColumnName.name] == sourceColumn and\
               fldmap[fmProps.destColumnName.name] == destColumnName:
                retVal = fldmap[fmProps.fieldMapId.name]
                break
        return retVal

    def deleteFieldMap(self, fldMapId, cancelUpdate=False):
        '''
        deletes a fieldmap entry

        :param fldMapId: the fieldmap id that identifies the record you want
                         to delete
        :type fldMapId: int/str
        :param cancelUpdate: You can override this parameter to cause the
                            method not to update the cached data about
                            fieldmaps.  This can save a lot of round trips
                            if you are deleting a lot of fieldmap data but
                            can then also result in stale data getting returned
                            if you forget to refresh it with a call to
                            getFieldMaps(force=True)
        :type cancelUpdate: bool
        '''

        fldMapUrl = urlparse.urljoin(self.fldmapUrl, str(fldMapId), True)
        fldMapUrl = self.baseObj.fixUrlPath(fldMapUrl)

        resp = requests.delete(fldMapUrl, headers=self.baseObj.authHeader)

        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(
                fldMapUrl, resp.status_code, resp.text)
            raise APIError(msg)

        self.logger.debug('response status code: %s', resp.status_code)

        if not cancelUpdate:
            # refresh the fieldmaps after the delete operation has takens place
            self.getFieldMaps(force=True)

        return resp


class Transformers(object):
    '''
    interactions with the 'transformers' end point
    '''

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        transformerUrl = urlparse.urljoin(self.baseObj.restUrl,
                                     constants.KirkApiPaths.Transformers, True)
        self.transformerUrl = self.baseObj.fixUrlPath(transformerUrl)
        self.logger.debug("transformer url: {0}".format(self.transformerUrl))
        self.transformers = None

    def getTransformers(self, force=None):
        if self.transformers is not None and not force:
            respJson = self.transformers
        else:
            response = requests.get(self.transformerUrl,
                                    headers=self.baseObj.authHeader)
            if response.status_code < 200 or response.status_code >= 300:
                msg = constants.GET_NON_200_ERROR_MSG.format(
                    self.transformerUrl,
                    response.status_code, response.text)
                raise APIError(msg)
            respJson = response.json()
            self.logger.debug("response json: %s", respJson)
            # print 'response:', respJson
            self.fldMaps = respJson
        return respJson

    def postTransformer(self, jobid, transformerType, parameters):
        '''
        :param jobid: the job id the transformer is related to
        :param transformerType:  the type of transformer
        :param parameters: This is a dictionary that is used to populate
                           the ts#_name and ts#_value parameters

        '''
        transProps = constants.TransformerProperties

        struct = {transProps.jobid.name: jobid,
                  transProps.transformer_type.name: transformerType}
        # restructure the dictionary into the key / value pairs used in
        # the api
        paramCnt = 1
        for paramName in parameters:
            propertyName_param = 'ts{0}_name'.format(paramCnt)
            propertyName_value = paramName
            propertyValue_param = 'ts{0}_value'.format(paramCnt)
            propertyValue_value = parameters[paramName]
            struct[propertyName_param] = propertyName_value
            struct[propertyValue_param] = propertyValue_value
            paramCnt += 1

        self.logger.debug("struct: {0}".format(struct))
        resp = requests.post(self.transformerUrl,
                             data=struct,
                             headers=self.baseObj.authHeader)
        self.logger.debug("response from transformer post: %s", resp.json())
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(self.transformerUrl,
                                                          resp.status_code,
                                                          resp.text)
            raise APIError(msg)
        self.getTransformers(force=True)
        return resp.json()

    def existsTransformer(self, jobid, transformerType, parameters):
        '''
        determines if there is a transformer that matches the information
        provided, The parameters will match only what is provided, so
        if you provide:

           status = global
        then it will only search for a transformer def that matches the
        job id, transformer type and status=global.
        '''
        transId = self.getTransformerId(jobid, transformerType, parameters)
        retVal = True
        if transId is None:
            retVal = False
        return retVal

    def getTransformerId(self, jobid, transformerType, parameters):

        transformers = self.getTransformers()
        props = constants.TransformerProperties
        retVal = None
        for transformer in transformers:
            if transformer[props.jobid.name] == jobid and \
               transformer[props.transformer_type.name] == transformerType:
                # job id and type match
                # now checking the properties
                matched = False
                self.logger.debug("transformer id and name match")
                for param_name in parameters:
                    param_value = parameters[param_name]
                    self.logger.debug("param_name: %s", param_name)
                    self.logger.debug("param_value: %s", param_value)
                    for paramCnt in range(1, 7):
                        paramName_name = 'ts{0}_name'.format(paramCnt)
                        paramValue_name = 'ts{0}_value'.format(paramCnt)

                        paramName_value = transformer[paramName_name]
                        paramValue_value = transformer[paramValue_name]
                        self.logger.debug("name: {0} = {1}".format(paramName_value, paramValue_value))
                        self.logger.debug("{0} {1}".format(type(param_value), type(paramValue_value)))
                        if type(param_value) != type(paramValue_value):
                            self.logger.warning("type mismatch {0} / {1}".format(type(param_value), 
                                                                                 type(paramValue_value))) 
                            self.logger.info("converting both to unicode")
                            param_value = unicode(param_value)
                            paramValue_value = unicode(paramValue_value)
                        if param_name == paramName_value and \
                           param_value == paramValue_value:
                            matched = True
                            break
                    if not matched:
                        # have iterated over all the parameters and have
                        # not found a match
                        msg = "cannot find a match for the parameter {0} " + \
                              " = {1}, breaking out of loop"
                        msg = msg.format(param_name, param_value)
                        self.logger.debug(msg)
                        break
                    else:
                        msg = "matched the parameter {0} " + \
                              " = {1}"
                        msg = msg.format(param_name, param_value)
                        self.logger.debug(msg)
                if matched:
                    retVal = transformer[props.transformer_id.name]
                    self.logger.debug("returning the id: %s", retVal)
                    break
        return retVal

    def deleteTransformer(self, transformerid, cancelUpdate=False):
        '''

        :param transformerid:
        :type transformerid:
        '''

        transformerUrl = urlparse.urljoin(self.transformerUrl,
                                     str(transformerid), True)
        transformerUrl = self.baseObj.fixUrlPath(transformerUrl)

        resp = requests.delete(transformerUrl, headers=self.baseObj.authHeader)

        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(
                transformerUrl, resp.status_code, resp.text)
            raise APIError(msg)

        self.logger.debug('response status code: %s', resp.status_code)

        if not cancelUpdate:
            # refresh the fieldmaps after the delete operation has takens place
            self.getTransformers(force=True)

        return resp


class Sources(object):
    '''
    A wrapper for the /sources end points used in kirk.
    '''

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        sourcesUrl = urlparse.urljoin(self.baseObj.restUrl,
                                      constants.KirkApiPaths.Sources, True)
        self.sourcesUrl = self.baseObj.fixUrlPath(sourcesUrl)
        self.logger.debug("sources url: %s", self.sourcesUrl)

    def getSources(self):
        '''
        :return: a list of all the sources currently configured
        '''
        response = requests.get(self.sourcesUrl,
                                headers=self.baseObj.authHeader)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(
                self.sourcesUrl, response.status_code, response.text)
            raise APIError(msg)
        respJson = response.json()
        self.logger.debug("response json: %s", respJson)
        return respJson

    def getJobSources(self, jobid):
        '''
        :param jobid: a jobid, method will return all the sources that
                      are associated with the job
        :return: a list or source objects associated with the jobid
        '''
        srcs = self.getSources()
        sourceProps = constants.SourceProperties
        jobSrcs = []
        for src in srcs:
            if src[sourceProps.jobid.name] == jobid:
                jobSrcs.append(src)
        return jobSrcs

    def postFileSources(self, jobid, sourceTable, sourceDataSet,
                        sourceType=constants.SourceTypes.file_geo_database):
        '''
        Writes file based sources, file based take a different set of args
        than database type sources.  Database sources will be added at a
        later date.

        :param jobid: the job id that the new source is to be associated with.
        :param sourceTable: the name of the source table
        :param sourceDataSet: the dataset path, for fgdb this is the path to
                              the fgdb.
        :param sourceType: the type of source, default value is fgdb.
        :return: the json object returned by the post request.
        '''
        sourceProps = constants.SourceProperties
        struct = {sourceProps.jobid.name: jobid,
                  sourceProps.sourceTable.name: sourceTable,
                  sourceProps.sourceFilePath.name: sourceDataSet,
                  sourceProps.sourceType.name: sourceType}
        resp = requests.post(self.sourcesUrl, data=struct,
                             headers=self.baseObj.authHeader)
        self.logger.debug("source post status code: %s", resp.status_code)
        self.logger.debug("full source post response: %s", resp.text)
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(
                self.sourcesUrl, resp.status_code, resp.text)
            raise APIError(msg)
        # TODO: Double check the return value is a 200 series
        return resp.json()

    def sourceFGDBTableExists(self, sourceTable, sourceFilePath, jobid=None):
        '''
        :param sourceTable: the source table name
        :param sourceFilePath: the path to the file that contains the table.
        :param jobid: optional/ if provided then will also try to match a
                      source that is configured for this job only.
        :return: a boolean value indicating whether the source defined in
                 parameters above exists or not
        '''
        srcs = self.getSources()
        sourceProps = constants.SourceProperties
        retVal = False
        for src in srcs:
            if src[sourceProps.sourceTable.name] == sourceTable or \
               src[sourceProps.sourceTable.name].lower() == \
               sourceTable.lower():
                self.logger.debug("Found the source: %s", sourceTable)
                self.logger.debug("source file path: %s and %s",
                                  src[sourceProps.sourceFilePath.name],
                                  sourceFilePath)

                # convert to norm path
                curSrcPathNorm = os.path.normpath(
                    src[sourceProps.sourceTable.name])
                passedSrcPathNorm = os.path.normpath(sourceTable)
                if curSrcPathNorm == passedSrcPathNorm:
                    if jobid:
                        if src[sourceProps.jobid.name] == jobid:
                            retVal = True
                            break
                    else:
                        retVal = True
                        break
        return retVal

    def deleteSource(self, srcId):
        '''
        :param srcId: the source id that is used to identify the source
                      record that is to be deleted.
        '''
        srcUrl = urlparse.urljoin(self.sourcesUrl, str(srcId), True)
        srcUrl = self.baseObj.fixUrlPath(srcUrl)

        resp = requests.delete(srcUrl, headers=self.baseObj.authHeader)

        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(
                self.sourcesUrl, resp.status_code, resp.text)
            raise APIError(msg)

        self.logger.debug('response status code: %s', resp.status_code)
        return resp


class Jobs(object):
    '''
    class that interacts with the Jobs end point
    '''

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.JobProperties = constants.JobProperties
        self.baseObj = baseObj
        self.logger.debug("self.baseObj.restUrl: %s", self.baseObj.restUrl)
        self.logger.debug("constants.KirkApiPaths.Jobs: %s",
                          constants.KirkApiPaths.Jobs)
        jobsUrl = urlparse.urljoin(self.baseObj.restUrl,
                                   constants.KirkApiPaths.Jobs, True)
        self.jobsUrl = self.baseObj.fixUrlPath(jobsUrl)
        self.logger.debug("kirk jobs url: %s", jobsUrl)
        self.logger.debug("jobs url: {0}".format(self.jobsUrl))

        # used to cache job lists so don't have to make a call to db every
        # time we want to determine if a job exists.
        self.cachedJobs = None

    def getJobs(self, force=False):
        '''
        queries the kirk rest api returning a complete list of all the jobs
        currently configured on the rest api.
        '''
        if self.cachedJobs and not force:
            respJson = self.cachedJobs
        else:
            response = requests.get(self.jobsUrl,
                                    headers=self.baseObj.authHeader)
            self.logger.debug("response Status: %s", response.status_code)
            if response.status_code < 200 or response.status_code >= 300:
                msg = constants.GET_NON_200_ERROR_MSG.format(
                    self.jobsUrl, response.status_code, response.text)
                raise APIError(msg)
            # print 'status:', response.status_code
            respJson = response.json()
            self.logger.debug("response json: %s", respJson)
            self.cachedJobs = respJson
            # print 'response:', respJson
        return respJson

    def getJob(self, jobid):
        '''
        returns specific information about a job if it exists.
        '''
        # could use the caching, but thinking stay away unless becomes a big
        # performance issue
        jobUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)

        response = requests.get(jobUrl, headers=self.baseObj.authHeader)
        self.logger.debug("response Status: %s", response.status_code)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(
                self.jobsUrl, response.status_code, response.text)
            raise APIError(msg)
        respJson = response.json()
        self.logger.debug("individual job response json: %s", respJson)
        return respJson

    def getJobSources(self, jobid):
        '''
        :param jobid: the jobid who's source you want to return
        '''
        jobUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        jobUrl = urlparse.urljoin(jobUrl, constants.KirkApiPaths.Sources, True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        response = requests.get(jobUrl, headers=self.baseObj.authHeader)
        self.logger.debug("response Status: %s", response.status_code)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(
                self.jobsUrl, response.status_code, response.text)
            raise APIError(msg)
        respJson = response.json()
        self.logger.debug("source for job %s response json: %s",
                          jobid, respJson)
        return respJson

    def getJobFieldMaps(self, jobid):
        '''
        gets the fieldmaps for the current jobid
        '''
        jobUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        jobUrl = urlparse.urljoin(jobUrl, constants.KirkApiPaths.FieldMaps,
                                  True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        response = requests.get(jobUrl, headers=self.baseObj.authHeader)
        self.logger.debug("response Status: %s", response.status_code)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(self.jobsUrl,
                                                         response.status_code,
                                                         response.text)
            raise APIError(msg)
        respJson = response.json()
        self.logger.debug("source for job %s response json: %s", jobid,
                          respJson)
        return respJson

    def postJobs(self, status, cronStr, destEnv, jobLabel, schema, fcName):
        '''
        Adds a Job to the api
           - jobStatus (PENDING, HOLD for test data or jobs that should not
                        be active)
           - CronStr
           - Destination env key

        # TODO: create an enumeration for possible status values.
        :param status: The job status, possible value PENDING, HOLD
        :type status: str
        :param cronStr: the cron string that describes recurrence of the
                        job.
        :type cronStr: str (quartz cron string format)
        :param destEnv: destination environment key, possible values include
                        DLV|TST|PRD
        :type destEnv: str
        :param jobLabel: A unique label that is used to identify the job,
                         should be a meaningful string similar to how we
                         named FMW's.
        :type jobLabel: str
        :param schema: The destination schema
        :type schema: str
        :param fcName: The destination table name
        :type fcName: str
        '''
        jobProps = constants.JobProperties
        struct = {jobProps.destField.name: destEnv,
                  jobProps.cronStr.name: cronStr,
                  jobProps.jobStatus.name: status,
                  jobProps.jobLabel.name:  jobLabel,
                  jobProps.destTableName.name: fcName,
                  jobProps.destSchema.name: schema}
        resp = requests.post(self.jobsUrl, data=struct,
                             headers=self.baseObj.authHeader)
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(
                self.jobsUrl, resp.status_code, resp.text)
            raise APIError(msg)

        self.getJobs(force=True)
        return resp.json()

    def addJobs(self, status, cronStr, destEnv, jobLabel, destSchema,
                destFeatureClass):
        '''
        This is a synonym to the postjob method.  Both do the same thing,
        see postjob for parameter description
        '''
        retVal = self.postJobs(status, cronStr, destEnv, jobLabel,
                               destSchema, destFeatureClass)
        return retVal

    def deleteJob(self, jobid):
        '''
        :param jobid: the unique identifier for the job that is to be deleted
        '''
        jobsUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobsUrl = self.baseObj.fixUrlPath(jobsUrl)
        self.logger.debug("delete url: %s", jobsUrl)
        print 'delete jobsUrl', jobsUrl
        resp = requests.delete(jobsUrl, headers=self.baseObj.authHeader)

        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(
                self.jobsUrl, resp.status_code, resp.text)
            raise APIError(msg)

        self.logger.debug('response status code: %s', resp.status_code)
        self.getJobs(force=True)
        return resp

    def jobExists(self, columnName, value):
        '''
        :param columnName: Used in combination with value, basically the job is
                       considered to exists, if there is a record where column
                       = value
        :param value: the value that the columnName should be equal to in a
                      record in order to consider the job as existing.
        '''
        retVal = False
        jobs = self.getJobs()
        for job in jobs:
            if job[columnName] == value:
                retVal = True
                break
        return retVal

    def jobIdExists(self, jobid):
        '''
        Returns true or false depending of whether a job exists or not
        '''
        retVal = self.jobExists(self.JobProperties.jobid.name, jobid)
        return retVal

    def jobLabelExists(self, jobLabel):
        '''
        :param jobLabel: the job label who's existence you want to determine
        :return: bool indicating if a job with the provided label exists

        '''
        retVal = self.jobExists(self.JobProperties.jobLabel.name, jobLabel)
        return retVal

    def getJobId(self, jobLabel):
        '''
        :param jobLabel: looks up the job id for this job label
        :return: jobid for the given job label.
        '''
        # todo: could create a cache whenever the jobs are fetched. Then
        #       check for the job label in the cache, if its there then
        #       return it, otherwise double check by doing a lookup.
        jobs = self.getJobs()
        jobId = None
        for job in jobs:
            if job[self.JobProperties.jobLabel.name] == jobLabel:
                jobId = job[self.JobProperties.jobid.name]
                break
        return jobId

    def getJobTransformers(self, jobid):
        jobUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        jobUrl = urlparse.urljoin(jobUrl, constants.KirkApiPaths.Transformers, True)
        jobUrl = self.baseObj.fixUrlPath(jobUrl)
        response = requests.get(jobUrl, headers=self.baseObj.authHeader)
        self.logger.debug("response Status: %s", response.status_code)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(
                self.jobsUrl, response.status_code, response.text)
            raise APIError(msg)
        respJson = response.json()
        self.logger.debug("transformers for job %s response json: %s",
                          jobid, respJson)
        return respJson

    def getCounterTransfomers(self, jobid):
        transformers = self.getJobTransformers(jobid)
        transParam = constants.TransformerProperties
        counterTransformers = []

        for trans in transformers:
            if trans[transParam.transformer_type.name] == constants.TransformerTypes.counter.name:
                counterTransformers.append(trans)
        return counterTransformers

    def jobTransformerExists(self, jobid, transformerType, params):
        '''
        Determines if a transformer with the parameters defined in 'params'
        of the type defined in 'transformerType' exists.
        
        :param jobid: the job id who's transformers you wish to query
        :type jobid: int/str
        :param transformerType: A transformer type defined in 
                                constants.TransformerTypes
        :type transformerType: PyKirk.constants.TransformerTypes
        :param params: a dictionary that represents a set of transformer
                       dynamic properties.  Will search the transformers
                       associated with the job/transformerType that match
                       the paramers defined here.
        :type params: dict
        '''
        exists = False
        # verify that tranformer type is defined
        if transformerType not in constants.TransformerTypes.__members__:
            msg = 'received a transformer type: {0}, Not a valid value, ' + \
                  'possible values defined in PyKirk.constants.TransformerTypes ' + \
                  'which are: {1}'
            msg = msg.format(transformerType, 
                             constants.JobProperties.__members__.keys())  # @UndefinedVariable
            raise ValueError(msg)
        
        # all the transformer associated with the job
        transformers = self.getJobTransformers(jobid)
        
        # filter the jobs that match 'transformerType' 
        transProps = constants.TransformerProperties
        jobTransformersList = []
        for transformer in transformers:
            if transformer[transProps.transformer_type.name] == transformerType:
                # now compare the params
                jobTransformersList.append(transformer)
        
        if jobTransformersList:
            paramMatch = ParamMatch(constants.CounterTransformerMap,
                                    constants.TRANSFORMER_NAME_TMPLT,
                                    constants.TRANSFORMER_VALUE_TMPLT,
                                    constants.TRANSFORMERS_DYNAMICFIELDS_LENGTH)
            
            firstMatch = paramMatch.getMatchingSchema(jobTransformersList, params)
            exists = True
        return exists

class APIError(Exception):
    '''
    Error / exception for non 200 responses.
    '''

    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(APIError, self).__init__(message)


class SchemaMisMatchError(Exception):
    '''
    Error / exception for non 200 responses.
    '''

    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(SchemaMisMatchError, self).__init__(message)
