'''
Created on Aug 7, 2018

@author: kjnether
'''

import pytest

# cludgy fix to the arcgis pathing problems
import ArcGisUtil.ConfigurePy3Paths
p3registry = ArcGisUtil.ConfigurePy3Paths.Py3PathRegistry()
p3registry.addToPATHEnvVar()
p3registry.addToPythonPath()

from fixtures.Parser_fixtures import *
from fixtures.FMWParser_Fixture import *
from fixtures.Secrets_Fixture import *
from fixtures.KirkAPI import *
from fixtures.FMEServerApiData_fixtures import *
from fixtures.pyKirkData_fixtures import *
from fixtures.FMEServer_fixture import *
from fixtures.PMP_Info import *
from fixtures.layerfile_fixture import *
from fixtures.arcproregistryreader_fixture import *
