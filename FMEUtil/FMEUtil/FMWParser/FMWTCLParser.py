'''
Created on Jul 24, 2018

@author: kjnether
'''

import logging
import re


class FMWTCLParser(object):

    def __init__(self, tclCodeList):
        self.logger = logging.getLogger(__name__)
        self.tclCodeList = tclCodeList
        self.fldMapLineRegex = re.compile('.+CopyAttributes.+')

    def getFieldMaps(self):
        '''
        This method will detect and extract field maps that get defined by drawing
        lines between columns.  To get field maps defined in the attributeRenamer
        transformers extract info from the xml object using the method
        _______
        
        searching for a line with a pattern similar to:
        FACTORY_DEF * RoutingFactory FACTORY_NAME "Destination Feature Type Routing Correlator"   INPUT FEATURE_TYPE *    ROUTE FME_GENERIC "$(SRC_SS_SCHEMA).$(SRC_FEATURE_1)" TO SHAPE __GO_TO_FINAL_OUTPUT_ROUTER__ <at>CopyAttributes<openparen>ENCODED<comma>FIRE_NUMBE<comma>FIRE_NUMBER<comma>VERSION_NU<comma>VERSION_NUMBER<comma>FIRE_SIZE_<comma>FIRE_SIZE_HECTARES<comma>FEATURE_CO<comma>FEATURE_CODE<comma>FIRE_STAT<comma>FIRE_STATUS<comma>FIRE_NT_ID<comma>FIRE_OF_NOTE_ID<comma>FIRE_NT_NM<comma>FIRE_OF_NOTE_NAME<comma>FIRE_NT_LK<comma>FIRE_OF_NOTE_URL<closeparen>,multi_writer_id,0,<at>SupplyAttributes<openparen>ENCODED<comma>__wb_out_feat_type__<comma>prot_current_fire_polys<closeparen> COORDINATE_SYSTEM BCALB-83 GEOMETRY   OUTPUT ROUTED FEATURE_TYPE * @FeatureType(ENCODED,@Value(__wb_out_feat_type__)) @RemoveAttributes(__wb_out_feat_type__)   OUTPUT NOT_ROUTED FEATURE_TYPE __nuke_me__ @Tcl2("FME_StatMessage 818059 [FME_GetAttribute fme_template_feature_type] 818060 818061 fme_warn")

        in the following line the field mapping is defined in the following
        sub section:
        CopyAttributes<openparen>ENCODED<comma>FIRE_NUMBE<comma>FIRE_NUMBER<comma>VERSION_NU<comma>VERSION_NUMBER<comma>FIRE_SIZE_<comma>FIRE_SIZE_HECTARES<comma>FEATURE_CO<comma>FEATURE_CODE<comma>FIRE_STAT<comma>FIRE_STATUS<comma>FIRE_NT_ID<comma>FIRE_OF_NOTE_ID<comma>FIRE_NT_NM<comma>FIRE_OF_NOTE_NAME<comma>FIRE_NT_LK<comma>FIRE_OF_NOTE_URL<closeparen>

        where source -> destinations are:
        ----------------------------------
        FIRE_NUMBER->FIRE_NUMBE
        VERSION_NUMBER->VERSION_NU
        FIRE_SIZE_HECTARES->FIRE_SIZE_
        etc..

        '''
        openParentRegex = re.compile('\<openparen\>ENCODED\<comma\>')
        closeParentRegex = re.compile('\<closeparen\>')
        fldMaps = []
        for tclCodeLine in self.tclCodeList:
            if self.fldMapLineRegex.match(tclCodeLine):
                # print 'matched line', tclCodeLine
                self.logger.debug('matched line: {0} '.format(tclCodeLine))
                # extract string from CopyAttributes on
                copyAtribsStr = 'CopyAttributes'
                srch = re.search(copyAtribsStr, tclCodeLine)
                if srch:
                    extractedString = tclCodeLine[srch.start():]
                    # sometimes there are lines like: 
                    #  @CopyAttributes(UTM_EASTING,LONGITUDE,UTM_NORTHING,LATITUDE)
                    # filtering those out for now.
                    if 'openparen' in extractedString:
                        # now do a search in the extracted string for 'openparen' and
                        # 'closeparen'
                        startPos = re.search(openParentRegex, extractedString).end()
                        endPos = re.search(closeParentRegex, extractedString).start()
                        # print 'startPos', startPos
                        # print 'endPos', endPos
                        # print 'extracted string:', extractedString[startPos:endPos]
                        self.logger.debug('startPos: {0}'.format(startPos))
                        self.logger.debug('endPos: {0}'.format(endPos))
                        self.logger.debug('extracted string: {0}'.format(extractedString[startPos:endPos]))
                        fieldMapParamString = extractedString[startPos:endPos]
                        fieldmapParamList = fieldMapParamString.split('<comma>')
                        # now rip through the list and re-order to list of lists
                        # where inner list:
                        #   - param 0 = source
                        #   - param 1 = dest
                        fldMap = []
                        for paramCnt in range(0, len(fieldmapParamList), 2):
                            tmplt = '{0} -> {1}'
                            # print tmplt.format( fieldmapParamList[paramCnt], fieldmapParamList[paramCnt + 1])
                            self.logger.debug(tmplt.format(fieldmapParamList[paramCnt], fieldmapParamList[paramCnt + 1]))
                            singleFieldMap = [fieldmapParamList[paramCnt + 1], fieldmapParamList[paramCnt]]
                            fldMap.append(singleFieldMap)
                        if fldMap:
                            fldMaps.append(fldMap)
        return fldMaps

