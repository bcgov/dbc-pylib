'''
Created on Feb 9, 2017

@author: kjnether
'''

from setuptools import setup

setup(name='BCDCUtil',
      version='0.1',
      description='wrapper for database communication',
      url='https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/BCDCUtil',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['BCDCUtil'],
      install_requires=[
          'requests',
      ],
      zip_safe=False)
