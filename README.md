[![Lifecycle:Stable](https://img.shields.io/badge/Lifecycle-Stable-97ca00)](<Redirect-URL>)

# DataBC Python Library

## This is the branch used to manage the python

This folder contains a bunch of python packages that tie together higher level functionality.  
The code here is used by multiple automation processes and is intended to make it easier to automate various tasks in support of databc's business.


I'm gradually working towards documentation of the more heavily used modules in the 'docs' folder.

You should see some examples there for the:
- [FMEServer Rest API wrapper](docs/FMEServer.md)
- [FME Parser](docs/FMWParser.md)
- [Secrets module](docs/secrets.md)
- [Password Manager Pro API Wrapper](docs/PasswordManagerPro.md)

FMEUtil
 - **PyFMEServerV3.py**: a wrapper to version 3 of the FME Server Rest api 
 - **PyFMEServerV2.py**: a wrapper to version 2 of the FME Server Rest api - no longer supported.
 - **FMEServerApiData.py**: the rest api can return large complicated data 
                            structures that require a lot of parsing work
                            to get to the information required.  This module
                            provides a wrapper for the actual data returned
                            by the api.  
 - **FMWParser** : a package to help with extracting information from FMW's.
                   This is a work in progress.  Code gets added on an as needed
                   basis.

