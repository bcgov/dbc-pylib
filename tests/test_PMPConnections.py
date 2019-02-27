'''
Created on Dec 12, 2018

@author: kjnether
'''
import PMP.PMPRestConnect


def test_PMPResource(PMP_ConfigDict, PMP_Resource_prd, PMP_Resource_dlv):
    print('PMP_ConfigDict: {PMP_ConfigDict}')
    pmp = PMP.PMPRestConnect.PMP(PMP_ConfigDict)
    #rtVal = pmp.getAccountPassword('WHSE_ADMIN_BOUNDARIES', PMP_Resource_prd)
    rtVal = pmp.getAccountPassword('WHSE_ADMIN_BOUNDARIES', PMP_Resource_dlv)

    print('pswd {rtVal}')
