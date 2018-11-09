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
        self.fieldMaps = FieldMaps(fldMapData)
        if destData:
            self.destinations = Destinations(destData)

    def getDestinations(self):
        return self.destinations

    def getType(self, type):
        if type.lower() == 'destinations':
            return self.destinations
        if type.lower() == 'jobs':
            return self.jobs
        if type.lower() == 'sources':
            return self.sources
        if type.lower() == 'transformers':
            return self.transformers
        if type.lower() == 'fieldMaps':
            return self.fieldMaps


class KirkDataList(object):

    def __init__(self, data):
        self.indexCntr = 0
        self.data = data

    def next(self):
        if self.indexCntr >= len(self.data):
            raise StopIteration
        data = self.data[self.indexCntr]
        self.indexCntr += 1
        return data

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.data)


class Jobs(object):

    def __init__(self, jobsData):
        self.data = jobsData
        self.indexCntr = 0
        self.props = constants.JobProperties

    def __iter__(self):
        return self

    def next(self):
        if self.indexCntr >= len(self.data):
            raise StopIteration
        jobData = self.data[self.indexCntr]
        job = Job(jobData)
        self.indexCntr += 1
        return job

    def __len__(self):
        return len(self.data)


class Job(object):

    def __init__(self, jobData):
        self.data = jobData
        self.props = constants.JobProperties

    def getJobId(self):
        return self.data[self.props.jobid.name]

    def getRestoreStruct(self):
        p = self.props
        returnObj = {
            p.destField.name: self.data[p.destField.name],
            p.jobStatus.name: self.data[p.jobStatus.name],
            p.destSchema.name: self.data[p.destSchema.name],
            p.jobLabel.name: self.data[p.jobLabel.name],
            p.destTableName.name: self.data[p.destTableName.name],
            p.cronStr.name: self.data[p.cronStr.name]}
        return returnObj


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
        self.srcProps = constants.SourceProperties

    def getRestoreStruct(self, jobid=None):
        p = self.srcProps
        returnObj = {
            p.sourceDBSchema.name: self.data[p.sourceDBSchema.name],
            p.sourceType.name: self.data[p.sourceType.name],
            p.sourceDBPort.name: self.data[p.sourceDBPort.name],
            p.jobid.name: self.data[p.jobid.name],
            p.sourceProjection.name: self.data[p.sourceProjection.name],
            p.sourceFilePath.name: self.data[p.sourceFilePath.name],
            p.sourceDBHost.name: self.data[p.sourceDBHost.name],
            p.sourceDBHost.name: self.data[p.sourceDBHost.name],
            p.sourceDBName.name: self.data[p.sourceDBName.name],
            p.sourceTable.name: self.data[p.sourceTable.name]}

        if jobid is not None:
            returnObj[p.jobid.name] = jobid


class Transformers(object):

    def __init__(self, transformers):
        self.transformers = transformers
        self.transProps = constants.TransformerProperties

    def getTransformers(self, jobId):
        transList = []
        for transformer in self.transformers:
            if transformer[self.transProps.jobid.name] == jobId:
                transList.append(Transformer(transformer))
        return transList


class Transformer(object):

    def __init__(self, transformer):
        self.transData = transformer


class FieldMaps(object):

    def __init__(self, fieldMapData):
        self.fieldMapData = fieldMapData
        self.fmProps = constants.FieldmapProperties

    def getFieldMaps(self, jobid):
        fieldMapList = []
        for fieldMap in self.fieldMapData:
            if fieldMap[self.fmProps.jobid.name] == jobid:
                fieldMapList.append(FieldMap(fieldMap))


class FieldMap(object):

    def __init__(self, fieldMapData):
        self.data = fieldMapData
        self.props = constants.FieldmapProperties

    def getRestoreStruct(self, newJobId=None):
        p = self.props
        returnObj = {
            p.destColumnName.name: self.data[p.destColumnName.name],
            p.fmeColumnType.name: self.data[p.fmeColumnType.name],
            p.sourceColumnName.name: self.data[p.sourceColumnName.name],
            p.jobid.name: self.data[p.jobid.name]}
        if newJobId is not None:
            returnObj[p.jobid.name] = newJobId
        return returnObj


class Destinations(KirkDataList):

    def __init__(self, destData):
        KirkDataList.__init__(self, destData)
        self.data = destData
        self.props = constants.DestinationsProperties
        self.indexCntr = 0

    def getDestination(self, destKey):
        returnDest = None
        for dest in self:
            if dest[self.destProps.dest_key.name] == destKey:
                returnDest = Destination(dest)
        return returnDest

    def next(self):
        if self.indexCntr >= len(self):
            raise StopIteration
        data = self.data[self.indexCntr]
        dest = Destination(data)
        self.indexCntr += 1
        return dest


class Destination(object):

    def __init__(self, destination):
        self.destination = destination

    def __str__(self):
        return unicode(self.destination)

