'''
Created on Feb 8, 2017

@author: kjnether

'''
from setuptools import setup

setup(name='Secrets',
      version='0.2',
      description='an api to retrieve secrets, see () for more details',
      url='https://gogs.data.gov.bc.ca/daops/DataBCPyLib/src/packagedVersion/Secrets',
      author='Kevin Netherton',
      author_email='kevin.netherton@gov.bc.ca',
      license='MIT',
      packages=['Secrets'],
      install_requires=[
          'requests==2.18.4'
               ],
      dependency_links=['git+https://gogs.data.gov.bc.ca/daops/DataBCPyLib.git@v2.1.12#egg=PMP&subdirectory=PMP'],
      zip_safe=False)
