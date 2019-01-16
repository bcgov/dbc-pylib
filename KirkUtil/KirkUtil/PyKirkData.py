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

    def getType(self, dataType):
        if dataType.lower() == 'destinations':
            return self.destinations
        elif dataType.lower() == 'jobs':
            return self.jobs
        elif dataType.lower() == 'sources':
            return self.sources
        elif dataType.lower() == 'transformers':
            return self.transformers
        elif dataType.lower() == 'fieldmaps':
            return self.fieldMaps
        else:
            msg = "invalid dataType: {0}".format(dataType)
            logger.debug(msg)
            raise ValueError(msg)


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

    def getJobLabel(self):
        return self.data[self.props.jobLabel.name]

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
        self.data = sourcesData
        self.props = constants.SourceProperties

    def getSource(self, jobId):
        jobSrc = None
        for src in self.data:
            if src[self.props.jobid.name] == jobId:
                jobSrc = Source(src)
        return jobSrc


class Source(object):

    def __init__(self, sourceData):
        self.data = sourceData
        self.props = constants.SourceProperties

    def getRestoreStruct(self, jobid=None):
        p = self.props
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
        return returnObj

    def getSourceType(self):
        return self.data[self.props.sourceType]


class Transformers(object):

    def __init__(self, transformers):
        self.data = transformers
        self.props = constants.TransformerProperties

    def getTransformers(self, jobId):
        transList = []
        for transformer in self.data:
            if transformer[self.props.jobid.name] == jobId:
                transList.append(Transformer(transformer))
        return transList


class Transformer(object):

    def __init__(self, transformer):
        self.data = transformer
        self.props = constants.TransformerProperties

    def getRestoreStruct(self, jobid=None):
        p = self.props
        returnObj = {
            p.jobid.name: self.data[p.jobid.name],
            p.transformer_type.name: self.data[p.transformer_type.name],
            p.ts1_value.name: self.data[p.ts1_value.name],
            p.ts1_name.name: self.data[p.ts1_name.name],
            p.ts2_value.name: self.data[p.ts2_value.name],
            p.ts2_name.name: self.data[p.ts2_name.name],
            p.ts3_value.name: self.data[p.ts3_value.name],
            p.ts3_name.name: self.data[p.ts3_name.name],
            p.ts4_value.name: self.data[p.ts4_value.name],
            p.ts4_name.name: self.data[p.ts4_name.name],
            p.ts5_value.name: self.data[p.ts5_value.name],
            p.ts5_name.name: self.data[p.ts5_name.name],
            p.ts6_value.name: self.data[p.ts6_value.name],
            p.ts6_name.name: self.data[p.ts6_name.name]}

        if jobid is not None:
            returnObj[p.jobid.name] = jobid
        return returnObj

    def getParameterStruct(self):
        p = self.props
        returnObj = {
            p.ts1_value.name: self.data[p.ts1_value.name],
            p.ts1_name.name: self.data[p.ts1_name.name],
            p.ts2_value.name: self.data[p.ts2_value.name],
            p.ts2_name.name: self.data[p.ts2_name.name],
            p.ts3_value.name: self.data[p.ts3_value.name],
            p.ts3_name.name: self.data[p.ts3_name.name],
            p.ts4_value.name: self.data[p.ts4_value.name],
            p.ts4_name.name: self.data[p.ts4_name.name],
            p.ts5_value.name: self.data[p.ts5_value.name],
            p.ts5_name.name: self.data[p.ts5_name.name],
            p.ts6_value.name: self.data[p.ts6_value.name],
            p.ts6_name.name: self.data[p.ts6_name.name]}
        return returnObj


class FieldMaps(object):

    def __init__(self, fieldMapData):
        self.data = fieldMapData
        self.props = constants.FieldmapProperties

    def getFieldMaps(self, jobid):
        fieldMapList = []
        for fieldMap in self.data:
            if fieldMap[self.props.jobid.name] == jobid:
                fieldMapList.append(FieldMap(fieldMap))
        return fieldMapList


class FieldMap(object):

    def __init__(self, fieldMapData):
        self.data = fieldMapData
        self.props = constants.FieldmapProperties

    def getRestoreStruct(self, jobid=None):
        p = self.props
        returnObj = {
            p.destColumnName.name: self.data[p.destColumnName.name],
            p.fmeColumnType.name: self.data[p.fmeColumnType.name],
            p.sourceColumnName.name: self.data[p.sourceColumnName.name],
            p.jobid.name: self.data[p.jobid.name]}
        if jobid is not None:
            returnObj[p.jobid.name] = jobid
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

