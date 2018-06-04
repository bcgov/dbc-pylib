# Interacting with FME Server using Python

<img src="https://lh3.googleusercontent.com/UwGUu2-fwqkEuGiup-VTs1yD2ZEgP-imuX6g37-BUfQc7Q4yzngPw5Xfw2RhP-kqzUYwnvqfHyzHbDecpw2BNp3icC7ak4HU24ogXe3RBVmDrGBenQ_ehH0nkmv5BHYxlK1t5CwcMj75LR-m1ttC6w0OelvuilSGvN0aB_Pso3Tqvj99hWC7IIuswiA4JJqAI8wrnOPc-Abbds2B5IXe8wQOQV1tx0yGHReuUsm8Hl6fsMb2-oowGxjDiukZ8V8DaP_J2oznxXZaBvkVJnis-o9KNIj_iV0DMh8ScAOZsVwEt2SHrvuQQto49ogOIA8SCo58I2IwCJIyLsDQrgcz7MXUu7noJiMjD9j38bCY_JQUZhAFCfMeiAJhCRl7SGL27iKmQbu3PooqPMMTWhnJTjMroff1mfH3n9i2Iow-ZyVGcWcjklPwQCcaTeo8aqUWlbmkwHDbIAzrPBfgs8uPT1YuAmFOKrgBOJHBHavptaSWLFcntevvhcw-FeHhwexNsiASEXTTKMGKKgv5e1LxDaU_Ic13P6efAisOmuJOg37zEXb-KqyjWQKuD1o_EQgKt7Kj03j1EKFrVxoL740pm_JL2I8Yj91jvdLElPeVxoA3yEpRPYXIsmouTAJlTPrSrgSFjMUkysY5j0cKIHOymrZcoSTBX9A58g=w1252-h704-no" width="600"/>


## Importing the Module:

The FME Server Python Module is part of the DataBCPyLib which is located in this repository in the FMEUtil package:

To install this package put the following line in your requirements.txt:
<add line>


And then install the requirements using pip 
`pip install -r requirements.txt`


## Connecting with FME Server

### Get Token

Before you can interact with FME Server you need to know the server host name, and also have a security token. 

So long as you have a username and password for one of those servers you can retrieve the token from the rest api documentation page. 

[http://FMESERVERHOST/fmerest/v2/apidoc/](http://FMESERVERHOST/fmerest/v2/apidoc/)

To find out what the token is you can click on the "Get Token" button at the top right after you have navigated to that link

***DO NOT PRESS "****Generate Token****"**
Especially if you have logged in using an application account that other applications might use for access.

### Create connection:

Before you can do anything with FME Server you must create a FMEServer object. 

``` python
import FMEUtil.PyFMEServerV2
server = r'http://fmeserver.servname.com'
token = r'e3224ccBost0nBru1nsSuck3234890g0Habsscfesdfs2342'
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)
```

On its own it doesn’t do anything very useful!  The FMEServer object is the entry point into all kinds of functionality though!

## Getting a list of the Repositories

Steps to accomplish this include:

* create FMEServer object
* from the FMEServer object get an Repository object
* from the repository object call the getRepositoryNames method

Example:

``` python
import FMEUtil.PyFMEServerV2
server = r'http://fmeserver.name.com'
token = r'e3224ccBost0nBru1nsSuck3234890g0Habsscfesdfs2342'
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)
repo = fmeSrv.getRepository()
names = repo.getRepositoryNames()
print 'repoNames', names
```


## Getting a list of Workspaces in a Repository

Steps to accomplish this include:

* create FMEServer object
* from the FMEServer object get an Repository object
* from the repository object call the getWorkspaces method with the repository whose workspaces you want to retrieve as the argument.

Example:

``` python
server = r'http://fmeserver.name.com'
token = r'e3224ccBost0nBru1nsSuck3234890g0Habsscfesdfs2342'
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)
repo = fmeSrv.getRepository()
wrkspcs = repo.getWorkspaces('FME_SERVER_REPOSITORY_NAME')
names = wrkspcs.getWorkspaceNames()
print 'wrkspcNames', names
```

## Getting a Published Parameters for a Workspace

### workspace that we want to retrieve

```
wrkspaceName = r'superFancy.fmw'
server = r'http://fmeserver.name.com' # server
token = r'e3224ccBost0nBru1nsSuck3234890g0Habsscfesdfs2342'# token
```

### create fme server object

`fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)`

### get a repository object

`repo = fmeSrv.getRepository()`

### get a workspaces object for the repo "FME_REPOSITORY"

`wrkspcs = repo.getWorkspaces('FME_REPOSITORY')`

### request the published parameters

`params = wrkspcs.getPublishedParams(wrkspaceName)`

### print the parameters

```
`print 'params', params
```

## Pretty Printing Data Structures

When creating the module PyFMEServerV2 in as many cases as possible I have tried to insulate the user from the complex data structures returned from the various REST calls.  In some cases it is unavoidable.  Returned data is frequently in the form of nested data structures (dictionaries of lists of …)  If you have trouble navigating these data structures the following link may help:

* Basics of python data structures: [https://docs.python.org/2/tutorial/datastructures.html](https://docs.python.org/2/tutorial/datastructures.html)
* Nested data structures: [http://www.pasteur.fr/formation/infobio/python/ch10.html](http://www.pasteur.fr/formation/infobio/python/ch10.html)

The pretty print module is useful when trying to decipher the data structure that is returned.  The following example "pretty" prints a nested data structure:

```
import pprint
# define the data structure here.
struct = [{u'model': u'list', u'defaultValue': [u'C:\\data\staging\\WHSE\\watery\\waterydb.accdb'], u'type': u'MULTIFILE', u'description': u'Source Dataset MSAccess:', u'name': u'SourceDataset_MDB_ADO'}, {u'model': u'string', u'defaultValue': u'WATER_ELIC.BCGOV', u'type': u'TEXT', u'description': u'Source Oracle Non-spatial Service:', u'name': u'SourceDataset_ORACLE8I_DB'}, {u'model': u'list', u'defaultValue': [u'C:\\data\staging\\WHSE\\watery\\waterydb_history.xlsx'], u'type': u'MULTIFILE', u'description': u'Source Microsoft Excel File(s):', u'name': u'SourceDataset_XLSXR_5'}, {u'model': u'list', u'defaultValue': [u'C:\\data\staging\\WHSE\\watery\\waterydb_ominec.xlsx'], u'type': u'MULTIFILE', u'description': u'Source Microsoft Excel File(s):', u'name': u'SourceDataset_XLSXR'}, {u'model': u'list', u'defaultValue': [u'C:\\data\staging\\WHSE\\watery\\waterydb_surrey.xlsx'], u'type': u'MULTIFILE', u'description': u'Source Microsoft Excel File(s):', u'name': u'SourceDataset_XLSXR_4'}]

# pretty print it
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(struct)
```

Pretty print will create output like the following. 
(*Note: data has been truncated for demo purposes*):

```
[   {   u'defaultValue': [   u'C:\\data\staging\\WHSE\\watery\\waterydb.accdb'],
        u'description': u'Source Dataset MSAccess:',
        u'model': u'list',
        u'name': u'SourceDataset_MDB_ADO',
        u'type': u'MULTIFILE'},
    {   u'defaultValue': u'WATER_ELIC.BCGOV',
        u'description': u'Source Oracle Non-spatial Service:',
        u'model': u'string',
        u'name': u'SourceDataset_ORACLE8I_DB',
        u'type': u'TEXT'},
    {   u'defaultValue': [   u'C:\\data\staging\\WHSE\\watery\\waterydb_history.xlsx'],
        u'description': u'Source Microsoft Excel File(s):',
        u'model': u'list',
        u'name': u'SourceDataset_XLSXR_5',
        u'type': u'MULTIFILE'},
    {   u'defaultValue': [   u'C:\\data\staging\\WHSE\\watery\\waterydb_ominec.xlsx'],
        u'description': u'Source Microsoft Excel File(s):',
        u'model': u'list',
        u'name': u'SourceDataset_XLSXR',
        u'type': u'MULTIFILE'},
    {   u'defaultValue': [   u'C:\\data\staging\\WHSE\\watery\\waterydb_surrey.xlsx'],
        u'description': u'Source Microsoft Excel File(s):',
        u'model': u'list',
        u'name': u'SourceDataset_XLSXR_4',
        u'type': u'MULTIFILE'}]
```

## Submit a Job for Processing

Example code for how to submit a job for processing using the default parameters defined in the job, then pretty print the response. 

```
jobName = r'dangerous_tsunami.fmw'
repo = 'FMESERVER_REPOSITORY'
server = r'http://fmeserver.name.com' # server
token = r'e3224ccBost0nSucks3234890scfesdfs2342'# token
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)
# gets a 'Jobs' object, from which you can get a 'Job' (singular) object
Jobs = fmeSrv.getJobs()
# submit for syncronous execution
reponse = Jobs.submitJobSync(repo, jobName)
# pretty printing the response.
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(reponse)
```

## Copy FMW to FME server and register with Job submitter

```
#importing various modules...
import os.path
import FMEUtil.PyFMEServerV2
wrkspc2Upload = r'C:/fmestuff/fancyFMW/fancyFMW.fmw'
# isolate just the name of the fmw file into the variable justfmw.
justfmw = os.path.basename(wrkspc2Upload)
repoName = 'FME_REPOSITORY_NAME'
server = r'http://fmeserver.name.com'
token = r'e3224ccBost0nSucks3234890scfesdfs2342'# token

# create the fme server object
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)

# get a repository object
repo = fmeSrv.getRepository()

# get a workspace object
wrkSpcs = repo.getWorkspaces(repoName)

# test to see if the workspace already exists
if not wrkSpcs.exists(justfmw):
    # if not then copy it to the repository.
    repo.copy2Repository(repoName, wrkspc2Upload)
    
# register with the job submitter
wrkSpcs.registerWithJobSubmitter(justfmw)
```

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
