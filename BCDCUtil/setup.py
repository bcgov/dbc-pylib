'''
Created on Feb 9, 2017

@author: kjnether
'''

from setuptools import setup

setup(name='BCDCUtil',
      version='0.1',
      description='wrapper for database communication',
      url='https://github.com/bcgov/dbc-pylib/tree/master/BCDCUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['BCDCUtil'],
      install_requires=[
          'requests',
      ],
      zip_safe=False)
