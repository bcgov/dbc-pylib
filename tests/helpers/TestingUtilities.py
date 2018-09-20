'''
Created on Jul 24, 2018

@author: kjnether
'''
import os.path


class Utils(object):

    def __init__(self):
        pass

    def getABMSJob(self):
        inFMW = 'abms_counties_sp_staging_gdb_bcgw.fmw'
        curDir = os.path.dirname(__file__)
        fullFMWPath = os.path.join(curDir, '..', 'test_data', inFMW)
        fullFMWPath = os.path.normpath(fullFMWPath)
        return fullFMWPath

    def getAMASnowmobile(self):
        # no schema job
        inFMW = 'ama_snowmobile_mgmt_areas_sp_staging_gdb_bcgw.fmw'
        curDir = os.path.dirname(__file__)
        fullFMWPath = os.path.join(curDir, '..', 'test_data', inFMW)
        fullFMWPath = os.path.normpath(fullFMWPath)
        return fullFMWPath

    def getFishForeshore(self):
        # no schema job
        inFMW = 'fish_foreshore_plant_hab_ok_sp_staging_gdb_bcgw.fmw'
        curDir = os.path.dirname(__file__)
        fullFMWPath = os.path.join(curDir, '..', 'test_data', inFMW)
        fullFMWPath = os.path.normpath(fullFMWPath)
        return fullFMWPath

    def getFieldMappedJobs(self):
        fldMapJobs = ['mta_acquired_tenure_history_sp_memprd_odb_bcgw.fmw',
                      'prot_current_fire_polys_ladder_sde_ftp.fmw',
                      'prot_current_fire_polys_sp_ladder_sde_agol.fmw']
        curDir = os.path.dirname(__file__)
        jobNum = 1
        fullFMWPath = os.path.join(curDir, '..', '..', '..', 'data',
                                   'fmwsWithFieldmapping',
                                   fldMapJobs[jobNum])
        fullFMWPath = os.path.normpath(fullFMWPath)
        return fullFMWPath

    def attributeRemapper(self):
        fmwList = ['dra_dgtl_road_atlas_dfar_sp_staging_gdb_bcgw']
