'''
Created on Feb 9, 2017

@author: kjnether
'''
from setuptools import setup

setup(name='PMP',
      version='0.4',
      description='wrapper for communication with PMP rest api',
      url='https://github.com/bcgov/dbc-pylib/tree/master/PMP',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['PMP'],
      install_requires=[
          'requests>=2.18.4',
      ],
      zip_safe=False)
