'''
Created on Feb 9, 2017

@author: kjnether
'''
from setuptools import setup

setup(name='FMEUtil',
      version='0.4',
      description='Various utilities to help with FME workflows.  PyFMEServerV2.py is the wrapper to the rest api',
      url='https://github.com/bcgov/dbc-pylib/tree/master/FMEUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['FMEUtil'],
      install_requires=[
          'requests', 'lxml', 'deepdiff', 'python-dateutil'
      ],
      zip_safe=False)
