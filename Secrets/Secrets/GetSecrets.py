"""


About
=========
:synopsis:     Simply getting credentials for scripts / tools / applications
:moduleauthor: Kevin Netherton
:date:         11-25-2016
:description:  Scripts / Tools / Applications require things like:
                   - database user names
                   - instance names
                   - connection ports
                   - passwords
                   - rest api tokens
                   - rest api server urls
                   - etc...

               These parameters should not embedded into the code associated
               with the script.  When parameters like this are embedded it
               creates security concerns and makes sharing the code difficult.

               The goal of this module is to define a standardize data structure
               where these parameters can be stored.  The structure will then
               integrate with PMP allowing the retrieval of things like database
               passwords and rest api tokens from pmp... easily.

               How it works?

               The script will start off by checking to see if there is an environment
               variable called. APPLICATION_SECRETS. If environment variable exists
               then the script will retrieve the secrets json string from that
               environment variable.

               If the env varible APPLICATION_SECRETS does not exist then the script
               will search for a ../secrets/secrets.json file.  If this exists then
               the secrets are retrieved from this file.

               The structure of json is described in this post: (requires login)
               http://test.apps.bcgov/guide/intdocs/credential-management-for-scriptstoolsapplications/

               Once the structure is found it can be used to retrieve secrets and return
               them to the application using the method getApplicationsCredentials() which
               will return the same data structure only with passwords / tokens etc
               retrieved from pmp.


:Author: <who made the changes>
:Modification:
   - Describe here the changes that were made in bullet form.  Use
     a new dash charachter '-' to create a new entry!
:Date: <enter the date the changes were made>


API DOC:
===============
"""

import json
import logging
import os
import pprint
import sys
import warnings

import PMP.PMPRestConnect

# moduleName = os.path.basename(__file__)
# msg = '{0} module is deprecated.  Please use Secrets.GetSecrets module. '.format(moduleName)
# warnings.warn("this module is deprecated", DeprecationWarning,
#              stacklevel=2)


class AppConstants(object):
    secrets_dir = '../secrets'
    secrets_file = 'secrets.json'

    secrets_env_var = 'APPLICATION_SECRETS'

    # parameters used to confirm the structure of
    # of the secrets struct.
    #
    # the key with a list of parameters describing the individual
    # account credentials to retrieve
    accountListKey = 'secrets2get'
    # simple comment field, ignord, useful for describing things in the json file
    commentField = '__comment__'
    # multiaccount key
    multiAccountsKey = 'multiaccountsettings'
    # miscellaneous key value pairs go in this section
    # stuff like file paths, or other secrets that
    # do not fit anywhere else
    miscParams = 'miscParams'
    # required keys at the root level
    pmpTokenParam = 'pmptoken'
    pmpHostParam = 'pmphost'
    pmpRestDirectoryParam = 'pmprestapidir'
    structRequiredRootElems = [pmpTokenParam, pmpHostParam, pmpRestDirectoryParam]
    # optional keys at root level
    structOptionalRootElems = [multiAccountsKey, commentField, miscParams, accountListKey]
    # different account types
    accntTypeDB = 'db'
    accntTypeDBext = 'dbext'
    accntTypeRest = 'restapi'
    accountTypes = [accntTypeDB, accntTypeRest, accntTypeDBext]

    # list of all the keys used to contruct the
    # various structures
    key_userName = 'username'
    key_pmpResource = 'PMPResource'
    key_userTypeKey = 'accounttype'  # the key that will contain one of the account types above
    key_host = 'host'
    key_port = 'port'
    key_sdeport = 'sdeport'
    key_label = 'label'
    key_serviceName = 'servicename'

    # rest api account types required and optional keys
    restRequiredKeys = [key_label, key_host, key_pmpResource, key_userName, key_userTypeKey]
    restOptionalKeys = [commentField]

    # databc database account required and optional keys
    dbRequiredKeys = [key_label, key_userName, key_pmpResource, key_userTypeKey]
    dbOptionalKeys = [key_host, key_serviceName, key_port, commentField, key_sdeport]

    # non databc or external resources required and optional keys
    dbExtRequiredKeys = [key_label, key_userTypeKey, key_userName, key_serviceName, key_pmpResource]
    dbExtOptionalKeys = [key_userName, key_host, key_port, key_serviceName, key_pmpResource, key_sdeport, commentField]

    # multiaccountSettings, this is always equal to a list of dictionaries
    # these are the optional and required keys for the dictionary
    multiAccountRequiredKeys = [key_label, key_pmpResource, key_serviceName]
    multiAccountOptionalKeys = [key_host, key_port, key_sdeport, commentField]


class CredentialRetriever(object):
    '''
    This is the root class for secret retrieval.  Always start here,
    it will return a secret object from which you can get the following:

     - getMiscParams -> returns a misc param object
     - getSecretsByLabel -> return single account object
     - getMultiAccounts -> returns a multi account object

    '''

    def __init__(self, secretFileName=None):
        # modDotClass = '{0}.{1}'.format(__name__,self.__class__.__name__)
        modDotClass = __name__
        self.logger = logging.getLogger(modDotClass)
        self.secretFileName = secretFileName

        # env manager deals with getting the credentials automatically
        # from either a secrets file or the environment variable
        secretEnvManager = EnvironmentManager(self.secretFileName)
        # secret struct is the secrets from etiher the file or env var in a dictionary
        secretStruct = secretEnvManager.getSecretStruct()
        # now validating that the structure keys are correct, and building
        # a pmp object that can be used to retrieve passwords and rest api
        # tokens
        secrets = SecretParameters(secretStruct)
        secrets.verifyStructure()
        # SecretParameters
        self.secrets = secrets

    def getPmpRestConnect(self):
        '''
        tends not be called externally, instead is a internal call
        to create a pmpRestConnect object.  Actual rest calls to PMP
        are all made through this object.
        '''
        configDict = {}
        configDict['token'] = self.secrets.getPMPToken()
        configDict['baseurl'] = self.secrets.getPMPHost()
        configDict['restdir'] = self.secrets.getPMPRestApiDirectory()

        pmpObj = PMP.PMPRestConnect.PMP(configDict)
        return pmpObj

    def getSecrets(self):
        '''
        Will read the secrets file that describes the accounts
        in the section: Constants.accountListKey (defaults
        at the moment to the value:  secrets2get

        Having read that it then proceeds with retrieving all the
        secrets defined in that section.

        These secrets can also be retrieved on an on demand basis
        by using the method, getSecretsByLabel()
        '''
        pmpObj = self.getPmpRestConnect()
        accountDetails = self.secrets.getAccountDetails(pmpObj)

        accountDetails.populateAccountDetailSecrets()
        return accountDetails

    def getSingleLineJsonStruct(self):
        struct = self.secrets.getSecretStruct()
        secrtsSingleLine = json.dumps(struct)
        return secrtsSingleLine

    def getSecretsByLabel(self, label):
        '''
        Receives the name of a label in the single account section (secrets2get)
        of your secrets.json file.

        Returns an AccountParameters object.  You can then use the various
        methods of this object to retrieve the individual parameters
        '''
        pmpObj = self.getPmpRestConnect()
        accountDetails = self.secrets.getAccountDetails(pmpObj)
        # accountDetails is SecretAccountDetails
        # details = self.secretsStruct[self.const.accountListKey]

        # secretAccounts = SecretAccountDetails(details, pmpObj)
        # accnt is a AccountParameters object
        accnt = accountDetails.getAccountByLabel(label)
        accnt.getSecrets()
        return accnt

    def getMiscParams(self):
        '''
        returns an object that can be used to retireve misc
        params by name

        '''
        miscParam = MiscParams(self.secrets)
        return miscParam

    def getMultiAccounts(self):
        '''
        returns an object that can be used to retrieve multiple
        accounts by name
        '''
        pmpObj = self.getPmpRestConnect()
        multiParams = MultiParams(self.secrets, pmpObj)
        return multiParams


class SecretParameters(object):
    '''
    This class provides wrapper api around the secrets data structure
    that is retrieved from either the secrets file or from the secrets
    environment variable.

    Class will also verify the structure of the data that has been retrieved
    to determine that it fits with expected structure

    Exected structure described here:

       {  "pmptoken": "abcdef123xyz333ppuuc",
          "pmpserver":"somewhere.pmp.server.ca",
          "pmprestapidir":"/v1/pmp/something",
        "secrets2get" : [
       {  "usertype": "db",
          "username": "bill",
          "pmpresource": "resource"},
       {  "usertype": "dbext",
          "username": "ron",
          "instance": "ora.junk.net",
          "pmpresource": "resourceForExternals"},
       {  "usertype": "restapi",
          "server": "google.com",
          "returntype": "password",
          "pmpresource": "restapiresource"},
       {  "usertype": "restapi",
          "server": "oracle.com",
          "returntype": "token",
          "pmpresource": "restapiresource"},
       ]
        }
    '''

    def __init__(self, inputSecretsStruct):
        self.const = AppConstants()
        modDotClass = '{0}.{1}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(modDotClass)

        self.secretsStruct = inputSecretsStruct

    def getSecretStruct(self):
        return self.secretsStruct

    def verifyStructure(self):
        # TODO:  Would make sense to define a custom exception for these errors
        # Only require pmp tokens if the the secrets2get key exists or if
        # the multiaccountsettings exist
        if self.const.multiAccountsKey in self.secretsStruct or \
           self.const.accountListKey in self.secretsStruct:
            # start with root elements
            for rootKey in self.const.structRequiredRootElems:
                if not rootKey in self.secretsStruct:
                    msg = 'The required key: {0} could not be found in the secret struct {1}'
                    self.logger.error(msg)
                    raise ValueError, msg.format(rootKey, self.secretsStruct)

        # now check to see if keys exist that are not in required list and
        # not in the optional list
        allValidKeys = self.const.structOptionalRootElems[0:]
        allValidKeys.extend(self.const.structRequiredRootElems)
        for key in self.secretsStruct.keys():
            if not key in allValidKeys:
                msg = "found the invalid key: {0} at the root level. " + \
                      "valid keys include: {1}"
                raise ValueError, msg.format(key, ', '.join(allValidKeys))
        if self.const.accountListKey in self.secretsStruct:
            if not isinstance(self.secretsStruct[self.const.accountListKey], list):
                msg = 'Expecting the parameter {0} to be a list.  Its currently a {1}'
                accntListType = self.secretsStruct[self.const.accountListKey]
                raise ValueError, msg.format(self.const.accountListKey, type(accntListType))
            # There needs to be at least 1 account
            if len(self.secretsStruct[self.const.accountListKey]) == 0:
                msg = 'There are no accounts defined in the secrets structure ' + \
                      'under the key: {0}'
                raise ValueError, msg.format(self.const.accountListKey)
            for accountStruct in self.secretsStruct[self.const.accountListKey]:
                # verify the types
                # make sure it has a userTypeKey
                if not self.const.key_userTypeKey in accountStruct:
                    msg = 'The required key {0} does not exist in this user account struct {1}'
                    raise ValueError, msg.format(self.const.key_userTypeKey, accountStruct)
                if not accountStruct[self.const.key_userTypeKey] in self.const.accountTypes:
                    msg = 'encountered an invalid account type: {0}'
                    raise ValueError, msg.format(accountStruct[self.const.key_userTypeKey])
                # of its an internal database record
                if accountStruct[self.const.key_userTypeKey] == self.const.accntTypeDB:
                    # verify it has required parameters
                    for param2check in self.const.dbRequiredKeys:
                        if not param2check in accountStruct:
                            msg = 'databse user parameter missing required key {0}'
                            raise ValueError, msg.format(param2check)
                    # verify parameter all exist either in the required list
                    # or the optional list
                    validParams = self.const.dbOptionalKeys[0:]
                    validParams.extend(self.const.dbRequiredKeys)
                    for param in accountStruct.keys():
                        if not param in self.const.dbOptionalKeys and \
                           not param in self.const.dbRequiredKeys:
                            msg = 'you included the invalid parameter: {0} ' + \
                                  'parameter names must be one of the following {1}'
                            raise ValueError, msg.format(param, validParams)
                # if its an external database record
                elif accountStruct[self.const.key_userTypeKey] == self.const.accntTypeDBext:
                    # verify it has required parameters
                    for param2check in self.const.dbRequiredKeys:
                        if not param2check in accountStruct:
                            msg = 'external databse user parameter missing required key {0}'
                            raise ValueError, msg.format(param2check)
                    validParams = self.const.dbExtOptionalKeys[0:]
                    validParams.extend(self.const.dbExtRequiredKeys)
                    for param in accountStruct.keys():
                        if not param in validParams:
                            msg = 'you included the invalid parameter: {0} ' + \
                                  'parameter names must be one of the following {1}'
                            raise ValueError, msg.format(param, validParams)

                # if its a a rest api record
                elif accountStruct[self.const.key_userTypeKey] == self.const.accntTypeRest:
                    for param2check in self.const.restRequiredKeys:
                        if not param2check in accountStruct:
                            msg = 'restapi parameter description is missing the required key: {0}'
                            raise ValueError, msg.format(param2check)

                        validParams = self.const.restRequiredKeys[0:]
                        validParams.extend(self.const.restOptionalKeys)
                        for param in accountStruct.keys():
                            if not param in self.const.restOptionalKeys and \
                               not param in self.const.restRequiredKeys:
                                msg = 'you included the invalid parameter: {0} ' + \
                                      'parameter names must be one of the following {1}'
                                raise ValueError, msg.format(param, validParams)
                # its a record type that is not in the spec
                else:
                    msg = 'you specified a record type of {0}.  Valid types include {1}'
                    raise ValueError, msg.format(accountStruct[self.const.key_userTypeKey],
                                                 ', '.join(self.const.accountTypes))
        self.verfiyMultiAccountParams()

    def verfiyMultiAccountParams(self):
        '''
        Sometimes we need access to all the passwords in a
        resource, example all passwords in a resource in pmp that
        contains delivery passwords

        This struct is designed to accomodate that situation.

        example of such a struct:
         {"label" : "tst",
          "port"  : "port",
          "server" : "servername",
          "serviceName": "oracle service name",
          "pmpresource": "pmpresource"}
        '''
        if self.const.multiAccountsKey in self.secretsStruct:
            multiAccntList = self.secretsStruct[self.const.multiAccountsKey]
            cnter = 1
            for multiAccount in multiAccntList:
                for requiredParam in self.const.multiAccountRequiredKeys:
                    if not requiredParam in multiAccount:
                        msg = 'Multi account entry number: {0} does not contain the ' + \
                              'required parameter: {1}, entry is {2}'
                        raise ValueError, msg.format(cnter, requiredParam, multiAccount)
                validParamList = self.const.multiAccountRequiredKeys[0:]
                validParamList.extend(self.const.multiAccountOptionalKeys)

                for param in  multiAccount.keys():
                    if param not in validParamList:
                        msg = 'Multi account entry number {0} contains the key {1} ' + \
                              'This is not a valid entry.  Valid entries include {2}'
                        raise ValueError, msg.format(cnter, param, ', '.join(validParamList))
                cnter += 1

    def getPMPToken(self):
        token = self.secretsStruct[self.const.pmpTokenParam]
        return token

    def getPMPHost(self):
        host = self.secretsStruct[self.const.pmpHostParam]
        return host

    def getPMPRestApiDirectory(self):
        restDir = self.secretsStruct[self.const.pmpRestDirectoryParam]
        return restDir

    def getAccountDetails(self, pmp):
        details = self.secretsStruct[self.const.accountListKey]
        accountDetails = SecretAccountDetails(details, pmp)
        return accountDetails

    def getSingleAccountLabels(self):
        '''
        reads the secrets structure and returns the keys
        associated with the key secrets2get

        '''
        labels = []
        if self.const.accountListKey in self.secretsStruct:
            for singleAccountDict in self.secretsStruct[self.const.accountListKey]:
                singleLabel = singleAccountDict[self.const.key_label]
                labels.append(singleLabel)
        return labels

    def getMultiAccountLabels(self):
        labels = []
        if self.const.multiAccountsKey in self.secretsStruct:
            for singleAccountDict in self.secretsStruct[self.const.multiAccountsKey]:
                singleLabel = singleAccountDict[self.const.key_label]
                labels.append(singleLabel)
        return labels


class SecretAccountDetails(object):

    def __init__(self, detailsStruct, pmp):
        self.logger = logging.getLogger(__name__)

        self.pmp = pmp
        self.const = AppConstants()
        self.details = detailsStruct
        self.cnter = 0

    def __iter__(self):
        return self

    def next(self):
        self.logger.debug("details: {0}".format(self.details))
        self.logger.debug("self.const.accountListKey: {0}".format(self.const.accountListKey))

        if self.cnter >= len(self.details):
            self.cnter = 0
            raise StopIteration
        struct = self.details[self.cnter]
        accountParams = AccountParameters(struct, self.pmp)
        self.cnter += 1
        return accountParams

    def populateAccountDetailSecrets(self):
        for accnt in self:
            username = accnt.getUserName()
            accntType = accnt.getAccountType()
            msg = u'retrieving secrets for username: {0} type: {1}'
            msg = msg.format(username, accntType)
            self.logger.debug(msg)
            accnt.getSecrets()

    def getAccountByLabel(self, label):
        account2Return = None
        for accnt in self:
            if label == accnt.getLabel() or (accnt.getLabel()).upper() == label.upper():
                account2Return = accnt
                break
        if not account2Return:
            self.logger.debug(u"no accounts found with the label {0}".format(label))
        return account2Return


class AccountParameters(object):
    '''
    To make this easy instead of creating separate
    classes for each account type (each account type
    will have a different set of parameters that can
    be retrieved) will be using this generic class
    to retrieve parameters regardless of type.
    '''

    def __init__(self, struct, pmp):
        self.logger = logging.getLogger(__name__)

        self.pmp = pmp
        self.const = AppConstants()
        self.struct = struct
        self.secretDetails = None
        self.password = None

    def __getParam(self, param):
        retVal = None
        if param in self.struct:
            retVal = self.struct[param]
        return retVal

    def getUserName(self):
        return self.__getParam(self.const.key_userName)

    def getPMPResourceName(self):
        return self.__getParam(self.const.key_pmpResource)

    def getAccountType(self):
        return self.__getParam(self.const.key_userTypeKey)

    def getHost(self):
        return self.__getParam(self.const.key_host)

    def getAccountLabel(self):
        return self.__getParam(self.const.key_host)

    def getPort(self):
        return self.__getParam(self.const.key_port)

    def getSDEPort(self):
        return self.__getParam(self.const.key_sdeport)

    def getLabel(self):
        return self.__getParam(self.const.key_label)

    def getServiceName(self):
        return self.__getParam(self.const.key_serviceName)

    def getSecretDetails(self):
        if not self.secretDetails:
            username = self.getUserName()
            resource = self.getPMPResourceName()
            resourceId = self.pmp.getResourceId(resource)
            userId = self.pmp.getAccountId(username, resourceId)
            self.secretDetails = self.pmp.getAccountDetails(userId, resourceId)
            # pp = pprint.PrettyPrinter(indent=4)
            # pp.pprint(self.secretDetails)
            pass

    def getCustomField(self, customFieldName):
        retVal = None
        self.getSecretDetails()
        pmpConst = self.pmp.const
        for customFld in self.secretDetails[pmpConst.resourcekeys_operation][pmpConst.resourcekeys_Details][pmpConst.resourceKeys_customFields]:
            print 'customFld', customFld
            if customFld[pmpConst.resourceKeys_customFieldLabel] == customFieldName:
                retVal = customFld[pmpConst.resourceKeys_customFieldValue]
                break
        return retVal

    def getLoginID(self):
        '''
        Returns the PMP custom field named 'login id'
        '''
        pmpConst = self.pmp.const
        fldName = pmpConst.resourceKeys_customFieldValue
        return self.getCustomField(fldName)

    def getAPI(self):
        '''
        Returns the PMP custom field named 'API'
        '''
        pmpConst = self.pmp.const
        fldName = pmpConst.customFieldLblAPI
        return self.getCustomField(fldName)

    def getServerFromPMP(self):
        '''
        Returns the PMP custom field named 'Server'
        '''
        pmpConst = self.pmp.const
        fldName = pmpConst.customFieldLblServer
        return self.getCustomField(fldName)

    def getKeePassNotes(self):
        '''
        Returns the PMP custom field named 'KeePassNotes'
        '''
        pmpConst = self.pmp.const
        fldName = pmpConst.customFieldLblKeePassNotes
        return self.getCustomField(fldName)

    def getSecrets(self):
        accountType = self.getAccountType()
        if accountType == self.const.accntTypeDB:
            # get username and pmp resource then get password
            username = self.getUserName()
            resource = self.getPMPResourceName()
            password = self.pmp.getAccountPassword(username, resource)
            self.password = password
        elif accountType == self.const.accntTypeDBext:
            # external db
            # This will change once we move to external credential
            # consolidation
            username = self.getUserName()
            resourceName = self.getPMPResourceName()
            serviceName = self.getServiceName()
            host = self.getHost()

            if not '@' in username:
                if serviceName:
                    usernameAndServiceName = "{0}@{1}".format(username, serviceName)
            else:
                usernameAndServiceName = username
            self.getExtDBPassword(usernameAndServiceName, serviceName, resourceName)
        elif accountType == self.const.accntTypeRest:
            # TODO: need to complete how rest api accounts are retrieved
            username = self.getUserName()
            resource = self.getPMPResourceName()
            password = self.pmp.getAccountPassword(username, resource)
            self.password = password

    def getPassword(self):
        if not self.password:
            self.getSecrets()
        return self.password


class EnvironmentManager(object):
    '''
    Used to get the credential json string either from the environment variable
    or from the ../secrets/secrets.json file
    '''

    def __init__(self, secretFileName=None):
        modDotClass = '{0}'.format(__name__)
        self.logger = logging.getLogger(modDotClass)
        self.secretFileName = secretFileName
        self.const = AppConstants()
        self.secretsStruct = None

    def getSecretStruct(self):
        if not self.secretsStruct:
            self.loadSecrets()
        return self.secretsStruct

    def getPMPRestConnectStruct(self):
        self.getSecretStruct()
        pmpConst = PMP.PMPRestConnect.PMPConst()
        retDict = {}
        retDict[pmpConst.connectKey_token] = self.secretsStruct[self.const.pmpTokenParam]
        retDict[pmpConst.connectKey_baseurl] = self.secretsStruct[self.const.pmpHostParam]
        retDict[pmpConst.connectKey_restdir] = self.secretsStruct[self.const.pmpRestDirectoryParam]
        return retDict

    def loadSecrets(self):
        struct = None
        if self.const.secrets_env_var in os.environ:
            secretString = os.environ[self.const.secrets_env_var]
            # self.logger.debug('secretString[140:150]: {0}'.format(secretString[140:150]))
        # elif self.secretFileName
        else:
            if self.secretFileName:
                if not os.path.dirname(self.secretFileName):
                    self.secretFileName = os.path.join(os.path.dirname(__file__),
                                                       self.secretFileName)
                secretsFileFullPath = self.secretFileName
                self.logger.debug("secret file being used: {0}".format(secretsFileFullPath))
            else:
                secretsFileFullPath = os.path.join(self.const.secrets_dir,
                                                   self.const.secrets_file)
                self.logger.debug("secret file being used: {0}".format(secretsFileFullPath))
            if not os.path.exists(secretsFileFullPath):
                # test to see if we are in a package directory and if so back up one
                initFile = os.path.join(os.path.dirname(__file__), '__init__.py')
                if os.path.exists(initFile):
                    secretsFileFullPath = os.path.join('..',
                                                       self.const.secrets_dir,
                                                       self.const.secrets_file)
            if os.path.exists(secretsFileFullPath):
                secretFH = open(secretsFileFullPath, 'r')
                secretString = secretFH.read()
                secretFH.close()
            else:
                msg = 'Secrets cannot be found in either the environment variable {0} or ' + \
                      'in the secrets file {1}'
                raise ValueError, msg.format(self.const.secrets_env_var, secretsFileFullPath)
        struct = json.loads(secretString)
        self.secretsStruct = struct


class MultiParams(object):

    def __init__(self, secrets, pmp):
        self.const = AppConstants()

        modDotClass = '{0}.{1}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(modDotClass)

        struct = secrets.getSecretStruct()
        self.multiAccntStruct = struct[self.const.multiAccountsKey]
        self.pmp = pmp

    def getAccountPassword(self, multiAccntLabel, accountName, resource=[]):
        # get the struct that matches the requested multiAccntLabel

        # recently reconfigured secrets to allow you to specify either one or multiple
        # pmp resources where an account password is located.  To allow backward
        # compatibility I am checking to make sure that the resource is a list here
        # and if its not then make it a list
        if resource:
            if not isinstance(resource, list):
                resources = [resource]
            else:
                resources = resource
        else:
            # accntInfo = self.getAccountInfoByLabel(multiAccntLabel)
            resources = self.getPMPResources(multiAccntLabel)

        msg = 'resources to check for account: {0}'.format(resources)
        self.logger.debug(msg)
        # if not resource:
            # resource = accntInfo[self.const.key_pmpResource]
        for resource in resources:

            msg = "getting password for label: {0} accntName: {1} resName: {2}".format(multiAccntLabel, accountName, resource)
            self.logger.debug(msg)
            password = self.pmp.getAccountPassword(accountName, resource)
            if password:
                msg = "got the password for label: {0}, account {1}, pasword {2}"
                self.logger.debug(msg.format(multiAccntLabel, accountName, '*' * len(password)))
                break
        return password

    def getPMPResource(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        self.logger.debug('accnt, type {0}'.format(type(accnt[self.const.key_pmpResource])))
        if isinstance(accnt[self.const.key_pmpResource], list):
            retVal = accnt[self.const.key_pmpResource][0]
        else:
            retVal = accnt[self.const.key_pmpResource]
        return retVal

    def getPMPResources(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        self.logger.debug('accnt, type {0}'.format(type(accnt[self.const.key_pmpResource])))
        if not isinstance(accnt[self.const.key_pmpResource], list):
            retVal = [accnt[self.const.key_pmpResource]]
        else:
            retVal = accnt[self.const.key_pmpResource]
        return retVal

    def getHost(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        return accnt[self.const.key_host]

    def getPort(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        return accnt[self.const.key_port]

    def getSDEPort(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        return accnt[self.const.key_sdeport]

    def getServiceName(self, multiAccntLabel):
        accnt = self.getAccountInfoByLabel(multiAccntLabel)
        return accnt[self.const.key_serviceName]

    def getAccountInfoByLabel(self, label):
        retVal = None
        for accntInfo in self.multiAccntStruct:
            if label.upper() == accntInfo[self.const.key_label].upper():
                retVal = accntInfo
        return retVal


class MiscParams(object):

    def __init__(self, secretParams):
        self.const = AppConstants()
        secretsStruct = secretParams.getSecretStruct()
        self.struct = secretsStruct[self.const.miscParams]

    def getParam(self, label):
        retVal = None
        for structKey in self.struct.keys():
            if structKey.upper() == label.upper():
                retVal = self.struct[structKey]
                break
        return retVal
