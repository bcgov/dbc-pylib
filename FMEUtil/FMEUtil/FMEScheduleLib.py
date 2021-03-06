'''
Created on Jul 13, 2018

@author: kjnether
'''
import copy
import datetime
import json
import logging
import os.path
import pprint

import FMEUtil.PyFMEServerV2
import deepdiff


class Schedules(object):

    '''
    Provides a api to work with a schedule.  Mostly provides caching functionality
    Caching exists due to extremely poor performance of schedule queries against
    fme server 2015.
    :ivar fme: a fme server object
    :type fme: FMEUtil.PyFMEServerV2.FMEServer

    :ivar scheds: fme schedule object
    :type scheds: FMEUtil.PyFMEServerV2.Schedule

    :ivar schedStruct: a data structure describing the schedules for the
                       fme server instance that was specified
    :type schedStruct: dict

    :ivar schedStructComparison:  This is a duplication of schedStruct with the
                    fields described in flds2Ignore removed from the structures
                    within this list

    :ivar flds2Ignore: fields that should be ignored when doing any comparison
                       operations. (in, -, +, etc)
    :type flds2Ignore:  list
    '''

    def __init__(self, fmeServUrl, fmeServToken, cacheLabel, cacheDir,
                 refreshCache=False, ignorePP=False):
        '''
        :param fmeServUrl: url to fme server, don't include paths
        :param fmeServToken: token to fme server
        :param cacheLabel: a label that is used to calculate the schedule cache
                           file name
        :param cacheDir: directory where the cache file should be located
        :param refreshCache: whether the cache should be refreshed or not.
                             cached schedules have a date on them.  Never
                             only valid for the day that they were generated
                             for.
        '''
        self.logger = logging.getLogger(__name__)
        self.pp = pprint.PrettyPrinter(indent=4)
        self.logger.debug("test log config")
        self.fme = FMEUtil.PyFMEServerV2.FMEServer(fmeServUrl, fmeServToken)
        self.scheds = self.fme.getSchedules()
        dateTimeStamp = datetime.datetime.now().strftime('%Y-%m-%d')
        # cacheDir = os.path.normpath(os.path.join(os.path.dirname(__file__),
        #                                              '..', 'data'))
        self.cacheFile = 'scheds_{0}_{1}.json'.format(cacheLabel, dateTimeStamp)
        self.cacheFile = os.path.join(cacheDir, self.cacheFile)
        if refreshCache:
            if os.path.exists(self.cacheFile):
                os.remove(self.cacheFile)
        self.schedStruct = None

        # These are fields in the schedules that should be ignored
        # when doing comparisons between the two structures
        self.flds2Ignore = ['begin', 'enabled']
        # this switch can be set using the method setIgnoredFields()
        # when set to true published parameters are not considered in the
        # comparison of the schedules.
        self.ignorePP = ignorePP
        # this data struct will get populated with everything in self.schedStruct
        # except the fields described in flds2Ignore
        self.schedStructComparison = []
        self.getSchedules()

    def getPyFMESchedule(self):
        '''
        :return: the pyFMEServer schedule object used in this class
        :type param: FMEUtil.PyFMEServerV2.Schedule
        '''
        return self.scheds

    def getPyFME(self):
        '''
        :return:  a FMEServer object
        :rtype:  FMEUtil.PyFMEServerV2.FMEServer:
        '''
        return self.fme

    def getScheduleData(self):
        '''
        :return: the data structure that describes the schedules in this
                 object.
        '''
        return self.schedStruct

    def setIgnoredFields(self, flds, ignorePublishedParameters=True):
        '''
        When doing a comparison between schedule objects you can set a
        list of fields to ignore when doing the comparison.  There are
        certain fields that are set by default, this method allows you to
        define your own fields.
        :param flds: a list of fields that should be ignored when comparing
                     schedule objects
        '''
        self.ignorePP = ignorePublishedParameters
        self.flds2Ignore = flds
        schedStructCleaned = []
        # schedIterator = self.schedStruct[0:]
        schedIterator = copy.deepcopy(self.schedStruct)
        for schedRef in schedIterator:
            sched = schedRef.copy()
            for fld2Del in self.flds2Ignore:
                if fld2Del in sched:
                    # self.logger.debug("cleaning entry for: {0}".format(fld2Del))
                    del sched[fld2Del]
            if self.ignorePP:
                # getting rid of published parameters too!
                # self.pp.pprint(sched)
                del sched['request']['publishedParameters']
            schedStructCleaned.append(sched)
        self.schedStructComparison = schedStructCleaned

    def isEnabled(self, scheduleName):
        '''
        :return: indicates if the schedule is enabled or not
        :rtype: boolean
        '''
        schedStruct = self.getScheduleByName(scheduleName)
        return schedStruct['enabled']

    def getSchedules(self):
        '''
        If no cache file exists then gets the scheds from fme server,
        otherwise loads from the cache file

        Also populates schedStructComparison which is the structure that is used
        for comparisons of data structures.  It has some fields removed that should
        not be used for comparison operations
        '''
        cacheFile = os.path.basename(self.cacheFile)
        if os.path.exists(self.cacheFile):
            with open(self.cacheFile) as f:
                msg = 'loading the schedules from the cache file {0}'.format(cacheFile)
                self.logger.info(msg)
                schedStruct = json.load(f)
        else:
            self.logger.info("retrieving the schedules from fme server, this" + \
                             "may take a while")
            schedStruct = self.scheds.getSchedules()
            self.logger.debug("schedStruct: {0}".format(schedStruct))
            with open(self.cacheFile, 'w') as outfile:
                msg = "dumping the schedules to the cache file {0}"
                self.logger.info(msg.format(cacheFile))
                json.dump(schedStruct, outfile)

        self.schedStruct = schedStruct
        self.setIgnoredFields(self.flds2Ignore, self.ignorePP)
        # self.logger.debug("schedStruct: {0}".format(self.schedStruct))

    def getScheduleByName(self, scheduleName):
        '''
        searches through the schedules for a schedule with the name 'scheduleName'
        and returns it.

        returns None if no schedule is found
        '''
        self.logger.debug("getting the parameters for the schedule: {0}".format(scheduleName))
        retVal = None
        for sched in self.schedStruct:
            if sched['name'] == scheduleName:
                retVal = sched
                break
        return retVal

    def __contains__(self, sched):  # pylint: disable=invalid-name
        '''
        :param sched: returns true or false based on whether the sched
                      object exists in this collection of schedules
        :type param: Schedule
        '''
        # clean the submitted schedule
        # self.logger.debug("called equivalent of 'in'")
        retVal = False
        schedCleaned = {}
        for fld in sched.keys():
            if fld not in self.flds2Ignore:
                schedCleaned[fld] = copy.deepcopy(sched[fld])
        # if the ignore published parameters flag is set then
        # don't look at them if they are defined.
        if self.ignorePP:
            if 'request' in schedCleaned:
                if 'publishedParameters' in schedCleaned:
                    del schedCleaned['request']['publishedParameters']

        if schedCleaned in self.schedStructComparison:
            retVal = True
        else:
            for curSched in self.schedStructComparison:
                if curSched['name'] == schedCleaned['name']:
                    diffs = deepdiff.DeepDiff(schedCleaned, curSched)
                    self.logger.info("differences for {1}: {0}".format(diffs, curSched['name']))
        return retVal

    def __sub__(self, schedules):  # pylint: disable=invalid-name
        '''
        identifies schedules that are in self, but not in supplied
        schedules
        '''
        retVals = []
        for sched in self.schedStructComparison:
            if sched not in schedules:
                retVals.append(sched)
        return retVals


class Parameters(object):
    '''
    published parameters returned by existing schedules often include
    scripted parameters.  When creating a schedule you cannot specify
    scripted parameters as they are... well... SCRIPTED!

    This class provides some methods that allow you to retrieve the
    published parameters associated with a repository/workspace in
    a format that can be used to construct a schedule, ie will not include
    scripted parameters in its reference.
    '''

    def __init__(self, schedule, scheduleName):
        self.logger = logging.getLogger(__name__)
        self.schedule = schedule
        self.scheduleStruct = self.schedule.getScheduleByName(scheduleName)

    def getPublishedParameters(self):
        '''
        :return:  the published parameters associated with the specified schedule.
        These are retrieved not from the schedule but from the FMW that the
        schedule calls.
        '''
        workspcName = self.scheduleStruct['workspace']
        repoName = self.scheduleStruct['repository']

        fme = self.schedule.getPyFME()
        repo = fme.getRepository()
        wrkspcs = repo.getWorkspaces(repoName)
        pubParams = wrkspcs.getPublishedParams4Schedule(workspcName)
        return pubParams

    def fixSchedulePublishedParameters(self):
        '''
        :return: a schedule json struct that can be sent to FME Server to define
                 a new schedule.
        '''
        # published parameters retrieved from the workspace on fme server
        pubParams = self.getPublishedParameters()
        # published parameters associated with the current schedule.
        # includes scripted parameters, which can not be used when redefining
        # a schedule.
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.scheduleStruct)
        schedulePubParams = self.scheduleStruct['request']['publishedParameters']

        # fixedSchedule = self.scheduleStruct['request']['publishedParameters'][0:]

        # Iterating through the published parameters associated with the
        # workspace and overriding values with values that were retrieved
        # from the schedule.
        params4Schedule = []
        for pubParam in pubParams:
            paramName = pubParam['name']
            for schedParams in schedulePubParams:
                if schedParams['name'] == paramName:
                    msg = 'updating the schedule parameter {0} from {1} to {2}'
                    msg = msg.format(schedParams['name'], pubParam['value'], schedParams['value'])
                    self.logger.info(msg)
                    pubParam['value'] = schedParams['value']
            params4Schedule.append(pubParam)

        # pubParams will have name / defaultvalue keys, need to modify for
        # schedules to name/value
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(params4Schedule)
        # raise
        self.scheduleStruct['request']['publishedParameters'] = params4Schedule
        return self.scheduleStruct
