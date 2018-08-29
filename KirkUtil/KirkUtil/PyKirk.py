'''
Created on Aug 8, 2018

@author: kjnether

A python wrapper around the kirk rest api.

'''

import logging
from . import constants
import urlparse
import requests


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

class Jobs():

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        constants.KirkApiPaths.Jobs
        print 'self.baseObj.restUrl', self.baseObj.restUrl
        print 'constants.KirkApiPaths.Jobs', constants.KirkApiPaths.Jobs
        jobsUrl = urlparse.urljoin(self.baseObj.restUrl, constants.KirkApiPaths.Jobs, True)
        self.jobsUrl = self.baseObj.fixUrlPath(jobsUrl)
        print 'kirk jobs url:', jobsUrl
        self.logger.debug("jobs url: {0}".format(self.jobsUrl))

    def getJobs(self):
        '''
        queries the kirk rest api returning a complete list of all the jobs
        currently configured on the rest api.
        '''
        # TODO: Define the actual rest call to the job
        response = requests.get(self.jobsUrl, headers=self.baseObj.authHeader)
        respJson = response.json()
        print 'response:', respJson
        return respJson
    
    def postJobs(self, status, cronStr, destEnv):
        '''
        Adds a Job to the api
           - jobStatus (PENDING, HOLD for test data or jobs that should not be active)
           - CronStr
           - Destination env key
        '''
        struct = {'destField': destEnv, 
                  'cronStr': cronStr, 
                  'jobStatus': status }
        resp = requests.post(self.jobsUrl, data=struct, headers=self.baseObj.authHeader)
        return resp.json()
    
    def deleteJob(self, jobid):
        '''
        :param jobid: the unique identifier for the job that is to be deleted
        '''
        jobsUrl = urlparse.urljoin(self.jobsUrl, str(jobid), True)
        jobsUrl = self.baseObj.fixUrlPath(jobsUrl)
        print 'delete jobsUrl', jobsUrl
        requests.delete(jobsUrl)

    def jobIdExists(self, jobid):

