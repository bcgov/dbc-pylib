'''
Created on Feb 8, 2017

@author: kjnether

'''
from setuptools import setup

setup(name='DBCSecrets',
      version='0.3',
      description='an api to retrieve secrets, see () for more details',
      url='https://github.com/bcgov/dbc-pylib/tree/master/DBCSecrets',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['DBCSecrets'],
      install_requires=[
          'requests>=2.18.4'
               ],
      dependency_links=['git+https://github.com/bcgov/dbc-pylib#egg=PMP&subdirectory=PMP'],
      zip_safe=False)
