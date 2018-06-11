'''
Created on Feb 8, 2017

@author: kjnether

'''
from setuptools import setup

setup(name='DB',
      version='0.3',
      description='wrapper for database communication',
      url='httpshttps://github.com/bcgov/dbc-pylib/tree/master/DB',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['DB'],
      install_requires=[
          'cx_Oracle',
      ],
      dependency_links = ['git+https://github.com/bcgov/dbc-pylib@v2.1.16#egg=Misc&subdirectory=Misc'],
      zip_safe=False)
