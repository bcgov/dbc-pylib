'''
Created on Aug 8, 2018

@author: kjnether

A python wrapper around the kirk rest api.

'''

import logging
from . import constants
import urlparse
import requests
import os.path


class BaseRestCall(object):

    def __init__(self, baseurl, token, apiVersion=1):
        self.logger = logging.getLogger(__name__)
        self.baseurl = baseurl
        self.restUrl = urlparse.urljoin(self.baseurl, 'api/v1/')
        self.authHeader = {'Authorization': 'Token {0}'.format(token)}

    def fixUrlPath(self, url):  # pylint: disable=no-self-use
        '''
        Receives a url path and ensures that it ends with a '/' character
        This is used when constructing urls to make sure the path can have
        another directory added to it using the urljoin method.
        '''
        if url[len(url) - 1] <> '/':
            url = url + '/'
        return url


class Kirk(BaseRestCall):

    def __init__(self, baseurl, token):
        BaseRestCall.__init__(self, baseurl, token)

    def getJobs(self):
        jobs = Jobs(self)
        return jobs
    
    def getSources(self):
        sources = Sources(self)
        return sources
    
    def getFieldMaps(self):
        fldMaps = FieldMaps(self)
        return fldMaps


class FieldMaps(object):
    
    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        fldmapUrl = urlparse.urljoin(self.baseObj.restUrl, constants.KirkApiPaths.FieldMaps, True)
        self.fldmapUrl = self.baseObj.fixUrlPath(fldmapUrl)
        self.logger.debug("fieldmaps url: %s", self.fldmapUrl)
        self.fldMaps = None
        
    def getFieldMaps(self, force=False):
        if self.fldMaps is not None and not force:
            respJson = self.fldMaps
        else:
            response = requests.get(self.fldmapUrl, headers=self.baseObj.authHeader)
            if response.status_code < 200 or response.status_code >= 300:
                msg = constants.GET_NON_200_ERROR_MSG.format(self.fldmapUrl, response.status_code, response.text)
                raise APIError, msg
            respJson = response.json()
            self.logger.debug("response json: %s", respJson)
            # print 'response:', respJson
            self.fldMaps = respJson
        return respJson
    
    def postFieldMaps(self, jobid, sourceColumnName, destColumnName):
        fldmapProps = constants.FieldmapProps
        
        struct = {fldmapProps.jobid.name: jobid,
                  fldmapProps.sourceColumnName.name: sourceColumnName,
                  fldmapProps.destColumnName.name: destColumnName }
        
        resp = requests.post(self.fldmapUrl, data=struct, headers=self.baseObj.authHeader)
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(self.fldmapUrl, resp.status_code, resp.text)
            raise APIError, msg
        self.getFieldMaps(force=True)
        return resp.json()
    
    def fieldMapExists(self, jobid, sourceColumn, destColumnName):
        '''
        look for a field map that matches the input jobid, source column name and 
        destination Column name
        :param jobid: the job id to match in the field map
        :param sourceColumn: the source column 
        :param destColumnName: the destination column
        
        :return: boolean value indicating whether a fieldmap record was found that matches
                 the provided input parameters
        '''
        fldMaps = self.getFieldMaps()
        fmProps = constants.FieldmapProps
        retVal = False
        for fldmap in fldMaps:
            if fldmap[fmProps.jobid.name] == jobid and\
               fldmap[fmProps.sourceColumnName.name] == sourceColumn and\
               fldmap[fmProps.destColumnName.name] == destColumnName:
                retVal = True
                break
        return retVal
    
    def getFieldMapId(self, jobid, sourceColumn, destColumnName):
        fldMaps = self.getFieldMaps()
        fmProps = constants.FieldmapProps
        retVal = None
        for fldmap in fldMaps:
            if fldmap[fmProps.jobid.name] == jobid and\
               fldmap[fmProps.sourceColumnName.name] == sourceColumn and\
               fldmap[fmProps.destColumnName.name] == destColumnName:
                retVal = fldmap[fmProps.fieldMapId.name]
                break
        return retVal
    
    def deleteFieldMap(self, fldMapId):
        fldMapUrl = urlparse.urljoin(self.fldmapUrl, str(fldMapId), True)
        fldMapUrl = self.baseObj.fixUrlPath(fldMapUrl)
        
        resp = requests.delete(fldMapUrl, headers=self.baseObj.authHeader)
        
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(self.fldMapUrl, resp.status_code, resp.text)
            raise APIError, msg

        self.logger.debug('response status code: %s', resp.status_code)
        
        # refresh the fieldmaps after the delete operation has takens place
        self.getFieldMaps(force=True)
        
        return resp
        

        
class Sources(object):
    '''
    A wrapper for the /sources end points used in kirk.
    '''
    
    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        sourcesUrl = urlparse.urljoin(self.baseObj.restUrl, constants.KirkApiPaths.Sources, True)
        self.sourcesUrl = self.baseObj.fixUrlPath(sourcesUrl)
        self.logger.debug("sources url: %s", self.sourcesUrl)
        
    def getSources(self):
        '''
        :return: a list of all the sources currently configured
        '''
        response = requests.get(self.sourcesUrl, headers=self.baseObj.authHeader)
        if response.status_code < 200 or response.status_code >= 300:
            msg = constants.GET_NON_200_ERROR_MSG.format(self.sourcesUrl, response.status_code, response.text)
            raise APIError, msg
        respJson = response.json()
        self.logger.debug("response json: %s", respJson)
        # print 'response:', respJson
        return respJson
    
    def getJobSources(self, jobid):
        '''
        :param jobid: a jobid, method will return all the sources that are associated with the 
                      job
        :return: a list or source objects associated with the jobid
        '''
        srcs = self.getSources()
        sourceProps = constants.SourceProperties
        jobSrcs = []
        for src in srcs:
            if src[sourceProps.Jobid.name] == jobid:
                jobSrcs.append(src)
        return jobSrcs
    
    def postFileSources(self, jobid, sourceTable, sourceDataSet, sourceType=constants.SourceTypes.file_geo_database):
        '''
        Writes file based sources, file based take a different set of args than database 
        type sources.  Database sources will be added at a later date.
        :param jobid: the job id that the new source is to be associated with.
        :param sourceTable: the name of the source table
        :param sourceDataSet: the dataset path, for fgdb this is the path to the fgdb.
        :param sourceType: the type of source, default value is fgdb.
        :return: the json object returned by the post request.
        '''
        sourceProps = constants.SourceProperties
        struct = {sourceProps.jobid.name: jobid,
                  sourceProps.sourceTable.name: sourceTable,
                  sourceProps.sourceFilePath.name: sourceDataSet,
                  sourceProps.sourceType.name: sourceType}
        resp = requests.post(self.sourcesUrl, data=struct, headers=self.baseObj.authHeader)
        self.logger.debug("source post status code: %s", resp.status_code)
        self.logger.debug("full source post response: %s", resp.text)
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(self.sourcesUrl, resp.status_code, resp.text)
            raise APIError, msg
        # TODO: Double check the return value is a 200 series
        return resp.json()
    
    def sourceFGDBTableExists(self, sourceTable, sourceFilePath, jobid=None):
        '''
        :param sourceTable: the source table name
        :param sourceFilePath: the path to the file that contains the table.
        :param jobid: optional/ if provided then will also try to match a source that is 
                      configured for this job only.
        :return: a boolean value indicating whether the source defined in parameters above exists 
                 or not
        '''
        srcs = self.getSources()
        sourceProps = constants.SourceProperties
        retVal = False
        for src in srcs:
            if src[sourceProps.sourceTable.name] == sourceTable or \
               src[sourceProps.sourceTable.name].lower() == sourceTable.lower():
                self.logger.debug("Found the source: %s", sourceTable)
                self.logger.debug("source file path: %s and %s", src[sourceProps.sourceFilePath.name], sourceFilePath)
                
                # convert to norm path
                curSrcPathNorm = os.path.normpath(src[sourceProps.sourceTable.name])
                passedSrcPathNorm = os.path.normpath(sourceTable)
                if curSrcPathNorm == passedSrcPathNorm:
                # if src[sourceProps.sourceFilePath.name] == \
                #  sourceFilePath:
                    if jobid:
                        if src[sourceProps.jobid.name] == jobid:
                            retVal = True
                            break
                    else:
                        retVal = True
                        break
        return retVal             

    def deleteSource(self, srcId):
        
        # response = requests.get(self.sourcesUrl, headers=self.baseObj.authHeader)
        
        sourceProps = constants.SourceProperties
        
        srcUrl = urlparse.urljoin(self.sourcesUrl, str(srcId), True)
        srcUrl = self.baseObj.fixUrlPath(srcUrl)
        
        resp = requests.delete(srcUrl, headers=self.baseObj.authHeader)
        
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.DELETE_NON_200_ERROR_MSG.format(self.sourcesUrl, resp.status_code, resp.text)
            raise APIError, msg

        self.logger.debug('response status code: %s', resp.status_code)
        return resp


class Jobs(object):

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.JobProperties = constants.JobProperties
        self.baseObj = baseObj
        self.logger.debug("self.baseObj.restUrl: %s", self.baseObj.restUrl)
        self.logger.debug("constants.KirkApiPaths.Jobs: %s", constants.KirkApiPaths.Jobs)
        jobsUrl = urlparse.urljoin(self.baseObj.restUrl, constants.KirkApiPaths.Jobs, True)
        self.jobsUrl = self.baseObj.fixUrlPath(jobsUrl)
        self.logger.debug("kirk jobs url: %s", jobsUrl)
        self.logger.debug("jobs url: {0}".format(self.jobsUrl))
        
        # used to cache job lists so don't have to make a call to db every time we
        # want to determine if a job exists.
        self.cachedJobs = None

    def getJobs(self, force=False):
        '''
        queries the kirk rest api returning a complete list of all the jobs
        currently configured on the rest api.
        '''
        # TODO: Define the actual rest call to the job
        if self.cachedJobs and not force:
            respJson = self.cachedJobs
        else:
            response = requests.get(self.jobsUrl, headers=self.baseObj.authHeader)
            self.logger.debug("response Status: %s", response.status_code)
            if response.status_code < 200 or response.status_code >= 300:
                msg = constants.GET_NON_200_ERROR_MSG.format(self.jobsUrl, response.status_code, response.text)
                raise APIError, msg
            # print 'status:', response.status_code
            respJson = response.json()
            self.logger.debug("response json: %s", respJson)
            self.cachedJobs = respJson
            # print 'response:', respJson
        return respJson
    
    def postJobs(self, status, cronStr, destEnv, jobLabel):
        '''
        Adds a Job to the api
           - jobStatus (PENDING, HOLD for test data or jobs that should not be active)
           - CronStr
           - Destination env key
        '''
        jobProps = constants.JobProperties
        struct = {jobProps.destField.name: destEnv,
                  jobProps.cronStr.name: cronStr,
                  jobProps.jobStatus.name: status,
                  jobProps.jobLabel.name:  jobLabel}
        resp = requests.post(self.jobsUrl, data=struct, headers=self.baseObj.authHeader)
        if resp.status_code < 200 or resp.status_code >= 300:
            msg = constants.POST_NON_200_ERROR_MSG.format(self.jobsUrl, resp.status_code, resp.text)
            raise APIError, msg
        
        self.getJobs(force=True)
        return resp.json()
    
    def addJobs(self, status, cronStr, destEnv, jobLabel):
        retVal = self.postJobs(status, cronStr, destEnv, jobLabel)
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
            msg = constants.DELETE_NON_200_ERROR_MSG.format(self.jobsUrl, resp.status_code, resp.text)
            raise APIError, msg
        
        self.logger.debug('response status code: %s', resp.status_code)
        self.getJobs(force=True)
        return resp

    def jobExists(self, columnName, value):
        '''
        :param columnName: Used in combination with value, basically the job is 
                       considered to exists, if there is a record where column 
                       = value
        :param value: the value that the columnName should be equal to in a record
                      in order to consider the job as existing.
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

    
class APIError(Exception):

    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(APIError, self).__init__(message)
    
