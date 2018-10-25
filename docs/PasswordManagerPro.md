# Interacting with Password Manager Pro Using Python.

<img src="https://lh3.googleusercontent.com/aTmyj9EvEkZx0TXegQgBsjhRzV1LMMPVm53AEe0ffoZW0gcDroTRiz9XXzRnY1RwtninayNRCDuaIC8y3tgR7DlxDqB3_9jPEo_EMznJUm-yvA1d4-5zXl4i3FPr3Q1KpQ8hGOyc2MaZyWwNvZrUgqZ8zHGNWgh0v3W5sYI8AqoIq6T_y1Mzrr4vcUxGS3Av37PGQMy_M0PV5R7LPXAG922N6-wb8gD8DnnONqb6XNhcZGDEZygWkY7HmtLJqLykmOzeSWze66hrdvMjKNeDCEuWuX6sFUAlV5UpWz3LQcm_6xurbpL8u2SS8i4YxJSLlIfyQQUmI0MbLIxkv-XP1YbWglgy5BUiq5QI9qMwxU94lMMSAuvLbkRPzemefA5NS_mjHGo25BhdLIgDEjeYUlcJ9Pr28Y0Uog8OjMCWraJh1RSPfGkFKX1Phocur1DvUBpa1PYs6YmIcIgZFDJ3hCKEW6UDMEGw-kchajNFoN1ZIdXlxcDrXhRj5p1fiCJBWUfATV6_MBppaTqfE0WqxqkIsCVjgrTxMJl_MNdfXZVZOOdfSHa1j3wUfp5uZDGoJHRtqXdn_zImLVtaKPcxanzkW--kZ2NzAYqwyBISvlvuMyzFkyj5NKlVT76z40W68XtADDWquOr5cbqT0HsI6jUgN5GBL2-H-INC-bUCGBPeokQRk8MkJaRN-w=w1404-h790-no" width="600"/>

## Overview of PMP

PMP is an application that can be used to help manage credentials for your
organization.  PMP includes a rest api that can be configured to allow for
credential retrievals using an API token.  The following link describes the
PMP Rest api which is what is wrapped by this python code.

[https://www.manageengine.com/products/passwordmanagerpro/help/restapi.html](https://www.manageengine.com/products/passwordmanagerpro/help/restapi.html)

In short PMP starts with a *"Resource"*.  Resources keep track of *"Accounts"*.  Database Schemas and accounts are the same thing.  Finally passwords are stored in accounts. 

The PMP rest api typically wants to use numeric ids to refer to "Resources", "Accounts", but people want to use the "name".  So if you know the resource name and the account / schema name, before you can request the password you will need to retrieve the ids for the "Resource" and the "Account". 

The python api attempts to hide this from you.  The functionality is still there but you probably won't need it.

## Getting the PMP Module

Add the following line to your requirements file:

`git+https://github.com/bcgov/dbc-pylib@v3.0.2#egg=PMP&subdirectory=PMP`

where:
  - **v3.0.2**: is the version / release number that you wish to install.
  
Then install your requirements using:
`pip install -r requirements.txt`

## Importing the Module

`import PMP.PMPRestConnect`

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

# Combining PMP and FME Server module

Leaving this example here in case it is of use, however most of what is 
described below is now accomplished using the *Secrets* module.  Docs 
available [here](docs/secrets.md)

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
