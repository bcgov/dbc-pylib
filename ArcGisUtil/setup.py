'''
Created on Feb 8, 2017

@author: kjnether

pip install -e vcs+protocol://repo_url/#egg=pkg&subdirectory=pkg_dir
[-e] git://git.myproject.org/MyProject.git@master#egg=MyProject
[-e] git://git.myproject.org/MyProject.git@v1.0#egg=MyProject
[-e] git://git.myproject.org/MyProject.git@{token}#egg=ArcGisUtil
'''

from setuptools import setup

setup(name='ArcGisUtil',
      version='0.2',
      description='Library to with functions to automate aspects of ArcGIS',
      url='https://github.com/bcgov/dbc-pylib/tree/master/ArcGisUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['ArcGisUtil'],
      zip_safe=False)