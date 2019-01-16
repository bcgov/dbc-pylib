'''
Created on Oct 29, 2018

@author: kjnether
'''
from __future__ import unicode_literals

import logging
from . import constants as KirkEnvConst
import DBCSecrets.GetSecrets
import KirkUtil.PyKirk
import os.path
import json
import warnings

JOBS_FILE = 'jobs.json'
FIELDMAPS_FILE = 'fieldmaps.json'
DESTINATIONS_FILE = 'destinations.json'
SOURCES_FILE = 'sources.json'
TRANSFORMERS_FILE = 'transformers.json'

msg = "Unverified HTTPS request is being made. Adding certificate verifi" + \
      "cation is strongly advised. See: https://urllib3.readthedocs.io/e" + \
      "n/latest/advanced-usage.html#ssl-warnings"
warnings.filterwarnings("ignore", message=msg)


class Backup(object):

    def __init__(self, backupDirectory, kirkEnv='dev', kirkSecretLabel=None):
        self.logger = logging.getLogger(__name__)

        # getting credentials necessary to communicate with kirk
        # - get secret label
        if kirkSecretLabel:
            secretLabel = kirkSecretLabel
        else:
            secretLabel = KirkEnvConst.KIRKENV[kirkEnv.upper()]

        if kirkEnv.upper() not in KirkEnvConst.KIRKENV:
            msg = 'you specified and invalid kirk env string ({0}). ' + \
                  'allowed values are: {1}'
            msg = msg.format(kirkEnv, KirkEnvConst.KIRKENV.keys())
            self.logger.error(msg)
            raise ValueError(msg)

        self.backupDirectory = backupDirectory
        if not os.path.exists(self.backupDirectory):
            os.mkdir(self.backupDirectory)

        secrets = DBCSecrets.GetSecrets.CredentialRetriever()
        kirkAccnt = secrets.getSecretsByLabel(secretLabel)
        kirkHost = kirkAccnt.getHost()
        kirkToken = kirkAccnt.getAPI()
        kirkUrl = 'https://{0}'.format(kirkHost)
        self.logger.debug('kirk baseurl: {0}'.format(kirkUrl))
        self.kirk = KirkUtil.PyKirk.Kirk(kirkUrl, kirkToken)

    def backupAll(self):
        '''
        will backup all the end points that make up the api
        '''
        self.backupJobs()
        self.backupFieldMaps()
        self.backupDestinations()
        self.backupSources()
        self.backupTransformers()

    def backupJobs(self):
        '''
        creates a backup of the jobs
        '''
        jobs = self.kirk.getJobs()
        jobStruct = jobs.getJobs()
        # now dump to file.
        dumpFile = os.path.join(self.backupDirectory, JOBS_FILE)
        self.struct2JsonFile(jobStruct, dumpFile)

    def struct2JsonFile(self, struct, dumpFile):
        if os.path.exists(dumpFile):
            self.logger.debug("removing the file: %s", dumpFile)
            os.remove(dumpFile)
        with open(dumpFile, 'w') as fp:
            self.logger.info("creating the dump file %s", dumpFile)
            json.dump(struct, fp, indent=2)

    def backupFieldMaps(self):
        fieldmaps = self.kirk.getFieldMaps()
        fieldMapsStruct = fieldmaps.getFieldMaps()
        fieldMapsFile = os.path.join(self.backupDirectory, FIELDMAPS_FILE)

        self.struct2JsonFile(fieldMapsStruct, fieldMapsFile)

    def backupDestinations(self):
        '''
        dumps the destinations to a json file
        '''
        destinations = self.kirk.getDestinations()
        destStruct = destinations.getDestinations()
        destFile = os.path.join(self.backupDirectory, DESTINATIONS_FILE)
        self.struct2JsonFile(destStruct, destFile)

    def backupSources(self):
        '''
        backs up the sources to a json file
        '''
        srcMaps = self.kirk.getSources()
        srcStruct = srcMaps.getSources()
        srcsFile = os.path.join(self.backupDirectory, SOURCES_FILE)
        self.struct2JsonFile(srcStruct, srcsFile)

    def backupTransformers(self):
        '''
        backup the transformer parameters
        '''
        transMap = self.kirk.getTransformers()
        transStruct = transMap.getTransformers()
        transFile = os.path.join(self.backupDirectory, TRANSFORMERS_FILE)
        self.struct2JsonFile(transStruct, transFile)


# if __name__ == '__main__':
#     env = 'dev'
#     backupDirForTesting = os.path.join(os.path.dirname(__file__), '..', 'data', 'kirk_backup_testing')
#     backup = Backup(backupDirForTesting, env)
#     backup.backupAll()
