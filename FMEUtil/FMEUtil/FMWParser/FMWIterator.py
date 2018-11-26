'''
Created on Aug 9, 2018

@author: kjnether

Frequently when testing FMW's on one platform or another we need the ability to 
iterate over all the FMW's in our FME Server repository.  In the past i've
built this into each script, thinking that having a re-usable iterator could
save a bunch of time.

'''
import datetime
import FMEUtil.PyFMEServerV2 as FMEServer
import DBCSecrets.GetSecrets
import logging
import time
import os
import json

class Constants(object):  # pylint: disable=too-few-public-methods
    pass

class FMEIterator(object):
    '''
    This class implements the iterator interface allowing easy
    iteration of the various workspaces in FME Server.
    '''
    def __init__(self, repositoryName, fmeKey, skipList=None, secretsFile=None):
            # LOG CONFIG
        self.const = Constants()
        
        self.logger = logging.getLogger(__name__)
        
        if skipList:
            self.skipList = []
            for skipFmw in skipList:
                self.skipList.append(skipFmw.lower())
        else:
            self.skipList = []
            
        # retrieving the credentials
        creds = DBCSecrets.GetSecrets.CredentialRetriever(secretsFile)
        self.logger.debug("secret key is: {0}".format(fmeKey))
        srcFMECreds = creds.getSecretsByLabel(fmeKey)
        hostName = srcFMECreds.getHost()
        self.logger.debug("host: {0}".format(hostName))
        fMEUrl = 'http://{0}'.format(hostName)
        fMEToken = srcFMECreds.getAPI()
        self.logger.debug("fMEUrl: {0}".format(fMEUrl))
        self.fme = FMEServer.FMEServer(fMEUrl, fMEToken)

        # make sure that the repository name provided is a valid
        # one.
        repo = self.fme.getRepository()
        repoNames = repo.getRepositoryNames()
        if repositoryName not in repoNames:
            msg = 'You specified an repository of: {0}.  This repo does not ' + \
                  'exist.  Valid repo\'s include: {1}'
            msg = msg.format(repositoryName, repoNames)
            raise ValueError, msg
        self.repositoryName = repositoryName
        self.workspaces = None
        self.curWorkspaceIdx = None
        self.numWorkspaces = None
        self.workspaceNames = None

    def __iter__(self):  # pylint: disable=invalid-name
        '''
        Implementing the python iteraable interface.
        More info:
        https://stackoverflow.com/questions/19151/build-a-basic-python-iterator
        '''
        return self

    def getWorkspaces(self):
        '''
        Gets the list workspace names for the current
        repository.
        '''
        repo = self.fme.getRepository()
        workspaces = repo.getWorkspaces(self.repositoryName)
        self.workspaces = workspaces.getWorkspaces()
        self.curWorkspaceIdx = 0
        self.workspaceNames = self.workspaces.keys()
        self.workspaceNames.sort()

    def next(self):
        '''
        Returns a workspace structure, describing the current
        workspace, includes the following properties:
         * description
         * lastSaveDate
         * name
         * title
         * type
        '''
        if self.workspaces is None:
            self.getWorkspaces()
        if self.curWorkspaceIdx >= len(self.workspaceNames):
            raise StopIteration
        workspaceName = self.workspaceNames[self.curWorkspaceIdx]
        curWorkspace = Workspace(self.fme, self.repositoryName, workspaceName)
        self.curWorkspaceIdx += 1
        if workspaceName.lower() in self.skipList:
            curWorkspace = self.next()
        return curWorkspace

class Workspace(object):
    '''
    used to wrap required functionality of individual
    workspaces, for example easy ability to run with
    a keyword with
    '''

    def __init__(self, fme, repo, workspaceName):
        self.logger = logging.getLogger(__name__)
        self.repositoryName = repo
        self.workspaceName = workspaceName
        self.fme = fme
        self.const = Constants()

    def __str__(self):
        '''
        return the object as a string!
        '''
        return '{0} {1}'.format(self.repositoryName, self.workspaceName)

    def getPubParms(self, reformat=True):
        '''
        Retrieves the published params for this (self) workspace
        '''
        repo = self.fme.getRepository()
        workspaces = repo.getWorkspaces(self.repositoryName)
        print self
        pubParams = workspaces.getPublishedParams(self.workspaceName, reformat)
        return pubParams

    def hasDestDbEnvKey(self, ne=None, eq=None):
        '''
        :param ne: allows you to specify a parameter that the dest db env key should
                   not be equal to
        :param eq: means the value has to be equal to return true
        '''
        retVal = False
        pubParams = self.getPubParms()
        print 'pubParams', pubParams
        for paramName in pubParams:
            paramValue = pubParams[paramName]
            if paramName.upper() == 'DEST_DB_ENV_KEY':
                self.logger.debug("paramValue: %s", paramValue)
                if isinstance(paramValue, list):
                    # making sure if the DEST_DB_ENV_KEY is a list that it only
                    # has 1 value
                    if len(paramValue) <> 1:
                        msg = 'the parameter %s is defined as a list and has ' + \
                              '%s values associated with it.  It should only ' + \
                              'have 1 value associated with it as it defines ' + \
                              'the destination for the script!'
                        self.logger.error(msg, paramName.upper(), len(paramValue))
                        raise ValueError, msg % paramName.upper(), len(paramValue)
                    else:
                        paramValue = paramValue[0]
                retVal = True
                if ne:
                    retVal = False
                    if paramValue.upper() <> ne.upper():
                        retVal = True
                if eq:
                    retVal = False
                    if paramValue.upper() == eq.upper():
                        retVal = True
        return retVal

    def run(self):
        '''
        Does the actual running of the script associated with this workspace object

        - checks to see if the workspace has already been run by checking the status
          dir.
        - if not then runs and collects the api's return value from the run event
          and caches that information with the status file
        '''
        # need to get the parameters
        self.logger.info("running the replication %s %s", self.repositoryName,
                         self.workspaceName)
        pubParams = self.getPubParms()
        status = Status(self.const.runEnv, self.repositoryName, self.workspaceName)
        if not status.hasRun():
            fileName = status.getStatusFileName()
            self.logger.info("status file: %s", fileName)
            jobs = self.fme.getJobs()
            if self.const.runEnvParam not in pubParams:
                msg = 'The fme workspace {0} in the repository: {1} does not ' + \
                      'have the parameter {2} defined for it.  Existing params ' + \
                      'include: {3}'
                msg = msg.format(self.workspaceName, self.repositoryName,
                                 self.const.runEnvParam,
                                 pubParams.keys())
                raise ValueError, msg
            if isinstance(pubParams[self.const.runEnvParam], list):
                pubParams[self.const.runEnvParam] = [self.const.runEnv]
            else:
                pubParams[self.const.runEnvParam] = self.const.runEnv
            try:
                retVal = None
                retVal = jobs.submitJob(self.repositoryName, self.workspaceName,
                                        params=pubParams, sync=True)
                self.logger.debug("job status: %s", retVal['status'])
            except Exception as e:
                self.logger.error("Problem with the script: %s (error: %s)",
                                  self.workspaceName, e.message)
            if retVal:
                # pp = pprint.PrettyPrinter(indent=4)
                # pp.pprint(retVal)
                status.setCompleted(retVal)
        else:
            self.logger.info("Job has already been run %s %s", self.repositoryName,
                             self.workspaceName)

    def runAndMonitor(self):
        '''
        Does the same thing as the run script but should be more reliable.  Seems like
        with the old version when it issues the build and waits the network connection
        between the job and the caller seems to get severed after a period of time.

        This approach will send the job as an async call, retrieving the jobid, then
        goes into a loop until the job completes, at which time it will retrieve the
        job metadata.
        '''
        self.logger.info("running the replication %s %s", self.repositoryName,
                         self.workspaceName)
        pubParams = self.getPubParms()

        # creates a status object, this is used to set the job as having run as well
        # as ability to determine if the job has been run.
        status = Status(self.const.runEnv, self.repositoryName, self.workspaceName)
        if not status.hasRun():
            fileName = status.getStatusFileName()
            self.logger.info("status file: %s", fileName)
            jobs = self.fme.getJobs()
            if self.const.runEnvParam not in pubParams:
                msg = 'The fme workspace {0} in the repository: {1} does not ' + \
                      'have the parameter {2} defined for it.  Existing params ' + \
                      'include: {3}'
                msg = msg.format(self.workspaceName, self.repositoryName,
                                 self.const.runEnvParam,
                                 pubParams.keys())
                raise ValueError, msg
            # making sure the destenv is set to DLV
            if isinstance(pubParams[self.const.runEnvParam], list):
                pubParams[self.const.runEnvParam] = [self.const.runEnv]
            else:
                pubParams[self.const.runEnvParam] = self.const.runEnv
            # disable change detection so job runs for sure!
            if 'FILE_CHANGE_DETECTION' in pubParams:
                pubParams['FILE_CHANGE_DETECTION'] = 'FALSE'
            
            try:
                retVal = None
                jobIdStruct = jobs.submitJob(self.repositoryName, self.workspaceName,
                                             params=pubParams, sync=False)
                self.logger.debug("jobIdStruct: %s", jobIdStruct)
                jobId = jobIdStruct['id']
                self.logger.debug("job id: %s", jobId)
                retVal = self.monitorAndWait(jobId)
                self.logger.debug("job description: %s", retVal)
                self.logger.info("job status: %s", retVal['status'])
            except Exception as e:
                #self.logger.error("Problem with the script: %s ERROR: %s",
                #                  self.workspaceName, e.message )
                self.logger.exception("Problem with the script: %s ERROR: %s",
                                  self.workspaceName, e.message)
                # raise
            if retVal:
                # pp = pprint.PrettyPrinter(indent=4)
                # pp.pprint(retVal)
                status.setCompleted(retVal)
        else:
            self.logger.info("Job has already been run %s %s",
                             self.repositoryName, self.workspaceName)

    def monitorAndWait(self, jobId):
        '''
        :param jobId: the job numerical id that the script is going to monitor
        support method for runAndMonitor, this method will recieve a job id, it
        will then enter into a 15 second polling interval until the job reports
        that it has completed.
        '''
        sleepInterval = 15
        sleepPeriod = 15
        # possible status values
        #  ['SUBMITTED', 'QUEUED', 'ABORTED', 'SUCCESS', 'FME_FAILURE',
        #   'JOB_FAILURE' or 'PULLED']: Job success, failure, or other status,
        # using this list as indication that processing is complete
        completedList = ['ABORTED', 'SUCCESS', 'FME_FAILURE', 'JOB_FAILURE']
        cnt = 0
        while True:
            self.logger.debug("getting jobs object")
            jobs = self.fme.getJobs()
            job = jobs.getJob(jobId)
            status = job.getJobStatus()
            if status.upper() in completedList:
                self.logger.debug("job status is %s, breaking monitor  loop", status)
                break
            if cnt > 5:
                # assuming that if its taken 2.5 minutes to run that its a longer running
                # job and so we are turning the wait interval up
                sleepPeriod = sleepPeriod + sleepInterval
                self.logger.debug("adjusting the polling interval to: %s", sleepPeriod)
            self.logger.debug("waiting and will repoll job...")
            time.sleep(sleepPeriod)
            cnt += 1
        return job.getJob()


class Status(object):
    '''
    Class used to determine whether a specific job has already
    been run.
    '''

    def __init__(self, env, repoName, fmw):
        self.const = Constants()
        self.repoName = repoName
        self.fmw = fmw
        curRunStatusDir = 'RunAsync2_{0}'.format(env)
        statusDir = os.path.join(os.path.dirname(__file__),
                                 '..',
                                 self.const.statusDir)
        if not os.path.exists(statusDir):
            os.mkdir(statusDir)
        self.statusDir = os.path.join(statusDir, curRunStatusDir)
        self.statusDir = os.path.normpath(self.statusDir)
        if not os.path.exists(self.statusDir):
            os.mkdir(self.statusDir)

    def getStatusFileName(self):
        '''
        :return: returns the status file name that is used for the information that
                 was defined in the constructor of this object.
        '''
        statusFile = "{0}___{1}.txt".format(self.repoName, self.fmw)
        statusFilePath = os.path.join(self.statusDir,
                                      statusFile)
        return statusFilePath

    def hasRun(self):
        '''
        :return: boolean value indicating whether the script has been run already
        '''
        statusFilePath = self.getStatusFileName()
        retVal = False
        if os.path.exists(statusFilePath):
            retVal = True
        return retVal

    def setCompleted(self, returnStruct=None):
        '''
        :param returnStruct: The output from the api call.  if nothing is sent
                             the status file will get created but it will not
                             have any data in it.
        Receives the status from the api call, and writes the output as a json
        string to the status file.
        '''
        statusFilePath = self.getStatusFileName()
        if not os.path.exists(statusFilePath):
            fh = open(statusFilePath, 'w')
            if returnStruct:
                json.dump(returnStruct, fh)
            fh.close()


