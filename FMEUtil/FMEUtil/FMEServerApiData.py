'''
Created on Oct 18, 2018

@author: kjnether

A Wrapper to support easy extraction of specific information from data that
is returned from various FME Server End points.
'''

import FMEConstants
import logging
import KirkUtil.constants
import sys
import dateutil.parser


class Schedules(object):
    '''
    wraps a schedule list with a various utility methods that allow the
    list to be interogated
    '''

    def __init__(self, schedulesData):
        self.logger = logging.getLogger(__name__)
        print 'name:', __name__
        self.logger.debug("logger created for {0}!".format(__name__))
        self.data = schedulesData
        self.curIter = 0

    def exists(self, scheduleName, casesensitve=False):
        '''
        :param scheduleName: name of the schedule who's existence is to be
                             determined
        :type scheduleName: str
        :param casesensitve: inidcates whether the schedule name should be
                             evaluated as a case sensitive string or not.
        :type casesensitve: bool
        '''

        schedExists = False
        for schedData in self.data:
            sched = Schedule(schedData)
            schedName = sched.getName()
            if not casesensitve:
                scheduleName = scheduleName.lower()
                schedName = schedName.lower()
            if scheduleName == schedName:
                schedExists = True
                self.logger.debug("job exists: %s", schedName)
                pubParms = sched.getPublishedParameters()
                self.logger.debug("published Params: %s", unicode(pubParms))
                break
        return schedExists

    def getFMWRepositorySchedule(self,
                                 repositoryName,
                                 fmwName,
                                 caseSensitive=False):
        '''
        iterates through all the schedules looking for one that is tied to
        the given repository name / fmw name.

        If no schedule is found will return None

        :param repositoryName: the name of the repository associated with
                               the returned schedule
        :param fmwName: the name of the fmw associated with the returned
                        schedule
        :param caseSensitive: whether the schedule / repository comparison
                              should take place using case sensitivity
        '''
        retVal = None
        if not caseSensitive:
            fmwName = fmwName.lower()
            repositoryName = repositoryName.lower()
        for schedule in self:
            schedFMWName = schedule.getFMWName()
            schedRepoName = schedule.getRepository()
            if not caseSensitive:
                schedFMWName = schedFMWName.lower()
                schedRepoName = schedRepoName.lower()
            if repositoryName == schedRepoName:
                # self.logger.debug("schedFMWName: %s", schedFMWName)
                # self.logger.debug("fmwName: %s", fmwName)
                # self.logger.debug("repositoryName: %s", repositoryName)
                # self.logger.debug("schedRepoName: %s", schedRepoName)
                if schedFMWName == fmwName:
                    # self.logger.debug("found: %s", fmwName)
                    retVal = schedule.getScheduleName()
                    # self.logger.debug("schedule name: %s", retVal)
                    self.reset()
                    break
        return retVal

    def kirkScheduleExists(self, kirkJobId, kirkType):
        '''
        specific to Kirk Jobs, returns the schedule associated with
        the particular kirkid provided

        :param kirkJobId: The job id for a kirk job who's existence is
                          being queried
        :type kirkJobId:  str/int
        :param kirkType: The type of Kirk Job, current options are defined
                         in the enumeration KirkUtil.constants.KirkFMWs
        :type kirkType: KirkUtil.constants.KirkFMWs
        '''
        retVal = False
        # start by making sure the type is correct
        if not isinstance(kirkType, KirkUtil.constants.KirkFMWs):
            msg = 'The arg kirkType has a type of: {0}.  Needs to be a ' + \
                  'KirkUtil.constants.KirkFMWs type.'
            msg = msg.format(type(kirkType))
            raise ValueError(msg)
        kirkFmwName = '{0}.fmw'.format(kirkType.name)
        self.logger.debug("kirk FMW name: %s", kirkFmwName)
        # now test for that name
        for schedData in self.data:
            sched = Schedule(schedData)
            fmwName = sched.getFMWName()
            self.logger.debug("fmw comparison sched fmw: %s", fmwName)
            if fmwName.lower() == kirkFmwName.lower():
                # now get the jobid associated with this job
                self.logger.debug("found the fmw: %s", fmwName)
                pp = sched.getPublishedParameters()
                ppKirkJobId = pp.getKirkJobId()
                self.logger.debug("kirk job id: %s",)
                if unicode(ppKirkJobId) == unicode(kirkJobId):
                    retVal = True
                    self.logger.debug("found match for %s", ppKirkJobId)
                    break
        return retVal

    def getSchedule(self, scheduleName, casesensitve=False):
        '''
        returns the schedule object if one is found with the name
        provided
        :param scheduleName: name of the schedule to be returned
        :type scheduleName: str
        :param casesensitve: whether to consider case when searching for
                             the job
        :type casesensitve: bool

        :return: the Schedule object for the requested schedule if one
                 is found, otherwise None
        :rtype: Schedule
        '''

        schedule = None
        for schedData in self.data:
            sched = Schedule(schedData)
            schedName = sched.getName()
            if not casesensitve:
                scheduleName = scheduleName.lower()
                schedName = schedName.lower()

            if scheduleName == schedName:
                schedule = sched
                break
        return schedule

    def __iter__(self):
        return self

    def next(self):
        '''
        iterator for these schedules, returning a Schedule object for
        each loop.
        '''
        if self.curIter >= len(self.data):
            self.reset()
            raise StopIteration
        else:
            #self.logger.debug("getting the next item, %s", self.curIter)
            schedData = self.data[self.curIter]
            schedObj = Schedule(schedData)
            self.curIter += 1
        return schedObj

    def reset(self):
        self.curIter = 0


class Schedule(object):

    def __init__(self, schedData):
        self.logger = logging.getLogger(__name__)
        self.data = schedData

    def getName(self):
        key = FMEConstants.Schedule.name.name
        # self.logger.debug("key: %s", key)
        # self.logger.debug("value: %s", self.data[key])
        return self.data[key]

    def getScheduleName(self):
        '''
        Schedule name as defined in the schedule object.  In the event that
        the schedule departs from the standard case this should retrieve the
        correct case.
        '''
        #self.logger.debug("retrieving the schedule name")
        key = FMEConstants.Schedule.name.name
        #self.logger.debug("key is: %s", key)
        return self.data[key]

    def getPublishedParameters(self):
        request = FMEConstants.Schedule.request.name
        publishedParameters = FMEConstants.Schedule.publishedParameters.name
        schedulePubParams = self.data[request][publishedParameters]
        pubparams = SchedulePublishedParameters(schedulePubParams)
        #self.logger.debug("pub params: %s", unicode(pubparams))
        return pubparams

    def getCategory(self):
        '''
        :return: the schedules category, used to uniquely identify schedules
        '''
        self.logger.debug("retrieving the category")
        key = FMEConstants.Schedule.category.name
        return self.data[key]

    def getCRON(self):
        '''
        :return: the cron recurrence string
        '''
        key = FMEConstants.Schedule.cron.name
        return self.data[key]

    def getFMWName(self):
        key = FMEConstants.Schedule.workspace.name
        return self.data[key]

    def getRepository(self):
        '''
        :return: the name of the repository that the schedule is pointing
                 to
        '''
        key = FMEConstants.Schedule.repository.name
        return self.data[key]

    def isEnabled(self):
        '''
        :return: bool indicating whether the current schedule is
                 enabled or disabled
        '''
        key = FMEConstants.Schedule.enabled.name
        enable = self.data[key]
        if not isinstance(enable, bool):
            # assume its a str
            enablestr = enable.lower()
            enable = False
            if enablestr == 'true':
                enable = True
        return enable


class SchedulePublishedParameters(object):

    def __init__(self, data):
        self.logger = logging.getLogger(__name__)
        self.data = data
        self.curIter = 0

    def getDestinationSchema(self, position=None):
        '''
        retrieves the destination schema if it is defined using the
        databc FME framework standard for published parameters

        if position is not specified returns the default parameter
        for destination schema which is DEST_SCHEMA

        if position is specified looks for a parameter with the
        position number.

        :param position: identifies which of the multiple destination schemas
                         is defined for the dataset.
                         DEST_SCHEMA_1 would be returned if you spedified
                         1. DEST_SCHEMA_2 is returned if you specified 2
                         etc..
        :type position:  str/int
        '''
        param = None
        pp = FMEConstants.FMEFrameworkPublishedParameters
        frameworkParamName = pp.DEST_SCHEMA.name
        self.logger.debug("frameworkParamName: %s", frameworkParamName)
        if position:
            frameworkParamName = '{0}_{1}'.format(frameworkParamName, position)
        if self.paramExists(frameworkParamName):
            param = self.getParamValue(frameworkParamName)
        else:
            msg = 'The destination schema name %s does not exist in the ' + \
                  'published parameter definitions'
            self.logger.warning(frameworkParamName)
        return param

    def getDestinationFeature(self, position=None):
        '''
        if the schedule uses the DBC published parameter standard then this
        method will extract the Destination feature.  There can be more then
        one destination feature.  If this is the case they are labelled
        by position, example DEST_FEATURE_1 DEST_FEATURE_2 etc.

        the position indicates which destination feature to return

        :param position: see notes above
        :type position: str/int
        '''
        param = None
        if position is None:
            position = 1
        destFeat = FMEConstants.FMEFrameworkPublishedParameters.DEST_FEATURE.name
        destFeatParamName = '{0}_{1}'.format(destFeat, position)
        self.logger.debug("destFeatParamName: %s", destFeatParamName)
        if self.paramExists(destFeatParamName):
            param = self.getParamValue(destFeatParamName)
        if param is None:
            msg = 'Trying to retrieve the parameter %s however it doesnt ' + \
                  'exist'
            self.logger.warning(msg, destFeatParamName)
        return param

    def getDestDbEnvKey(self):
        destDbEnv = self.getParamValue('DEST_DB_ENV_KEY')
        return destDbEnv

    def paramExists(self, paramName):
        param = self.getParamValue(paramName)
        retVal = True
        if param is None:
            retVal = False
        return retVal

    def getParamValue(self, paramName):
        retVal = None
        #self.logger.debug("paramName: %s", paramName)
        for param in self.data:
            if param['name'] == paramName:
                # sometimes the data is stored in a parameter called 'raw'
                if 'value' in param:
                    retVal = param['value']
                elif 'raw' in param:
                    retVal = param['raw']
                    self.logger.warning("using the raw value: %s", retVal)
                else:
                    msg = 'the published parameter %s does not have the ' + \
                          'any of the expected keys, ie value, or raw'
                    self.logger.error(param)
                    raise ValueError(msg)
                break
        if retVal is None:
            msg = 'unable to find a parameter in the published parameters ' + \
                  'named %s'
            self.logger.warning(msg, paramName)
        return retVal

    def getKirkJobId(self):
        '''
        :return: If the kirk job id parameter is defined it is retrieved
                 and returned, if it is not defined returns None
        '''
        kirkJobIdParamName = \
            FMEConstants.FMEFrameworkPublishedParameters.KIRK_JOBID.name
        retVal = self.getParamValue(kirkJobIdParamName)
        return retVal

    def __unicode__(self):
        return u'{0}'.format(self.data)

    def __str__(self):
        return self.__unicode__()

    def __iter__(self):
        return self

    def next(self):
        if self.curIter >= len(self.data):
            self.reset()
            raise StopIteration
        else:
            self.logger.debug("getting the next item, %s", self.curIter)
            pubParam = self.data[self.curIter]
            pubParamData = PublishedParameter(pubParam)
            self.curIter += 1
        return pubParamData

    def reset(self):
        self.curIter = 0


class PublishedParameter(object):

    def __init__(self, data):
        self.data = data
        self.logger = logging.getLogger(__name__)
        self.logger.debug('PublishedParameter data: %s', data)

    def getName(self):
        return self.data['name']

    def getValue(self):
        retVal = None
        if 'value' in self.data:
            retVal = self.data['value']
        elif 'raw' in self.data:
            retVal = self.data['raw']
        else:
            msg = 'No defined value: %s', self.data
            raise ValueError(msg)
        return retVal


class Workspaces(object):

    def __init__(self, data):
        self.logger = logging.getLogger(__name__)
        self.data = data
        self.curIter = 0
        self.workspaceNames = None

    def populateworkspaceNames(self):
        self.workspaceNames = self.data.keys()
        self.workspaceNames.sort()

    def __iter__(self):
        return self

    def next(self):
        '''
        iterator for these workspaces, returning a workspace object for
        each loop.
        '''
        if self.curIter >= len(self.data):
            raise StopIteration
        else:
            if self.workspaceNames is None:
                self.populateworkspaceNames()
            wrkspaceNameKey = self.workspaceNames[self.curIter]
            wrkspceData = self.data[wrkspaceNameKey]
            wrkspcObj = Workspace(wrkspceData)
            self.curIter += 1
        return wrkspcObj


class Workspace(object):

    def __init__(self, data):
        self.data = data
        self.logger = logging.getLogger(__name__)
        # self.curIter = 0

    def getWorkspaceName(self):
        '''
        :return: the workspace name, ie what is the underlying fmw.
        '''
        key = FMEConstants.Workspace.name.name
        return self.data[key]

    def getLastSaveDate(self):
        key = FMEConstants.Workspace.lastSaveDate.name
        param = self.data[key]
        # best way to parse iso8601 datetimes
        saveDate = dateutil.parser.parse(param)
        return saveDate

    def getLastPublishedDate(self):
        key = FMEConstants.Workspace.lastPublishDate.name
        param = self.data[key]
        # best way to parse iso8601 datetimes
        pubDate = dateutil.parser.parse(param)
        return pubDate

    def getRepositoryName(self):
        key = FMEConstants.Workspace.repositoryName.name
        return self.data[key]


class WorkspaceInfo(object):
    '''
    wraps the data that gets returned by
    /fmerest/apidoc/v3/#!/repositories/get_get_9
    '''

    def __init__(self, data):
        self.logger = logging.getLogger(__name__)
        self.data = data

    def getSources(self):
        pass

