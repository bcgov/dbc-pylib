'''
Created on Jun 29, 2018

@author: kjnether
'''

import KirkUtil.PyKirk
import KirkUtil.constants as constants
import pytest
import logging


def test_getJobs(KirkConnectInfo_openShift_dev):
    # KirkConnectInfo = KirkConnectInfo_local
    # makes assumption that data has already been loaded to the system
    KirkConnectInfo = KirkConnectInfo_openShift_dev
    logging.debug('KirkConnectInfo.url: %s', KirkConnectInfo.url)
    logging.debug('KirkConnectInfo.token: %s', KirkConnectInfo.token)
    if KirkConnectInfo.url is None or KirkConnectInfo.token is None:
        msg = 'unable to retrieve the kirk url/token used for testing'
        raise ValueError(msg)
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    jobList = kirkJobs.getJobs()
    logging.debug('jobList: %s', jobList)
    assert len(jobList) > 0
    assert jobList[0] in "jobid"


def test_addJobs(KirkConnectInfo):

    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    postResp = kirkJobs.postJobs(status='DELETE', cronStr='0 0 0 0 0',
                                 destEnv='DLV', jobLabel='testy123',
                                 schema='DUMMY', fcName='DUMBER')
    logging.debug('kirkJobs: %s', postResp)
    jobid = kirkJobs.getJobId('testy123')
    # jobid = postResp[KirkUtil.constants.JobProperties.jobid.name]
    # assert the job exists
    exists = kirkJobs.jobLabelExists('testy123')
    assert exists

    job = kirkJobs.getJob(jobid)
    logging.debug('fc is: %s',
                  job[KirkUtil.constants.JobProperties.destTableName.name])
    assert job[KirkUtil.constants.JobProperties.destTableName.name] == 'DUMBER'
    # now test the jobs field maps are null
    fldMap = kirkJobs.getJobFieldMaps(jobid)
    logging.debug('fldMap: %s', fldMap)
    assert not fldMap


def test_deleteJobs(KirkConnectInfo):
    '''
    creates a job and then deletes it
    '''
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    jobList = kirkJobs.getJobs()
    jobExists = False
    jobs2Del = []

    # check to see if the DELETE job exists
    for job in jobList:
        if job[constants.JobProperties.jobStatus.name] == 'DELETE':
            jobExists = True
            jobs2Del.append(job[constants.JobProperties.jobid.name])
        else:
            # DELETING ALL JOBS keep commented out unless you really
            # want to delete all job ids
            # jobs2Del.append(job['jobid'])
            pass

    # create the delete job if it doesn't exist
    if not jobExists:
        # create the job for deletion
        postResp = kirkJobs.postJobs(status='DELETE', cronStr='0 0 0 0 0',
                                     destEnv='DLV', jobLabel='deletemejob')
        jobList = kirkJobs.getJobs()
        for job in jobList:
            if job[constants.JobProperties.jobStatus.name] == 'DELETE':
                jobExists = True
                jobs2Del.append(job[constants.JobProperties.jobid.name])

    for job2Del in jobs2Del:
        # now delete the job
        logging.debug("deleting the job: %s", job2Del)
        kirkJobs.deleteJob(job2Del)
    # now assert that the job doesnt exist
    exists = kirkJobs.jobExists('jobid', job2Del)
    assert not exists


def test_jobExists(KirkConnectInfo):
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    jobs = kirkJobs.getJobs()
    maxJobId = 0
    for job in jobs:
        logging.debug('job: %s', job)
        jobid = job['jobid']
        jobExists = kirkJobs.jobIdExists(jobid)
        # calculate the max job id so that at the end we can increment by
        # one then verify that the job doesn't exist
        if jobid > maxJobId:
            maxJobId = jobid
        assert jobExists
    maxJobId = maxJobId + 1
    jobExists = kirkJobs.jobIdExists(maxJobId)
    assert not jobExists


def test_getSources(KirkConnectInfo):
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkSources = kirk.getSources()
    sources = kirkSources.getSources()
    logging.info("kirk sources: %s", sources)
    assert len(sources) > 0

    # verify the record returned complies with the schema defined in
    # the constants
    # assert
    for enum in constants.SourceProperties:
        assert enum.name in sources[0]


def test_postSources(KirkConnectInfo):
    # create the job
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    kirkSources = kirk.getSources()
    jobLbl = 'testy123'
    if not kirkJobs.jobLabelExists(jobLbl):
        postResp = kirkJobs.postJobs(status='DELETE', cronStr='0 0 0 0 0',
                                     destEnv='DLV', jobLabel=jobLbl,
                                     schema='DUMBSCHEMA', fcName='DUMBFCNAME')
    jobId = kirkJobs.getJobId(jobLbl)
    sourceTable = 'junk'
    sourceDataSet = r'c:\tmp\somepath\myfgdb.fgdb'
    srcInfo = kirkSources.postFileSources(jobId, sourceTable, sourceDataSet)
    logging.debug("srcInfo: %s", srcInfo)
    srcExists = kirkSources.sourceFGDBTableExists(sourceTable, sourceDataSet)
    assert srcExists

    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    sources = kirkJobs.getJobSources(jobId)
    logging.debug("testing the source end point off the jobs: %s", sources)
    assert sources[0][constants.SourceProperties.sourceFilePath.name] == sourceDataSet

    kirkJobs.deleteJob(jobId)
    kirkSources.deleteSource(srcInfo[constants.SourceProperties.sourceid.name])


def test_sourceExists(KirkConnectInfo):
    # test data set
    tableName = 'DGTL_ROAD_ATLAS_DFAR_SP'
    jobLbl = 'DELETE_DRA_DFAR_test'

    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    kirkJobs = kirk.getJobs()
    kirkSources = kirk.getSources()

    # setup, make sure the job exists
    if not kirkJobs.jobLabelExists(jobLbl):
        postResp = kirkJobs.postJobs(status='DELETE', cronStr='0 0 0 0 0',
                                     destEnv='DLV', jobLabel=jobLbl,
                                     schema='DUMBSCHEMA', fcName='DUMBFCNAME')

    jobId = kirkJobs.getJobId(jobLbl)
    # make sure the source exists
    srcInfo = kirkSources.postFileSources(jobId, tableName, tableName)

    # verify that exists works
    srcExists = kirkSources.sourceFGDBTableExists(tableName, tableName)
    logging.info("testing for the source: %s", tableName)
    assert srcExists

    # now cleanup
    # delete the source
    srcs2Del = kirkSources.getJobSources(jobId)
    for src in srcs2Del:
        kirkSources.deleteSource(src[constants.SourceProperties.sourceid.name])

    # now delete the job
    kirkJobs.deleteJob(jobId)

# def test_deleteAllSources(KirkConnectInfo):
#     # just created for housekeeping during debugging, make sure stays
#     # commented out
#     kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
#     kirkSources = kirk.getSources()
#     allSources = kirkSources.getSources()
#     sourceProps = constants.SourceProperties
#
#     for src in allSources:
#         logging.debug("removing the source: %s", src[sourceProps.sourceid.name])
#         kirkSources.deleteSource(src[sourceProps.sourceid.name])


def test_fieldmaps(KirkConnectInfo):
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    fldmaps = kirk.getFieldMaps()
    fldMaps = fldmaps.getFieldMaps()
    logging.debug('fldMaps: %s', fldMaps)

# DON'T RUN unless you want to delete all the field maps
# def test_deleteAllFieldmaps(KirkConnectInfo):
#     kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
#     fldmaps = kirk.getFieldMaps()
#     fldMaps = fldmaps.getFieldMaps()
#     # logging.debug('fldMaps: %s', fldMaps)
#     for fldmap in fldMaps:
#         fldmaps.deleteFieldMap(fldmap[constants.FieldmapProperties.fieldMapId.name], cancelUpdate=True)


def test_addFieldMap(KirkConnectInfo):
    kirk = KirkUtil.PyKirk.Kirk(KirkConnectInfo.url, KirkConnectInfo.token)
    fldmaps = kirk.getFieldMaps()
    kirkJobs = kirk.getJobs()
    # create dummy job if it doesnt exist
    if not kirkJobs.jobLabelExists('deletemejob'):
        postResp = kirkJobs.postJobs(status='DELETE', cronStr='0 0 0 0 0', 
                                     destEnv='DLV', jobLabel='deletemejob',
                                     schema='TESTSCHEMA', fcName='TESTFCNAME')

    # get the job id
    jobid = kirkJobs.getJobId('deletemejob')

    # now create the fieldmap
    sourceColumnName = 'dummy1'
    destColumnName = 'dummy2'
    if not fldmaps.fieldMapExists(jobid, sourceColumnName, destColumnName):
        fldmaps.postFieldMaps(jobid, sourceColumnName, destColumnName)

    # verify it exists
    fldExists = fldmaps.fieldMapExists(jobid, sourceColumnName, destColumnName)
    assert fldExists

    # now delete
    fldMapId = fldmaps.getFieldMapId(jobid, sourceColumnName, destColumnName)
    fldmaps.deleteFieldMap(fldMapId)

    fldExists = fldmaps.fieldMapExists(jobid, sourceColumnName, destColumnName)
    assert not fldExists

    # cleanup
    kirkJobs.deleteJob(jobid)


def test_getTransformers(PyKirk_addedJob_Fixture):
    kirk = PyKirk_addedJob_Fixture[0]
    jobDesc = PyKirk_addedJob_Fixture[1]

    # try adding a counter
    kirkJobs = kirk.getJobs()
    kirkJobId = kirkJobs.getJobId(jobDesc['label'])
    transformers = kirkJobs.getJobTransformers(kirkJobId)
    msg = 'transformers are: {0}'.format(transformers)
    logging.debug(msg)

    # get all the transformers
    trans = kirk.getTransformers()
    transObjs = trans.getTransformers()
    msg = 'transformers are: {0}'.format(transObjs)
    logging.debug(msg)

    transCols = KirkUtil.constants.CounterTransformerMap
    coreAtribs = KirkUtil.constants.TransformerCoreAttributes
    # ---------------------------------
    # now try adding a transformer
    # ---------------------------------
    transformerDescr = {coreAtribs.jobid.name: kirkJobId,
                        coreAtribs.transformer_type.name: KirkUtil.constants.TransformerTypes.counter.name}
    params = {transCols.counterStartNumber.name: '1',
              transCols.counterScope.name: 'global'}
    if not trans.existsTransformer(jobid=transformerDescr['jobid'],
                                   transformerType=transformerDescr[coreAtribs.transformer_type.name],
                                   parameters=params):
        logging.debug("the transformer does not exist adding it")
        trans.postTransformer(jobid=transformerDescr['jobid'],
                              transformerType=transformerDescr[coreAtribs.transformer_type.name],
                              parameters=params)

    # ---------------------------------
    # testing that the existence method works
    # ---------------------------------
    existsTransformer = \
        trans.existsTransformer(jobid=transformerDescr['jobid'],
                                transformerType=transformerDescr[coreAtribs.transformer_type.name],
                                parameters=params)
    assert existsTransformer == True

    # ---------------------------------
    # testing that the existence method for job/transformer works
    # this one works off the jobs end point
    # ---------------------------------
    existsTransformer = kirkJobs.jobTransformerExists(transformerDescr['jobid'], KirkUtil.constants.TransformerTypes.counter.name, params)
    assert existsTransformer == True

    logging.debug("the transfomrer exists")
    # ---------------------------------
    # test the get transformer id from kirk
    # ---------------------------------
    transId = trans.getTransformerId(jobid=transformerDescr['jobid'],
                          transformerType=transformerDescr[coreAtribs.transformer_type.name],
                          parameters=params)
    logging.debug("transformer id is: %s", transId)
    # delete the transformer
    logging.debug("deleting the transformer id: %s", transId)
    trans.deleteTransformer(transId)
    while trans.existsTransformer(jobid=transformerDescr['jobid'],
                                  transformerType=transformerDescr['transformer_type'],  # @IgnorePep8
                                  parameters=params):
        transId = trans.getTransformerId(
            jobid=transformerDescr['jobid'],
            transformerType=transformerDescr['transformer_type'],
            parameters=params)
        trans.deleteTransformer(transId)
    existsTransformer = \
        trans.existsTransformer(
            jobid=transformerDescr['jobid'],
            transformerType=transformerDescr['transformer_type'],
            parameters=params)
    assert existsTransformer is False

