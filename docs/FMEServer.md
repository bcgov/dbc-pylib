# Interacting with FME Server using Python

<img src="https://lh3.googleusercontent.com/UwGUu2-fwqkEuGiup-VTs1yD2ZEgP-imuX6g37-BUfQc7Q4yzngPw5Xfw2RhP-kqzUYwnvqfHyzHbDecpw2BNp3icC7ak4HU24ogXe3RBVmDrGBenQ_ehH0nkmv5BHYxlK1t5CwcMj75LR-m1ttC6w0OelvuilSGvN0aB_Pso3Tqvj99hWC7IIuswiA4JJqAI8wrnOPc-Abbds2B5IXe8wQOQV1tx0yGHReuUsm8Hl6fsMb2-oowGxjDiukZ8V8DaP_J2oznxXZaBvkVJnis-o9KNIj_iV0DMh8ScAOZsVwEt2SHrvuQQto49ogOIA8SCo58I2IwCJIyLsDQrgcz7MXUu7noJiMjD9j38bCY_JQUZhAFCfMeiAJhCRl7SGL27iKmQbu3PooqPMMTWhnJTjMroff1mfH3n9i2Iow-ZyVGcWcjklPwQCcaTeo8aqUWlbmkwHDbIAzrPBfgs8uPT1YuAmFOKrgBOJHBHavptaSWLFcntevvhcw-FeHhwexNsiASEXTTKMGKKgv5e1LxDaU_Ic13P6efAisOmuJOg37zEXb-KqyjWQKuD1o_EQgKt7Kj03j1EKFrVxoL740pm_JL2I8Yj91jvdLElPeVxoA3yEpRPYXIsmouTAJlTPrSrgSFjMUkysY5j0cKIHOymrZcoSTBX9A58g=w1252-h704-no" width="600"/>


## Installing:

The FME Server Python Module is part of the DataBCPyLib which is located in this repository in the FMEUtil package:

To install this package put the following line in your requirements.txt:

`git+https://github.com/bcgov/dbc-pylib@v3.0.2#egg=FMEUtil&subdirectory=FMEUtil`

where: 
  - **v3.0.2**: is the release that you want to use.

And then install the requirements using pip 

`pip install -r requirements.txt`

## Which module to use?

There are two modules in the FMEUtil package:
 - PyFMEServerV2
 - PyFMEServerV3
 
Each of these corresponds with a different rest api version. Version 2 (v2) 
was used on FME 2015, 2016, and I believe v3 is used on 2017, and 2018.  

Currently both versions are interchangeable, however v3 will gradually 
introduce new features that won't be available in v2.  While most of the
documentation below uses v2 you should be able to safely swap the import
statements to use v3 without any problems.

For example you would change the line:

`import FMEUtil.PyFMEServerV2`

with the line:

`import FMEUtil.PyFMEServerV3`

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
# fmw name who's published parameter we want to get
wrkspaceName = r'superFancy.fmw'

# provide the server / token and create fmeserver object
server = r'http://fmeserver.name.com'
token = r'e3224ccBost0nBru1nsSuck3234890g0Habsscfesdfs2342'
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)

#get a repository object
repo = fmeSrv.getRepository()

# get a workspaces object for the repo "FME_REPOSITORY"
wrkspcs = repo.getWorkspaces('FME_REPOSITORY')

# request the published parameters
params = wrkspcs.getPublishedParams(wrkspaceName)

# print the parameters
print 'params', params

# (optional) pretty print the parameters
import pprint
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(params)
```

## Pretty Printing Data Structures

When creating the module PyFMEServerV2 in as many cases as possible I have tried to insulate the user from the complex data structures returned from the various REST calls.  In some cases it is unavoidable.  Returned data is frequently in the form of nested data structures (dictionaries of lists of …)  If you have trouble navigating these data structures the following link may help:

* Basics of python data structures: [https://docs.python.org/2/tutorial/datastructures.html](https://docs.python.org/2/tutorial/datastructures.html)
* Nested data structures: [http://www.pasteur.fr/formation/infobio/python/ch10.html](http://www.pasteur.fr/formation/infobio/python/ch10.html)

The pretty print module is useful when trying to decipher the data 
structure that is returned.  The previous example showed how to format 
the published parameters that were returned. The following example 
"pretty" prints a more complex nested data structure:

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

## Download an FMW
```
import FMEUtil.PyFMEServerV2
imort os.path

# identify the source repository
repoName = 'FME_REPOSITORY_NAME'

# identify the source FMW
wrkspcName = 'myFancy.fmw'

# create an fme server object
server = r'http://fmeserver.name.com'
token = r'e3224ccBost0nSucks3234890scfesdfs2342'
fmeSrv = FMEUtil.PyFMEServerV2.FMEServer(server, token)

# get a repository object
repo = fmeSrv.getRepository()

# get a workspaces object
workspaces = repo.getWorkspaces(repoName)

# identify the destination path
destinationPath = os.path.join('/home/guylafleur/fmws', wrkspcName)

# perform the download
workspaces.downloadWorkspace(wrkspcName, destinationPath)

```




