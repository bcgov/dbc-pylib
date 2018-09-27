'''
Created on Feb 9, 2017

@author: kjnether
'''
from setuptools import setup

setup(name='KirkUtil',
      version='0.4',
      description='wrapper for communication with Kirk rest api',
      url='https://github.com/bcgov/dbc-pylib/tree/master/KirkUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='Apache',
      packages=['KirkUtil'],
      install_requires=[
          'requests', 'enum34',
      ],
      zip_safe=False)
