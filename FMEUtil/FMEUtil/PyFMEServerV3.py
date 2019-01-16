'''
About
=========
:synopsis:     A THIRD attempt at an FME Server Rest API python wrapper,
               This attempt will use FMEServers V3 Rest api, while
               trying to maintain backward compatibility with the
               python api defined by the original module
:moduleauthor: Kevin Netherton
:date:         9-30-2017
:description:  Previous attempts at this library are messy!
               (FMEServerInteraction.py) This is a third run at an FME
               server library.  This is the base class and attempts to
               remain decoupled from other code like PMP access modules
               for example.

               This attempt tries to mimic the fme rest api hierarchy.
               Scripts always start with an FMEServer object.

'''
import json
import logging
import os.path
import pprint
import re
import urllib
from urllib.parse import urlparse

import requests

# pylint: disable=invalid-name


class JSONConstants(object):
    '''
    various constants used by the module
    '''
    items = 'items'
    description = 'description'
    name = 'name'
    defaultValue = 'defaultValue'
    parameters = 'parameters'
    id = 'id'
    category = 'category'
    enabled = 'enabled'
    connections = 'connections'
    filesys = 'filesys'


class FMERestBase(object):
    '''
    This class is not called directly.  It contains functionality to perform
    the actual rest call interaction.  Other modules will construct the end
    points, the parameters, data to include, headers etc, then will call one
    of these methods to perform the actual request to the rest api.
    '''

    def __init__(self, baseurl, token):
        self.logger = logging.getLogger(__name__)
        self.baseurl = baseurl
        # self.restUrl = self.baseurl + '/' +  'fmerest'
        restDir = 'fmerest/v3/'
        self.restUrl = urllib.parse.urljoin(self.baseurl, restDir)
        self.token = token
        self.repositoryDir = 'repositories'
        self.scheduleDir = 'schedules'
        self.jobsDir = 'transformations'
        self.resourcesDir = 'resources'
        self.logsDir = 'logs'
        self.dataType = 'json'
        self.detail = 'low'
        self.repos = []
        self.payloadDict = {'fmetoken': self.token,
                            'accept': self.dataType}
        self.restUrl = self.fixUrlPath(self.restUrl)
        self.tokenHeaderValue = 'fmetoken token={0}'.format(self.token)

    def fixUrlPath(self, url):
        '''
        Receives a url path and ensures that it ends with a '/' character
        This is used when constructing urls to make sure the path can have
        another directory added to it using the urljoin method.
        '''
        if url[len(url) - 1] != '/':
            url = url + '/'
        self.logger.debug("url: %s", url)
        return url

    def preUrl(self, url, returnType, additionalParams=''):
        '''
        All of the interactions with fme server require the token to be
        passed along as part of the request payload.  This method merges
        these required parameters with any other existing parameters.

        when there is duplication of parameters between default values
        and those passed to this method in the parameter additionalParams
        the additionalParams will take precedence
        '''
        payloadDict = self.payloadDict.copy()
        if additionalParams:
            payloadDict.update(additionalParams)
        if 'accept' not in payloadDict:
            payloadDict['accept'] = returnType
        if payloadDict['accept'] != returnType:
            payloadDict['accept'] = returnType
        return payloadDict

    def getResponse(self, url, returnType='json', additionalParams=None,
                    header=None, body=None, dontErrorStatusCodes=None,
                    returnRequestObj=False):
        '''
        generic method for handling get requests.
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
        payloadDict = self.preUrl(url, returnType, additionalParams)

        if returnType == 'raw':
            if 'accept' in payloadDict:
                del payloadDict['accept']
            r = requests.get(url, params=payloadDict, stream=True,
                             headers=header, data=body)
            self.logger.debug("request is made with 'raw'")
        else:
            r = requests.get(url, params=payloadDict, headers=header,
                             data=body)
        if r.status_code != 200 and r.status_code not in dontErrorStatusCodes:
            msg = 'Request did not succeed!  Status Code is: {0} and ' + \
                  'returned body is {1}'
            msg = msg.format(r.status_code, r.text)
            raise ValueError(msg)
        if returnType == 'json':
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        if returnRequestObj:
            response = r
        return response

    def deleteResponse(self, url, returnType='json', data='', header=None,
                       acceptCodes=None):
        '''
        generic method for handling delete requests.
        '''
        if header is None:
            header = {}
        if acceptCodes is None:
            acceptCodes = []

        payloadDict = self.preUrl(url, returnType)
        self.logger.debug("payloadDict: %s", payloadDict)
        if not header:
            # header = { 'Content-Type': 'application/x-www-form-urlencoded',
            #           'Accept': 'application/json',
            #           'Authorization':  tokenValue}
            header = {'Accept': 'application/json',
                      'Authorization':  self.tokenHeaderValue}
        elif 'Authorization' not in header:
            header['Authorization'] = self.tokenHeaderValue
        r = requests.delete(url, data=data, headers=header)

        AcceptableStatusCodes = [200, 201, 204]
        if acceptCodes:
            AcceptableStatusCodes = AcceptableStatusCodes + acceptCodes
        if r.status_code not in AcceptableStatusCodes:
            msg = 'Received the error code: {0} when trying to ' + \
                  'request the url with delete method {1} encoded url is {2}'
            msg = msg.format(r.status_code, url, r.url)
            self.logger.debug("rtext: %s", r.text)
            self.logger.debug("result: %s", r)
            raise ValueError(msg)
        return r

    def putResponse(self, url, returnType='json', data='', header=None,
                    params=None):
        '''
        generic method for put requests
        '''
        if header is None:
            header = {}
        if params is None:
            params = {}

        defaultHeader = {'Content-Type': 'application/octet-stream',
                         'Accept': 'application/json'}
        if not header:
            header = defaultHeader
        else:
            if 'Authorization' not in header:
                header['Authorization'] = self.tokenHeaderValue
        params = self.preUrl(url, returnType, params)
        self.logger.debug("url: %s", url)
        self.logger.debug("data: %s", data)
        r = requests.put(url=url, headers=header, data=data)
        response = None
        if r.status_code not in [200, 204]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'put the job {1}'
            msg = msg.format(r.status_code, url)
            self.logger.debug("r.text: %s", r.text)
            self.logger.debug("result: %s", r)
            raise ValueError(msg)
        if returnType == 'json':
            if r.text:
                response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def postResponseFormData(self, url, returnType='json', data='',
                             header=None, params=None):
        '''
        generic method for post requests, that use form data, could
        probably merge this with the method postResponse.  This method used
        to be required for older version of the fme api.
        '''
        if header is None:
            header = {}
        if params is None:
            params = {}
        if not header:
            header = {'Content-Type': 'application/octet-stream',
                      'Accept': 'application/json',
                      'Authorization':  self.tokenHeaderValue}
        else:
            # make sure the header has the authorization
            if 'Authorization' not in header:
                header['Authorization'] = self.tokenHeaderValue
        if params:
            r = requests.post(url, data=data, headers=header, params=params)
            self.logger.debug("url: %s", r.url)
        else:
            r = requests.post(url, data=data, headers=header)
        if r.status_code not in [200, 201]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'schedule the job {1}'
            msg = msg.format(r.status_code, url)
            raise ValueError(msg)
        response = None
        if returnType == 'json':
            self.logger.debug('rtext: %s', r.text)
            response = r.json()
        elif returnType == 'text':
            response = r.text()
        elif returnType == 'raw':
            response = r.raw
        return response

    def postResponse(self, url, returnType='json', data=None,
                     header=None, params=None):
        '''
        Generic post request.
        '''
        if data is None:
            data = {}
        if header is None:
            header = {}
        if params is None:
            params = {}

        payloadDict = self.preUrl(url, returnType, additionalParams=params)
        if isinstance(data, dict):
        # if type(data) is dict:
            data = json.dumps(data)
            self.logger.debug("data: %s", data)
        if header:
            # 'Authorization':  self.tokenHeaderValue
            if 'Authorization' not in header:
                header['Authorization'] = self.tokenHeaderValue
        else:
            header = {'Authorization':  self.tokenHeaderValue,
                      'Accept': 'application/json',
                      'Content-Type': 'application/json'}

        r = requests.post(url, data=data, headers=header, params=payloadDict)
        if r.status_code not in [200, 201, 202]:
            msg = 'Received the error code: {0} when trying to ' + \
                  'schedule the job {1} {2}'
            msg = msg.format(r.status_code, url, r.text)
            raise ValueError(msg)
        response = None
        if r.text:
            if returnType == 'json':
                response = r.json()
            elif returnType == 'text':
                response = r.text()
            elif returnType == 'raw':
                response = r.raw
        return response

    def getURL(self, url, returnType='json', additionalParams=None):
        '''
        prepares a request and returns the url that will be used for the
        request with the parameter string
        '''
        if additionalParams is None:
            additionalParams = {}
        payloadDict = self.preUrl(url, returnType, additionalParams)
        r = requests.Request('GET', url, data=payloadDict)
        # payloadDict['testparam'] =  'sal#mon'
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
        :param baseurl: should be just: http://servername.  Don't include any
               paths, those are handed by the module
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


class Logs(object):
    '''
    Used to retrieve Log objects.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        # example of v1 url to a log
        # V2 logs are moved under the jobs.
        # category for jobs: completed | running | queued
        self.url = urllib.parse.urljoin(self.baseObj.restUrl,
                                        self.baseObj.jobsDir, True)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, 'jobs', True)
        self.url = self.baseObj.fixUrlPath(self.url)

    def getLog(self, logId):
        '''
        :return: a Log object
        '''
        log = Log(self, logId)
        return log


class Schedules(object):
    '''
    used for automated schedule management
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.logger = logging.getLogger(__name__)
        self.schedsList = None
        self.const = JSONConstants()
        self.url = urllib.parse.urljoin(self.baseObj.restUrl,
                                        self.baseObj.scheduleDir, True)

    def getSchedule(self):
        '''
        Returns a schedule object
        '''
        sched = Schedule(self)
        return sched

    def getSchedules(self):
        '''
        returns a list of schedules.
        '''
        response = self.baseObj.getResponse(self.url)
        retList = []
        for i in response[self.const.items]:
            retList.append(i)
        return retList

    def exists(self, schedName, category=None):
        '''
        :param schedName: the name of the schedule who's existence you wish
                          to determine
        :param category: the category (optional).  If the category is specified
                         will look for a schedule / category combination
        :return: boolean value indicating whether the schdule name in question
                 exists or not.
        '''
        schedsList = self.getSchedules()
        # cached for use by subsequent processes where applicable
        self.schedsList = schedsList
        retVal = False
        for sched in schedsList:
            self.logger.debug("sched: %s", sched)
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

    def isEnabled(self, schedName, category=None):
        '''
        :param schedName: the name of the schedule that you want to determine
                          whether it is enabled or not.
        :param category: the category (optional) when provided searches for a
                         schedule / category combination.
        :return: None, when no schedule can be found, false when its found but
                not enabled, true when enabled.
        '''
        if not self.exists(schedName, category):
            msg = 'Cannot determine if the schedule is enabled or not as there is no ' + \
                  'schedule with the name {0}'
            msg = msg.format(schedName)
            if category:
                msg = msg + ' and the category {0}'
                msg = msg.format(category)
            raise ValueError(msg)
        # exists should have cached the schedules list so can now
        # reuse to get the parameters
        retVal = None
        for sched in self.schedsList:
            if sched[self.const.name] == schedName:
                if category:
                    if sched[self.const.category] == category:
                        retVal = sched[self.const.enabled]
                        break
                else:
                    retVal = sched[self.const.enabled]
                    break
        return retVal


class Schedule(object):
    '''
    Used for managing individual schedules.

    '''

    def __init__(self, Schedules):
        self.baseObj = Schedules.baseObj
        self.schedules = Schedules
        self.const = JSONConstants()
        self.logger = logging.getLogger(__name__)

    def addSchedule(self, scheduleDescription):
        '''
        This method will receive a schedule description object.  The
        Structure / properties of a schedule description object are
        defined with the FME Server rest api.

        The following object is an example of a schedule description:
            {'category': 'extra terrestrials of bc',
             'recurrence': 'cron',
             'begin': '2012-05-31T02:30:00',
             'name': 'special_secret_replication_script.fmw',
             'repository': 'GuyLaFleur',
             'request':
                 {'publishedParameters':
                     {'name': 'Dest_Server',
                     'value': 'server.bcgov'}
                 },
             'enabled': True,
             'cron': '0 30 2 * * 2,3,4,5,6',
             'workspace': 'special_secret_replication_script.fmw'}


        :param  scheduleDescription: schedule description object as defined by
                                     the fme server rest api.
        :type scheduleDescription: dict
        '''
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}
        response = self.baseObj.postResponse(
            self.schedules.url, data=scheduleDescription, header=header)
        self.logger.debug('response %s', response)

    def delete(self, scheduleName, category):
        '''
        :param scheduleName: the schedule that you want to delete.
        :param category: the category of the schedule that you want to delete
                         (required)
        :return: response object
        '''
        url = self.schedules.baseObj.fixUrlPath(self.schedules.url)
        url = urllib.parse.urljoin(url, category)
        url = self.schedules.baseObj.fixUrlPath(url)
        url = urllib.parse.urljoin(url, scheduleName)
        url = self.schedules.baseObj.fixUrlPath(url)
        self.logger.debug("schedule url now: %s", url)
        header = {'Accept': 'application/json'}
        response = self.baseObj.deleteResponse(url, header=header,
                                               acceptCodes=[204])
        self.logger.debug("response is: %s", response)
        return response

    def updateParameters(self, scheduleName, category, newParams):
        '''
        used to update an existing parameter.  Quick fix to support
        need to be able to automate update of kirk schedules.

        :param scheduleName: Name of the schedule that is to be updated
        :type scheduleName: str
        :param category: Name of the category that is to be updated
        :type category: str
        :param newParams: a dictionary where the key is the parameter name
                          and the value is the parameter value.
        :type newParams: dict
        '''
        # makeing the keys all lower case.
        paramsLowerCase = {}
        for k, v in newParams.iteritems():
            paramsLowerCase[k.lower()] = v

        sched2Use = self.__verifyScheduleCategory(scheduleName, category)
        url = self.__getScheduleCategoryUrl(scheduleName, category)
        # update the params defined in sched2Use
        pubParams = sched2Use['request']['publishedParameters']
        paramCnt = 0
        for param in pubParams:
            paramValue = param['value']
            paramName = param['name']
            # now iterate through the list of new params
            if paramName.lower() in paramsLowerCase:
                pubParams[paramCnt]['value'] = \
                    paramsLowerCase[paramName.lower()]
                msg = 'updated {0} from {1} to {2}'.format(
                    paramName, paramValue, paramsLowerCase[paramName.lower()])
                self.logger.info(msg)
            paramCnt += 1
        sched2Use['request']['publishedParameters'] = pubParams
        body = sched2Use
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}
        bodyStr = json.dumps(body)
        resp = self.baseObj.putResponse(url=url, data=bodyStr,
                                        header=header)
        return resp

    def __getScheduleCategoryUrl(self, scheduleName, category):
        catEncode = urllib.parse.quote(category)
        scheduleNameEncode = urllib.parse.quote(scheduleName)
        url = self.schedules.baseObj.fixUrlPath(self.schedules.url)
        url = urllib.parse.urljoin(url, catEncode)
        url = self.schedules.baseObj.fixUrlPath(url)
        url = urllib.parse.urljoin(url, scheduleNameEncode)
        return url

    def __verifyScheduleCategory(self, scheduleName, category):
        '''
        checks to make sure that a given schedule and category actually
        exist.  Will also return the data object that is currently associated
        with a schedule / category.

        :param scheduleName: name of the schedule to verify
        :type scheduleName: str
        :param category: name of the category to verify
        :type category: str

        :return: the data associated with the schedule and category provided
                 as arguments
        '''
        if not self.schedules.exists(scheduleName, category):
            msg = 'Cannot enable/disable the schedule: {0} in the category {1} ' + \
                  'as there is no schedule with this name and category'
            msg = msg.format(scheduleName, category)
            raise ValueError(msg)
        # now we have the schedule list in self.schedules.schedsList
        sched2Use = None
        for sched in self.schedules.schedsList:
            if scheduleName == sched[self.const.name]:
                if category == sched[self.const.category]:
                    sched2Use = sched
                    break
        if not sched2Use:
            msg = "Cannot enable/disable the schedule {0} in the category" + \
                  " {1} as I am unable to find a schedule that matches " + \
                  "this combination"
            msg = msg.format(scheduleName, category)
            raise ValueError(msg)
        return sched2Use

    def __setEnabledFlag(self, scheduleName, category, enabledFlag):
        sched2Use = self.__verifyScheduleCategory(scheduleName, category)
        url = self.__getScheduleCategoryUrl(scheduleName, category)

        validStrings = ['true', 'false']
        if isinstance(enabledFlag, bool):
            if enabledFlag:
                enabledFlag = 'true'
            else:
                enabledFlag = 'false'
        elif isinstance(enabledFlag, str):
            if enabledFlag.lower() not in validStrings:
                msg = 'Specified a the value {0} to the parameter enabledFlag. ' + \
                      'this is not a valid value.  Supply either a boolean value ' + \
                      'or one of the following values: {1}'
                msg = msg.format(enabledFlag, validStrings)
                raise ValueError(msg)
            else:
                enabledFlag = enabledFlag.lower()
        else:
            msg = 'Specified a the value {0} which is a type {1} for the the ' + \
                  'parameter enabledFlag. This is not a valid value or type. ' + \
                  'Supply either a boolean value or a string with one of the ' + \
                  'following values: {2}'
            msg = msg.format(enabledFlag, type(enabledFlag), validStrings)
            raise ValueError(msg)

        if enabledFlag == 'true':
            enabledFlagBool = True
        else:
            enabledFlagBool = False

        # before proceed check to see if there is actually a change to the
        # enabled property of it is already set to whatever the target is.
        if sched2Use[self.const.enabled] != enabledFlagBool:
            sched2Use[self.const.enabled] = enabledFlag
            msg = "enabled flag: {0}".format(sched2Use[self.const.enabled])
            self.logger.debug(msg)
            body = sched2Use
            header = {'Content-Type': 'application/json',
                      'Accept': 'application/json'}
            bodyStr = json.dumps(body)
            resp = self.baseObj.putResponse(url=url, data=bodyStr,
                                            header=header)
        return resp

    def disable(self, scheduleName, category):
        '''
        disables the specified schedule
        :param scheduleName: the name of the schedule that you want to disable
        :param category: the category of the schedule that you wish to disable
        '''
        self.__setEnabledFlag(scheduleName, category, enabledFlag=False)

    def enable(self, scheduleName, category):
        '''
        enables the specified schedule
        :param scheduleName: the name of the schedule that you want to enable
        :param category: the category of the schedule that you wish to enable
        '''
        self.__setEnabledFlag(scheduleName, category, enabledFlag=True)


class Log(object):
    '''
    Used to manage individual log files.
    '''

    def __init__(self, logs, logId):
        #  url = self.baseUrl + '/' + self.resturi + '/' + self.logDefWord + '/' + str(jobId) + \
        #  '/' + viewOrDownload + '?' + self.tokenId + '=' + self.token
        # http://fmeserver/fmerest/v3/transformations/jobs/id/42/log?accept=json&detail=low
        self.logger = logging.getLogger(__name__)

        self.responseContent = None
        self.response = None

        logId = str(logId)
        # logRequestType = 'download'  # options view|download
        self.url = urllib.parse.urljoin(logs.url, 'id')
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, logId)
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, 'log')
        self.url = logs.baseObj.fixUrlPath(self.url)
        self.logger.debug("log url is: %s", self.url)
        self.logs = logs

    def getUrl(self):
        '''
        retrieves the base log url
        '''
        url = self.logs.baseObj.getURL(self.url)
        return url

    def getLog(self):
        '''
        Gets the log file as text and returns it
        '''
        header = {'Accept': 'application/octet-stream'}
        self.response = self.logs.baseObj.getResponse(self.url, header=header,
                                                      returnType='raw',
                                                      returnRequestObj=True)
        responseText = self.response.text
        self.responseContent = responseText
        # responseContent = responseText.read()
        return responseText

    def extractFromLog(self, startRegexStr, extractRegexStr, endRegexStr, srchStr):
        '''
        Used to extract data from the log file.
        '''
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written
        #                                       59
        # startRegexStr = '^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+\.\d+\|STATS\s*\|\s*Features\s+Written\s+Summary\s*$'
        # extractRegexStr = '^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+\.\d+\|STATS\s*\|\s*\w+\s+\d+$'
        # endRegexStr = '^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+\.\d+\|STATS\s*\|\s*Total\s+Features\s+Written\s+\d+$'
        # srchStr1 = '^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+\|\s*\d+\.\d+\|STATS\s*\|\s*'

        StartRegex = re.compile(startRegexStr, re.IGNORECASE)
        ExtractRegex = re.compile(extractRegexStr, re.IGNORECASE)
        EndRegex = re.compile(endRegexStr, re.IGNORECASE)

        # pattern to retrieve is:
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |QSOI_BC_REGIONS
        #                                                    59
        # where QSOI_BC_REGIONS is the feature and 59 is the records.
        # occurs after the line
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |
        #         Features Written Summary
        # and before the line
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written
        #                                                     59
        if self.responseContent is None:
            self.getLog()
        retData = []
        start = False
        for line in self.responseContent.split('\n'):
            line = line.strip()
            if start:
                if EndRegex.match(line):
                    start = False
                elif ExtractRegex.match(line):
                    startPos = re.search(srchStr, line).end()
                    lineList = re.split(r'\s+', line[startPos:])
                    fc = lineList[0]
                    feats = lineList[1]
                    retData.append([fc, feats])
            if StartRegex.match(line):
                start = True
        return retData

    def getFeaturesWritten(self):
        '''
        extracts the features written from the log file.
        '''
        # 2015-04-25 12:55:38|   2.5|  0.0|STATS |Total Features Written
        #                                                     59
        StartRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.' + \
            r'\d+\|\s*\d+\.\d+\|STATS\s*\|\s*Features\s+Written\s+Summary\s*$'
        ExtractRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.' + \
            r'\d+\|\s*\d+\.\d+\|STATS\s*\|\s*\w+(\.\w+)*\s+\d+$'
        EndRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.' + \
            r'\d+\|\s*\d+\.\d+\|STATS\s*\|\s*Total\s+Features\s+Written\s+\d+$'
        srchStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+' + \
            r'\|\s*\d+\.\d+\|STATS\s*\|\s*'
        retData = self.extractFromLog(StartRegexStr, ExtractRegexStr,
                                      EndRegexStr, srchStr)
        return retData

    def getFeaturesRead(self):
        '''
        extracts the features read from the log file.
        '''
        StartRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.' + \
            r'\d+\|\s*\d+\.\d+\|STATS\s*\|\s*Features\s+Read\s+Summary\s*$'
        ExtractRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.' + \
            r'\d+\|\s*\d+\.\d+\|STATS\s*\|\s*\w+(\.\w+)*\s+\d+$'
        EndRegexStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d' + \
            r'+\|\s*\d+\.\d+\|STATS\s*\|\s*Total\s+Features\s+Read\s+\d+$'
        srchStr = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*\|\s*\d+\.\d+' + \
            r'\|\s*\d+\.\d+\|STATS\s*\|\s*'
        retData = self.extractFromLog(StartRegexStr, ExtractRegexStr,
                                      EndRegexStr, srchStr)
        return retData


class Jobs(object):
    '''
    used to get information about past jobs.
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.const = JSONConstants()
        self.logger = logging.getLogger(__name__)
        # job types: # 'completed', 'running' or 'queued'.
        # http://fmeserver/fmerest/v2/transformations/jobs/completed?
        # detail=low&limit=-1&offset=-1
        self.transformationsUrl = urllib.parse.urljoin(
            self.baseObj.restUrl,
            self.baseObj.jobsDir,
            True)
        self.transformationsUrl = self.baseObj.fixUrlPath(
            self.transformationsUrl)
        self.url = urllib.parse.urljoin(self.transformationsUrl, 'jobs', True)
        self.url = self.baseObj.fixUrlPath(self.url)

        # when retrieving jobs from fme server, and the queue gets to the
        # end of of the job list it will return a null object. The null
        # object won't trigger the end of the loop.  This parameter sets
        # the number of blank pages to read before the loop is closed.
        self.jobNullPagesToEndLoop = 2
        self.jobNullPagesRead = 0

    def getJobs(self, jobType='completed', limit=None, offset=None):
        '''
        :return: a struct that describes the jobs that have been executed
        '''
        # returns a dictionary which is indexed by job id.
        # down the road can enhance this method to allow for time queries
        url = urllib.parse.urljoin(self.url, jobType, True)

        jobs = {}
        params = {}

        if limit:
            params['limit'] = str(limit)
            params['offset'] = 0
        if offset:
            params['offset'] = str(offset)
        self.logger.debug('params: {0}'.format(params))
        #print 'params:', params
        response = self.baseObj.getResponse(url, additionalParams=params)
        cnt = 0
        for job in response[self.const.items]:
            jobs[job[self.const.id]] = job
            cnt += 1
        self.logger.debug('number of jobs returned: %s', cnt)
        if cnt == 0:
            self.jobNullPagesRead += 1
        return jobs

    def isEndOfPage(self):
        '''
        Used for paging through the results, lets you know that the end of
        the page has been reached.
        '''
        retVal = False
        if self.jobNullPagesRead >= self.jobNullPagesToEndLoop:
            retVal = True
        return retVal

    def getJob(self, jobId):
        '''
        gets the job object for the jobid
        '''
        # detail param is no longer used as its not valid in FMEServer
        # rest api V3, but is kept here for backward compatibility
        job = Job(self, jobId)
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
        # this url is no longer the one
        # http://server/fmerest/v3/transformations/commands/submit/BCGW_SCHEDULED/GSR_CLIMATE_STATIONS_SVW_staging_csv_bcgw.fmw
        # new url in v3 is
        # http://server/fmerest/v3/transformations/submit/BCGW_SCHEDULED/GSR_CLIMATE_STATIONS_SVW_staging_csv_bcgw.fmw
        # url = urlparse.urljoin(self.transformationsUrl, 'commands')
        # url = self.baseObj.fixUrlPath(url)
        url = self.transformationsUrl
        url = self.baseObj.fixUrlPath(url)
        if sync:
            url = urllib.parse.urljoin(url, 'transact')
        else:
            url = urllib.parse.urljoin(url, 'submit')
        url = self.baseObj.fixUrlPath(url)
        url = urllib.parse.urljoin(url, repoName)
        url = self.baseObj.fixUrlPath(url)
        url = urllib.parse.urljoin(url, jobName)
        self.logger.debug("url is: %s", url)
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

        self.logger.debug('body:-----')
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(body)

        body = json.dumps(body)
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}

        response = self.baseObj.postResponse(url, data=body, header=header)
        return response

    def submitJobSync(self, repoName, jobName, params=None):
        '''
        submits the job for synchronous execution
        '''
        response = self.submitJob(repoName, jobName, params, sync=True)
        return response

    def submitJobASync(self, repoName, jobName, params=None):
        '''
        submits the job for async execution
        '''
        response = self.submitJob(repoName, jobName, params, sync=False)
        return response


class Job(object):
    '''
    used for individual jobs
    '''

    def __init__(self, jobs, jobId):
        self.jobId = jobId
        # http://server/fmerest/v2/transformations/jobs/id/9021?accept=json&detail=high
        self.url = urllib.parse.urljoin(jobs.url, 'id')
        self.url = jobs.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, str(jobId))
        self.url = jobs.baseObj.fixUrlPath(self.url)
        self.baseObj = jobs.baseObj
        # self.url = urlparse.urljoin(jobs.url, str(jobId) + jobs.baseObj.dataType)
        response = jobs.baseObj.getResponse(self.url)
        self.response = response

    def getJob(self):
        '''
        returns information about the job
        '''
        return self.response

    def getJobLog(self):
        '''
        returns the log for the current job
        '''
        logs = Logs(self.baseObj)
        log = logs.getLog(self.jobId)
        return log

    def getJobStatus(self):
        '''
        :return: the status ofr the current job
        '''
        return self.response['status']


class Repository(object):
    '''
    Repository class contains functionality for retrieving the
    various FME Server repositories.  Various methods in this
    class will return Workspace objects allowing you to identify
    fmw's in a repository as well as get information about FMW's
    '''

    def __init__(self, baseObj):
        self.baseObj = baseObj
        self.logger = logging.getLogger(__name__)
        self.const = JSONConstants()
        self.repos = []
        self.pp = pprint.PrettyPrinter(indent=4)
        self.url = urllib.parse.urljoin(self.baseObj.restUrl, self.baseObj.repositoryDir, True)

    def fetchRepositories(self):
        '''
        Queries the rest api for a list of the repositories on an
        fme server instance.  Populates the object property:
        self.repos with a dictionary with the following structure:

        self.repos[<repository name>] = { 'description': <description of repo>,
                                          'name': <same value as key, ie repository name }

        '''
        response = self.baseObj.getResponse(self.url)
        self.repos = {}
        for repo in response[self.const.items]:
            self.repos[repo[self.const.name]] = \
                {self.const.description : repo[self.const.description],
                 self.const.name: repo[self.const.name]}

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
        self.logger.debug("repoNames: %s", repoNames)
        if repoName not in  repoNames:
            raise InvalidRepositoryNameException(repoName, self.url)
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
        itemUrl = urllib.parse.urljoin(itemUrl, repoName)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urllib.parse.urljoin(itemUrl, 'items')
        self.logger.debug("itemUrl: %s)", itemUrl)
        baseName = os.path.basename(fmwPath)
        headers = {'Content-Disposition': 'attachment; filename="' + str(baseName) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        dataPayload = open(fmwPath, 'rb')
        params = {'type': 'WORKSPACE'}
        response = self.baseObj.postResponseFormData(itemUrl, params=params,
                                                     header=headers, 
                                                     data=dataPayload)
        self.logger.debug("response from post: %s", response)
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
        itemUrl = urllib.parse.urljoin(itemUrl, repoName)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urllib.parse.urljoin(itemUrl, 'items')
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urllib.parse.urljoin(itemUrl, justFMW)
        self.logger.debug("itemUrl: %s", itemUrl)
        headers = {'Content-Disposition': 'attachment; filename="' + str(fmwPath) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        dataPayload = open(fmwPath, 'rb')
        params = {'item': justFMW,
                  'repository': repoName}
        #          'detail': 'low'}

        response = self.baseObj.putResponse(itemUrl, header=headers,
                                            data=dataPayload, params=params)
        # http://server/fmerest/v3/repositories/REPO/items
        self.logger.debug("response: %s", response)

    def exists(self, repoName):
        '''
        Used to determine if a specific fmw exists in fme server.  The repoName
        parameter passed to this method is case sensitive.  'REPO' and 'repo' would
        be considered two different repositories.

        :return: a boolean value indicating if the repository exists or not
        :rtype: boolean
        '''
        retVal = False
        # flush the cached repositories
        self.repos = None
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
        if self.exists(repName):
            self.logger.debug("the repo %s already exists", repName)
        else:
            # body:
            # description=This%20is%20part%20of%20the%20REST%20example%20suite&name=MyTest
            self.logger.debug("creating the repo: %s", repName)
            # header:
            # Content-Type: application/x-www-form-urlencoded
            # Accept: application/json
            # dataPayload = {'description': descr,
            #               'name':repName}
            descr = urllib.parse.quote_plus(descr)
            dataPayload = 'description={0}&name={1}'.format(descr, repName)
            self.logger.debug('dataPayload: %s', dataPayload)
            # dataPayload = urllib.quote_plus(dataPayload)
            self.logger.debug('url: %s', self.url)
            self.logger.debug('dataPayload: %s', dataPayload)
            response = self.baseObj.postResponseFormData(self.url,
                                                         data=dataPayload,
                                                         returnType=None)
            self.logger.debug("response from post: %s", response)
            self.logger.debug("created the repo: %s", repName)

    def delete(self, repName):
        '''
        deletes a repository
        :param repName:  the repository that you want to delete
        '''
        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urllib.parse.urljoin(itemUrl, repName)

        self.logger.debug("url is: %s", itemUrl)
        if self.exists(repName):
            self.baseObj.deleteResponse(itemUrl)


class Workspaces(object):
    '''
    python wrapper to the workspaces end point.
    '''

    def __init__(self, repos, repo):
        self.repos = repos
        self.logger = logging.getLogger(__name__)
        self.const = JSONConstants()
        self.repo = repo
        self.repoName = repo['name']
        self.baseObj = self.repos.baseObj
        self.pp = pprint.PrettyPrinter(indent=4)
        # http://server/fmerest/v2/repositories/Samples/items?detail=low
        self.url = urllib.parse.urljoin(self.baseObj.restUrl, self.baseObj.repositoryDir)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, self.repoName)
        self.url = self.baseObj.fixUrlPath(self.url)
        self.url = urllib.parse.urljoin(self.url, 'items')
        self.logger.info("workspace url: %s", self.url)
        self.workspaces = {}

    def fetchWorkspaces(self):
        '''
        Queries fme server for the workspaces in the repository that was
        specified when this object was created.  (in property repoName)
        and populates the object property self.workspaces with a dictionary
        who's key is the name of the workspace and the value is the full
        data structure returned by the rest api.
        '''
        # http://host/fmerest/repositories/DWRS.json
        params = {'type': 'WORKSPACE'}
        response = self.baseObj.getResponse(self.url, additionalParams=params)
        self.logger.debug("response: %s", response)
        # workspaces = response['serviceResponse']['repository']['workspaces']['workspace']
        self.workspaces = {}
        # self.pp.pprint(response)
        for workspace in response[self.const.items]:
            self.workspaces[workspace[self.const.name]] = workspace

    def getWorkspaceNames(self):
        '''
        gets the workspace names
        '''
        if not self.workspaces:
            self.fetchWorkspaces()
        workSpaceNames = self.workspaces.keys()
        return workSpaceNames

    def getWorkspaces(self):
        '''
        gets a Workspaces object/struct
        '''
        # returns the data structure returned by the
        # REST query.
        if not self.workspaces:
            self.fetchWorkspaces()
        return self.workspaces

    def getWorkspaceInfo(self, wrkspcName):
        '/repositories/< repository >/items/< item'
        url = self.baseObj.fixUrlPath(self.url)
        url = urllib.parse.urljoin(url, wrkspcName)
        header = {'Accept': r'application/json'}
        response = self.baseObj.getResponse(url, returnType='json', header=header)
        return response

    def exists(self, wrkSpaceName):
        '''
        :return: boolean based on whether the given workspace exists or not
        '''
        # workspace names are cached for some operations, but for
        # this to work we have to re-retrieve them.
        self.workspaces = {}
        workSpaceNames = self.getWorkspaceNames()
        retVal = False
        for curWorkspc in workSpaceNames:
            if curWorkspc.lower() == wrkSpaceName.lower():
                retVal = True
                break
        return retVal

    def registerWithJobSubmitter(self, wrkspcName):
        '''
        registers a given workspace with the job submitter.  This MUST be done
        if you wish to run the FMW on fme server.
        '''
        # url to send
        # http://host/fmeserver/repositories/junk_bcgwdlv/replicationScriptName.fmw
        # http://host/fmerest/v2/repositories/junk_bcgwdlv/items/replicationScriptName.fmw/services?accept=json&detail=low
        # print 'baseurl', self.url
        url = self.baseObj.fixUrlPath(self.url)
        url = urllib.parse.urljoin(url, wrkspcName)
        url = self.baseObj.fixUrlPath(url)
        url = urllib.parse.urljoin(url, 'services')

        # print 'url:', url
        datacont = 'services=fmejobsubmitter'
        header = {'Content-Type': 'application/x-www-form-urlencoded',
                  'Accept': 'application/json'}
        # response = self.baseObj.postResponse(url, detail='high', data=datacont, header=header )
        response = self.baseObj.postResponseFormData(url, data=datacont, header=header)
        self.logger.debug("response: %s", response)
        # print 'response:', response

    def getPublishedParams(self, wrkspcName, reformat4JobReRun=False):
        '''
        Retrieves the published parameters for the given workspace.

        reformat4JobReRun - if this parameter is set to true then will reformat
                            the published parameters so they can used un modified
                            to re-run a fmw.

        The returned structure is a list of dictionaries.  Each dictionary
        describes a single published parameter.  The following is an
        example of one of these dictionaries:
            {   u'defaultValue': u'evpro99',
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
        url = urllib.parse.urljoin(url, wrkspcName)
        response = self.baseObj.getResponse(url)
        params = response[self.const.parameters]
        if reformat4JobReRun:
            # should look like this:
            # {
            #  "name": "MAXY",
            #  "value": "42"
            # }, ...
            reformatParams = {}
            for param in params:
                reformatParams[param[self.const.name]] = param[self.const.defaultValue]
                # paramDict = {}
                # paramDict['name'] = param['name']
                # paramDict['value'] = param['defaultValue']
                # reformatParams.append(paramDict)
            params = reformatParams
        return params

    def downloadWorkspace(self, wrkspcName, destination):
        '''
        downloads a given workspace from fme server.
        '''
        # http://server/fmerest/v2/repositories/Samples/items/austinDownload.fmw?detail=low
        # print 'baseurl', self.url
        url = self.baseObj.fixUrlPath(self.url)
        url = urllib.parse.urljoin(url, wrkspcName)
        self.logger.debug("url: %s", url)
        self.logger.debug("wrkspcName: %s", wrkspcName)
        # print 'wrkspc url:', url
        header = {'Accept': r'application/octet-stream'}
        response = self.baseObj.getResponse(url, returnType='raw', header=header, returnRequestObj=True)
        fh = open(destination, 'wb')
        cnt = 0
        # modified to read from the request content, before was reading
        # from raw which as of fme2017 means that its reading the
        # compressed stream this way doesn't require decompression as all
        # handled by requests module.
        for chunk in response.iter_content(chunk_size=128):
        # for reponseLine in response:
            # fh.write(reponseLine)
            fh.write(chunk)
            cnt += 1
        fh.close()

    def deleteWorkspace(self, wrkspcName):
        '''
        like the titles says deletes the workspace
        '''
        url = self.baseObj.fixUrlPath(self.url)
        url = urllib.parse.urljoin(url, wrkspcName)
        self.logger.debug("url: %s", url)
        self.logger.debug("wrkspcName: %s", wrkspcName)
        header = {'Accept': 'application/json'}
        resp = self.baseObj.deleteResponse(url, header=header, acceptCodes=[204])
        self.logger.debug("response: %s", resp)


class Resources(object):
    '''
    Used to interact with Resource end points.
    '''

    def __init__(self, baseObj):
        self.logger = logging.getLogger(__name__)
        self.baseObj = baseObj
        self.const = JSONConstants()
        # self.rootDir = 'connections'
        # self.fileSysDir = 'filesys'
        self.url = urllib.parse.urljoin(self.baseObj.restUrl, self.baseObj.resourcesDir, True)

    def getRootDirContents(self):
        '''
        gets the current contents of the root directory
        '''
        # http://fmeserver/fmerest/v2/resources/connections?detail=low
        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urllib.parse.urljoin(itemUrl, self.const.connections)
        response = self.baseObj.getResponse(itemUrl)
        return response[self.const.items]

    def getDirectory(self, dirType, dirList):
        '''
        returns a python struct that describes the directory.
        '''
        # http://fmeserver/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/filesys/foo/bar?depth=1&detail=low
        # dirTypes:
        #   FME_SHAREDRESOURCE_BACKUP
        #   FME_SHAREDRESOURCE_DATA
        #   FME_SHAREDRESOURCE_ENGINE
        #   FME_SHAREDRESOURCE_LOG
        #   FME_SHAREDRESOURCE_TEMP
        itemUrl = self.__calcURL(dirType, dirList)
        # print 'url is:', itemUrl
        addparams = {'depth': 10}
        dontErrorStatusCodes = [404]
        response = self.baseObj.getResponse(itemUrl, additionalParams=addparams,
                                            dontErrorStatusCodes=dontErrorStatusCodes)
        return response

    def exists(self, dirType, dirList):
        '''
        returns boolean based on whether the directory exists or not.
        '''
        response = self.getDirectory(dirType, dirList)
        retVal = True
        if response.has_key('message'):
            if "does not exist" in response['message']:
                retVal = False
        return retVal

    def __calcURL(self, dirType, dirList):
        '''
        internal method that helps calculate the url to a specific resource
        directory.
        '''
        # if type(dirList) is not list:
        if not isinstance(list, dirList):
            msg = 'you specifed a value of {0} which has a type of {1} for ' + \
                  'the "dirList" parameter.  This parameter should be a list ' + \
                  'descrbing the directory hierarchy you are trying to get ' + \
                  'information about'
            msg = msg.format(dirList, type(dirList))
            raise ValueError(msg)
        rootDirs = self.getRootDirContents()
        dirType = dirType.upper().strip()
        valid = False
        validTypes = []
        for curRootDir in rootDirs:
            # print 'dir: {0}'.format(dir)
            if curRootDir['name'].upper().strip() == dirType:
                valid = True
                break
            validTypes.append(curRootDir['name'])
        if not valid:
            msg = 'you supplied a directory type of {0} which is ' + \
                  'an invalid type. Valid types include {1}'
            msg = msg.format(dirType, validTypes)
            raise ValueError(msg)

        itemUrl = self.baseObj.fixUrlPath(self.url)
        itemUrl = urllib.parse.urljoin(itemUrl, self.const.connections)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urllib.parse.urljoin(itemUrl, dirType)
        itemUrl = self.baseObj.fixUrlPath(itemUrl)
        itemUrl = urllib.parse.urljoin(itemUrl, self.const.filesys)
        for curDir in dirList:
            itemUrl = self.baseObj.fixUrlPath(itemUrl)
            itemUrl = urllib.parse.urljoin(itemUrl, curDir)
        self.logger.debug("itemUrl: %s", itemUrl)
        return itemUrl

    def createDirectory(self, dirType, dirList, dir2Create):
        '''
        Request URL
        http://server/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/filesys/foo/bar?detail=low

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
        self.logger.debug("response: %s", response)

    def deleteDirectory(self, dirType, dirList):
        '''
        Used to delete a directory from the resources

        :param dirType: the directory type, valid types listed below.
        :param dirList: a list that describes the path that you want to
                        delete
         - FME_SHAREDRESOURCE_BACKUP
         - FME_SHAREDRESOURCE_DATA
         - FME_SHAREDRESOURCE_ENGINE
         - FME_SHAREDRESOURCE_LOG
         - FME_SHAREDRESOURCE_TEMP
        '''
        itemUrl = self.__calcURL(dirType, dirList)
        header = {'Accept': 'application/json'}
        self.baseObj.deleteResponse(itemUrl, header=header, acceptCodes=[204])

    def copyFile(self, dirType, dirList, file2Upload, overwrite=False,
                 createDirectories=False):
        '''
        copies a file to a resource directory on fme server.
        '''
        itemUrl = self.__calcURL(dirType, dirList)
        params = {'createDirectories': str(createDirectories).lower(),
                  'overwrite': overwrite}

        # http://fmeserver/fmerest/v2/resources/connections/FME_SHAREDRESOURCE_TEMP/...
        # filesys/foo/bar?createDirectories=false&detail=low&overwrite=false
        baseName = os.path.basename(file2Upload)
        # baseName = urllib.quote(baseName)
        baseName = baseName.decode('utf8')
        self.logger.debug('baseName: {0}'.format(baseName))
        headers = {'Content-Disposition': 'attachment; filename="' + str(baseName) + '"',
                   'Content-Type': 'application/octet-stream',
                   'Accept': 'application/json'}
        # Content-Disposition: attachment; filename="uploadtest.txt"
        # Accept: application/json
        dataPayload = open(file2Upload, 'rb')
        self.logger.debug("itemUrl: %s", itemUrl)
        response = self.baseObj.postResponseFormData(itemUrl, header=headers,
                                                     data=dataPayload, params=params)
        self.logger.debug("response: %s", response)
        dataPayload.close()

    def getResourceInfo(self, dirType, dirList):
        '''
        returns information about the given directory type / path combination.
        '''
        # /resources/connections/< resource >/filesys/< path >
        itemUrl = self.__calcURL(dirType, dirList)
        self.logger.debug("item url: %s", itemUrl)
        response = self.baseObj.getResponse(itemUrl)
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(response)
        return response


class InvalidRepositoryNameException(Exception):
    '''
    custom exception for repositories name errors.
    '''

    def __init__(self, repoName, serverUrl):
        self.repoName = repoName
        self.serverUrl = serverUrl

    def __str__(self):
        msg = "[ERROR] the repository provided ('{0}') does not match up with a " + \
              "repository at the url {1}\n"
        msg = msg.format(self.repoName, self.serverUrl)

        return msg
