# Secrets

This is a module that has been designed to store an applications secrets.
A description of how this module works is available at: 

https://github.com/bcgov/Data-BC-PyLib/blob/master/docs/secrets.md

At its core it allows you to store all of an applications secrets in a
json data structure.  When developing this file is stored in a json 
file. Then when the job gets deployed to jenkins they are stored in a
environment variable that gets injected into the build script.


