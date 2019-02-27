'''
Created on Nov 9, 2018

@author: kjnether
'''
import KirkUtil.constants as constants
import KirkUtil.PyKirkData
import pytest
import logging


def test_getJobs(Kirk_Destinations):
    dests = KirkUtil.PyKirkData.Destinations(Kirk_Destinations)
    for dest in dests:
        print(f'dest: {dest}')
    print(f'Kirk_Destinations: {Kirk_Destinations}')
