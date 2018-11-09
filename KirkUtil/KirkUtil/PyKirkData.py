'''
Created on Nov 9, 2018

@author: kjnether

The module PyKirk addresses interactions with the rest api.  Interactions
with the rest api returns json objects.  This class provides a wrapper
around the various data objects that are returned.

It gets used both by the pyKirk module as well as data restoration modules.
With PyKirk the data is comming from the api, with restoration modules
the data comes from backed up data files
'''

import logging
from . import constants

logger = logging.getLogger(__name__)


class KirkData(object):
    '''
    kirk job data contains relationships to other end points.  This class
    acts as a coordinator for methods that require access to multiple
    data end points.
    '''

    def __init__(self, jobData, sourcesData,
                 transData, fldMapData, destData=None):
        self.jobs = Jobs(jobData)
        self.sources = Sources(sourcesData)
        self.transformers = Transformers(transData)


class Jobs(object):

    def __init__(self, jobsData):
        self.jobsData = jobsData
        self.curJobIdx = 0

    def __iter__(self):
        return self

    def next(self):
        if self.curJobIdx >= len(self.jobs):
            raise StopIteration
        jobData = self.jobs[self.curJobIdx]
        job = Job(jobData)
        self.curJobIdx += 1
        return job

    def __len__(self):
        return len(self.jobsData)


class Job(object):

    def __init__(self, jobData):
        self.jobData = jobData
        self.jobProps = constants.JobProperties

    def getJobId(self):
        return self.jobData[self.jobProps.jobid.name]


class Sources(object):

    def __init__(self, sourcesData):
        self.sourcesData = sourcesData
        self.srcProps = constants.SourceProperties

    def getSource(self, jobId):
        jobSrc = None
        for src in self.sourcesData:
            if src[self.srcProps.jobid.name] == jobId:
                jobSrc = Source(src)


class Source(object):

    def __init__(self, sourceData):
        self.sourceData = sourceData


class Transformers(object):

    def __init__(self, transformers):
        self.transformers = transformers

