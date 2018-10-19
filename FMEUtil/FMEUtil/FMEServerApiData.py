'''
Created on Oct 18, 2018

@author: kjnether

A Wrapper to support easy extraction of specific information from data that
is returned from various FME Server End points.
'''

import FMEConstants
import logging
import KirkUtil.constants


class Schedules(object):

    def __init__(self, schedulesData):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("logger created!")
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
        # start by making sure the type is correct
        if not isinstance(kirkType, KirkUtil.constants.KirkFMWs):
            msg = 'The arg kirkType has a type of: {0}.  Needs to be a ' + \
                  'KirkUtil.constants.KirkFMWs type.'
            msg = msg.format(type(kirkType))
            raise ValueError(msg)
        kirkFmwName = '{0}.fmw'.format(kirkType.name)
        # now test for that name
        for schedData in self.data:
            sched = Schedule(schedData)
            schedName = sched.getName()
            if schedName.lower() == kirkFmwName.lower():
                # now get the jobid associated with this job
                pp = sched.getPublishedParameters()
                kirkJobId = pp.getKirkJobId()
        

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

    def getPublishedParameters(self):
        request = FMEConstants.Schedule.request.name
        publishedParameters = FMEConstants.Schedule.publishedParameters.name
        schedulePubParams = self.data[request][publishedParameters]
        pubparams = SchedulePublishedParameters(schedulePubParams)
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
                retVal = param['value']
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

