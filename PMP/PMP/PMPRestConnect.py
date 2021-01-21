'''
Created on Sep 2, 2014

@author: kjnether

playing around for now trying to figure out if I can connect
to the PMP rest interface from python
'''
import logging
import os.path
import urlparse

import requests


class PMPConst(object):
    '''
    Class used to store application / properties / enumerations.
    '''
    tokenKey = 'AUTHTOKEN'

    resourcekeys_operation = 'operation'
    resourcekeys_Details = 'Details'
    resourceKeys_resourceName = 'RESOURCE NAME'
    resourceKeys_resourceID = 'RESOURCE ID'
    resourceKeys_accountList = 'ACCOUNT LIST'
    resourceKeys_accountName = 'ACCOUNT NAME'
    resourceKeys_accountID = 'ACCOUNT ID'
    resourceKeys_customFields = 'CUSTOM FIELD'
    resourceKeys_customFieldName = 'CUSTOMFIELDCOLUMNNAME'
    resourceKeys_customFieldValue = 'CUSTOMFIELDVALUE'
    resourceKeys_customFieldLabel = 'CUSTOMFIELDLABEL'
    resourceKeys_description = 'DESCRIPTION'
    resourceKeys_password = 'PASSWORD'

    connectKey_token = 'token'
    connectKey_baseurl = 'baseurl'
    connectKey_restdir = 'restdir'

    # server custom field name, these are possible values
    # that can exist in the column resourceKeys_customFieldLabel
    customFieldLblServer = 'Server'
    customFieldLblLoginId = 'Login ID'
    customFieldLblKeePassNotes = 'KeePassNotes'
    customFieldLblAPI = 'API'

    # external database parameters
    usernameDelimiter = '@'
    dbParamsDelimiter = ':'


class PMP(object):
    '''
    This class provides a simple python api that will
    interface with the pmp rest api.  It interacts with
    the rest api allowing for the retrieval of accounts
    and then passwords assocated with those accounts.
    '''

    def __init__(self, configDict):
        self.logger = logging.getLogger(__name__)
        self.const = PMPConst()
        self.token = configDict[self.const.connectKey_token]
        self.baseUrl = configDict[self.const.connectKey_baseurl]
        self.restDir = configDict[self.const.connectKey_restdir]
        # make sure the last character on the rest dir is /
        if self.restDir[-1] != '/':
            self.restDir = self.restDir + '/'
        self.logger.debug("self.restDir: %s", self.restDir)
        self.logger.debug("last char in rest dir: %s", self.restDir[-1])

    def getTokenDict(self):
        '''
        :return: the token dictionary used to connect to pmp
        '''
        tokenDict = {self.const.tokenKey: self.token}
        return tokenDict

    def getResources(self):
        '''
        :return: the resources that are available to the token that you used to
                 get access to pmp.
        '''
        url = 'https://' + self.baseUrl + self.restDir + 'resources'
        self.logger.debug("PMP resource url:" + url)
        tokenDict = self.getTokenDict()

        r = requests.get(url, params=tokenDict, verify=False)
        if r.status_code >= 400 and r.status_code < 600:
            # stop
            msg = "unsuccessful connection status code: %s", r.status_code
            self.logger.error(msg)
            raise PMPCommunicationProblem(msg)

        resources = r.json()
        resourcObjects = None
        resOpKey = self.const.resourcekeys_operation
        resDets = self.const.resourcekeys_Details

        if (resOpKey in resources) and resDets in resources[resOpKey]:

            resourcObjects = resources[resOpKey][resDets]
            # self.logger.debug("returned resource objects: " + \
            # str(resourcObjects))
        else:
            msg = 'unable to read resources from PMP. Probably a token ' + \
                  'problems!  PMP message {0}'
            msg = msg.format(resources)
            self.logger.error(msg)
            raise PMPCommunicationProblem(msg)
        return resourcObjects

    def getResourceId(self, resourceName):
        '''
        pmp organizes everything by numeric ids. This method takes a
        resource name and retrieves the corresponding resource id from pmp.

        :param resourceName: The name of the resource who's id you want to
                             retrieve.
        :return: the resource id corresponding to the
                 resourceName
        '''
        resourceId = None
        self.logger.debug("getting the resource id for the resource name:" +
                          str(resourceName))
        resources = self.getResources()
        iterResourceNames = []
        for resource in resources:
            iterResourceName = resource[self.const.resourceKeys_resourceName]
            iterResourceNames.append(iterResourceName)
            if resource[self.const.resourceKeys_resourceName].upper() == \
               resourceName.upper():
                resourceId = resource[self.const.resourceKeys_resourceID]
                break
        self.logger.debug("resource id for (" + str(resourceName) + ') is (' +
                          str(resourceId) + ')')
        if not resourceId:
            msg = 'Unable to find the resource: {0}.  Resources that are ' + \
                  'currently visible: {1}'
            msg = msg.format(resourceName, ', '.join(iterResourceNames))
            self.logger.error(msg)
            raise ResourceNotFound(msg)
        return resourceId

    def getAccounts(self, resourceName):
        '''
        Given a resource name, the method will retrieve the resource id
        for the resource name.  It will then query that resource for a
        list of all the accounts, and will return a list of dictionaries
        with information about those accounts.

        Each element in the returned list will contain the following keys:
            PASSWORD STATUS
            ACCOUNT ID - This is the value that we want to retrieve to query
                         the account for the actual password.
            PASSWDID
            ISREASONREQUIRED
            ISFAVPASS
            ACCOUNT NAME    - This is the text value with the actual account
                              name.
            AUTOLOGONLIST
            AUTOLOGONSTATUS

        This is an example of the raw data returned by the query to the
        rest end point before the account information is extracted
                {u'operation':
            {u'Details':
                {u'RESOURCE ID': u'3453',
                 u'RESOURCE NAME': u'SOMERES',
                 u'DNS NAME': u'urlinthegov.bcgov',
                 u'RESOURCE TYPE': u'Database Computer',
                 u'RESOURCE URL': u'',
                 u'PASSWORD POLICY': u'a_polcy',
                 u'LOCATION': u'',
                 u'RESOURCE DESCRIPTION': u'passwordDescript',
                 u'RESOURCE OWNER': u'IDIR\\someUser',
                 u'DEPARTMENT': u'',
                 u'ACCOUNT LIST': [
        - struct indented here

        {u'PASSWORD STATUS': u'****',
         u'ACCOUNT ID': u'12375',
         u'PASSWDID': u'12375',
         u'ISREASONREQUIRED': u'false',
         u'ISFAVPASS': u'false',
         u'ACCOUNT NAME': u'app_pmp',
         u'AUTOLOGONLIST': [],
         u'AUTOLOGONSTATUS':
         u'User is not allowed to automatically logging in to remote systems in mobile'},  # @IgnorePep8
        {u'PASSWORD STATUS': u'****', u'ACCOUNT ID': u'123',
        u'PASSWDID': u'123', u'ISREASONREQUIRED': u'false',
         u'ISFAVPASS': u'false', u'ACCOUNT NAME': u'AnAccountName',
          u'AUTOLOGONLIST': [],
         u'AUTOLOGONSTATUS': u'dont let this user login from apple device'},
        {u'PASSWORD STATUS': u'****', u'ACCOUNT ID': u'124',
        u'PASSWDID': u'166', u'ISREASONREQUIRED': u'false',
         u'ISFAVPASS': u'false', u'ACCOUNT NAME': u'AnAcocountName',
         u'AUTOLOGONLIST': [],
         u'AUTOLOGONSTATUS':
         u'User is not allowed to automatically logging in to remote systems in mobile'}  # @IgnorePep8
         ...

        '''
        self.logger.debug("resourceName is: %s", resourceName)
        resId = self.getResourceId(resourceName)
        accnts = self.getAccountsForResourceID(resId)
        self.logger.debug("retrieved %s accounts for the resource %s",
                          resId, len(accnts))
        return accnts

    def getAccountsForResourceID(self, resId):
        '''
        Given a resource id will return the accounts
        for that resource id.

        structure returned is a list of dictionaries, example :
        [   {   u'ACCOUNT ID': u'123',
                u'ACCOUNT NAME': u'someaccnt@server',
                u'AUTOLOGONLIST': [u'something'],
                u'AUTOLOGONSTATUS': u'text text text ...',
                u'ISFAVPASS': u'false',
                u'ISREASONREQUIRED': u'false',
                u'IS_TICKETID_REQD': u'false',
                u'IS_TICKETID_REQD_ACW': u'false',
                u'IS_TICKETID_REQD_MANDATORY': u'false',
                u'PASSWDID': u'2454',
                u'PASSWORD STATUS': u'****'},
                ...
        ]
        '''
        url = 'https://' + self.baseUrl + self.restDir + \
              'resources' + '/' + str(resId) + '/accounts'
        tokenDict = self.getTokenDict()
        self.logger.debug("using the url: %s", url)
        r = requests.get(url, params=tokenDict, verify=False)
        accnts = r.json()

        opKey = self.const.resourcekeys_operation
        dets = self.const.resourcekeys_Details
        accntList = self.const.resourceKeys_accountList
        justAccnts = accnts[opKey][dets][accntList]
        return justAccnts

    def getAccountId(self, accntName, resourceId):
        '''
        :param accntName: The account name in pmp
        :param resourceId: The numeric resource id to look for the account in
        :return: the numeric id for the given account name
        '''
        accntId = None

        accnts = self.getAccountsForResourceID(resourceId)
        self.logger.debug("accounts retrieved for resource id (%s): %s",
                          resourceId, len(accnts))
        for accnt in accnts:
            if accnt[self.const.resourceKeys_accountName].lower().strip() == \
               accntName.lower().strip():
                accntId = accnt[self.const.resourceKeys_accountID]
                break
        self.logger.debug("Account id for the account name (" +
                          "(" + str(accntName) + ") is (" + str(accntId) + ')')
        if not accntId:
            msg = 'unable to find an account with the name: {0} in the ' + \
                  'resource id {1}'
            msg = msg.format(accntName, resourceId)
            self.logger.warning(msg)
        return accntId

    def getAccountPassword(self, accntName, resourceName):
        '''
        Given an account name will do a search for the
        account.  The account search will not consider
        case. (upper or lower)
        '''
        resId = self.getResourceId(resourceName)
        if not resId:
            msg = 'Unable to retrieve a resource id in pmp for the resource ' + \
                  'name {0} using the token {1}'
            msg = msg.format(resourceName, self.token)
            self.logger.error(msg)
            raise ValueError(msg)
        self.logger.debug("getting account ids")
        accntId = self.getAccountId(accntName, resId)
        psswd = None
        if accntId:
            try:
                psswd = self.getAccountPasswordWithAccountId(accntId, resId)
            except ValueError:
                msg = 'PMP response for the resource ({0}) and account ({1}) was {2}. ' + \
                      'which indicates the token used ({3}) does not have permissions to ' + \
                      'access this password'
                msg = msg.format(resourceName, accntName, psswd, self.token)
                self.logger.error(msg)
                raise ValueError(msg)
        else:
            msg = 'unable to find the account: {0} in the resource: {1}'
            msg = msg.format(accntName, resourceName)
            self.logger.debug(msg)
        return psswd

    def getPasswordFiles(self, accntName, resourceName):
        '''
        Some pmp accounts contain files, example ssh keys etc.  This method
        will download the files in those resources.

        :param accntName: The name of the account that contains the secret file
        :param resourceName: The resource in pmp to search for the resource

        :return: a string with the contents of the file that was requested
        '''
        resId = self.getResourceId(resourceName)
        if not resId:
            msg = 'Unable to retrieve a secret / password file using the resource name: ' + \
                  ' {0}. Returned resource id {1} using the token {2}'
            msg = msg.format(resourceName, resId, self.token)
            self.logger.error(msg)
            raise ValueError(msg)
        accntId = self.getAccountId(accntName, resId)
        if not accntId:
            msg = 'unable to find the account: {0} in the resource: {1}'
            msg = msg.format(accntName, resourceName)
        msg = 'Found the resource {0} and the account {1}'
        msg = msg.format(resourceName, accntName)
        self.logger.debug(msg)
        urlTemplate = 'https://{0}{1}/resources/{2}/accounts/{3}/downloadfile'
        url = urlTemplate.format(self.baseUrl, self.restDir, resId, accntId)

        tokenDict = self.getTokenDict()
        self.logger.debug("url used to get password %s", url)
        r = requests.get(url, params=tokenDict, verify=False)
        retVal = r.text
        return retVal

    def getAccountDetails(self, accntId, resourceId):
        '''
        :param accntId: The account id who's details you want to retrieve
        :param resourceId: The resource id for the resource that the account is
                            located inside of
        :return: a python data structure with the details of the account.
        '''
        url = 'https://' + self.baseUrl + self.restDir + \
              'resources/' + str(resourceId) + '/accounts/' + \
              str(accntId)
        tokenDict = self.getTokenDict()
        self.logger.debug('url: %s', url)
        r = requests.get(url, params=tokenDict, verify=False)
        self.logger.debug("status_code: %s", r.status_code)
        accntDtls = r.json()
        self.logger.debug("response: %s", accntDtls)
        return accntDtls

    def getRestAPIPassword(self, accountName, apiUrl, resourceName):
        '''
        Currently we have a resource in pmp that stores rest api usernames
        and passwords.  The standard for storing them is to store the username
        as the account name.  The path to the rest service then gets stored
        in the "Account Notes".  When passwords are stored in this way this
        method should be able to retrieve them.

        How it works:
          a) accountName received if it includes @http://rest.api...
             the account name and the url are separated
          b) retrieves the accounts for the resourceName
          c) iterates through each account, if the account name includes
             a url it is separated from the username
              - bare usernames are compared for a match, ie just the user
                name supplied as an arg and just the user name in the iteration
                of accounts for the resourceName
              - if usernames match then retrieve the url from the
                  "Account Notes"
                if the url matches the received apiUrl then get the password
                and return it for that account.
              - if the the "account notes" url does not match and there was a
                url appended to the end of the username example:
                user@http://blah
                then that url is compared with the supplied url.
                if they match then get th password.

              - if neither of the url's match then raises and error saying
                there is no account for the username url combination

        :param  accountName: The name account name who's password we want
        :type accountName: str

        :param  apiUrl: The url to the rest api that corresponds with the
                        username.
        :type apiUrl: str

        :param  resourceName: The name of the resource in pmp who's password
                              we are trying to retrieve.
        :type resourceName: str
        '''
        self.logger.debug("params are %s, %s, %s", accountName,
                          apiUrl, resourceName)

        parsed_uri = urlparse.urlparse(apiUrl)
        apiUrl = parsed_uri.netloc
        self.logger.debug("apiUrl: %s", apiUrl)

        # checking to see if the syntax for the account is
        # username@url or if it is just username
        #   example 'apiuser'
        #   or can come as 'apiuser@https://blah.com/blah/blah/blah'
        if '@' in accountName:
            justUser, apiUrlfromAccntName = accountName.split('@')
            # only comparing the domain right now
            parsed_uri = urlparse.urlparse(apiUrlfromAccntName)
            apiUrlfromAccntName = parsed_uri.netloc
            self.logger.debug("apiUrlfromAccntName: %s", apiUrlfromAccntName)
        else:
            justUser = accountName
            apiUrlfromAccntName = None

        # a get the resource id
        resId = self.getResourceId(resourceName)

        # now get all the accounts for that resource using a heuristic
        # to search for the userName.
        # start by getting all the accounts for the userid
        accnts = self.getAccountsForResourceID(resId)
        accntsRetrieved = []
        # will be where the extracted account name is stored assuming it is
        # found
        extractedAccntId = None
        self.logger.debug("found (%s) accounts in the resource", len(accnts))
        for accnt in accnts:
            # splitting up the received account name and url in case
            # the version stored in pmp is username@url
            self.logger.debug("current Account name: %s, searching for: %s",
                              accnt[self.const.resourceKeys_accountName],
                              justUser)
            accntsRetrieved.append(accnt[self.const.resourceKeys_accountName])
            if '@' in accnt[self.const.resourceKeys_accountName]:
                currAccntName, currAccntUrl = \
                    accnt[self.const.resourceKeys_accountName].split('@')
                parsed_uri = urlparse.urlparse(currAccntUrl)
                currAccntUrl = parsed_uri.netloc
                self.logger.debug("currAccntUrl: %s", currAccntUrl)
            else:
                currAccntName = accnt[self.const.resourceKeys_accountName]
                currAccntUrl = None
            currAccntId = accnt[self.const.resourceKeys_accountID]
            self.logger.debug("account id: %s", currAccntId)
            # if the usernames match, next we want to check if the
            # urls matches
            if currAccntName.lower() == justUser.lower():
                # get the details for the account and pull the url
                # from the details field
                details = self.getAccountDetails(currAccntId, resId)
                server = self.getServerColumn(details)

                parsed_uri = urlparse.urlparse(server)
                urlFromDetails = parsed_uri.netloc
                self.logger.debug("Server from Details: %s", urlFromDetails)

                # now if the urlFromDetails matches apiUrl provided as an arg
                # then assume this is the account
                if urlFromDetails.lower().strip() == apiUrl.lower().strip():
                    extractedAccntId = currAccntId
                    break

                # otherwise check to see if the url in the account name in
                # pmp matches the url sent as an arg
                elif currAccntUrl:
                    if apiUrl.lower().strip() == currAccntUrl.lower().strip():
                        extractedAccntId = currAccntId
                        break
        if not extractedAccntId:
            self.logger.debug("account name: %s", accountName)
            msg = 'unable to find an account that matches the account name:' + \
                  ' {0} and the resource name {1}, accounts that are ' + \
                  'visible: {2}'
            msg = msg.format(accountName, resourceName,
                             ', '.join(accntsRetrieved))
            self.logger.error(msg)
            raise AccountNotFound(msg)

        return self.getAccountPasswordWithAccountId(extractedAccntId, resId)

    def getServerColumn(self, struct):
        '''
        Takes the structure returned by a getAccountDetails() method call
        parses and returns the contents of the custom column 'Server'

        example of a struct expected data structure.

        {u'operation': {u'Details': {
            u'PASSWORD STATUS': u'****',
            u'LAST ACCESSED TIME': u'Nov 21, 2005 01:24 PM',
            u'DESCRIPTION': u'',
            u'EXPIRY STATUS': u'Valid',
            u'COMPLIANT REASON': u'Password must have mixed case alphabets',
            u'PASSWORD POLICY': u'APIs',
            u'LAST MODIFIED TIME': u'N/A',
            u'COMPLIANT STATUS': u'Non-Compliant',
            u'CUSTOM FIELD': [{
                u'CUSTOMFIELDTYPE': u'Character',
                u'CUSTOMFIELDCOLUMNNAME': u'COLUMN_CHAR3',
                u'CUSTOMFIELDVALUE': u'',
                u'CUSTOMFIELDLABEL': u'API',
                }, {
                u'CUSTOMFIELDTYPE': u'Character',
                u'CUSTOMFIELDCOLUMNNAME': u'COLUMN_CHAR4',
                u'CUSTOMFIELDVALUE': u'https://google.com/googlerestapi',
                u'CUSTOMFIELDLABEL': u'Server',
                }, {
                u'CUSTOMFIELDTYPE': u'Character',
                u'CUSTOMFIELDCOLUMNNAME': u'COLUMN_CHAR1',
                u'CUSTOMFIELDVALUE': u'',
                u'CUSTOMFIELDLABEL': u'Login ID',
                }, {
                u'CUSTOMFIELDTYPE': u'Character',
                u'CUSTOMFIELDCOLUMNNAME': u'COLUMN_CHAR2',
                u'CUSTOMFIELDVALUE': u'',
                u'CUSTOMFIELDLABEL': u'billsnotes',
                }],
            u'PASSWDID': u'1234',
            }, u'name': u'GET RESOURCE ACCOUNT DETAILS',
                u'result': {u'status': u'Success',
                            u'message': u'Account details fetched successfully'}}}  # @IgnorePep8


        '''
        server = self.getCustomFieldLabel(struct,
                                          self.const.customFieldLblServer)
        return server

    def getCustomFieldLabel(self, struct, labelName2Get):
        '''
        PMP has a set of standard fields.  This method will search the pmp
        entry for a specific custom field, and if it exists then returns
        the value associated with it.  If it doesn't then just returns
        null
        :param struct: The python data structure that should be searched to
                       find the custom parameter in.
        :param labelName2Get: the label or name of the custom property that
                              is to be extracted.
        '''
        retVal = None
        if self.const.resourcekeys_operation in struct:
            operation = struct[self.const.resourcekeys_operation]
            if self.const.resourcekeys_Details in operation:
                details = operation[self.const.resourcekeys_Details]
                if self.const.resourceKeys_customFields in details:
                    customFields = \
                        details[self.const.resourceKeys_customFields]
                    for fld in customFields:
                        fldLabel = \
                            fld[self.const.resourceKeys_customFieldLabel]
                        if fldLabel.lower() == labelName2Get.lower():
                            retVal = \
                                fld[self.const.resourceKeys_customFieldValue]
                            break
        if not retVal:
            msg = 'Unable to find the custom field label: %s'
            self.logger.warning(msg, labelName2Get)
        return retVal

    def getDetailsColumn(self, struct):
        '''
        This will return the contents of the details column parsed out
        of the structure returned by a getAccountDetails() returned
        structure.
        :param struct: the data structure returned by the getAccountDetails()
                       method
        :type struct: dictionary
        :return: Returns the contents of the "description" column from the
                 struct that is sent
        :rtype: str
        '''
        details = None
        opkey = self.const.resourcekeys_operation
        reskey = self.const.resourcekeys_Details
        resdesc = self.const.resourceKeys_description
        if ((self.const.resourcekeys_operation in struct) and
            reskey in struct[opkey]) and \
                resdesc in struct[opkey][reskey]:
            # leaving this here in case the logic above was translated
            # incorrectly
            # if ((struct.has_key(self.const.resourcekeys_operation)) and \
            #      struct[opkey].has_key(reskey)) and \
            #      struct[opkey][reskey].has_key(resdesc):

            urlFromDetails = struct[opkey][reskey][resdesc]
            self.logger.debug("url details: %s", urlFromDetails)

            parsed_uri = urlparse.urlparse(urlFromDetails)
            details = parsed_uri.netloc
            self.logger.debug("urlFromDetails: %s", details)
        return details

    def getAccountPasswordWithAccountId(self, accntId, resourceId):
        '''
        Given a PMP account id, and resource id, this method will extract the
        password from PMP.
        :param accntId: The account id (numeric) for the password to be
                        retrieved
        :param resourceId: the resource id (numeric) for the password that
                           is to be retrieved
        '''
        url = 'https://' + self.baseUrl + self.restDir + \
              'resources/' + str(resourceId) + '/accounts/' + \
              str(accntId) + '/password'
        tokenDict = self.getTokenDict()
        self.logger.debug("url used to get password %s", url)
        r = requests.get(url, params=tokenDict, verify=False)
        passwdStruct = r.json()
        opKey = self.const.resourcekeys_operation
        detKey = self.const.resourcekeys_Details
        pssedKey = self.const.resourceKeys_password
        psswd = passwdStruct[opKey][detKey][pssedKey]

        if psswd.upper() == '[Request]'.upper():
            msg = 'PMP response for the resource ID ({0}) and account ID ' + \
                  '({1}) was {2}. which indicates the token used ({3}) ' + \
                  'does not have permissions to access this password'
            msg = msg.format(resourceId, accntId, psswd, self.token)
            self.logger.error(msg)
            raise ValueError(msg)
        return psswd

    def getExtDBPassword(self, accountName, serviceName, resourceName):
        '''
        accounts for passwords for external databases need to be
        entered as username@service_name in order for them to be
        unique.

        long term plan is to consolidate the 4 external database
        password resources into a single resource.  Once that happens
        parameters will come from:
          - login name
          - server
        Until that happens we are using the username or account name
        and parsing out the server portion.
        '''
        password = None
        # get accounts for the resourceName
        resId = self.getResourceId(resourceName)
        accntList = self.getAccountsForResourceID(resId)
        accntid = None
        for accntDict in accntList:
            if accntDict['ACCOUNT NAME'] == accountName or \
              accntDict['ACCOUNT NAME'].upper() == accountName.upper():
                accntid = accntDict['ACCOUNT ID']
                break
            else:
                # if no exact match then will check for
                # a match after removing the domains.  example
                # idwprod1.bcgov becomes just idwprod1
                accntTemplateStr = '{0}@{1}'
                if '@' in accntDict['ACCOUNT NAME']:
                    iterAccntName = accntDict['ACCOUNT NAME']
                    iterAccnt, server = accntDict['ACCOUNT NAME'].split('@')
                    server = server.strip()
                    stringList = server.split('.')
                    server = stringList[0].strip()
                    iterAccntName = accntTemplateStr.format(iterAccnt, server)

                    # parse kevin@something.com to
                    # kevin@something
                    curAccnt, server = accountName.split('@')
                    server = server.strip()
                    stringList = server.split('.')
                    server = stringList[0].strip()
                    curAccnt = accntTemplateStr.format(curAccnt, server)
                    if (curAccnt == iterAccntName or
                      curAccnt.upper() == iterAccntName.upper()):  # @IgnorePep8
                        accntid = accntDict['ACCOUNT ID']
                        break
        if accntid:
            # now get the password for the account id
            password = self.getAccountPasswordWithAccountId(accntid, resId)
        return password


class ExternalAccountName(object):
    '''
    This class includes methods that can be used to parse the
    account names that are stored in the external database
    resource where the account name SHOULD contain

    username@serviceName:host:port

    '''

    def __init__(self, pmpExternalAccountName):
        self.logger = logging.getLogger(__name__)
        self.pmpAccntName = pmpExternalAccountName
        self.const = PMPConst()
        self.host = None
        self.serviceName = None
        self.port = None
        self.username = None
        self.sqlServer = False

    def parseAccountName(self):
        '''
        Takes an external database account format and parses out the various \
        pieces of information stored in it.
        '''
        if not self.username:
            if self.const.usernameDelimiter not in self.pmpAccntName:
                msg = 'the account name delimiter "{0}" was not found in ' + \
                      'the account name: {1}, unable to parse out other ' + \
                      'parameters like servicename, host, and port'
                msg = msg.format(self.const.usernameDelimiter,
                                 self.pmpAccntName)
                self.logger.warning(msg)
            else:
                self.username, remainderStr = \
                    self.pmpAccntName.split(self.const.usernameDelimiter)
                remainderList = remainderStr.split(
                    self.const.dbParamsDelimiter)
                self.logger.debug('username: %s', self.username)
                self.logger.debug('remainderList: %s', remainderList)
                # SQLSERVER:ssdbname:dbhost.com:1005 DATABCREPLICATION
                if len(remainderList) == 4:
                    if remainderList[0].lower() == 'sqlserver':
                        self.sqlServer = True
                        self.host = remainderList[2]
                        self.port = remainderList[3]
                        self.serviceName = remainderList[1]
                # ssdbname:dbhost:1005 DATABCREPLICATION
                elif len(remainderList) == 3:
                    self.host = remainderList[1]
                    self.port = remainderList[2]
                    self.serviceName = remainderList[0]

    def getHost(self):
        '''
        Returns the host for this pmp record
        '''
        self.parseAccountName()
        return self.host

    def isSqlServer(self):
        '''
        Identifies if this pmp record corresponds with a description for
        a sql server record
        '''
        self.parseAccountName()
        return self.sqlServer

    def getServiceName(self):
        '''
        Returns the server name described in this pmp record
        '''
        self.parseAccountName()
        return self.serviceName

    def getServiceNameNoDomain(self):
        ''' strips off any domain info that may
        exist on the service name and returns just the service
        name
        '''
        sn = self.getServiceName()
        snNoDomain = self.stripDomain(sn)
        return snNoDomain

    def stripDomain(self, param):
        '''
        takes a parameter and strips out all domain related inforation,
        example if you sent 'myserver.gov.bc.ca' to this method it would
        return 'myserver'
        '''
        paramList = param.split('.')
        self.logger.debug("removing domain from %s, returning %s",
                          param, paramList[0])
        return paramList[0]

    def getUserName(self):
        '''
        Extracts the username defined in this pmp record
        '''
        self.parseAccountName()
        return self.username

    def getPort(self):
        '''
        Extracts the port that should be used when connecting to the database
        defined in this object.
        '''
        self.parseAccountName()
        return self.port


class AccountNotFound(Exception):
    '''
    Adding new error types for when Accounts are not found in a specified
    repository
    '''

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class ResourceNotFound(Exception):
    '''
    Adding a new error type for when a Resource is not found
    '''

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class PMPCommunicationProblem(Exception):
    '''
    Adding a new error type for when a Resource is not found
    '''

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
