# Working with Secrets

<img src="https://lh3.googleusercontent.com/8UhPEzONm7jPXh_5743KRFxe8UiyxPfIt5XZiaK-JIk_Z6-f5eosqXG1kzdueL7nP1KW7qCIVCRiUvLpj7HHokpZj9Gze4MBYfCmY_hdbNM5mpxDfLFjzRA9Y6I03rpl8ymXmyNz4zto63eDl-crz-RwMSibLn5IO-H0o38ko6_PYMq-vg8LfE5vWqLJLBIPPvFv3ixkDo1KcgpJQ7tkD-gdDtec8lh9liMX0joEYrI6jOAb93o-u6TEFh5apjoPsr32F5IIrXZ8068I223a2uuYW90bpCIrTV0XQSsb_lGdAdohoCEqlfvXqqWia1NYFjfvwM8aVkoqlnHmOFA3yWKMrgUaeQkOqDBxaN59v-lplKuBiN-VK75cbVO8A7UWgKcvTbTyk2EYLs2EfeJqO0EHbFvu5QiL7m7RFznsuQrrDy5T8VTXjuwG7ZRshDZ5scbIJGWXG-1fTrLBQubvpRY6Nxd005i5OwrLWgao0snjuRguY0tJw2Vbo6w06L7YgRSj0d84ytuedYoC_4kpLVDG_9Y1EIyGdj5FX9N0DMyvPkw9875xBkdNsPbwthVxxQYfBm24xhGr71uL27E7wHBCVmMyt4SnBJVboxtEN3IrGSN6Hrr_DX3k7lDrKgLWmisFYPyy-b4WsF0WjNmC1IxMis41zXIK4iQABOCzQf0=w1157-h651-no " alt="Picture" width="600">

We have created many scripts to automate various processes that would not be possible if they had to be completed manually.  Examples include:

*   Reading the contents of all layer files in the layer file library and using the information in them to update the GWIP tables that drive the TSAT toolbar. (GWIP_Update)
*   Touching every spatial dataset in the BCGW, using schema level permissions.  The act of touching the dataset ensures that SDE's metadata stays up to date with the actual object it defines.
*   and more...

With each of these scripts the secrets associated with them should be stored outside of the actual code.  

We also however need an easy way of transferring all the secrets from our development environment to Jenkins or some other place where the scripts will run.

Further to this retrieval of credentials should not be a cumbersome overly complex process.  Ideally every script should use the same approach.

That is the challenge this document and the api attempt to solve...


# What's  a secret?

All of the following are considered secrets that should not exist inside source code:

*   file paths
*   database schemas
*   database instances / service names / SIDS
*   server / host names
*   port addresses
*   rest api urls
*   rest api tokens
*   rest api credentials
*   passwords of any sort
*   account names of any type
*   pmp resource names
*   anything else you can think of that think might be sensitive...

# Overview of how this will work

Managing secrets for scripts, can be broken up into 3 phases, these are briefly described here.  Remainder of the document is going to focus on Phase 2 and 3.

## Phase 1: Configuration

1.  What secrets are required.  Are passwords or api tokens required. 
2.  If you require passwords / api tokens make sure they exist in PMP
3.  Configure a PMP api account that also has access to these passwords.
4.  Have an api token generated for the PMP api account for the host that the script will be running on. (usually you will require 2 tokens, one for development and then another for when you move to production / jenkins)

## Phase 2: Set up secrets in JSON file

Having identified what secrets your script requires, and having dealt with the PMP setup and acquisition to required PMP passwords, you now need to enter that information into you the secrets json file, and then configure your script to use the credentials api to retrieve them in your script.


## Phase 3: Move to Jenkins

Assuming your script is going to be configured to run in Jenkins, you will need to complete these steps.  If you script is never going to be run from Jenkins you do not need to worry about this phase.

*   Get a PMP token for the Jenkins node that your script is going to be configured to run on. 
*   Options:
    1. Enter the json secrets object into an environment variable in your script
    2. Maintain secrets in a secured git repo, and set up the secrets as a submodule. that the jenkins process has access to. 
   
*   Update the pmp tokens, and path delimiters.

# Getting Started

Each script / project will have its own dependencies, configurations, outputs etc.  If each script stores these pieces using the same structure, it will be easier to manage our collection of scripts.  The following link defines directory structure for pythons scripts. [LINK TO SCRIPT DIRECTORY STRUCTURE DOC].  Hoping it works for your projects.  If it does not please add a comment to that post.  The credential api has been set up to automatically retrieve secrets json files from a secrets directory.  No need to provide paths if the project meets the standard.

The remainder of this section will discuss how the `secrets.json` file and the credential retrieval api work together.

Secrets can be broken up into 3 different types:

*   **Simple Key Value Pairs (link):** Very simple, basically you define a label for your secret and it is retrieved by that label.  I use this type mostly for storing file paths.
*   **Individual credentials (link):** These types of secrets are usually tied to single database accounts.  For example your script might need access to WHSE_SOMETHING account.  This is where you would configure this type  of access.
*   **Multiple credential (link):** This type is used for situations where you need to access many different accounts that are all stored in a single schema.  The Touch script is an example of this where it needs to get passwords for all the different schemas that store spatial objects.

There is also an appendix that goes over details like:

*   _Setting up a project_
*   _Getting dependencies_
*   _Overview of all the possible parameters you can use in a secrets file._

## Simple Key Value Pair Retrieval

This example shows how you can set up a 'label' that returns a single 'secret' string.  I use this option mostly for storing file paths.

#### SECRETS FILE: 

 ``` 
"miscParams":{
     "__comment__": "this section remains unstructured, api allows retrieval of elements by object name" ,
     "label4FilePath": "C:\\tmp\\work"
   }
 }
```

#### PYTHON CODE: 

``` python
# importing the module
import Secrets.GetSecrets
# define the label in the json file that we want to retrieve
credLabel = 'label4FilePath'
# create credential retrieval object
credRetrieval = Secrets.GetSecrets.CredentialRetriever()
# get a miscellaneous parameters object
miscParams = credRetrieval.getMiscParams()
# retrieve a parameter by its label
credValue = miscParams.getParam(credLabel)
# print the results
print 'label = {0}'.format(credLabel)
print 'value = {0}'.format(credValue)
```

## Retrieve Single Database Parameters

This same method can be used to retrieve a variety of parameter types. In this example you will notice that the all the information about a specific database account (schema, host, port, service name) are provided in the secrets file but the actual password is not.  The credential retrieval object will automatically retrieve the password for you from pmp.


#### SECRETS FILE: 
    
```
   {"pmphost":"pmp host here",
    "pmprestapidir":"path to rest api here",
    "__comment__":"this pmp token is for development",
    "pmptoken":"PMP token here",
    "secrets2get": [
      {"__comment__": "tables to update for Delivery are in this instance/schema",
       "label" : "test_accnt_dlv",
       "accounttype": "db",
       "username": "WHSE_SCHEMA",
       "PMPResource": "PMPRESOURCE",
       "port": 1521,
       "servicename": "database service name",
       "host": "database host"}
      ],
  "miscParams":{
       "__comment__": "this section remains unstructured, api allows retrieval of elements by object name",
       "path1": "C:\\tmp\\work\\someDir"
  }
}
```


#### PYTHON CODE: 

```
import Secrets.GetSecrets 
# these are the labels associated with secrets that
# we are trying to retrieve from secrets file
filePathLabel = 'label4FilePath'
oracleAccountLabel = 'test_accnt_dlv'
# creating a CredentialRetriever object
credRetrieval = Secrets.GetSecrets.CredentialRetriever()
# retrieve an individual account secret object
#   - this method extracts an entry by label from the secrets files
#     section: secrets2get
#   - This example is getting the secrets for the label
#     in the variable oracleAccountLabel
secretAccnt = credRetrieval.getSecretsByLabel(oracleAccountLabel)
# now to retrieve the actual parameters from the AccountParameters object
password = secretAccnt.getPassword()
host = secretAccnt.getHost()
port = secretAccnt.getPort()
schema = secretAccnt.getUserName()
serviceName = secretAccnt.getServiceName()
# now get the parameter label4FilePath from the
# miscparameter section
miscParams = credRetrieval.getMiscParams()
credValue = miscParams.getParam(filePathLabel)
```


## Multiple Database Accounts

This example shows how you can configure credential retrieval for multiple accounts in a given pmp resource.  The most common use case for this approach is when you don't necessarily know that name of the account you need to retrieve when the script is run.  The name of the account is comming from some other source.  For example with the FME Template code, it reads the individual FMW destination schema and instance.  Using that information the script then needs to retrieve a password.

If you know the account name who's password you require use the 'Single Database Password' approach.

#### SECRETS FILE: 

```
{"pmphost":"pmp address",
 "pmprestapidir":"pmp rest dir",
 "__comment__":"this pmp token is for development",
 "pmptoken":"X232jsi3-PMPTOKEN-*#892jf93n2kh",
 "multiaccountsettings": [
      {
       "__comment__": "multiaccount settings allow for retrieval of multiple accounts by account name",
       "label" : "dlv",
       "port"  : "sdeport",
       "host" : "dbhost",
       "servicename": "dbservicename",
       "PMPResource": "PMPRESRNAME"
      }
     ],
 "miscParams":{
        "__comment__": "this section remains unstructured, api allows retrieval of elements by object name",
        "layerFilePath": "C:\\tmp\\layer_library"
   }
 }
```

#### PYTHON CODE: $PROJDIR/src/pmpExample.

```
import Secrets.GetSecrets  # @UnresolvedImport
# these are the labels associated with secrets that
# we are trying to retrieve from secrets file
filePathLabel = 'label4FilePath'
oracleAccountLabel = 'test_accnt_dlv'
multiAccountLabel = 'multipleOra'
# creating a CredentialRetriever object
credRetrieval = Secrets.GetSecrets.CredentialRetriever()
# get a multiaccount setup
multiAccnt = credRetrieval.getMultiAccounts()
# now get account by name.  This is a very simple example
# ideally if you only needed this one account you
# would not use this approach, and instead would
# use the single database account approach.  Use
# this appoach when the name of the account is not
# known at run time or if it is a calculated parameter
pswd = multiAccnt.getAccountPassword('dlv', 'WHSE_CORP')
```
# Appendix

## secrets.json schema

The secrets.json file (contents can be pasted into an environment variable called APPLICATION_SECRETS as well). Can contain the following root elements:

### __comment__

Can be used for commenting the secrets file, keys with this value will always be ignored. You can include as many __comment__ elements as you like in the file.

### pmphost

A string defining the name of the pmp host.  Do not include the protocol, that will automatically be appended.  Example value: `mypmphost.ca`

### pmprestapidir

The directory on the pmphost that contains the rest api.  By default [pmps rest api](https://www.manageengine.com/products/passwordmanagerpro/help/restapi.html) is located at `/restapi/json/v1/`

### pmptoken

The api key / token that has been configured for you to use.

### secrets2get

This parameter is equal to a list that can contain the following object types:

*   internal database descriptions
*   external database descriptions
*   rest api credential descriptions

### multiaccountsettings

This parameter is equal to a list of multiaccount description objects.  This parameter is useful when you need to retrieve passwords for many different accounts from the same pmp resource.

### miscParams

This parameter is most commonly used to keep a simple string out of your code,  You can put anything you want in this section.  Its basically made up of key value pairs.  Your retrieve the value using the key.  An example of where you might use this is for file paths.  This parameter is a dictionary, containing key / value pairs.

## Object types:

### `secrets2get` objects:

The secrets2get list is composed of a list of the following objects.  The structure (properties) of each object is defined below.  Each element in the list describes a specific database account who's credentials you will require.

#### __comment__

Use anywhere to document your secrets file.  This parameter is ignored by the api.

#### label

The label or the name that will use with the api to retrieve this property

#### accounttype

The account type, valid values include:__db|dbext |restapi__

#### username

The username to use when connecting to either the database or the rest api.

#### PMPResource

The pmp resource in which the passwords is stored.

#### port

The port to use for a database connection (not required for rest api secrets)

#### servicename

The database service name

#### host

The host of the database, or the rest api.

### multiaccountsettings

This section is equal to a list of the following object types.  Each multiaccount entry is tied to a pmp resource.  The api will consume the multiaccount settings described here, and allow you to retrieve passwords for any account in the configured resource.  Multiaccount connection are only for database connections.

#### __comment__

ignored by the api, but can be used to document this entry in your json file.

#### label

The label that is used in your code to retrieve a multiaccount object, that is then in turn used to access secrets described by this object.

#### port

The database port

#### host

The host on which the database is located

#### servicename

database service name

#### PMPResource

The pmp resource where the passwords are located.

## API Documentation

This is not an exhaustive documentation of the api, but instead a highlight of what types of objects the various methods return

All credential retrieval starts with these two lines:

**`import Secrets.GetSecrets`
 `credRetrieval = Secrets.GetSecrets.CredentialRetriever()`**

The second line is creating a CredentialRetriever object.  While it should not matter to you, what this method is doing behind the scenes is:

*   Looks for the credentials file $PROJDIR/secrets/secrets.json, if it finds it, it reads the contents into memory and then converts to a python data structure.
*   If there is no json file it looks for json in the environment variable _APPLICATION_SECRETS _as is defined by the modules constant variable `secrets_env_var`.
*   Once the secrets are read to memory they go through a validation procedure.  (not describing how that works here, its in the code in the method `verifyStructure`
*   Finally the json data is stored in a property.

Once you have this object, you can now retrieve either information about any entry in the section `secrets2get`. using the label of the entry you want to retrieve.

**`secretObj = credRetrieval.getSecretsByLabel('labelFromSecretsFile')
 `**

to get individual parameters you can use one of the following methods:

*   **`getUserName()`**
*   **`getPMPResourceName()`**
*   **`getAccountType()`**
*   **`getHost()`**
*   **`getAccountLabel()`**
*   **`getPort()`**
*   **`getLabel()`**
*   **`getServiceName()`**
*   **`getLoginID()`**
*   **`getAPI()`**
*   **`getServerFromPMP()`**
*   **`getKeePassNotes()`**
*   **`getPassword()`**

and a specific example:

**`loginId = secretObj.getLoginID()`**

Back to the credential Retrieval object, to get values from either the miscparams section or the multi account section you will need to use one of these methods:

**`miscParams = credRetrieval.getMiscParams()
 ``multiParams = credRetrieval.getMultiAccounts()`**

Getting a specific value from the misc params:

**`value = miscParams.<span class="s1">getParam('label')</span>`**

Goes into the misc params section of the json struct and returns the value that is associated with the label 'label' in this case.

And finally for multiaccounts, use the multiParams object created above:

**`password = multiParams.getAccountPassword('multiLabel', 'WHSE_SOMETHING')`**

Goes into the json struct, the multiaccount section can be made up of any number of configs.  As a result this method requires you to define the label associated with the multiaccount configuration you set up in the secrets file.  The other parameter is the name of the account whos password you are trying to retrieve.

## Project directory setup

While you can set up your scripts projects any way you want, if we stick with a standard it should make it easier for other people to use your scripts, contribute to your projects, and generally understand how they work.

Standard Python directory structure is defined [here](http://test.apps.bcgov/guide/intdocs/jenkins-python-scripts-configuration/#Structuring_your_Code)

## Dealing with Dependencies

### Dependencies Directory (lib)

All dependencies required by a project should be located in the 'lib' directory.  The only file that should be included in the source code repository (GOGS) for this directory, is the _requirements.txt_ file.  This file defines the requirements for your project.

To install requirements you can either:

*   set up a virtualenv and install them into your virtual env
*   use pip with the -t option to install to this directory and then configure paths for your project, either using:

        *   PYTHONPATH environment variable
    *   Path in your development environment
    *   Use usercustomize.py files.

Typically if working on non windows platforms I use virtualenv, and when on windows I use pip with -t option as is shown in the example below:

**`cd $PROJDIR/lib_ext
 pip install -t . -r requirements.txt`**

To use the PMP package you must have the **[requests](http://docs.python-requests.org/en/master/)** python module available to your project.


