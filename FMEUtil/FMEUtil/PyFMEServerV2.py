"""

About
=========
:synopsis:     A THIRD attempt at an FME Server Rest API python wrapper,
               This attempt will use FMEServers V2 Rest api, while
               trying to maintain backward compatibility with the
               python api defined by the original module
:moduleauthor: Kevin Netherton
:date:         4-30-2015
:description:  Previous attempts at this library are messy! (FMEServerInteraction.py)
               This is a second run at an FME server library.  This is the
               base class and attempts to remain decoupled from other code
               like PMP access modules for example.

               This attempt tries to mimic the fme rest api hierarchy.  Scripts
               always start with an FMEServer object.

Dependencies:
-------------------
 - Requests


API DOC:
===============
"""
import json
import logging
import os.path
import pprint
import re
import urllib
import urlparse

import requests


class FMERestBase(object):
    '''
    This class is not called directly.  It contains functionality to perform
    the actual rest call interaction.  Other modules will construct the end
    points, the parameters, data to include, headers etc, then will call one
    of these methods to perform the actual request to the rest api.
    '''

    def __init__(self, baseurl, token):
        self.logger = logging.getLogger(__name__)

        # baseurl should be http://servername
        self.baseurl = baseurl
        self.restUrl = urlparse.urljoin(self.baseurl, 'fmerest/v2/')
        self.token = token
        self.repositoryDir = 'repositories'
        self.scheduleDir = 'schedules'
        self.jobsDir = 'transformations'
        self.resourcesDir = 'resources'
        self.logsDir = 'logs'
        self.dataType = 'json'
        self.detail = 'low'
        self.repos = []
        self.payloadDict = {'token': self.token,
                            'accept': self.dataType,
                            'detail': self.detail}
        self.restUrl = self.fixUrlPath(self.restUrl)

    def fixUrlPath(self, url):  # pylint: disable=no-self-use
        '''
        Receives a url path and ensures that it ends with a '/' character
        This is used when constructing urls to make sure the path can have
        another directory added to it using the urljoin method.
        '''
        if url[len(url) - 1] <> '/':
            url = url + '/'
        return url

    def preUrl(self, url, returnType, detail, additionalParams=''):  # pylint: disable=unused-argument
        '''
        All of the interactions with fme server require the token to be
        passed along as part of the request payload.  This method merges
        these required parameters with any other existing parameters.

        when there is duplication of parameters between default values
        and those passed to this method in the parameter additionalParams
        the additionalParams will take precedence
        '''
        payloadDict = self.payloadDict.copy()
        if detail <> payloadDict['detail']:
            payloadDict['detail'] = detail
        if additionalParams:
            payloadDict.update(additionalParams)
        if not payloadDict.has_key('accept'):
            payloadDict['accept'] = returnType
        if payloadDict['accept'] <> returnType:
            payloadDict['accept'] = returnType
        return payloadDict

    def getResponse(self, url, returnType='json', detail='low', additionalParams=None,
                    header=None, body=None, dontErrorStatusCodes=None):
        '''
        Sends the rest query and returns the raw json response.
        '''
        if additionalParams is None:
            additionalParams = {}
        if header is None:
            header = {}
        if body is None:
            body = {}
        if dontErrorStatusCodes is None:
            dontErrorStatusCodes = []

        # will always request data be returned as json,
        # return type determines whether the json returned will be
        # raw text, or converted into python objects
        payloadDict = self.preUrl(url, returnType, detail, additionalParams)

        if returnType == 'raw':
            if payloadDict.has_key('accept'):
                del payloadDict['accept']
            r = requests.get(url, params=payloadDict, stream=True, headers=header, data=body)
        else:
            r = requests.get(url, params=payloadDict, headers=header, data=body)
        if r.status_code <> 200 and r.status_code not in dontErrorStatusCodes:
            msg = 'Request did not succeed!  Status Code is: {0} and ' + \
                  'returned body is {1}'
            msg = msg.format(r.status_code, r.text)
            raise ValueError, msg
        if returnType == 'json':
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def deleteResponse(self, url, returnType='json', detail='low', data='', \
                        header=None, acceptCodes=None):
        '''
        Used by other methods to complete DELETE rest calls
        '''
        # print 'url', url
        payloadDict = self.preUrl(url, returnType, detail)
        # print 'payloadDict', payloadDict
        if not header:
            header = {'Content-Type': 'application/x-www-form-urlencoded',
                      'Accept': 'application/json'}
        r = requests.delete(url, params=payloadDict, data=data, headers=header)

        AcceptableStatusCodes = [200, 201]
        if acceptCodes:
            AcceptableStatusCodes = AcceptableStatusCodes + acceptCodes
        if not r.status_code in AcceptableStatusCodes:
            msg = 'Received the error code: {0} when trying to ' + \
                  'request the url with delete method {1} encoded url is {2}'
            msg = msg.format(r.status_code, url, r.url)
            # print 'rtext', r.text
            # print 'r is', r
            raise ValueError, msg
        # print 'r.text', r.text
        # print 'requests', r
        return r

    def putResponse(self, url, returnType='json', detail='low', data='', header=None, params=None):
        '''
        manages POST requests by the other methods that require interact with fme server
        '''

        defaultHeader = {'Content-Type': 'application/octet-stream',
                         'Accept': 'application/json'}
        if not header:
            header = defaultHeader
        # if params:
        params = self.preUrl(url, returnType, detail, params)
        # print 'params', params
        # print 'url', url
        # print 'data', data
        r = requests.put(url=url, headers=header, data=data, params=params)
        if not r.status_code in [200]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'put the job {1}'
            msg = msg.format(r.status_code, url)
            # print 'rtext', r.text
            # print 'r is', r
            raise ValueError, msg
        if returnType == 'json':
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def postResponseFormData(self, url, returnType='json', detail='low', data='', header=None, \
                             params=None):
        '''
        Low level POST rest calls.  Method acts as an interface between the actual rest call
        and the results
        '''
        payloadDict = self.preUrl(url, returnType, detail, additionalParams=params)
        if not header:
            header = {'Content-Type': 'application/x-www-form-urlencoded',
                      'Accept': 'application/json'}
        r = requests.post(url, params=payloadDict, data=data, headers=header)
        if not r.status_code in [200, 201]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'schedule the job {1}'
            msg = msg.format(r.status_code, url)
            raise ValueError, msg
        if returnType == 'json':
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def postResponse(self, url, returnType='json', detail='low', data=None, header=None, \
                     params=None):
        '''
        handles POST rest calls for the rest of the module, hopefully hideing all interactions
        with the rest api.
        '''
        if data is None:
            data = {}
        payloadDict = self.preUrl(url, returnType, detail, additionalParams=params)
        if isinstance(data, dict):
            data = json.dumps(data)
        if header:
            header['Authorization'] = 'fmetoken token=' + payloadDict['token']
            del payloadDict['token']
            r = requests.post(url, data=data, headers=header, params=payloadDict)
        else:

            r = requests.post(url, params=payloadDict, data=data)
        if not r.status_code in [200, 201, 202]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'schedule the job {1} {2}'
            msg = msg.format(r.status_code, url, r.text)
            raise ValueError, msg
        if returnType == 'json':
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def getURL(self, url, returnType='json', detail='low', additionalParams=None):
        '''
        Makes GET request for the rest of the methods described below.
        '''
        payloadDict = self.preUrl(url, returnType, detail, additionalParams)
        r = requests.Request('GET', url, data=payloadDict)
        prep = r.prepare()
        prep.prepare_url(url, payloadDict)
        return prep.url


class FMEServer(FMERestBase):
    '''
    This is the starting class / entry class for all interactions with this
    api.  This class sets up the base parameters required to interact with
    fme server. (ie, token / url)
    '''

    def __init__(self, baseurl, token):
        '''
        :param baseurl: should be just: http://servername.  Don't include any paths, \
                        those are handed by the module
        :type baseurl: str
        :param token: the api token for interacting with fme server
        :type token: str
        '''
        FMERestBase.__init__(self, baseurl, token)

    def getRepository(self):
        '''
        Returns a Repository object
        '''
        repos = Repository(self)
        return repos

    def getJobs(self):
        '''
        returns a job object
        '''
        jobs = Jobs(self)
        return jobs

    def getLogs(self):
        '''
        returns a Logs object
        '''
        logs = Logs(self)
        return logs

    def getSchedules(self):
        '''
        returns a schedules object
        '''
        sched = Schedules(self)
        return sched

    def getResources(self):
        '''
        returns a Resources object
        '''
        resources = Resources(self)
        return resources


class Logs(object):  # pylint: disable=too-few-public-methods
    '''
    functionality around logs generated by Jobs.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        # example of v1 url to a log
        # V2 logs are moved under the jobs.
        # category for jobs: completed | running | queued
        # http://fmeserver/fmerest/v2/transformations/jobs/completed?detail=low&limit=-1&offset=-1
        self.url = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.jobsDir, True)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, 'jobs', True)
        self.url = self.baseObj.fixUrlPath(self.url)

        # self.url = urlparse.urljoin(self.url, 'complete', True)
        # self.url = self.baseObj.fixUrlPath(self.url)

    def getLog(self, logId):
        '''
        Returns a Log object for a given log id. Job id?
        '''
        log = Log(self, logId)
        return log


class Schedules(object):
    '''
    interface to schedules stored in fme server.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.url = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.scheduleDir, True)

    def getSchedule(self):
        '''
        Returns a 'Schedule' object
        '''
        sched = Schedule(self)
        return sched

    def getSchedules(self, detail='high'):
        '''
        Returns a list of schedule dictionaries that describe the individual schedules
        '''
        response = self.baseObj.getResponse(self.url, detail=detail)
        retList = []
        for i in response:
            retList.append(i)
        return retList

    def exists(self, schedName, category=None):
        '''
        Returns a boolean that indicates whether a schedule exists or not.
        '''
        schedsList = self.getSchedules(detail='low')
        retVal = False
        # print 'schedList:', schedsList
        for sched in schedsList:
            # self.logger.debug("current sched in iteration %s", sched)
            if sched['name'] == schedName:
                # if a category is supplied then require that that match also
                if category:
                    if category == sched['category']:
                        retVal = True
                        break
                else:
                    retVal = True
                    break
        return retVal


class Schedule(object):
    '''
    an interface to individual schedules
    '''

    def __init__(self, schedules):
        self.baseObj = schedules.baseObj
        self.schedules = schedules
        self.logger = logging.getLogger(__name__)

    def addSchedule(self, scheduleDescription):
        '''
        This method will receive a schedule description object.  The
        Structure / properties of a schedule description object are
        defined with the FME Server rest api.

        The following object is an example of a schedule description:
            {'category': 'subterrestrial beings occurrences',
             'recurrence': 'cron',
             'begin': '2012-05-31T02:30:00',
             'name': 'fancyfmwName.fmw',
             'repository': 'GuyLaFleur',
             'request':
                 {'publishedParameters':
                     {'name': 'Dest_Server',
                     'value': 'somehost.bcgov'}
                 },
             'enabled': True,
             'cron': '0 30 2 * * 2,3,4,5,6',
             'workspace': 'fancyfmwName.fmw'}


        :param  scheduleDescription: schedule description object as defined by
                                     the fme server rest api.
        :type scheduleDescription: dict
        '''
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}
        response = self.baseObj.postResponse(self.schedules.url,
                                             data=scheduleDescription,
                                             header=header,
                                             detail='low')
        # print 'response', response
        self.logger.debug("response is: %s", response)

    def delete(self, category, scheduleName):
        '''
        :param category: The name of the category that the job exists within
                         that should be deleted
        :param scheduleName: the name of the schedule that should be deleted
        deletes a schedule in the given category with the provided schedule name
        '''
        # catEncode = urllib.quote(category)
        # print 'catEncode:', catEncode
        # scheduleNameEncode = urllib.quote(scheduleName)
        print 'schedules url', self.schedules.url
        url = self.schedules.baseObj.fixUrlPath(self.schedules.url)

        # url = urlparse.urljoin(url, catEncode)
        url = urlparse.urljoin(url, category)
        url = self.schedules.baseObj.fixUrlPath(url)
        # url = urlparse.urljoin(url, scheduleNameEncode)
        url = urlparse.urljoin(url, scheduleName)
        url = self.schedules.baseObj.fixUrlPath(url)
        print 'schedule url now:', url
        header = {'Accept': 'application/json'}
        response = self.baseObj.deleteResponse(url, header=header, acceptCodes=[204])
        print 'response', response
        return response

    def disable(self, category, scheduleName):
        '''
        disables the schedule and returns the response from the request to
        the rest api.
        '''
        catEncode = urllib.quote(category)
        scheduleNameEncode = urllib.quote(scheduleName)
        url = self.schedules.baseObj.fixUrlPath(self.schedules.url)
        url = urlparse.urljoin(url, catEncode)
        url = self.schedules.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, scheduleNameEncode)
        url = self.schedules.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, 'enabled')
        body = {'value':'false'}
        header = {'Content-Type': 'application/x-www-form-urlencoded',
                  'Accept'      : 'application/json'}
        resp = self.baseObj.putResponse(url=url, data=body, header=header, detail='low')
        return resp


class Log(object):
    '''
    A interface to Logs that get generated for each job.
    '''

    def __init__(self, logs, logId):
        #  url = self.baseUrl + '/' + self.resturi + '/' + self.logDefWord + '/' + str(jobId) + \
        #  '/' + viewOrDownload + '?' + self.tokenId + '=' + self.token
        # http://fmeserver/fmerest/v2/transformations/jobs/id/42/log?accept=json&detail=low
        logId = str(logId)
        # logRequestType = 'download'  # options view|download
        self.url = urlparse.urljoin(logs.url, 'id')
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, logId)
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, 'log')
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.logs = logs
        self.response = None
        self.responseContent = None

    def getUrl(self):
        '''
        :return: The base url used by log rest api calls
        '''
        url = self.logs.baseObj.getURL(self.url, detail='high')
        return url

    def getLog(self):
        '''
        :return: retrieves the text contains in the log described by this object
        '''
        self.response = self.logs.baseObj.getResponse(self.url, returnType='raw', detail='high')
        self.responseContent = self.response.read()
        return self.responseContent

    def extractFromLog(self, startRegexStr, extractRegexStr, endRegexStr, srchStr):
        '''
        uses supplied regular expressions to extact information from a log
        :param startRegexStr: the regex that identifies the start of the text that we are looking
                              for
        :param endRegexStr: the regex that identifies the end a section of the log that contains
                            the text that is being searched for
        :param extractRegexStr: in between the start and end regex this parameter is applied to
                                extract the desired string
        :param srchStr: the string that is used to seach for the values.

        '''
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written            59
        startRegex = re.compile(startRegexStr, re.IGNORECASE)
        extractRegex = re.compile(extractRegexStr, re.IGNORECASE)
        endRegex = re.compile(endRegexStr, re.IGNORECASE)

        # pattern to retrieve is: (spaces trimmed)
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |QSOI_BC_REGIONS         59
        # where QSOI_BC_REGIONS is the feature and 59 is the records.
        # occurs after the line
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |       Features Written Summary
        # and before the line
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written  59
        retData = []
        start = False
        for line in self.responseContent.split('\n'):
            line = line.strip()
            if start:
                # print line
                # is it the end?
                if endRegex.match(line):
                    start = False
                elif extractRegex.match(line):
                    startPos = re.search(srchStr, line).end()
                    tmpList = re.split(r'\s+', line[startPos:])
                    fc = tmpList[0]
                    feats = tmpList[1]
                    retData.append([fc, feats])
            if startRegex.match(line):
                start = True
        return retData

    def getFeaturesWritten(self):
        '''
        used to extract the features written line from the log
        '''
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written    59
        StartRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+' + \
                        r'\.\d+\|STATS\s*\|\s*Features\s+Written\s+Summary\s*$'
        ExtractRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*' + \
                          r'\d+\.\d+\|STATS\s*\|\s*\w+(\.\w+)*\s+\d+$'
        EndRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+\.' + \
                    r'\d+\|STATS\s*\|\s*Total\s+Features\s+Written\s+\d+$'
        srchStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|' + \
                  r'\s*\d+\.\d+\|STATS\s*\|\s*'
        retData = self.extractFromLog(StartRegexStr, ExtractRegexStr, EndRegexStr, srchStr)
        return retData

    def getFeaturesRead(self):
        '''
        extracts the number of features read as described in the log and
        returns it
        '''
        # print self.responseContent
        StartRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|' + \
                        r'\s*\d+\.\d+\|STATS\s*\|\s*Features\s+Read\s+Summary\s*$'
        ExtractRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|' + \
                          r'\s*\d+\.\d+\|STATS\s*\|\s*\w+(\.\w+)*\s+\d+$'
        EndRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|' + \
                      r'\s*\d+\.\d+\|STATS\s*\|\s*Total\s+Features\s+Read\s+\d+$'
        srchStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+' + \
                  r'\.\d+\|STATS\s*\|\s*'
        retData = self.extractFromLog(StartRegexStr, ExtractRegexStr, EndRegexStr, srchStr)
        return retData


class Jobs(object):
    '''
    Class used to wrap FME Jobs, ie information about FMW's that
    have been run.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        # job types: # 'completed', 'running' or 'queued'.
        # http://fmeserver/fmerest/v2/transformations/jobs/completed?detail=low&limit=-1&offset=-1
        self.transformationsUrl = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.jobsDir, True)
        self.transformationsUrl = self.baseObj.fixUrlPath(self.transformationsUrl)
        self.url = urlparse.urljoin(self.transformationsUrl, 'jobs', True)
        self.url = self.baseObj.fixUrlPath(self.url)

        # when retrieving jobs from fme server, and the queue gets to the end of
        # of the job list it will return a null object. The null object won't trigger
        # the end of the loop.  This parameter sets the number of blank pages
        # to read before the loop is closed.
        self.jobNullPagesToEndLoop = 2
        self.jobNullPagesRead = 0

    def getJobs(self, statusType='completed', detail='low', limit=None, offset=None):
        '''
        Returns a list of job objects
        '''
        # returns a dictionary which is indexed by job id.
        # down the road can enhance this method to allow for time queries
        url = urlparse.urljoin(self.url, statusType, True)
        # print 'jobs url,', url

        # params = {}
        jobs = {}
        params = {}

        if limit:
            params['limit'] = str(limit)
            params['offset'] = 0
        if offset:
            params['offset'] = str(offset)
        print 'params:', params
        response = self.baseObj.getResponse(url, detail=detail, additionalParams=params)
        cnt = 0
        for job in response:
            jobs[job['id']] = job
            cnt += 1
        print 'cnt:', cnt
        if cnt == 0:
            self.jobNullPagesRead += 1
        return jobs

    def isEndOfPage(self):
        '''
        When retrieving jobs frequently the list of jobs is larger than
        an individual rest call can handle so they get broken up into
        pages.  This method is used to determine whether the end of
        a page has been reached.
        '''
        retVal = False
        if self.jobNullPagesRead >= self.jobNullPagesToEndLoop:
            retVal = True
        return retVal

    def getJob(self, jobId, detail='low'):
        '''
        Given a specific job id returns a job object that describes
        the job number supplied
        '''
        job = Job(self, jobId, detail)
        return job

    def submitJob(self, repoName, jobName, params=None, sync=False):
        '''
        Submits a job for transformation.  the parameter sync determines whether
        the job will be submitted syncronously or asynchronously The job to  run
        is defined by the two args sent to this method, repoName and jobName,
        which are described below.

        :param  repoName: The repository name that contains the
                          job that we want to submit for running to
                          fme server.
        :type repoName: string
        :param  jobName: The name of the workspace/FMW/Job that we
                         want to run.
        :type jobName: string
        :param  params: a dictionary who's keys contain the name
                        of a published parameter, and the value
                        is the value for that published parameter
                        example: {'paramName':'paramValue'}
        :type params: dict
        :param sync: a boolean indicating whether the job should be run
                     synchronously or asynchronously.  set true if you want to
                     run synchronously

        :returns: a dictionary containing a response object that
                  was returned by FME server.  The following is an
                  example of this object:

        {   u'id': 12249,
            u'numFeaturesOutput': 0,
            u'priority': 100,
            u'requesterHost': u'host',
            u'requesterResultPort': 55352,
            u'status': u'SUCCESS',
            u'statusMessage': u'Translation Successful',
            u'timeFinished': u'2015-06-25T09:30:25',
            u'timeRequested': u'2015-06-25T09:30:23',
            u'timeStarted': u'2015-06-25T09:30:23'}

        :rtype: dict
        '''
        url = urlparse.urljoin(self.transformationsUrl, 'commands')
        url = self.baseObj.fixUrlPath(url)
        if sync:
            url = urlparse.urljoin(url, 'transact')
        else:
            url = urlparse.urljoin(url, 'submit')
        url = self.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, repoName)
        url = self.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, jobName)
        print 'url', url
        paramsStruct = []
        body = {}
        if params:
            for paramName in params.keys():
                singleParm = {'name': paramName,
                              'value': params[paramName]}
                paramsStruct.append(singleParm)
            body['publishedParameters'] = paramsStruct
        body['FMEDirectives'] = {}
        body['subsection'] = "REST_SERVICE"
        body['TMDirectives'] = {'priority': 100}

        print 'body:-----'
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(body)

        body = json.dumps(body)
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}

        response = self.baseObj.postResponse(url, data=body, header=header)
        return response

    def submitJobSync(self, repoName, jobName, params=None):
        '''
        Used to run a fmw / repository combination.
        '''
        response = self.submitJob(repoName, jobName, params, sync=True)
        return response

    def submitJobASync(self, repoName, jobName, params=None):
        '''
        Run a job / repo name combination asyncronously.  Job gets
        added to a queue, and returns not waiting for the job to
        complete.
        '''
        response = self.submitJob(repoName, jobName, params, sync=False)
        return response


class Job(object):

    '''
    used to describe individual jobs.
    '''

    def __init__(self, jobs, jobId, detail='low'):
        self.logger = logging.getLogger(__name__)
        self.jobId = jobId
        # http://fmeserver/fmerest/v2/transformations/jobs/id/9021?accept=json&detail=high
        self.url = urlparse.urljoin(jobs.url, 'id')
        self.url = jobs.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, str(jobId))
        self.url = jobs.baseObj.fixUrlPath(self.url)
        # print 'job url', self.url
        self.baseObj = jobs.baseObj
        # self.url = urlparse.urljoin(jobs.url, str(jobId) + jobs.baseObj.dataType)
        response = jobs.baseObj.getResponse(self.url, detail=detail)
        self.response = response
        # print 'response', response

    def getJob(self):
        '''
        Retrieves the response for the job described by this object
        '''
        return self.response

    def getJobLog(self):
        '''
        Retrieves the log for the job with this id.
        '''
        logs = Logs(self.baseObj)
        log = logs.getLog(self.jobId)
        return log

    def getJobStatus(self):
        returnValue = None
        if 'result' in self.response:
            if 'status' in self.response['result']:
                returnValue = self.response['result']['status']
        elif 'status' in self.response:
            returnValue = self.response['status']
        else:
            msg = "cannot find a status in the response object!, searched for " + \
                  "self.response['result']['status'] and self.response['status'] " + \
                  'neither of which exist.  Full reponse object is: {0}'
            msg = msg.format(self.response)
            self.logger.error(msg)
            raise ValueError, msg
        return returnValue


class Repository(object):
    '''
    Repository class contains functionality for retrieving the
    various FME Server repositories.  Various methods in this
    class will return Workspace objects allowing you to identify
    fmw's in a repository as well as get information about FMW's
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.repos = []

        self.url = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.repositoryDir, True)

    def fetchRepositories(self):
        '''
        Queries the rest api for a list of the repositories on an
        fme server instance.  Populates the object property:
        self.repos with a dictionary with the following structure:

        self.repos[<repository name>] = { 'description': <description of repo>,
                                          'name': <same value as key, ie repository name }

        '''
        response = self.baseObj.getResponse(self.url, detail='high')
        self.repos = {}
        for repo in response:
            self.repos[repo['name']] = {'description' : repo['description'],
                                        'name': repo['name']}

    def getRepositoryNames(self):
        '''
        Checks to see if the self.repos property has been populated.  If
        it has it will extract a list of the repository names and return it.

        If the data structure is not populated it will call fetchRepositories
        method to populate the structure and then return a list of the various
        repository names.

        :return: a list of strings describing the name of the repositories on
                 the fme server instance
        :rtype: list
        '''
        if not self.repos:
            self.fetchRepositories()
        names = self.repos.keys()
        return names

    def getWorkspaces(self, repoName):
        '''
        Receives a repository name.  Returns a Workspaces object for that
        repository.  The Workspaces object can be used to query the FMW's in
        the repository.

        :param repoName: Name of the repository that the workspace object that will
                     be returned should describe.
        :type repoName: string

        :return: A workspaces object that can be used to describe the contents
                 of the repository that was sent as an arg to this method.
        :rtype: Workspaces
        '''
        repoNames = self.getRepositoryNames()
        # print 'repoNames', repoNames
        if repoName not in  repoNames:
            raise InvalidRepositoryNameException, (repoName, self.url)
        wrkSpace = Workspaces(self, self.repos[repoName])
        return wrkSpace

    def copy2Repository(self, repoName, fmwPath):
        '''
        This method can be used to copy a FMW to a specific repository.  Use
        this method for a net new fmw, ie the fmw does not already exist in
        the repository.  Use the method updateRepository if an older version of
        the fmw already exists in the repository.

        :param repoName: The name of the repository that you want to copy
                         the fmw to.
        :type repoName: string
        :param fmwPath: the file path to the fmw that you wish to upload to
                        the specified repository.
        :type fmwPath: string(path)

        '''
        # url example
        # http://host/fmerest/v2/repositories/Samples/items?accept=json&detail=high
        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urlparse.urljoin(itemUrl, repoName)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urlparse.urljoin(itemUrl, 'items')
        baseName = os.path.basename(fmwPath)
        headers = {'Content-Disposition': 'attachment; filename="' + str(baseName) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        dataPayload = open(fmwPath, 'rb')
        self.baseObj.postResponseFormData(itemUrl, header=headers, detail='high', data=dataPayload)
        dataPayload.close()

    def updateRepository(self, repoName, fmwPath):
        '''
        Use this method to update an fmw that has already been uploaded to
        fme server.
        :param repoName: The name of the repository that you want to update
                         with a new version of an fmw.
        :type repoName: string
        :param fmwPath: the file path to the fmw that you wish to use to update the
                        the specified repository.
        :type fmwPath: string(path)
        '''
        justFMW = os.path.basename(fmwPath)
        # itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urlparse.urljoin(itemUrl, repoName)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urlparse.urljoin(itemUrl, 'items')
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urlparse.urljoin(itemUrl, justFMW)
        print 'itemUrl', itemUrl
        headers = {'Content-Disposition': 'attachment; filename="' + str(fmwPath) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        dataPayload = open(fmwPath, 'rb')
        params = {'item': justFMW,
                  'repository': repoName,
                  'accept': 'json',
                  'detail': 'low'}
        response = self.baseObj.putResponse(itemUrl, header=headers, detail='high',
                                            data=dataPayload, params=params)
        return response

    def exists(self, repoName):
        '''
        Used to determine if a specific fmw exists in fme server.  The repoName
        parameter passed to this method is case sensitive.  'REPO' and 'repo' would
        be considered two different repositories.

        :return: a boolean value indicating if the repository exists or not
        :rtype: boolean
        '''
        retVal = False
        repoNames = self.getRepositoryNames()
        for name in repoNames:
            if name == repoName:
                retVal = True
                break
        return retVal

    def create(self, repName, descr):
        '''
        create a repository with the name, and description parameter
        provided as arguements

        :param repName: The name of the repository that is to be created
        :type repName: string
        :param descr: a string describing the repository that is to be created
        :type descr: string


        '''
        # example url:
        # http://host.dmz/fmerest/v2/repositories?accept=json&detail=high
        response = None
        if not self.exists(repName):
            # body:
            # description=This%20is%20part%20of%20the%20REST%20example%20suite&name=MyTest

            # header:
            # Content-Type: application/x-www-form-urlencoded
            # Accept: application/json
            dataPayload = {'description': descr,
                           'name':repName}
            print 'url:', self.url
            response = self.baseObj.postResponseFormData(self.url, detail='high', data=dataPayload)
        return response


class Workspaces(object):
    '''
    Workspaces describe individual fmw scripts that reside in an fme server
    repository.
    '''

    def __init__(self, repos, repo):
        self.repos = repos
        self.repo = repo
        self.repoName = repo['name']
        self.baseObj = self.repos.baseObj
        self.url = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.repositoryDir)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, self.repoName)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urlparse.urljoin(self.url, 'items')
        self.workspaces = {}

    def fetchWorkspaces(self):
        '''
        Queries fme server for the workspaces in the repository that was
        specified when this object was created.  (in property repoName)
        and populates the object property self.workspaces with a dictionary
        who's key is the name of the workspace and the value is the full
        data structure returned by the rest api.
        '''
        # http://host/fmerest/repositories/__.json
        params = {'type': 'WORKSPACE'}
        response = self.baseObj.getResponse(self.url, detail='high', additionalParams=params)
        # workspaces = response['serviceResponse']['repository']['workspaces']['workspace']
        self.workspaces = {}
        for workspace in response:
            self.workspaces[workspace['name']] = workspace

    def getWorkspaceNames(self):
        '''
        gets a list of the workspace names (fmw scripts) that are
        inside the repo.
        '''
        if not self.workspaces:
            self.fetchWorkspaces()
        workSpaceNames = self.workspaces.keys()
        return workSpaceNames

    def getWorkspaces(self):
        '''
        Returns a dictionary of workspaces, each key contains the name of the workspace
        and the contents include these properties:
          - description: a description of the workspace
          - lastSaveDate:
          - name: the name of the fmw including the .fmw suffix
          - title: frequently the same as the fmw name but without the suffix
          - type: the type of workspace, most often "WORKSPACE" see the api docs
            for more info
        '''
        # returns the data structure returned by the
        # REST query.
        if not self.workspaces:
            self.fetchWorkspaces()
        return self.workspaces

    def getWorkspaceInfo(self, wrkspcName, detail='low'):
        '''
        :param wrkspcName: Name of the workspace that you want to get a detailed description
        :param detail: Controls how much detail you want fme server to return.

        http://fmeserver/fmerest/v2/apidoc/#!/repositories/featuretypes_get_14
        '''
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        header = {'Accept': r'application/json'}
        response = self.baseObj.getResponse(url, detail=detail, returnType='json', header=header)
        return response

    def getWorkspaceDatasets(self, wrkspcName, srcOrDest='source'):
        '''
        Queries the rest end point for the source / destination data sets
        used in the fmw.

        :param wrkspcName: name of the workspace that is being queried
        :param srcOrDest: either 'source' or 'destination' to indicate
                          what dataset types you want retrieved.
        '''
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        url = self.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, 'datasets')
        url = self.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, srcOrDest)
        print 'url:', url
        header = {'Accept': r'application/json'}
        response = self.baseObj.getResponse(url, detail='high', returnType='json', header=header)
        return response

    def exists(self, wrkSpaceName):
        '''
        :param wrkSpaceName: Name of the workspace that is to be downloaded
        tests to see if a workspace with a given name exists
        '''
        workSpaceNames = self.getWorkspaceNames()
        retVal = False
        for curWorkspc in workSpaceNames:
            if curWorkspc.lower() == wrkSpaceName.lower():
                retVal = True
                break
        return retVal

    def registerWithJobSubmitter(self, wrkspcName):
        '''
        registers the workspace with the job submitter service.  This is necessary to
        to be able to run the workspace.  Without this registration you will not be
        able to run the job from fme server.
        '''
        # url to send
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        url = self.baseObj.fixUrlPath(url)
        url = urlparse.urljoin(url, 'services')
        # print 'url:', url
        datacont = 'services=fmejobsubmitter'
        header = {'Content-Type': 'application/x-www-form-urlencoded', \
                  'Accept': 'application/json'}
        response = self.baseObj.postResponseFormData(url, detail='high', \
                                                     data=datacont, header=header)
        return response

    def getPublishedParams(self, wrkspcName, reformat4JobReRun=False):
        '''
        Retrieves the published parameters for the given workspace.

        reformat4JobReRun - if this parameter is set to true then will reformat
                            the published parameters so they can used un modified
                            to re-run a fmw.

        The returned structure is a list of dictionaries.  Each dictionary
        describes a single published parameter.  The following is an
        example of one of these dictionaries:
            {   u'defaultValue': u'evpr91',
                u'description': u'Source Oracle Instance:',
                u'model': u'string',
                u'name': u'SRC_ORA_INSTANCE',
                u'type': u'TEXT'}

        and anther...
            {   u'defaultValue': [u'DLV'],
                u'description': u'Destination Database Keyword (DLV|TST|PRD):',
                u'featuregrouping': False,
                u'listOptions': [   {   u'caption': u'DLV', u'value': u'DLV'},
                                    {   u'caption': u'TST', u'value': u'TST'},
                                    {   u'caption': u'PRD', u'value': u'PRD'}],
                u'model': u'list',
                u'name': u'DEST_DB_ENV_KEY',
                u'type': u'STRING_OR_CHOICE'}]
.
        :param  wrkspcName: The name of the workspace who's published parameters
                            are to be retrieved.
        :type wrkspcName: str

        :returns: a list of dictionaries describing the published parameters
                  of the specified workspace.  Each dictionary describes a different
                  published parameter.  The datamodel of that dictionary is described
                  above in part but in more detail in the fme server rest api.
        :rtype: list of dictionaries
        '''
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        response = self.baseObj.getResponse(url, detail='high')
        params = response['parameters']
        if reformat4JobReRun:
#             should look like this:
#             {
#               "name": "MAXY",
#               "value": "42"
#             }, ...
            reformatParams = {}
            for param in params:
                reformatParams[param['name']] = param['defaultValue']
                # paramDict = {}
                # paramDict['name'] = param['name']
                # paramDict['value'] = param['defaultValue']
                # reformatParams.append(paramDict)
            params = reformatParams
        return params

    def downloadWorkspace(self, wrkspcName, destination):
        '''
        :param wrkspcName: name of the workspace that you want to download
        :param destination: destination path for where you want to download the
                            workspace to.
        Downloads the given fmw to the destination path
        '''
        # http://fmeserver/fmerest/v2/repositories/Samples/items/austinDownload.fmw?detail=low
        # print 'baseurl', self.url
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        # print 'wrkspc url:', url
        header = {'Accept': r'application/octet-stream'}
        response = self.baseObj.getResponse(url, detail='high', returnType='raw', header=header)
        fh = open(destination, 'w')
        for reponseLine in response:
            # reponseLine = reponseLine.strip()
            fh.write(reponseLine)
        fh.close()

    def deleteWorkspace(self, wrkspcName):
        '''
        deletes a workspace with the workspace name
        '''
        url = self.baseObj.fixUrlPath(self.url)
        url = urlparse.urljoin(url, wrkspcName)
        print 'url', url
        print 'wrkspcName', wrkspcName
        header = {'Accept': 'application/json'}
        resp = self.baseObj.deleteResponse(url, header=header, acceptCodes=[204])
        return resp


class Resources(object):
    '''
    interface to fme server 'Resource' objects. Resources are used mostly
    for loading specific python dependencies.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.rootDir = 'connections'
        self.fileSysDir = 'filesys'
        self.url = urlparse.urljoin(self.baseObj.restUrl, self.baseObj.resourcesDir, True)

    def getRootDirContents(self):
        '''
        :return: Returns the contents of the current resource directory
        '''
        # http://fmeserver/fmerest/v2/resources/connections?detail=low
        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urlparse.urljoin(itemUrl, self.rootDir)
        response = self.baseObj.getResponse(itemUrl)
        return response

    def getDirectory(self, dirType, dirList):
        '''
        Gets the contents of the directory described by dirType and dirList
        '''
        # http://fmeserver/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/filesys/foo/bar?depth=1&detail=low
        # dirTypes:
        #   FME_SHAREDRESOURCE_BACKUP
        #   FME_SHAREDRESOURCE_DATA
        #   FME_SHAREDRESOURCE_ENGINE
        #   FME_SHAREDRESOURCE_LOG
        #   FME_SHAREDRESOURCE_TEMP
        itemUrl = self.__calcURL(dirType, dirList)
        print 'url is:', itemUrl
        addparams = {'depth': 10}
        dontErrorStatusCodes = [404]
        response = self.baseObj.getResponse(itemUrl, additionalParams=addparams,
                                            dontErrorStatusCodes=dontErrorStatusCodes)
        return response

    def exists(self, dirType, dirList):
        '''
        :param dirType: a string describing whether a directory type exists
        :param dirList: a list that describes a directory path.
        :return: Returns a boolean value indicating whether the resource described
                 exists or not.
        '''
        response = self.getDirectory(dirType, dirList)
        retVal = True
        if response.has_key('message'):
            if "does not exist" in response['message']:
                retVal = False
        return retVal

    def __calcURL(self, dirType, dirList):
        '''
        Used to calculate the url for given list of directories contained in
        dirList
        '''
        if not isinstance(dirList, list):
            msg = 'you specified a value of {0} which has a type of {1} for ' + \
                  'the "dirList" parameter.  This parameter should be a list ' + \
                  'describing the directory hierarchy you are trying to get ' + \
                  'information about'
            msg = msg.format(dirList, type(dirList))
            raise ValueError, msg
        rootDirs = self.getRootDirContents()
        dirType = dirType.upper().strip()
        valid = False
        validTypes = []
        for rootDir in rootDirs:
            if rootDir['name'].upper().strip() == dirType:
                valid = True
                break
            validTypes.append(rootDir['name'])
        if not valid:
            msg = 'you supplied a directory type of {0} which is ' + \
                  'an invalid type. Valid types include {1}'
            msg = msg.format(dirType, validTypes)
            raise ValueError, msg

        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urlparse.urljoin(itemUrl, self.rootDir)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urlparse.urljoin(itemUrl, dirType)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urlparse.urljoin(itemUrl, self.fileSysDir)
        for curDir in dirList:
            itemUrl = self.baseObj.fixUrlPath(itemUrl)
            itemUrl = urlparse.urljoin(itemUrl, curDir)
        return itemUrl

    def createDirectory(self, dirType, dirList, dir2Create):
        '''
        Request URL
        http://fmeserver/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/filesys/foo/bar?detail=low

        Request Headers
        Content-Type: application/x-www-form-urlencoded
        Accept: application/json

        Request Body
        directoryname=testdir&type=DIR
        '''

        # Request Headers
        # Content-Type: application/x-www-form-urlencoded
        # Accept: application/json

        # body: directoryname=testdir&type=DIR
        itemUrl = self.__calcURL(dirType, dirList)
        data = {'directoryname': dir2Create,
                'type': 'DIR'}
        response = self.baseObj.postResponseFormData(itemUrl, data=data)
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(response)
        return response

    def deleteDirectory(self, dirType, dirList):
        '''
        Used to delete a directory or a file described by the parameters
        sent.
        '''
        itemUrl = self.__calcURL(dirType, dirList)
        header = {'Accept': 'application/json'}
        self.baseObj.deleteResponse(itemUrl, header=header, acceptCodes=[204])

    def copyFile(self, dirType, dirList, file2Upload, overwrite=False, createDirectories=False):
        '''
        copies a file from the given path in file2Upload to fme server.  Destination
        in fme server described by dirType and dirList
        '''
        itemUrl = self.__calcURL(dirType, dirList)
        params = {'createDirectories': str(createDirectories).lower(),
                  'overwrite': str(overwrite).lower()}

        # http://fmeserver/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/...
        # filesys/foo/bar?createDirectories=false&detail=low&overwrite=false
        baseName = os.path.basename(file2Upload)
        # baseName = urllib.quote(baseName)
        baseName = baseName.decode('utf8')
        print 'baseName', baseName
        headers = {'Content-Disposition': 'attachment; filename="' + str(baseName) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        # Content-Disposition: attachment; filename="uploadtest.txt"
        # Accept: application/json
        dataPayload = open(file2Upload, 'rb')
        print 'itemUrl', itemUrl
        response = self.baseObj.postResponseFormData(itemUrl, header=headers, data=dataPayload,
                                                     params=params)
        dataPayload.close()
        return response

    def getResourceInfo(self, dirType, dirList):
        '''
        Gets the resource info object for the given resource and
        returns it
        '''
        # /resources/connections/< resource >/filesys/< path >
        itemUrl = self.__calcURL(dirType, dirList)
        print 'url:', itemUrl
        response = self.baseObj.getResponse(itemUrl)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(response)
        return response


class InvalidRepositoryNameException(Exception):
    '''
    define a custom exception for when a repository name is invalid.
    '''

    def __init__(self, repoName, serverUrl):
        self.message = "[ERROR] the repository provided ('{0}') does not match up with a " + \
                       "repository at the url {1}\n"

        self.repoName = repoName
        self.serverUrl = serverUrl
        message = self.message.format(self.repoName, self.serverUrl)
        super(InvalidRepositoryNameException, self).__init__(message)

    def __str__(self):
        msg = self.message.format(self.repoName, self.serverUrl)
        return msg
