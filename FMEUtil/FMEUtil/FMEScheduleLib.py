'''
Created on Jul 13, 2018

@author: kjnether
'''
import logging
import FMEUtil.PyFMEServerV2
import datetime
import os.path
import json

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

    '''

    def __init__(self, fmeServUrl, fmeServToken, cacheLabel, refreshCache=False):
        self.logger = logging.getLogger(__name__)
        print '__name__: ', __name__
        self.logger.debug("test log config")
        self.fme = FMEUtil.PyFMEServerV2.FMEServer(fmeServUrl, fmeServToken)
        self.scheds = self.fme.getSchedules()
        dateTimeStamp = datetime.datetime.now().strftime('%Y-%m-%d')
        cacheDir = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                      '..', 'data'))
        self.cacheFile = 'scheds_{0}_{1}.json'.format(cacheLabel, dateTimeStamp)
        self.cacheFile = os.path.join(cacheDir, self.cacheFile)
        if refreshCache:
            if os.path.exists(self.cacheFile):
                os.remove(self.cacheFile)
        self.schedStruct = None
        self.getSchedule()

    def getSchedule(self):
        '''
        If no cache file exists then gets the scheds from fme server,
        otherwise loads from the cache file
        '''
        cacheFile = os.path.basename(self.cacheFile)
        if os.path.exists(self.cacheFile):
            with open(self.cacheFile) as f:
                msg = 'loading the schedules from the cache file {0}'.format(cacheFile)
                self.logger.info(msg)
                self.schedStruct = json.load(f)
        else:
            self.logger.info("retrieving the schedules from fme server, this" + \
                             "may take a while")
            self.schedStruct = self.scheds.getSchedules()
            with open(self.cacheFile, 'w') as outfile:
                msg = "dumping the schedules to the cache file {0}"
                self.logger.info(msg.format(cacheFile))
                json.dump(self.schedStruct, outfile)
        self.logger.debug("schedStruct: {0}".format(self.schedStruct))
                
    def __contains__(self, sched):
        '''
        :param sched: returns true or false based on whether the sched
                      object exists in this collection of schedules
        :type param: Schedule
        '''
        pass
        #for self.schedStruct;
        
        
class SchedCompare(object):
    
    def __init__(self, sched1, sched2):
        self.sched1 = sched1
        self.sched2 = sched2
        
class Schedule(object):
    
    def __init__(self):
        pass
        
        
        