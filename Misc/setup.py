'''
Created on Feb 9, 2017

@author: kjnether
'''
'''
Created on Feb 8, 2017

@author: kjnether

'''
from setuptools import setup

setup(name='Misc',
      version='0.1',
      description='wrapper for communication with PMP rest api',
      url='https://github.com/bcgov/dbc-pylib/tree/master/Misc',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['Misc'],
      install_requires=[
          'win_unc',
      ],
      zip_safe=False)
