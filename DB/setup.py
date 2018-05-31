'''
Created on Feb 8, 2017

@author: kjnether

'''
from setuptools import setup

setup(name='DB',
      version='0.3',
      description='wrapper for database communication',
      url='https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/DB',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['DB'],
      install_requires=[
          'cx_Oracle',
      ],
      dependency_links = ['git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git@packagedVersion#egg=Misc&subdirectory=Misc'],
      zip_safe=False)
