'''
Created on Jul 28, 2015

@author: kjnether

keyless access to BCDC rest api, 

This library has mostly been replaced in favour of using the ckanapi lib at: 
https://github.com/ckan/ckanapi
'''
import logging
import urlparse

import requests


class BCDCRestQuery():
    '''
    class provides a simple python interface to some commonly used rest queries
    used against BCDC (catalog.gov.bc.ca).


    '''
    destKeyDict = {'PROD': r'https://catalogue.data.gov.bc.ca',
                   'TEST': r'https://cat.data.gov.bc.ca',
                   'DELIV': r'https://cad.data.gov.bc.ca' }

    def __init__(self, destKeyWord='PROD'):
        self.logger = logging.getLogger(__name__)
        destKeyWord = destKeyWord.upper()
        if not self.destKeyDict.has_key(destKeyWord):
            msg = 'Invalid destKeyWord provided  "{0}", valid valued include {1}'
            msg = msg.format(destKeyWord, ','.join(self.destKeyDict.keys()))
            self.logger.error(msg)
            raise ValueError, msg
        self.baseUrl = self.destKeyDict[destKeyWord]
        self.apiDir = 'api/3/action'

    def executeRequest(self, url, params):
        '''
        :param url: the url to query.
        :param params: python dictionaries with the data to go along with the
                       get request

        '''
        r = requests.get(url, params=params)
        self.logger.debug('request status: %s', r.status_code)
        self.logger.debug('request json: %s', r.json())

        retVal = {}
        if r.status_code == 200:
            retVal = r.json()
        else:
            msg = 'Rest call returned a status code of {0}.  url called: ' + \
                  '{1} params are: {2}'
            msg = msg.format(r.status_code, url, str(params))
            raise ValueError, msg
        return retVal

    def getResource(self, field, queryString):
        '''
        :param field: the name of the field that is to be searched
        :param queryString: the value associated with the field that we are searching

        '''
        method = 'resource_search'
        url = urlparse.urljoin(self.baseUrl, self.apiDir) + '/'
        url = urlparse.urljoin(url, method)
        self.logger.debug("url: %s", url)
        query = {'query': field.strip() + ':' + queryString.strip()}
        self.logger.debug('query: %s', query)
        response = self.executeRequest(url, query)
        # now verify that the request returned success
        if not response['success']:
            msg = 'Rest Request did not return success, response is: {0}'.format(str(response))
            # TODO: Again define a better error, just getting things working for now
            raise ValueError, msg
        # delete the help from the response
        del response['help']
        return response

    def getRevision(self, revisionID):
        '''
        :param revisionID: returns the revision object for a given revision id.

        '''
        method = 'revision_show'
        url = urlparse.urljoin(self.baseUrl, self.apiDir) + '/'
        url = urlparse.urljoin(url, method)
        query = {'id': revisionID}
        # print 'query', query
        self.logger.debug("query: %s", query)
        self.logger.debug("url: %s", url)
        response = self.executeRequest(url, query)
        self.logger.debug("response: %s", response)
        return response
