# Interacting with Password Manager Pro Using Python.

*This next section shows you how you can read the published parameters of a script in FME server, from the published parameters infer the*
*destination schema, then query PMP to retrieve the password for that schema, finally calling the job with the credentials.  This is portrayed*
*just as an example.  All of the production processes / automations now use the Secrets package to identify and retrieve secrets used by a *
*particular process.*

Like FME Server in order to interact with PMP you must have a PMP token.  Token's are not provided in this document for obvious security purposes.   
PMP tokens are specific to host.  In other words if you are developing code on one server, and then deploying on another you will require two different PMP security tokens.
What follows are some examples showing you how you can interact with PMP using the PMP.PMPRestConnect.py module.

## Overview of PMP

Ok before we get to the code its useful to have a bit of an idea as to how the PMP api is structured.  The following link describes the PMP Rest api which is what is wrapped by this python code.

[https://www.manageengine.com/products/passwordmanagerpro/help/restapi.html](https://www.manageengine.com/products/passwordmanagerpro/help/restapi.html)

In short PMP starts with a "Resource".  Resources keep track of "Accounts".  Database Schemas and accounts are the same thing.  Finally passwords are stored in accounts.  

The PMP rest api typically wants to use numeric ids to refer to "Resources", "Accounts", but people want to use the "name".  So if you know the resource name and the account / schema name, before you can request the password you will need to retrieve the ids for the "Resource" and the "Account". 

The python api attempts to hide this from you.  The functionality is still there but you probably won't need it.

## Importing the Module

Like the FME Server code, the pmp module is a package in the DataBC python library.  To use download and set up the PYTHONPATH or install to a virtualenv.

## Creating a PMP Object

To create a PMP object you call the PMP class constructor with a PMP configuration Dictionary.  The dictionary requires the following keys:
* token - the security token used to allow access to PMP
* baseurl - the url to the PMP application
* restdir - the path to the v1 pmp rest api.

Typically the dictionary looks something like this. (Please note the token used here will not work)

```
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
               'baseurl': 'pmp.server.name',
               'restdir': r'/directory/topmp/apidir/'}
```

And putting it all together into a functional example:

```
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
               'baseurl': 'pmp.server.name',
               'restdir': r'/directory/topmp/apidir/'}
pmp = PMP.PMPRestConnect.PMP(pmpConfDict)
```

## Getting a list of the PMP Resources available:

```
# importing modules
import PMP.PMPRestConnect
import pprint

# the configuration dictionary
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
                'baseurl': 'pmp.server.name',
                'restdir': r'/get/the/pmpdir/'}

# creating a pmp object
pmp = PMP.PMPRestConnect.PMP(pmpConfDict)

# getting a resources data structure
resources = pmp.getResources()

# pretty printing it.
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(resources)
```

## Getting a list of the Accounts for a Resource:

```
import PMP.PMPRestConnect
import pprint

rsrcNm = 'DA-IDWTEST1-WHSE'
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
               'baseurl': 'pmp.server.name',
               'restdir': r'/dir/to/restapi/'}

pmp = PMP.PMPRestConnect.PMP(pmpConfDict)

# getting the accounts for the resource 'FME_SERVER_NAME'
accnts = pmp.getAccounts(rsrcNm)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(accnts)
```

## Getting a password for Resource / Account.

```
import PMP.PMPRestConnect
rsrcNm = 'PMP_REPO_NAME'
schema = 'ORACLE_SCHEMA_NAME'
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
               'baseurl': 'pmp.server.name',
               'restdir': r'/dir/to/restapi/'}

pmp = PMP.PMPRestConnect.PMP(pmpConfDict)
pswd = pmp.getAccountPassword(schema, rsrcNm)
print 'password for {0} in DELIVERY is {1}'.format(schema, pswd)
```

# Putting it all together

## Example 1:

This example will:
* Create an FME Server object
* Create a PMP Object
* Define a FME Server Repo Name
* Define a FME workspace in the repo
* Get the default published parameters for the FME Workspace
* Extract the User_ID from the published parameters and retrieve the password for this schema in IDWTEST1
* Override the default parameters for the values Dest_Instance_Connect, Dest_Server, Dest_Password so the script will run on IDWTEST1
* Runs the script synchronously
* Retrieve the job id and use it to retrieve the log and print the log to STDOUT.

```
import PMP.PMPRestConnect
import pprint
import FMEUtil.PyFMEServerV2
pmpResource = 'PMP_RESOURCE_NAME'
jobName = r'illuminatiCauzedTsunamis.fmw'

repoName = 'NAME_OF_REPOOSITORY'
server = r'http://fmeserver.server.name' # server
token = r'd8239sdf3fsGoHabsdhsdfkll23llknnfc63823' # token, not the real one

# Create the fme server object
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)

# Get an fme server repository object
repo = fmeSrv.getRepository()

# from the repository object get the workspace
wrkspcs = repo.getWorkspaces(repoName)

# from the workspace get the published parameters
pubPrms = wrkspcs.getPublishedParams(jobName)

# restructure the published parameter values in a dictionary 
# where the parameter name is the key and the parameter value is 
# the corresponding value.
paramDict = {}
for param in pubPrms:
    paramDict[param['name']] = param['defaultValue']

# the destination schema is in the parameter User_ID
# retrieving it and passing it to pmp to get the Oracle instance name
# password for it

# Creating the pmp config dictionary
pmpConfDict = {'token':'0BA2313A-MOn-TreaL-CanA-Iens23121-1',
               'baseurl': 'pmpserver.name.com',
               'restdir': r'/pmp/restdir/directory/name/'}

# creating a pmp object
pmp = PMP.PMPRestConnect.PMP(pmpConfDict)

# getting the password for test from PMP for the account
pswd = pmp.getAccountPassword(paramDict['User_ID'], pmpResource)

# now change the Dest_Server / Dest_Instance_Connect / Dest_Password to
# point to test in the restructured published parameter dictionary
paramDict['Dest_Instance_Connect'] = 'port:<enterporthere>'
paramDict['Dest_Server'] = 'database.server.name'
paramDict['Dest_Password'] = pswd

# and now run the job with the published parameters
jobs = fmeSrv.getJobs()
results = jobs.submitJobSync(repoName, jobName, paramDict)

# and from the result object get the job id, and use this
# to retrieve and print the log.
logs = fmeSrv.getLogs()
log = logs.getLog(results['id'])
logTxt = log.getLog()
print 'The log is:'
print logTxt
```
