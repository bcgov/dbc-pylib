'''
Created on Feb 26, 2019

@author: kjnether
'''

import pytest


def test_getInstallPath(getRegistryReader):
    apRoot = getRegistryReader.getArcProRootPath()
    arcpyRoot = getRegistryReader.getArcProPythonPath()
    print(f'arcpro root dir: {apRoot}')
    print(f'arcpyRoot is: {arcpyRoot}')

def test_importArcPy(getRegistryReader):
    getRegistryReader.addToPythonPath()
    getRegistryReader.addToPATHEnvVar()
    import arcpy  # @UnresolvedImport
    print(f'arcpy imported!')

    