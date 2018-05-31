'''
Created on Feb 9, 2017

@author: kjnether
'''
'''
Created on Feb 8, 2017

@author: kjnether

pip install -t . git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git/packagedVersion

pip install -t . -e git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git@packagedVersion#egg=ArcGisUtil&subdirectory=ArcGisUtil

pip install -t . -e git:

https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git

pip install -e vcs+protocol://repo_url/#egg=pkg&subdirectory=pkg_dir
[-e] git://git.myproject.org/MyProject.git@master#egg=MyProject
[-e] git://git.myproject.org/MyProject.git@v1.0#egg=MyProject
[-e] git://git.myproject.org/MyProject.git@da39a3ee5e6b4b0d3255bfef95601890afd80709#egg=ArcGisUtil

https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/ArcGisUtil

pip install -t . -e git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git@packagedVersion#egg=arcgisutil&subdirectory=arcgisutil/arcgisutil
pip install -t . -e git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/arcgisutil
https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/arcgisutil


https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/arcgisutil/arcgisutil

https://gogs.data.gov.bc.ca/GuyLafleur/DataBCPyLib/src/master/FMEUtil/FMEUtil
'''
from setuptools import setup

setup(name='FMEUtil',
      version='0.2',
      description='Various utilities to help with FME workflows.  PyFMEServerV2.py is the wrapper to the rest api',
      url='https://gogs.data.gov.bc.ca/GuyLafleur/DataBCPyLib/src/master/FMEUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['FMEUtil'],
      install_requires=[
          'requests',
      ],
      zip_safe=False)
