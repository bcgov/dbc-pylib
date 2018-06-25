'''
Created on May 2, 2018

@author: kjnether
'''
import abc


class ReporterBase(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, inFile):
        '''
        constructor
        '''
        return

    @abc.abstractmethod
    def addNewFMW(self, parser):
        '''
        Gets a parser object, uses it to extract necessary information
        and then adds it to the data to be included in the report.
        '''
        return

    @abc.abstractmethod
    def setHeader(self, header):
        '''
        defines the header for the report
        '''
        return

    @abc.abstractmethod
    def render(self):
        '''
        Takes all the data that was assembled by the addNewFMW() methods
        and dumps to a report.
        '''
        return
