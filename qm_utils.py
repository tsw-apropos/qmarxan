"""
/***************************************************************************
 utils - contains some core functions to simplify code base of QMarxan plugin
                              -------------------
        begin                : 2013-08-23
        copyright            : (C) 2013 by Apropos Information Systems Inc.
        email                : tsw@aproposinfosystems.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import *
import rasterstats, fiona
from PyQt4 import QtCore
import qgis.utils
import os, time, sys


class qmCalculateThread(QtCore.QThread):

    # initialize class
    def __init__(self,puFile,puId,srcFile,outCnt,measType,calcField,operator,outFldName,writeToCSV):
        super(qmCalculateThread, self).__init__()
        # Import required plugins and if missing show the plugin's name
        ftPath = os.path.join(str(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path()), 'python/plugins/fTools')
        if not ftPath in sys.path:
            sys.path.append(ftPath)
        req_plugin = "ftools 0.5.10"
        try:
            import ftools_utils
        except:
            QtGui.QMessageBox.information(self, self.tr("Missing Plugins"), 
                    self.tr("Missing plugin: %s" % req_plugin))
        #self.parent = parentObject
        self.running = False
        self.puFile = str(puFile)
        self.puId = str(puId)
        self.srcFile = str(srcFile)
        self.outCnt = str(outCnt)
        self.measType = str(measType)
        self.calcField = str(calcField)
        self.operator = str(operator)
        self.outFldName = str(outFldName)
        self.issueWarning = False
        self.warningText = ''
        self.logText = ''
        self.puProblemFeatures = []
        self.message = ''
        self.writeToCSV = writeToCSV
        self.ccPU = 0

    def run(self):
        import ftools_utils
        self.running = True
        tfnb = 'tempint' + str(os.getpid())
        tfn = tfnb + '.shp'
        tfp = os.path.dirname(self.puFile)
        outFileName = os.path.join(tfp,tfn)
        isRaster = False
        rasterLayer = ''
        # determine if raster and process accordingly
        if os.path.splitext(os.path.basename(self.srcFile))[1] <> '.shp':
           for key, value in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if ('raster' in str(value.__class__).lower()) and \
                str(value.source()) == self.srcFile:
                    isRaster = True
                    rasterLayer = value
        cellSize = 0.0
        cellSize = (rasterLayer.extent().height() / rasterLayer.height()) \
            * (rasterLayer.extent().width() / rasterLayer.width())
        if isRaster == True:
            layers = ftools_utils.getLayerNames([QGis.Polygon])
            temp = os.path.splitext(os.path.basename(self.puFile))[0]
            if temp in layers:
                puLyr = ftools_utils.getVectorLayerByName(temp)
                self.ccPU = int(puLyr.dataProvider().fieldCount())
            # user rasterstats library to calculate values and aggregate data
            if self.outCnt == 'single':
                # determine mean value in PU
                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Raster Tabulation')
                ok, valDict, subKeys = self.calcRasterStats(self.srcFile,self.puFile,self.puId,'mean',cellSize)
                # update table
                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Update PU Layer')
                ok, self.message = self.addUpdateColumn(puLyr,self.puId,self.outFldName,valDict)
                if ok == -1:
                    self.stop()
            else:
                # treat raster layer as categorical layer and have columns
                # for each value in final output
                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Raster Tabulation')
                ok, valDict, subKeys = self.calcRasterStats(self.srcFile,self.puFile,self.puId,'categorical',cellSize)
                # update table
                fldList = []
                for key in subKeys:
                    fldList.append('%s%03d' % (self.outFldName,key))
                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Update PU Layer')
                ok, self.message = self.addUpdateColumns(puLyr,self.puId,fldList,subKeys,valDict)
                if ok == -1:
                    self.stop()
        else:
            # determine if single or multiple field output
            if self.outCnt == 'single':
                # determine type of single measure
                if self.measType == 'measure' or self.measType == 'presence':
                    # do intersection
                    self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Intersection')
                    ok, self.message, puLyr, valField = self.intersectLayers(self.srcFile,self.puFile,outFileName,[],[self.puId])
                    self.ccPU = int(puLyr.dataProvider().fieldCount())
                    if ok == -1:
                        self.stop()
                        print self.message
                    else:
                        # ok so now aggregate the data
                        outLyr = QgsVectorLayer(outFileName, 'output', 'ogr')
                        if outLyr.isValid():
                            outPv = outLyr.dataProvider()
                            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Data Aggregation')
                            ok, valDict = self.aggregateById(outPv,('i'+self.puId)[:10],valField,'',self.operator,self.measType)
                            if ok == -1:
                                self.stop()
                            else:
                                # aggregation worked so now update the pu layer
                                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Update PU Layer')
                                ok, self.message = self.addUpdateColumn(puLyr,self.puId,self.outFldName,valDict)
                                if ok == -1:
                                    self.stop()
                elif self.measType == 'calculate':
                    # do intersection
                    self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Intersection')
                    ok, self.message, puLyr, valField = self.intersectLayers(self.srcFile,self.puFile,outFileName,[self.calcField],[self.puId])
                    self.ccPU = int(puLyr.dataProvider().fieldCount())
                    if ok == -1:
                        self.stop()
                        print self.message
                    else:
                        # ok so now aggregate the data
                        outLyr = QgsVectorLayer(outFileName, 'output', 'ogr')
                        if outLyr.isValid():
                            outPv = outLyr.dataProvider()
                            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Data Aggregation')
                            ok, valDict = self.aggregateById(outPv,('i'+self.puId)[:10],valField,('s'+self.calcField)[:10],self.operator,self.measType)
                            if ok == -1:
                                self.stop()
                            else:
                                # aggregation worked so now update the pu layer
                                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Update PU Layer')
                                ok, self.message = self.addUpdateColumn(puLyr,self.puId,self.outFldName,valDict)
                                if ok == -1:
                                    self.stop()
                else:
                    self.stop()
            else:
                # do intersection
                self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Intersection')
                ok, self.message, puLyr, valField = self.intersectLayers(self.srcFile,self.puFile,outFileName,[self.calcField],[self.puId])
                self.ccPU = int(puLyr.dataProvider().fieldCount())
                if ok == -1:
                    self.stop()
                    print self.message
                else:
                    # ok so now aggregate the data
                    outLyr = QgsVectorLayer(outFileName, 'output', 'ogr')
                    if outLyr.isValid():
                        outPv = outLyr.dataProvider()
                        self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Data Aggregation')
                        ok, valDict, subKeys = self.aggregateByIdAndMod(outPv,('i'+self.puId)[:10],valField,('s'+self.calcField)[:10])
                        if ok == -1:
                            self.stop()
                        else:
                            # aggregation worked so now update the pu layer
                            fldList = []
                            for key in subKeys:
                                fldList.append('%s%03d' % (self.outFldName,key))
                            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Update PU Layer')
                            ok, self.message = self.addUpdateColumns(puLyr,self.puId,fldList,subKeys,valDict)
                            if ok == -1:
                                self.stop()
            if os.path.exists(outFileName):
                outPv = None
                outLyr = None
                # update successful so now delete the temporary file 
                os.remove(os.path.join(tfp,tfnb+'.shp'))
                os.remove(os.path.join(tfp,tfnb+'.dbf'))
                os.remove(os.path.join(tfp,tfnb+'.shx'))
                os.remove(os.path.join(tfp,tfnb+'.prj'))
                os.remove(os.path.join(tfp,tfnb+'.qpj'))
            self.stop()
        self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Completed')
        # create log entry
        if self.issueWarning:
            self.logText = 'pu_layer: '+self.puFile+os.linesep
            self.logText = self.logText+'puid: '+self.puId+os.linesep
            self.logText = self.logText+'measure_layer: '+self.srcFile+os.linesep
            self.logText = self.logText+'field_output: '+self.outCnt+os.linesep
            self.logText = self.logText+'measure_type: '+self.measType+os.linesep
            self.logText = self.logText+'calculation_field: '+self.calcField+os.linesep
            self.logText = self.logText+'operator: '+self.operator+os.linesep
            self.logText = self.logText+'output_name: '+self.outFldName+os.linesep+os.linesep
            if len(self.puProblemFeatures) > 0:
                self.logText = self.logText+'Possible errors were detected with: '+self.warningText+os.linesep+os.linesep
                self.logText = self.logText+'Examination of the below PU layer features is necessary.'+os.linesep
                self.logText = self.logText+'Spatially coincident features in measure layer may be the cause of the error.'+os.linesep
                for fid in self.puProblemFeatures:
                    self.logText = self.logText+'%s%s' % (fid, os.linesep)
            else:
                self.logText = self.logText+self.message+os.linesep+self.warningText+os.linesep
            self.logText = self.logText + os.linesep

    def stop(self):
        self.running = False

    #
    # intersection
    #
    
    # intersect layers to create new layer with desired field names
    def intersectLayers(self, srcLayerName, intLayerName, outFName, srcSelFields, intSelFields, srcUseSelected=False, intUseSelected=False):

        import ftools_utils
        self.message = 'Intersection success'
        valField = ''
        # load layers if needed
        layers = ftools_utils.getLayerNames([QGis.Polygon,QGis.Point,QGis.Line])
        temp = os.path.splitext(os.path.basename(srcLayerName))[0]
        if temp in layers:
            srcLyr = ftools_utils.getVectorLayerByName(temp)
        else:
            srcLyr = QgsVectorLayer(srcLayerName, 'src', 'ogr')
            if not srcLyr.isValid():
                self.issueWarning = True
                if self.warningText == '':
                    self.warningText = 'oth;'
                else:
                    self.warningText += 'oth;'
                self.message = '%s failed to load' % srcLayerName
                return(-1, self.message, None, None)
                self.issueWarning = True
        temp = os.path.splitext(os.path.basename(intLayerName))[0]
        if temp in layers:
            intLyr = ftools_utils.getVectorLayerByName(temp)
        else:
            intLyr = QgsVectorLayer(intLayerName, 'int', 'ogr')
            if not intLyr.isValid():
                self.issueWarning = True
                if self.warningText == '':
                    self.warningText = 'oth;'
                else:
                    self.warningText += 'oth;'
                self.message = '%s failed to load' % intLayerName
                return(-1, self.message, None, None)
        # confirm that their CRS matches
        if srcLyr.crs().isValid() and srcLyr.crs() == intLyr.crs():
            pass
        else:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth;'
            else:
                self.warningText += 'oth;'
            self.message = 'Map projections are not valid or do not match'
            return(-1, self.message, None, None)
        # set up data providers
        srcPv = srcLyr.dataProvider()
        intPv = intLyr.dataProvider()
        attrMList = []
        # create writer for intersection results
        outFields = 'si_id'
        try:
            # get source fields
            srcFields = srcPv.fields().values()
            intFields = intPv.fields().values()
            fieldDict = {0:QgsField("si_id", QtCore.QVariant.Int)}
            x = 1
            # add source fields
            for field in srcSelFields:
                y = 0
                for fObj in srcFields:
                    if fObj.name() == field:
                        newName = ('s' + fObj.name())[:10]
                        fieldDict[x] = QgsField(newName,fObj.type())
                        outFields = outFields + ', ' + newName
                        attrMList.append([y,'src',fObj.name(),x,'out',newName])
                        x = x + 1
                    y = y + 1
            # add intersect fields
            for field in intSelFields:
                y = 0
                for fObj in intFields:
                    if fObj.name() == field:
                        newName = ('i' + fObj.name())[:10]
                        fieldDict[x] = QgsField(newName,fObj.type())
                        outFields = outFields + ', ' + newName
                        attrMList.append([y,'int',fObj.name(),x,'out',newName])
                        x = x + 1
                    y = y + 1
            # add calc field
            if srcLyr.geometryType() == QGis.Polygon:
                valField = 'si_area'
                fieldDict[x] = QgsField('si_area', QtCore.QVariant.Double, "Real", 19, 10)
                outFields = outFields + ', si_area'
            elif srcLyr.geometryType() == QGis.Line:
                valField = 'si_len'
                fieldDict[x] = QgsField('si_len', QtCore.QVariant.Double, "Real", 19, 10)
                outFields = outFields + ', si_len'
            else:
                valField = 'si_cnt'
                fieldDict[x] = QgsField('si_cnt', QtCore.QVariant.Double, "Real", 19, 10)
                outFields = outFields + ', si_cnt'
            # create writer
            writer = QgsVectorFileWriter(outFName, srcPv.encoding(), fieldDict, srcPv.geometryType(), srcLyr.crs())
        except:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth;'
            else:
                self.warningText += 'oth;'
            self.message = 'Could not create %s with fields: %s' % (outFName, outFields)
            return(-1,self.message,None,None)
        # create spatial index for intersect layer
        try:
            intFeat = QgsFeature()
            intGeom = QgsGeometry()
            intIndex = QgsSpatialIndex()
            intPv.select([], QgsRectangle(), True, False)
            while intPv.nextFeature(intFeat):
                intIndex.insertFeature(intFeat)
        except:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth;'
            else:
                self.warningText += 'oth;'
            self.message = 'Could not create spatial index for %s ' % intLayerName
            return(-1,self.message,None,None)
        # begin stepping through source layer
        try:
            # reset blank feature holders
            # intersect layer
            intPv.rewind()
            intFeat = QgsFeature()
            intAttrs = intPv.attributeIndexes()
            intPv.select(intAttrs)
            # source layer
            srcFeat = QgsFeature()
            srcAttrs = srcPv.attributeIndexes()
            srcPv.select(srcAttrs)
            # destination
            ok = -1
            outFeat = QgsFeature()
            x = 1
            y = 1
            if srcUseSelected == False:
                # emit src feature count
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
                nFeat = srcLyr.featureCount()
                self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
                # intersect using all source layer featuers
                if intUseSelected == False:
                    # intersect using all intersect layer features
                    while srcPv.nextFeature(srcFeat):
                        # emit progress update
                        self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),y)
                        # get the geometry & attributes
                        # test if source bounding box intersects with the intersect layer feature
                        srcGeom = QgsGeometry(srcFeat.geometry())
                        features = intIndex.intersects(srcGeom.boundingBox())
                        for fid in features:
                            # retreive all the information for the selected feature
                            intPv.featureAtId(int(fid), intFeat, True, intAttrs)
                            ok, outFeat = self.intersectFeatures(x,srcFeat,intFeat,srcPv,intPv,fieldDict,attrMList)
                            if ok == 0:
                                # write feature
                                writer.addFeature(outFeat)
                                x = x + 1
                        y += 1 
                else:
                    # intersect using selected intersect layer features
                    intSelectedIds = intLyr.selectedFeaturesIds()
                    # begin processing
                    while srcPv.nextFeature(srcFeat):
                        # emit progress update
                        self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),y)
                        # get the geometry & attributes
                        # test if source bounding box intersects with the intersect layer feature
                        srcGeom = QgsGeometry(srcFeat.geometry())
                        features = intIndex.intersects(srcGeom.boundingBox())
                        for fid in features:
                            if fid in intSelectedIds:
                                # retreive all the information for the selected feature
                                intPv.featureAtId(int(fid), intFeat, True, intAttrs)
                                ok, outFeat = self.intersectFeatures(x,srcFeat,intFeat,srcPv,intPv,fieldDict,attrMList)
                                if ok == 0:
                                    # write feature
                                    writer.addFeature(outFeat)
                                    x = x + 1
                        y += 1 
            else:
                srcSelectedIds = srcLyr.selectedFeaturesIds()
                # emit src feature count
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
                self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,len(srcSelectedIds)))
                # intersect using selected source layer featuers
                if intUseSelected == False:
                    # intersect using all intersect layer features
                    while srcPv.nextFeature(srcFeat):
                        # emit progress update
                        self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),y)
                        if srcFeat.id() in srcSelectedIds:
                            # get the geometry & attributes
                            # test if source bounding box intersects with the intersect layer feature
                            srcGeom = QgsGeometry(srcFeat.geometry())
                            features = intIndex.intersects(srcGeom.boundingBox())
                            for fid in features:
                                # retreive all the information for the selected feature
                                intPv.featureAtId(int(fid), intFeat, True, intAttrs)
                                ok, outFeat = self.intersectFeatures(x,srcFeat,intFeat,srcPv,intPv,fieldDict,attrMList)
                                if ok == 0:
                                    # write feature
                                    writer.addFeature(outFeat)
                                    x = x + 1
                        y += 1
                else:
                    # intersect using selected intersect layer features
                    intSelectedIds = intLyr.selectedFeaturesIds()
                    # begin processing
                    while srcPv.nextFeature(srcFeat):
                        # emit progress update
                        self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),y)
                        if srcFeat.id() in srcSelectedIds:
                            # get the geometry & attributes
                            # test if source bounding box intersects with the intersect layer feature
                            srcGeom = QgsGeometry(srcFeat.geometry())
                            features = intIndex.intersects(srcGeom.boundingBox())
                            for fid in features:
                                if fid in intSelectedIds:
                                    # retreive all the information for the selected feature
                                    intPv.featureAtId(int(fid), intFeat, True, intAttrs)
                                    ok, outFeat = self.intersectFeatures(x,srcFeat,intFeat,srcPv,intPv,fieldDict,attrMList)
                                    if ok == 0:
                                        # write feature
                                        writer.addFeature(outFeat)
                                        x = x + 1
                        y += 1
        except:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth;'
            else:
                self.warningText += 'oth;'
            self.message = "Failed to complete intersection"
            return(-1,self.message,None,None)
        # completed successfully
        del writer
        intPv = None
        return(0,self.message,intLyr,valField)

    # intersect geometries
    def intersectFeatures(self,idVal,srcFeat,intFeat,srcPv,intPv,fieldDict,attrMList):

        import ftools_utils
        ok = -1
        outFeat = QgsFeature()
        try:
            srcGeom = QgsGeometry(srcFeat.geometry())
            intMap = intFeat.attributeMap()
            srcMap = srcFeat.attributeMap()
            # test if real intersection
            try:
                tmpGeom = QgsGeometry(intFeat.geometry())
                if srcGeom.intersects(tmpGeom):
                    # calculate intersection
                    try:
                        int_geom = QgsGeometry(srcGeom.intersection(tmpGeom))
                        if int_geom.wkbType() == 0:
                            int_com = srcGeom.combine(tmpGeom)
                            int_sym = srcGeom.symDifference(tmpGeom)
                            int_geom = QgsGeometry(int_com.difference(int_sym))
                        gList = ftools_utils.getGeomType(srcGeom.wkbType())
                        # check if geometry ok
                        if int_geom.wkbType() in [1,4] or int_geom.wkbType() in gList:
                            # create new feature
                            # start with geometry
                            outFeat.setGeometry(int_geom)
                            ok = 0
                            # then attributes
                            for key, value in fieldDict.iteritems():
                                fldName = value.name()
                                if key == 0:
                                    outFeat.addAttribute(0,idVal)
                                else:
                                    if fldName == 'si_area':
                                        measure = QgsDistanceArea()
                                        #measure.setProjectionsEnabled(True)
                                        area = measure.measure(int_geom)
                                        outFeat.addAttribute(key,area)
                                    elif fldName == 'si_len':
                                        outFeat.addAttribute(key,int_geom.length())
                                    elif fldName == 'si_cnt':
                                        outFeat.addAttribute(key,1.0)
                                    else:
                                        # use master attribute list to copy over
                                        for i in attrMList:
                                            if fldName == i[5]:
                                                if i[1] == 'src':
                                                    if srcMap[i[0]].typeName() == 'QString':
                                                        transValue = srcMap[i[0]].toString()
                                                    elif srcMap[i[0]].typeName() == 'int':
                                                        transValue =  srcMap[i[0]].toInt()[0]
                                                    else:
                                                        transValue =  srcMap[i[0]].toDouble()[0]
                                                    outFeat.addAttribute(i[3],transValue)
                                                elif i[1] == 'int':
                                                    if intMap[i[0]].typeName() == 'QString':
                                                        transValue = intMap[i[0]].toString()
                                                    elif intMap[i[0]].typeName() == 'int':
                                                        transValue =  intMap[i[0]].toInt()[0]
                                                    else:
                                                        transValue =  intMap[i[0]].toDouble()[0]
                                                    outFeat.addAttribute(i[3],transValue)
                    except:
                        self.issueWarning = True
                        if self.warningText == '':
                            self.warningText = 'pu_layer;'
                        elif not 'pu_layer' in self.warningText:
                            self.warningText += 'pu_layer;'
                        if self.warningText == '':
                            self.warningText = 'measure_layer;'
                        elif not 'measure_layer' in self.warningText:
                            self.warningText += 'measure_layer;'
                        featAttr = ''
                        for i in attrMList:
                            if i[1] == 'int':
                                if intMap[i[0]].typeName == 'QString':
                                    featAttr += intMap[i[0]].toString()+';'
                                elif intMap[i[0]].typeName() == 'int':
                                    featAttr += str(intMap[i[0]].toInt()[0])+';'
                                else:
                                    featAttr += str(intMap[i[0]].toDouble()[0])+';'
                        self.puProblemFeatures.append(featAttr)
            except:
                self.issueWarning = True
                if self.warningText == '':
                    self.warningText = 'pu_layer;'
                elif not 'pu_layer' in self.warningText:
                    self.warningText += 'pu_layer;'
                featAttr = ''
                for i in attrMList:
                    if i[1] == 'int':
                        if intMap[i[0]].typeName == 'QString':
                            featAttr += intMap[i[0]].toString()+';'
                        elif intMap[i[0]].typeName() == 'int':
                            featAttr += str(intMap[i[0]].toInt()[0])+';'
                        else:
                            featAttr += str(intMap[i[0]].toDouble()[0])+';'
                self.puProblemFeatures.append(featAttr)
        except:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'measure_layer;'
            elif not 'measure_layer' in self.warningText:
                self.warningText += 'measure_layer;'
            featAttr = ''
            for i in attrMList:
                if i[1] == 'int':
                    if intMap[i[0]].typeName == 'QString':
                        featAttr += intMap[i[0]].toString()+';'
                    elif intMap[i[0]].typeName() == 'int':
                        featAttr += str(intMap[i[0]].toInt()[0])+';'
                    else:
                        featAttr += str(intMap[i[0]].toDouble()[0])+';'
            self.puProblemFeatures.append(featAttr)
        return(ok,outFeat)

    #
    # data aggregation
    #

    # aggregate data by id
    # used for single measures
    def aggregateById(self, inPv, keyField, valField, modField, aggOp='sum', modOp='measure'):

        # setup variables
        inFeat = QgsFeature()
        allAttrs = inPv.fields()
        selectedAttrs = []
        keyIdx = -1
        valIdx = -1
        modIdx = -1
        valDict = {}
        modDict = {}
        # set indexes
        for key, fld in allAttrs.iteritems():
            if fld.name() == keyField:
                keyIdx = key
                selectedAttrs.append(key)
            elif fld.name() == valField:
                valIdx = key
                selectedAttrs.append(key)
            elif fld.name() == modField:
                modIdx = key
                selectedAttrs.append(key)

        # confirm that we can do this
        if keyIdx < 0 or valIdx < 0 or keyIdx == valIdx:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth;'
            else:
                self.warningText += 'oth;'
            return(-1,{})
        
        # retrieve attributes only, skip geometry
        inPv.select(selectedAttrs,QgsRectangle(),False)
        # emit feature count
        self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
        nFeat = inPv.featureCount()
        self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
        
        # iterate over features put values in dictionaries
        x = 1
        if modIdx <> -1:
            while inPv.nextFeature(inFeat):
                # emit progress udpate
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                featAttrs = inFeat.attributeMap()
                keyVal = featAttrs[keyIdx].toInt()[0]
                valVal = featAttrs[valIdx].toDouble()[0]
                modVal = featAttrs[modIdx].toDouble()[0]
                if keyVal in valDict:
                    valDict[keyVal].append(valVal)
                    modDict[keyVal].append(modVal)
                else:
                    valDict[keyVal] = [valVal]
                    modDict[keyVal] = [modVal]
                x += 1
        else:
            while inPv.nextFeature(inFeat):
                # emit progress udpate
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                featAttrs = inFeat.attributeMap()
                keyVal = featAttrs[keyIdx].toInt()[0]
                valVal = featAttrs[valIdx].toDouble()[0]
                if keyVal in valDict:
                    valDict[keyVal].append(valVal)
                else:
                    valDict[keyVal] = [valVal]
                x += 1

        # process results
        if modOp == 'measure':
            # no modifer operation is valid
            if aggOp == 'sum':
                for key, val in valDict.iteritems():
                    valDict[key] = sum(valDict[key])
            elif aggOp == 'mean':
                for key, val in valDict.iteritems():
                    valDict[key] = sum(valDict[key])/len(valDict[key])
            elif aggOp == 'max':
                for key, val in valDict.iteritems():
                    valDict[key] = max(valDict[key])
            elif aggOp == 'min':
                for key, val in valDict.iteritems():
                    valDict[key] = min(valDict[key])
            elif aggOp == 'count':
                for key, val in valDict.iteritems():
                    valDict[key] = len(valDict[key])
        elif modOp == 'presence':
            for key, val in valDict.iteritems():
                valDict[key] = 1
        elif modOp == 'calculate':
            if aggOp == 'sum':
                for key, val in valDict.iteritems():
                    valDict[key] = sum([a*b for a,b in zip(valDict[key],modDict[key])])
            elif aggOp == 'mean':
                for key, val in valDict.iteritems():
                    valDict[key] = sum([a*b for a,b in zip(valDict[key],modDict[key])])/len(valDict[key])
            elif aggOp == 'max':
                for key, val in valDict.iteritems():
                    valDict[key] = max([a*b for a,b in zip(valDict[key],modDict[key])])
            elif aggOp == 'min':
                for key, val in valDict.iteritems():
                    valDict[key] = min([a*b for a,b in zip(valDict[key],modDict[key])])
            elif aggOp == 'count':
                for key, val in valDict.iteritems():
                    valDict[key] = len(valDict[key])
                
        return(0,valDict)

    # aggregate data by id and modifier field
    # used for multiple measures  
    def aggregateByIdAndMod(self, inPv, keyField, valField, modField):

        # setup variables
        inFeat = QgsFeature()
        allAttrs = inPv.fields()
        selectedAttrs = []
        keyIdx = -1
        valIdx = -1
        modIdx = -1
        valDict = {}
        modDict = {}
        # set indexes
        for key, fld in allAttrs.iteritems():
            if fld.name() == keyField:
                keyIdx = key
                selectedAttrs.append(key)
            elif fld.name() == valField:
                valIdx = key
                selectedAttrs.append(key)
            elif fld.name() == modField:
                modIdx = key
                selectedAttrs.append(key)
        # confirm ok
        if keyIdx == -1 or valIdx == -1 or modIdx == -1:
            self.issueWarning = True
            if self.warningText == '':
                self.warningText = 'oth (key: %d (%s), val: %d (%s), mod: %d (%s));' % (keyIdx,keyField,valIdx,valField,modIdx,modField)
            else:
                self.warningText += 'oth (key: %d (%s), val: %d (%s), mod: %d (%s));' % (keyIdx,keyField,valIdx,valField,modIdx,modField)
            return(-1,valDict,[])
        # retrieve attributes only, skip geometry
        inPv.select(selectedAttrs,QgsRectangle(),False)
        # emit feature count
        # get values
        while inPv.nextFeature(inFeat):
            # emit progress update
            featAttrs = inFeat.attributeMap()
            keyVal = featAttrs[keyIdx].toInt()[0]
            valVal = featAttrs[valIdx].toDouble()[0]
            modVal = featAttrs[modIdx].toDouble()[0]
            if keyVal in valDict:
                valDict[keyVal].append(valVal)
                modDict[keyVal].append(modVal)
            else:
                valDict[keyVal] = [valVal]
                modDict[keyVal] = [modVal]
        # aggregate values
        subKeys = []
        for val in modDict.values():
            for subVal in val:
                if not subVal in subKeys:
                    subKeys.append(int(subVal))
        subKeys.sort()
        for key, val in valDict.iteritems():
            modVals = modDict[key]
            measVals = val
            columns = {}
            for i in range(len(modVals)):
                col = int(modVals[i])
                if col in columns:
                    columns[col] += measVals[i]
                else:
                    columns[col] = measVals[i]
            valDict[key] = columns

        return(0,valDict,subKeys)

    #
    # raster calculation & aggregation
    #

    # calculate rasterstats
    def calcRasterStats(self,srcFile,puFile,key,action,cellSize):
        results = {}
        fldList = []
        if action == 'mean':
            puLyr = fiona.open(puFile)
            nFeat = len(puLyr)
            self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
            ok = True
            x = 1
            while ok:
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                try:
                    feat = puLyr.next()
                    rowres = rasterstats.raster_stats(feat,srcFile,stats='mean')
                    results[int(feat['properties'][key])] = rowres[0]['mean']
                except:
                    ok = False
                x += 1
            puLyr.close()
        else:
            # calculate
            puLyr = fiona.open(puFile)
            nFeat = len(puLyr)
            self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
            ok = True
            x = 1
            while ok:
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                try:
                    feat = puLyr.next()
                    rowres = rasterstats.raster_stats(feat,srcFile,categorical=True)
                    results[feat['properties'][key]] = rowres[0]
                    fldList = list(set(fldList + rowres[0].keys()))
                except:
                    ok = False
                x += 1
            puLyr.close()
            # aggregate
            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Raster Aggregation')
            self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
            if '__fid__' in fldList:
                fldList.remove('__fid__')
            fldList.sort()
            x = 1
            for key, value in results.iteritems():
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                results[key] = {}
                for fld in fldList:
                    if fld in value.keys():
                        results[key][fld] = value[fld] * cellSize
                    else:
                        results[key][fld] = 0.0
                x += 1
        return(0,results,fldList)

    #
    # data update
    #

    # generic function 
    # get field indexes
    def getFieldIndexes(self, lyr, fldList):
        # determine if field exists
        updatePv = lyr.dataProvider()
        allAttrs = updatePv.fields()
        keys = [-1] * len(fldList)
        for key, fld in allAttrs.iteritems():
            for i in range(len(fldList)):
                if fld.name() == fldList[i]:
                    keys[i] = key
        return(keys)
        
    # generic function
    # create new real field
    def createNewFields(self, lyr, fldList):
        self.message = 'Success'
        for fldName in fldList:
            lyr.startEditing()
            lyr.beginEditCommand("Attribute(s) added")
            newField = QgsField(fldName, QtCore.QVariant.Double, "Real", 19, 10)
            if not lyr.addAttribute(newField):
                self.message = "Could not add the new field(s) to the PU layer."
                lyr.destroyEditCommand()
                if not updateLyr.isEditable():
                    lyr.rollBack()
                return (-1, self.message)
            # commit changes to table structure
            lyr.endEditCommand()
            lyr.commitChanges()
        #lyr.setModified(True, False)
        return(0, self.message)

    # add if needed and update contents of a single column
    def addUpdateColumn(self, updateLyr, keyField, updateField, updateDict):

        if self.writeToCSV == False:
            # setup layer for editing by locking it
            updateLyr.blockSignals(True)
            if not updateLyr.isEditable():
                updateLyr.startEditing()
                if not updateLyr.isEditable():
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    self.message = "Unable to edit input pu layer: Please choose a layer with edit capabilities."
                    return (-1, self.message)
            # get field indexes
            keyIdx,valIdx = self.getFieldIndexes(updateLyr,[keyField,updateField])
            # add if needed
            if valIdx == -1:
                if not updateLyr.dataProvider().capabilities() > 7: # can't add attributes
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    self.message = "Data provider does not support adding attributes: " + \
                        "Cannot add required field."
                    if not updateLyr.isEditable():
                        updateLyr.rollBack()
                    return(-1,self.message)
                # try to create new field if possible, otherwise write to CSV
                # check column count and write to file if needed
                if self.ccPU >= 254:
                    self.writeToCSV = True;
                else:
                    ok, self.message = self.createNewFields(updateLyr, [updateField])
                    if ok == -1:
                        return(ok, self.message)
                    # update field index
                    keyIdx,valIdx = self.getFieldIndexes(updateLyr,[keyField,updateField])
            if self.writeToCSV == False:
                if keyIdx == -1 or valIdx == -1:
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    return(-1,'broken')
                # update values
                # put update layer into edit state
                updateLyr.blockSignals(True)
                if not updateLyr.isEditable():
                    updateLyr.startEditing()
                    if not updateLyr.isEditable():
                        self.issueWarning = True
                        if self.warningText == '':
                            self.warningText = 'oth;'
                        else:
                            self.warningText += 'oth;'
                        self.message = "Unable to edit input pu layer: Please choose a layer with edit capabilities."
                        return (-1, self.message)
                # begin editing
                updateLyr.select([keyIdx,valIdx], QgsRectangle(), False, False)
                updateLyr.beginEditCommand("Data updated")
                updateFeat = QgsFeature()
                # emit featuer count
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
                nFeat = updateLyr.featureCount()
                self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
                x = 1
                while updateLyr.nextFeature(updateFeat):
                    # emit progress update
                    self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                    featAttrs = updateFeat.attributeMap()
                    keyVal = featAttrs[keyIdx].toInt()[0]
                    if keyVal in updateDict:
                        writeVal = updateDict[keyVal]
                    else:
                        writeVal = 0.0
                    updateLyr.changeAttributeValue(updateFeat.id(), valIdx, writeVal, False)
                    x += 1
                updateLyr.endEditCommand()
                updateLyr.commitChanges()
                # unblock signals
                updateLyr.blockSignals(False)

        if self.writeToCSV == True:
            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Writing CSV')
            outDir = os.path.dirname(str(updateLyr.source()))
            outFName = os.path.splitext(os.path.basename(self.puFile))[0] + \
                '_' + os.path.splitext(os.path.basename(self.srcFile))[0] + '.csv'
            outPath = os.path.join(outDir,outFName)
            f = open(outPath,'w')
            f.write('%s,%s%s' % (keyField,updateField,os.linesep))
            self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
            nFeat = len(updateDict)
            self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
            x = 1
            for key,value in updateDict.iteritems():
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                if value <> 0.0 and value <> None:
                    f.write('%s,%s%s' % (str(key),str(value),os.linesep))
                x += 1
            f.close()


        return(0,'Success')

    # add if needed and update contents of multiple columns
    def addUpdateColumns(self, updateLyr, keyField, updateFields, updateFieldValues, updateDict):

        if self.writeToCSV == False:
            # setup layer for editing by locking it
            updateLyr.blockSignals(True)
            if not updateLyr.isEditable():
                updateLyr.startEditing()
                if not updateLyr.isEditable():
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    self.message = "Unable to edit input pu layer: Please choose a layer with edit capabilities."
                    return (-1, self.message)
            # get field indexes
            fldIdxs = self.getFieldIndexes(updateLyr,[keyField] + updateFields)
            keyIdx = fldIdxs[0]
            # add new fields if needed
            if -1 in fldIdxs:
                if not updateLyr.dataProvider().capabilities() > 7: # can't add attributes
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    self.message = "Data provider does not support adding attributes: " + \
                        "Cannot add required field."
                    if not updateLyr.isEditable():
                        updateLyr.rollBack()
                    return(-1,self.message)
                    
                # try to create new fields 
                newList = []
                for i in range(len(fldIdxs)):
                    if fldIdxs[i] == -1:
                        # note that the minus 1 in the line below handles
                        # the fact that we've pre-pended the key to the index list
                        newList.append(updateFields[i-1])
                # check if # exceeds shape file supported total
                if self.ccPU + len(newList) >= 254:
                    self.writeToCSV = True;
                else:
                    ok, self.message = self.createNewFields(updateLyr, newList)
                    if ok == -1:
                        return(ok, self.message)
                    # update field index
                    fldIdxs = self.getFieldIndexes(updateLyr,[keyField] + updateFields)
                    keyIdx = fldIdxs[0]
            if self.writeToCSV == False:
                if -1 in fldIdxs:
                    self.issueWarning = True
                    if self.warningText == '':
                        self.warningText = 'oth;'
                    else:
                        self.warningText += 'oth;'
                    return(-1,'broken')
                # update values
                # put update layer into edit state
                updateLyr.blockSignals(True)
                if not updateLyr.isEditable():
                    updateLyr.startEditing()
                    if not updateLyr.isEditable():
                        self.issueWarning = True
                        if self.warningText == '':
                            self.warningText = 'oth;'
                        else:
                            self.warningText += 'oth;'
                        self.message = "Unable to edit input pu layer: Please choose a layer with edit capabilities."
                        return (-1, self.message)
                # begin editing
                updateLyr.select(fldIdxs, QgsRectangle(), False, False)
                updateLyr.beginEditCommand("Data updated")
                updateFeat = QgsFeature()
                # emit feature count
                while updateLyr.nextFeature(updateFeat):
                    #  emit progress update
                    featAttrs = updateFeat.attributeMap()
                    keyVal = featAttrs[keyIdx].toInt()[0]
                    # check to see if record in dictionary for this feature
                    if keyVal in updateDict:
                        writeVals = updateDict[keyVal]
                        for i in range(len(updateFields)):
                            writeVal = 0.0
                            for key, val in writeVals.iteritems():
                                if updateFieldValues[i] == key:
                                    writeVal = val
                            updateLyr.changeAttributeValue(updateFeat.id(), fldIdxs[i+1], writeVal, False)
                    else:
                        for i in range(len(updateFields)):
                            updateLyr.changeAttributeValue(updateFeat.id(), fldIdxs[i+1], 0.0, False)
                updateLyr.endEditCommand()
                updateLyr.commitChanges()
                # unblock signals
                updateLyr.blockSignals(False)
                #updateLyr.setModified(True, False)

        if self.writeToCSV == True:
            self.emit(QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),'Writing CSV')
            outDir = os.path.dirname(str(updateLyr.source()))
            baseFName = os.path.splitext(os.path.basename(self.puFile))[0] + \
                '_' + os.path.splitext(os.path.basename(self.srcFile))[0]
            self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),0)
            nFeat = len(updateFields)
            self.emit(QtCore.SIGNAL("runSubRange(PyQt_PyObject)" ),(0,nFeat))
            for x in range(len(updateFields)):
                self.emit(QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),x)
                outPath = os.path.join(outDir,baseFName+'_'+updateFields[x]+'.csv')
                f = open(outPath,'w')
                header = '%s,%s%s' % (keyField,updateFields[x],os.linesep)
                f.write(header)
                for key,value in updateDict.iteritems():
                    if value[updateFieldValues[x]] <> 0.0 and value[updateFieldValues[x]] <> None:
                        line = str(key)+','+str(value[updateFieldValues[x]])+os.linesep
                        f.write(line)
                f.close()
                x += 1
            
        return(0,'Success')
