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
from ctypes.test.test_array_in_pointer import Value


class Schedules(object):

    def __init__(self, schedulesData):
        self.logger = logging.getLogger(__name__)
        print 'name:', __name__
        self.logger.debug("logger created for {0}!".format(__name__))
        self.data = schedulesData

    def exists(self, scheduleName, casesensitve=False):
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

    def kirkScheduleExists(self, kirkJobId, kirkType):
        '''

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
            # self.logger.debug("schedName: %s", fmwName)
            if fmwName.lower() == kirkFmwName.lower():
                # now get the jobid associated with this job
                self.logger.debug("found the fmw: %s", fmwName)
                pp = sched.getPublishedParameters()
                ppKirkJobId = pp.getKirkJobId()
                if unicode(ppKirkJobId) == unicode(kirkJobId):
                    retVal = True
                    self.logger.debug("found match for %s", ppKirkJobId)
                    break
        return retVal

    def getSchedule(self, scheduleName, casesensitve=False):
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
        self.logger.debug("retrieving the schedule name")
        key = FMEConstants.Schedule.name.name
        self.logger.debug("key is: %s", key)
        return self.data[key]

    def getPublishedParameters(self):
        request = FMEConstants.Schedule.request.name
        publishedParameters = FMEConstants.Schedule.publishedParameters.name
        schedulePubParams = self.data[request][publishedParameters]
        pubparams = SchedulePublishedParameters(schedulePubParams)
        self.logger.debug("pub params: %s", unicode(pubparams))
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


class SchedulePublishedParameters(object):

    def __init__(self, data):
        self.logger = logging.getLogger(__name__)
        self.data = data

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

    def paramExists(self, paramName):
        param = self.getParamValue(paramName)
        retVal = True
        if param is None:
            retVal = False
        return retVal

    def getParamValue(self, paramName):
        retVal = None
        self.logger.debug("paramName: %s", paramName)
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
