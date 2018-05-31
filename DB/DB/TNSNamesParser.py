'''
Created on Dec 5, 2016

@author: kjnether

a quick module created to allow the parsing of TNSNames files

In a nutshell there are few different classes that make up the parser:
a) a parser that will return a dictionary with the structure:
     tnslabel:
        parameter:
           parameter:
              etc.

   will take an entry like this:
   database.domain.net =
      (DESCRIPTION=
        (ADDRESS=
          (PROTOCOL=TCP)
          (HOST=server.domain)
          (PORT=1521)
        )
        (CONNECT_DATA=
          (INSTANCE_NAME=instprod8)
          (SERVICE_NAME=servicename.bc.ca)
        )
      )
    and create a python data structure like this:
    {'database.domain.net':
        {'DESCRIPTION':
            {'ADDRESS':
                { 'PROTOCOL': 'TCP',
                  'HOST':'server.domain',
                  'PORT':'1521'},
             'CONNECT_DATA':
                { 'INSTANCE_NAME':'instprod8' ,
                  'SERVICE_NAME':'servicename.bc.ca'}
            }
        }
    }

    There is also a class that will wrap this datastructure with methods that
    allow recursive searches for parameters, or specific retrieval of specific
    parameters.  This class has been developed on an as needed basis.  Inother words
    if some other application requires access to a specific parameter that
    is when the method will be defined
'''

import re
import pprint
import logging


class TNSConst(object):
    key_Description = 'DESCRIPTION'
    key_ConnectData = 'CONNECT_DATA'
    key_Service_Name = 'SERVICE_NAME'
    key_Host = 'HOST'
    key_Port = 'PORT'
    key_GlobalName = 'GLOBAL_NAME'
    key_SID = 'SID'
    key_Inst = 'INSTANCE_NAME'

    # version of lib with project includes a populated version of this parameter
    manualData = {
    }


class TNSNames(object):

    def __init__(self, struct):
        self.const = TNSConst

        modDotClass = '{0}.{1}'.formatSql(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(modDotClass)

        self.struct = struct
        for entry in self.const.manualData.keys():
            if entry in self.struct:
                msg = 'the manually configured entry for {0} already exists in the tnsnames file'
                msg = msg.formatSql(entry)
                raise ValueError, msg
            else:
                # print 'self.struct type:', type(self.struct)
                self.struct[entry] = self.const.manualData[entry]
        self.pp = None

    def pprint(self):
        if not self.pp:
            self.pp = pprint.PrettyPrinter(indent=4)
        self.pp.pprint(self.struct)

    def clean(self, text):
        '''
        the parser is including the trailing ')' character in the
        strings it is extracting.  Too lazy at the moment to deal with
        this so just gonna clean them up for now with this method.

        Long term if this turns into something that gets used a lot will
        have to go in and patch up the parser.
        '''
        if text:
            retVal = text.strip().replace(')', '').replace('(', '')
        else:
            retVal = text
        return retVal

    def removeSuffix(self, text):
        retVal = (text.split('.'))[0]
        retVal = retVal.strip()
        return retVal

    def getTNSEntryByLabelNoSuffix(self, serverName, inStruct=None, rootKey=None):
        rootCall = False
        if not inStruct:
            inStruct = self.struct
            rootCall = True
        serverNameNoSuffix = self.removeSuffix(serverName)
        matchedServers = []
        for entry in inStruct.keys():
            if not rootKey:
                rootKey = entry
            entryNameNoSuffix = self.removeSuffix(entry)
            if serverNameNoSuffix.upper() == entryNameNoSuffix.upper():
                matchedServers.append(entry)
        if not matchedServers:
            for entry in inStruct.keys():
                if isinstance(inStruct[entry], dict):
                    retVal = self.getTNSEntryByLabelNoSuffix(serverName, inStruct[entry], rootKey)
                    if retVal:
                        matchedServers.extend(retVal)
                else:
                    entryNameNoSuffix = self.removeSuffix(entry)
                    if serverNameNoSuffix.upper() == entryNameNoSuffix.upper():
                        matchedServers.append(rootKey)
                        print 'found match for key {0}, and value {1}'.formatSql(entry, inStruct[entry])
        if rootCall:
            if len(matchedServers) > 1:
                msg = 'found more than one entry in the TNSNames file for the server name: {0}' + \
                      ' entries include: {1}'
                # if they all have the same servicename / host / port then send back
                # any of them.
                cmprHost, cmprPort, cmprSrvNm, cmprSid = [None, None, None, None]
                for matchedServer in matchedServers:
                    matchStruct = self.getTNSEntryByLabel(matchedServer)
                    curHost = self.getHostFromStruct(matchStruct)
                    curPort = self.getPortFromStruct(matchStruct)
                    curSrvNm = self.getServicenameFromStruct(matchStruct)
                    curSid = self.getSIDFromStruct(matchStruct)
                    # if these are none values then convert to strings
                    # because comparison does case insensitive test
                    if not curSid:
                        curSid = str(curSid)
                    if not curSrvNm:
                        curSrvNm = str(curSrvNm)
                    if not cmprHost:
                        cmprHost = curHost
                        cmprPort = curPort
                        cmprSrvNm = curSrvNm
                        cmprSid = curSid
                    elif curHost.lower() <> cmprHost.lower() or \
                         curPort <> cmprPort or \
                         curSrvNm.lower() <> cmprSrvNm.lower() or \
                         curSid.lower() <> cmprSid.lower():
                        msg = 'multiple hosts: {0} match the entry name {1} but have ' + \
                              'differing connect params.\n  host: {2} {3}\n  port: {4} {5}\n' + \
                              '  curSrvNm: {6} {7}\n  curSid  {8} {9}\n label {10}\n {11}'
                        raise ValueError, msg.formatSql(
                            matchedServers, serverName, curHost, cmprHost, \
                            curPort, cmprPort, curSrvNm, cmprSrvNm, \
                            curSid, cmprSid, matchedServer, matchStruct)
                retVal = matchedServers[0]
            else:
                if matchedServers:
                    retVal = matchedServers[0]
                else:
                    retVal = None
        else:
            retVal = None
        return retVal

    def getServiceName(self, text2srch, inStruct=None):
        '''
        small sample of the data in the self.struct variable:
            ...
        '''
        # srchFields are the columns to search for the value
        # in the variable 'text2srch'
        if not inStruct:
            inStruct = self.struct
        retVal = None
        srchFields = [self.const.key_Service_Name, self.const.key_Host, self.const.key_GlobalName, self.const.key_SID]
        for entry in inStruct.keys():
            if text2srch.upper() == entry.upper():
                value = inStruct[entry][self.const.key_Description][self.const.key_ConnectData][self.const.key_Service_Name]
                value = self.clean(value)
                retVal = value
        if not retVal:
            # for srchField in srchFields:
                    # if entry.upper() == srchField.upper():
                    #    # now is the value the same
                    #    value =
            key, value = self.recursiveSearch(text2srch, inStruct)
            print 'found the value in the key: ', key
            retVal = value
        return retVal

    def getKey(self, srchKey, struct):
        retVal = None
        keys = struct.keys()
        for key in keys:
            if key.upper() == srchKey.upper():
                retVal = struct[key]
                break
            elif  isinstance(struct[key], dict):
                retVal = self.getKey(srchKey, struct[key])
                if retVal:
                    break
        retVal = self.clean(retVal)
        return retVal

    def getHostFromStruct(self, struct):
        retVal = self.getKey(self.const.key_Host, struct)
        retVal = self.clean(retVal)
        return retVal

    def getPortFromStruct(self, struct):
        retVal = self.getKey(self.const.key_Port, struct)
        retVal = self.clean(retVal)
        return retVal

    def getServicenameFromStruct(self, struct):
        self.logger.debug("struct {0}".formatSql(struct))
        retVal = self.getKey(self.const.key_Service_Name, struct)
        retVal = self.clean(retVal)
        return retVal

    def getSIDFromStruct(self, struct):
        self.logger.debug("struct {0}".formatSql(struct))
        retVal = self.getKey(self.const.key_SID, struct)
        retVal = self.clean(retVal)
        return retVal

    def getLabel(self, text2srch):
        '''
        provide a value that can exist in either:
           - label
           - servicename
           - instance name
           - host

        and will return the label that corresponds with that value.  Then retriving
        other information about that connection will be easier.
        '''
        retVal = None
        for entry in self.struct.keys():
            entrycln = self.clean(entry)
            if text2srch.upper() == entrycln.upper():
                retVal = entrycln
                break
        if not retVal:
            for entry in self.struct.keys():
                retList = self.recursiveSearch(text2srch, self.struct[entry])
                if retList:
                    if retList[1]:
                        retVal = entry
                        break
        return retVal

    def recursiveSearch(self, text2srch, struct):
        structKeys = struct.keys()
        retVal = None
        for structKey in structKeys:
            if isinstance(struct[structKey], dict):
                retVal = self.recursiveSearch(text2srch, struct[structKey])
                break
            else:
                value = self.clean(struct[structKey])
                print '{0} : {1}'.formatSql(text2srch, value)
                if text2srch == value or text2srch.upper() == value.upper():
                    retVal = [structKey, value]
                    print 'found the value'
                    break
        return retVal

    def getTNSEntryByLabel(self, label):
        retVal = None
        structKeys = self.struct.keys()
        if label:
            for entry in structKeys:
                if ',' in entry:
                    entryList = entry.split(',')
                    for singleEntry in entryList:
                        if singleEntry == label:
                            retVal = self.struct[entry]
                            break
                entryCln = self.clean(entry)
                if entryCln.upper() == label.upper():
                    retVal = self.struct[entry]
                    break
        return retVal


class TNSParser(object):

    def __init__(self, tnsNamesPathName):
        self.tnsNamesPathName = tnsNamesPathName
        # self.destFile = destFile
        self.populatedStruct = {}
        print 'self.tnsNamesPathName', self.tnsNamesPathName

        self.tnsNamesFH = open(self.tnsNamesPathName, 'r')
        self.tnsNamesContent = []
        regexMultiLineLabel = re.compile('^\s*\w+(\.\w+)*,\s*$', re.IGNORECASE)
        bufferStr = ''
        for tnsNameLine in self.tnsNamesFH:
            # move the multiline labels onto a single line
            if regexMultiLineLabel.match(tnsNameLine):
                bufferStr = bufferStr + tnsNameLine
            else:
                bufferStr = bufferStr + tnsNameLine
                bufferStr = bufferStr.replace('\n', ' ') + '\n'
                self.tnsNamesContent.append(bufferStr)
                # print 'bufferStr', bufferStr,
                bufferStr = ''
        self.tnsNamesFH.close()
        # self.contents = open(self.destFile, 'w')
        #labelRegex = re.compile("\w\.(\w\.)*\s*=\s*")

        #parseLevel = 0
        #dataStruct = {}
        self.labelLineLoc = None
        # self.pp = pprint.PrettyPrinter(indent=4)

    def parse(self):
        # self.getRootLabels()
        bracketLocations = self.getBracketLocations()
        rcrsr = RecurseStruct(bracketLocations)
        rcrsr.createStruct()
        structuredBrackets = rcrsr.getNestedStruct()
        populatedStruct = {}
        self.populateStruct(populatedStruct, structuredBrackets, True)
        # self.pp.pprint(populatedStruct)
        # DONE, this struct 'populatedStruct' can be used to retrieve values!
        return populatedStruct

    def getTNSNames(self):
        '''
        if the file has not already been parsed, it will parse it and
        populate the structure self.populatedStruct.

        It will then create a TNSNames object which includes a wrapper
        wrapper class around the data structure self.populatedStruct.
        '''
        populatedStruct = self.parse()
        TNSNamesObj = TNSNames(populatedStruct)

        return TNSNamesObj

    def populateStruct(self, newStruct, oldStruct, start=False):
        for elemStr in oldStruct.keys():
            elemInt = map(int, elemStr.split(','))
            elemLabel = self.getNestedLabel(elemInt)
            if start:
                rootLabel = self.getLabel(elemInt)
                newStruct[rootLabel] = {}
                newStruct[rootLabel][elemLabel] = {}
            elif oldStruct[elemStr]:
                newStruct[elemLabel] = {}
            else:
                # get the actual value for this parameter
                elemValue = self.getNestedValue(elemInt)
                newStruct[elemLabel] = elemValue
            if start:
                # print 'newStruct[rootLabel][elemLabel]', newStruct[rootLabel][elemLabel]
                # print 'oldStruct[elemStr]', oldStruct[elemStr]
                self.populateStruct(newStruct[rootLabel][elemLabel], oldStruct[elemStr])
            else:
                self.populateStruct(newStruct[elemLabel], oldStruct[elemStr])

    def getRootLabels(self):
        '''
        Searching for the start of a label
        '''
        firstLine = re.compile(r'^\s*\w(\.\w)*\s*=*\s*.*$')
        lineCnt = 0
        self.labelStruct = {}
        self.labelLineLoc = []
        # lineCnt = 0
        # while lineCnt < len(self.tnsNamesContent):
        #    tnsNamesLine = self.tnsNamesContent[lineCnt]
        for tnsNamesLine in self.tnsNamesContent:
            tnsNamesLineStrp = tnsNamesLine.strip()
            if (tnsNamesLineStrp) and tnsNamesLineStrp[0] <> '#':
                if firstLine.match(tnsNamesLine):
                    # if the last character has a , in it read the next line and
                    # append
                    # while tnsNamesLine[0] == ',':
                    # print 'labelLine:', tnsNamesLine
                    label, rest = tnsNamesLine.split('=')
                    label = label.strip()
                    self.labelStruct[label] = {}
                    self.labelLineLoc.append(lineCnt)
            lineCnt += 1

    def getLabel(self, currentBrackets):
        '''
        returns the root label for the bracket
        '''
        startLine = currentBrackets[0]
        if not self.labelLineLoc:
            self.getRootLabels()
        for labelPos in self.labelLineLoc:
            if labelPos < startLine:
                curValue = labelPos
            if labelPos > startLine:
                break
        label, rest = self.tnsNamesContent[curValue].split('=')
        label = label.strip()
        return label

    def getBracketLocations(self):
        openBrackets = []
        linecnt = 0
        level = 0

        position = {}
        arrayPos = 0

        for tnsLine in self.tnsNamesContent:
            tnsLineStripped = tnsLine.strip()
            if (tnsLineStripped) and tnsLineStripped[0] <> '#':
                # find the open bracets:
                charcntr = 0
                for char in tnsLine:
                    if char == '(':
                        openBrackets.append([linecnt, charcntr])
                        position[level] = arrayPos
                        arrayPos += 1
                        level += 1
                    elif char == ')':
                        level -= 1
                        openBrackets[position[level]].extend([linecnt, charcntr])
                    charcntr += 1
            linecnt += 1
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(openBrackets)
        # self.openBrackets = openBrackets
        return openBrackets

    def getValue(self, param):
        # deal with this later
        return 'value'

    def __getNestedData(self, bracketParams, paramType):
        startLine = bracketParams[0]
        endLine = bracketParams[2]
        startChar = bracketParams[1]
        endChar = bracketParams[3]

        data = []
        if startLine == endLine:
            data.append(self.tnsNamesContent[startLine][startChar:endChar + 1])
        else:
            dataCntr = startLine
            while endLine > dataCntr:
                if dataCntr == startLine:
                    data.append(self.tnsNamesContent[dataCntr][startChar:])
                elif dataCntr == endLine:
                    data.append(self.tnsNamesContent[dataCntr][:endChar + 1])
                else:
                    data.append(self.tnsNamesContent[dataCntr])
                dataCntr += 1
        # print 'data: {0} {1}'.formatSql(data, type(data))
        dataStr = ' '.join(data)
        paramsplit = dataStr.split('=')
        if paramType == 'label':
            retVal = paramsplit[0]
            retVal = retVal.replace('(', '')
        else:
            retVal = paramsplit[1]
        retVal = retVal.strip()
        # print 'retVal', retVal
        return retVal

    def getNestedLabel(self, bracketParams):
        return self.__getNestedData(bracketParams, 'label')

    def getNestedValue(self, bracketParams):
        return self.__getNestedData(bracketParams, 'value')


class RecurseStruct(object):

    def __init__(self, bracketList):
        self.pp = pprint.PrettyPrinter(indent=4)
        self.openBrackets = bracketList
        self.accounted = []
        self.struct = {}
        self.rootElems = self.getRootElements()

    def getRootElements(self):
        rootElems = []
        for bracket in self.openBrackets:
            if not rootElems:
                rootElems.append(bracket)
                currentRoot = bracket
            else:
                if not self.isNested(currentRoot, bracket):
                    rootElems.append(bracket)
                    currentRoot = bracket
        pp = pprint.PrettyPrinter(indent=4)
        # print 'ROOT ELEMENTS'
        # pp.pprint(rootElems)
        return rootElems

    def isNested(self, param1, param2):
        '''
        is param2 nested in param1
        These are nested
            param1 [6, 2, 14, 2]
            param2 [7, 4, 9, 4]

        These are not:
            param1 [12, 6, 12, 29],
            param2 [17, 2, 25, 2],


        example:
        '''
        retVal = True
        if param2[0] > param1[2]:
            retVal = False
        elif param2[0] == param1[2]:
            if param2[1] > param1[3]:
                retVal = False
        return retVal

    def getChildren(self, bracketList):
        children = []
        for chld in self.openBrackets:
            if chld[0] >= bracketList[0] and chld[2] <= bracketList[2]:
                if chld[0] == bracketList[0] and chld[2] == bracketList[2]:
                    if chld[1] > bracketList[1] and chld[3] <= bracketList[3]:
                        children.append(chld)
                else:
                    # yes its a child
                    children.append(chld)
        return children

    def createStruct(self):
        oneElem = self.rootElems[0]
        for rootElem in self.rootElems:
            # print 'rootElem', rootElem
            self.restruct(rootElem, self.struct)
        # self.pp.pprint(self.struct)
        # for rootElem in self.rootElems:
        #    rootElemStr = ','.join(map(str, rootElem))

    def restruct(self, elem, struct):
        # print 'elem', elem
        elemKey = ','.join(map(str, elem))
        if not elem in self.accounted:
            self.accounted.append(elem)
            struct[elemKey] = {}
            struct = struct[elemKey]
            elemChildren = self.getChildren(elem)
            for chld in elemChildren:
                self.restruct(chld, struct)

    def getNestedStruct(self):
        return self.struct
