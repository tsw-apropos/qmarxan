"""
# -*- coding: utf-8 -*-
#
# ========================================================
# 
# Purpose: Create a square or hexagon grid for use with Marxan
# Author: Trevor Wiens
# Copyright: Apropos Information Systems Inc.
# Acknolwedgements: This function was derived from QGIS fTools VectorGrid
#                   function created by Carson Farmer
# Date: 2011-11-11
# License: GPL2 
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#---------------------------------------------------------------------
"""

from PyQt4 import QtCore, QtGui
import qmarxan
from qgis.core import *
from ui_qm_mkgrid import Ui_qm_mkgrid
import math,os
from qm_utils import qmCalculateThread

class qmMkGrid(QtGui.QDialog):

    def __init__(self, iface):
    
        self.iface = iface
        self.mLayer = None
        self.tLayer = None

        # Import required plugins and if missing show the plugin's name
        import sys
        ftPath = os.path.join(str(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path()), 'python/plugins/fTools')
        if not ftPath in sys.path:
            sys.path.append(ftPath)
        req_plugin = "ftools 0.5.10"
        try:
            import ftools_utils
        except:
            QtGui.QMessageBox.information(self, self.tr("Missing Plugins"), 
                    self.tr("Missing plugin: %s" % req_plugin))
                    
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_qm_mkgrid()
        self.ui.setupUi(self)
        self.setFixedSize(460,582)
        QtCore.QObject.connect(self.ui.toolOut, QtCore.SIGNAL("clicked()"), self.outFile)
        QtCore.QObject.connect(self.ui.spnUnitArea, QtCore.SIGNAL("valueChanged(double)"), self.offset)
        QtCore.QObject.connect(self.ui.spnSideLength, QtCore.SIGNAL("valueChanged(double)"), self.offset)
        QtCore.QObject.connect(self.ui.spnXmax, QtCore.SIGNAL("valueChanged(double)"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.spnXmin, QtCore.SIGNAL("valueChanged(double)"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.spnYmax, QtCore.SIGNAL("valueChanged(double)"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.spnYmin, QtCore.SIGNAL("valueChanged(double)"), self.updateCellCount)
        #QObject.connect(self.inShape, SIGNAL("currentIndexChanged(QString)"), self.updateInput)
        QtCore.QObject.connect(self.ui.rdoArea, QtCore.SIGNAL("clicked()"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.rdoSideLength, QtCore.SIGNAL("clicked()"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.rdoHexagon, QtCore.SIGNAL("clicked()"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.rdoSquare, QtCore.SIGNAL("clicked()"), self.updateCellCount)
        QtCore.QObject.connect(self.ui.btnUpdate, QtCore.SIGNAL("clicked()"), self.updateLayer)
        QtCore.QObject.connect(self.ui.btnCanvas, QtCore.SIGNAL("clicked()"), self.updateCanvas)
        self.ui.buttonOk = self.ui.buttonBox_2.button( QtGui.QDialogButtonBox.Ok )
        self.setWindowTitle(self.tr("Create Planning Unit Grid"))
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layermap.iteritems():
            self.ui.inShape.addItem( unicode( layer.name() ) )
        self.ui.progressBar.setRange( 0, 100 )

    def updateCellCount( self ):
        try:
            xmin = self.ui.spnXmin.value()
            ymin = self.ui.spnYmin.value()
            xmax = self.ui.spnXmax.value()
            ymax = self.ui.spnYmax.value()
            xdiff = xmax - xmin
            ydiff = ymax - ymin
            if self.ui.rdoHexagon.isChecked():
                if self.ui.rdoArea.isChecked():
                    sideLen = self.CalculateHexagonSideLength(self.ui.spnUnitArea.value())
                    tarea = float(self.ui.spnUnitArea.value())
                else:
                    sideLen = float(self.ui.spnSideLength.value())
                    tarea = float(sideLen)**2 * math.sqrt(3)/4
                # basic trig needed to calculate effective length
                angle_a = math.radians(30)
                hyp = sideLen
                side_b = hyp * math.cos(angle_a)
                side_a = hyp * math.sin(angle_a)
                cellcount = ((xdiff + sideLen)/(2 * side_b)) * (((ydiff+side_b)/(sideLen + side_a))+1)
            else:
                if self.ui.rdoArea.isChecked():
                    sideLen = math.sqrt(float(self.ui.spnUnitArea.value()))
                    tarea = float(self.ui.spnUnitArea.value())
                else:
                    sideLen = float(self.ui.spnSideLength.value())
                    tarea = float(self.ui.spnSideLength.value())**2
                cellcount = ((xdiff/sideLen)+1) * ((ydiff/sideLen)+1)
            if cellcount < 100:
                outText = str(int(round(cellcount,-1)))
            elif cellcount < 10000:
                outText = str(int(round(cellcount,-2)))
            elif cellcount < 1000000:
                outText = str(int(round(cellcount,-3)))
            elif cellcount < 100000000:
                outText = str(int(round(cellcount,-4)))
            else:
                outText = str(int(round(cellcount,-5)))
            self.ui.leUnitNumber.setText( QtCore.QString( outText ) )
        except:
            self.ui.leUnitNumber.setText( QtCore.QString( '' ) )
            
    def offset(self, value):
        if self.ui.rdoArea.isChecked():
            self.ui.spnUnitArea.setValue(value)
        self.updateCellCount()

    def updateLayer( self ):
        import ftools_utils
        mLayerName = self.ui.inShape.currentText()
        if not mLayerName == "":
            self.mLayer = ftools_utils.getMapLayerByName( unicode( mLayerName ) )
            boundBox = self.mLayer.extent()
            self.updateExtents( boundBox )
    
    def updateCanvas( self ):
        canvas = self.iface.mapCanvas()
        boundBox = canvas.extent()
        self.updateExtents( boundBox )
    
    def updateExtents( self, boundBox ):
        self.ui.spnXmin.setValue( boundBox.xMinimum() )
        self.ui.spnYmin.setValue( boundBox.yMinimum() )
        self.ui.spnXmax.setValue( boundBox.xMaximum() ) 
        self.ui.spnYmax.setValue( boundBox.yMaximum() )
        self.updateCellCount()

    def accept(self):
        import ftools_utils
        self.ui.buttonOk.setEnabled( False )
        if self.ui.spnXmin.text() == "" or self.ui.spnXmax.text() == "" or self.ui.spnYmin.text() == "" or \
        self.ui.spnYmax.text() == "":
            QtGui.QMessageBox.information(self, self.tr("Planning Grid"), \
            self.tr("Please specify valid extent coordinates"))
        elif self.ui.outShape.text() == "":
            QtGui.QMessageBox.information(self, self.tr("Planning Grid"), \
            self.tr("Please specify output shapefile"))
        else:
            try:
                boundBox = QgsRectangle(
                float( self.ui.spnXmin.value() ),
                float( self.ui.spnYmin.value() ),
                float( self.ui.spnXmax.value() ),
                float( self.ui.spnYmax.value() ) )
            except:
                QtGui.QMessageBox.information(self, self.tr("Planning Grid"), 
                    self.tr("Invalid extent coordinates entered"))
            sideLen = self.ui.spnSideLength.value()
            unitArea = self.ui.spnUnitArea.value()
            if self.ui.rdoHexagon.isChecked(): 
                hexagon = True
            else: 
                hexagon = False
            if self.ui.rdoArea.isChecked() == True:
                if hexagon == True:
                    sideLen = self.CalculateHexagonSideLength(unitArea)
                else:
                    sideLen = self.CalculateSquareSideLength(unitArea)
                makegrid = QtGui.QMessageBox.question(self, self.tr("Side Length Check"), \
                    self.tr("Planning grid side length will %d map units. Proceed?" % sideLen), \
                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.NoButton)
                if makegrid != QtGui.QMessageBox.Yes:
                    self.ui.progressBar.setValue(0)
                    self.ui.buttonOk.setEnabled(True)
                    return()
            self.ui.outShape.clear()
            if self.ui.cbLimit.isChecked():
                # create temp 4 x 4 grid
                tfn = 'tempgrid' + str(os.getpid()) + '.shp'
                tin = 'tempint' + str(os.getpid()) + '.shp'
                tfp = os.path.dirname(str(self.mLayer.source()))
                tfpn = os.path.join(tfp,tfn)
                tipn = os.path.join(tfp,tin)
                tempLen = min((boundBox.yMaximum()-boundBox.yMinimum()),(boundBox.xMaximum()-boundBox.xMinimum()))
                self.writeTempFile(boundBox,tempLen/3.8,tfpn,self.encoding)
                # intersect temp 4 x 4 grid with source layer
                d = qmCalculateThread(tfpn,'temp_id',str(self.mLayer.source()),'','','','','')
                mLayerName = str(self.mLayer.source())
                QtCore.QObject.connect(d,QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),self.setThreadProgress)
                QtCore.QObject.connect(d,QtCore.SIGNAL("runSubRange(PyQt_PyObject)"),self.setThreadRange)
                ok,message,intLyr,valField = d.intersectLayers(mLayerName,tfpn,tipn,[],['temp_id'])
                intLyr = None
                os.remove(tfpn)
                os.remove(tfpn[:-4]+'.dbf')
                os.remove(tfpn[:-4]+'.shx')
                os.remove(tfpn[:-4]+'.prj')
                os.remove(tfpn[:-4]+'.qpj')
                # write output with continual intersection checks
                self.tLayer = QgsVectorLayer(tipn, 'int', 'ogr')
                self.writeFile(boundBox, sideLen, hexagon, self.shapefileName, self.encoding)
                self.tLayer = None
                os.remove(tipn)
                os.remove(tipn[:-4]+'.dbf')
                os.remove(tipn[:-4]+'.shx')
                os.remove(tipn[:-4]+'.prj')
                os.remove(tipn[:-4]+'.qpj')
            else:
                self.writeFile(boundBox, sideLen, hexagon, self.shapefileName, self.encoding)
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.repaint()
            addToTOC = QtGui.QMessageBox.question(self, self.tr("Generate Vector Grid"), \
                self.tr("Created output shapefile:" + \
                "\n%1\n\nWould you like to add the new layer to the TOC?").arg(unicode(self.shapefileName)), \
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.NoButton)
            if addToTOC == QtGui.QMessageBox.Yes:
                ftools_utils.addShapeToCanvas( self.shapefileName )
        self.ui.progressBar.setValue(0)
        self.ui.buttonOk.setEnabled( True )

    def writeTempFile(self, bound, sideLen, shapefileName, encoding):
        
        import ftools_utils
        crs = self.iface.mapCanvas().mapRenderer().destinationSrs()
        if not crs.isValid():
            crs = None
        fields = {0:QgsField("temp_id", QtCore.QVariant.Int)}
        check = QtCore.QFile(shapefileName)
        if check.exists():
            if not QgsVectorFileWriter.deleteShapeFile(shapefileName):
                return
        writer = QgsVectorFileWriter(shapefileName, encoding, fields, QGis.WKBPolygon, crs)
        outFeat = QgsFeature()
        outGeom = QgsGeometry()
        idVar = 0
        # place squares from top left corner
        y = bound.yMaximum()
        rowCount = int((bound.yMaximum()-bound.yMinimum())/sideLen)
        row = 1
        while y >= bound.yMinimum():
            x = bound.xMinimum()
            while x <= bound.xMaximum():
                polygon = self.CreateSquare(x, y, sideLen)
                outFeat.setGeometry(outGeom.fromPolygon(polygon))
                outFeat.addAttribute(0, QtCore.QVariant(idVar))
                writer.addFeature(outFeat)
                idVar = idVar + 1
                x = x + sideLen
            y = y - sideLen
        del writer

    def CalculateSquareSideLength(self, unitArea):
    
        squareSideLength = math.sqrt(unitArea)
        return(squareSideLength)
    
    def CalculateHexagonSideLength(self, unitArea):   

        triangleArea = unitArea/6.0
        #
        # area of an equilateral triangle = length^2 * sqrt(3)/4 
        # sqrt(3)/4 * area = length^2
        # sqrt( sqrt(3)/4 * area) = length
        #
        hexagonSideLength = math.sqrt( triangleArea / (math.sqrt(3.0)/4.0) )
        return(hexagonSideLength)
        
    def CalculateHexagonArea(self, sideLen):
    
        tarea = float(sideLen)**2 * math.sqrt(3)/4
        return(tarea*6)

    def CreateHexagon(self, x, y, sideLen):

        # basic trig
        angle_a = math.radians(30)
        hyp = sideLen
        side_b = hyp * math.cos(angle_a)
        side_a = hyp * math.sin(angle_a)
 
        # create points
        pt1 = QgsPoint(x, y)
        pt2 = QgsPoint(x + hyp, y)
        pt3 = QgsPoint(x + hyp + side_a, y + side_b)
        pt4 = QgsPoint(x + hyp, y + (2 * side_b))
        pt5 = QgsPoint(x, y + (2 * side_b))
        pt6 = QgsPoint(x - side_a, y + side_b)
        pt7 = QgsPoint(x, y)
        hexagon = [[pt1, pt2, pt3, pt4, pt5, pt6, pt7]]
        return(hexagon)
        
    def CreateSquare(self, x, y, sideLen):
    
        pt1 = QgsPoint(x, y)
        pt2 = QgsPoint(x + sideLen, y)
        pt3 = QgsPoint(x + sideLen, y - sideLen)
        pt4 = QgsPoint(x, y - sideLen)
        pt5 = QgsPoint(x, y)
        square = [[pt1, pt2, pt3, pt4, pt5]]
        return(square)
        
    def writeFile(self, bound, sideLen, isHexagon, shapefileName, encoding):
        crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        self.ui.progressBar.setRange( 0, 100 )
        if not crs.isValid():
            crs = None
        # TSW - 2011-10-11 - row and column fields for adjancency determination when exporting
        # modified to 20,5 for float field to match calc
        fields = {0:QgsField("pu_id", QtCore.QVariant.Int), 
                1:QgsField("pu_cost", QtCore.QVariant.Double, "real", 19, 10), 
                2:QgsField("pu_status", QtCore.QVariant.Double, "real", 19, 10),
                3:QgsField("bnd_cost", QtCore.QVariant.Double, "real", 19, 10), 
                4:QgsField("area", QtCore.QVariant.Double, "real", 19, 10), 
                5:QgsField("perimeter", QtCore.QVariant.Double, "real", 19, 10), 
                6:QgsField("sidelength", QtCore.QVariant.Double, "real", 19, 10) }
        check = QtCore.QFile(shapefileName)
        if check.exists():
            if not QgsVectorFileWriter.deleteShapeFile(shapefileName):
                return
        writer = QgsVectorFileWriter(shapefileName, encoding, fields, QGis.WKBPolygon, crs)
        outFeat = QgsFeature()
        outGeom = QgsGeometry()
        idVar = 0
        if self.ui.cbLimit.isChecked():
            # create spatial index
            tFeat = QgsFeature()
            newFeat = QgsFeature()
            tGeom = QgsGeometry()
            tIndex = QgsSpatialIndex()
            tPv = self.tLayer.dataProvider()
            tPv.select([], QgsRectangle(), True, False)
            while tPv.nextFeature(tFeat):
                tIndex.insertFeature(tFeat)
            # begin creating records
            if not isHexagon:
                # place squares from top left corner
                puArea = float(sideLen)**2
                puPerimeter = float(sideLen)*4
                y = bound.yMaximum()
                rowCount = int((bound.yMaximum()-bound.yMinimum())/sideLen)
                row = 1
                while y >= bound.yMinimum():
                    x = bound.xMinimum()
                    while x <= bound.xMaximum():
                        polygon = self.CreateSquare(x, y, sideLen)
                        outFeat.setGeometry(outGeom.fromPolygon(polygon))
                        outFeat.addAttribute(0, QtCore.QVariant(idVar))
                        outFeat.addAttribute(1, QtCore.QVariant(1.0))
                        outFeat.addAttribute(2, QtCore.QVariant(0.0))
                        outFeat.addAttribute(3, QtCore.QVariant(1.0))
                        outFeat.addAttribute(4, QtCore.QVariant(puArea))
                        outFeat.addAttribute(5, QtCore.QVariant(puPerimeter))
                        outFeat.addAttribute(6, QtCore.QVariant(sideLen))
                        # test to see if new feature intersects bounding box of
                        # source extent layer
                        outGeom = QgsGeometry(outFeat.geometry())
                        features = tIndex.intersects(outGeom.boundingBox())
                        for fid in features:
                            # now test if actually intersects
                            tPv.featureAtId(int(fid), tFeat, True, [])
                            tGeom = QgsGeometry(tFeat.geometry())
                            if outGeom.intersects(tGeom):
                                # intersects so add and go on to next new feature
                                writer.addFeature(outFeat)
                                break 
                        idVar = idVar + 1
                        x = x + sideLen
                    y = y - sideLen
                    self.ui.progressBar.setValue((row*100)/rowCount)
                    self.ui.progressBar.repaint()
            else:
                # NOTE each start point needs special calculation
                # because of space between bottom corners of hexagons in a 
                # same row or column
                #
                # basic trig to determine placement of hexagons
                angle_a = math.radians(30)
                hyp = sideLen
                side_b = hyp * math.cos(angle_a)
                side_a = hyp * math.sin(angle_a)
                puArea = self.CalculateHexagonArea(sideLen)
                puPerimeter = float(sideLen)*6
                # place hexagons from within top left corner
                y = bound.yMaximum() - side_b
                rowCount = int((bound.yMaximum()-bound.yMinimum())/sideLen)
                row = 1
                while y >= bound.yMinimum() - (2 * side_a) - sideLen:
                    if row%2 == 0:
                        x = bound.xMinimum() + sideLen 
                    else:
                        x = bound.xMinimum() - side_a
                    while x <= bound.xMaximum() + sideLen:
                        polygon = self.CreateHexagon(x, y, sideLen)
                        outFeat.setGeometry(outGeom.fromPolygon(polygon))
                        outFeat.addAttribute(0, QtCore.QVariant(idVar))
                        outFeat.addAttribute(1, QtCore.QVariant(1.0))
                        outFeat.addAttribute(2, QtCore.QVariant(0.0))
                        outFeat.addAttribute(3, QtCore.QVariant(1.0))
                        outFeat.addAttribute(4, QtCore.QVariant(puArea))
                        outFeat.addAttribute(5, QtCore.QVariant(puPerimeter))
                        outFeat.addAttribute(6, QtCore.QVariant(sideLen))
                        # test to see if new feature intersects bounding box of
                        # source extent layer
                        outGeom = QgsGeometry(outFeat.geometry())
                        features = tIndex.intersects(outGeom.boundingBox())
                        for fid in features:
                            # now test if actually intersects
                            tPv.featureAtId(int(fid), tFeat, True, [])
                            tGeom = QgsGeometry(tFeat.geometry())
                            if outGeom.intersects(tGeom):
                                # intersects so add and go on to next new feature
                                writer.addFeature(outFeat)
                                break 
                        idVar = idVar + 1
                        x = x + (2*sideLen) + (2*side_a)
                    y = y - side_b
                    row = row + 1
                    self.ui.progressBar.setValue((row*100)/rowCount)
                    self.ui.progressBar.repaint()
            self.ui.progressBar.setRange( 0, 100 )
            tPv = None
        else:
            if not isHexagon:
                # place squares from top left corner
                puArea = float(sideLen)**2
                puPerimeter = float(sideLen)*4
                y = bound.yMaximum()
                rowCount = int((bound.yMaximum()-bound.yMinimum())/sideLen)
                row = 1
                while y >= bound.yMinimum():
                    x = bound.xMinimum()
                    while x <= bound.xMaximum():
                        polygon = self.CreateSquare(x, y, sideLen)
                        outFeat.setGeometry(outGeom.fromPolygon(polygon))
                        outFeat.addAttribute(0, QtCore.QVariant(idVar))
                        outFeat.addAttribute(1, QtCore.QVariant(1.0))
                        outFeat.addAttribute(2, QtCore.QVariant(0.0))
                        outFeat.addAttribute(3, QtCore.QVariant(1.0))
                        outFeat.addAttribute(4, QtCore.QVariant(puArea))
                        outFeat.addAttribute(5, QtCore.QVariant(puPerimeter))
                        outFeat.addAttribute(6, QtCore.QVariant(sideLen))
                        # INSERT CODE HERE TO DETERMINE IF INSIDE REFERENCE LAYER
                        writer.addFeature(outFeat)
                        idVar = idVar + 1
                        x = x + sideLen
                    y = y - sideLen
                    self.ui.progressBar.setValue((row*100)/rowCount)
                    self.ui.progressBar.repaint()
            else:
                # NOTE each start point needs special calculation
                # because of space between bottom corners of hexagons in a 
                # same row or column
                #
                # basic trig to determine placement of hexagons
                angle_a = math.radians(30)
                hyp = sideLen
                side_b = hyp * math.cos(angle_a)
                side_a = hyp * math.sin(angle_a)
                puArea = self.CalculateHexagonArea(sideLen)
                puPerimeter = float(sideLen)*6
                # place hexagons from within top left corner
                y = bound.yMaximum() - side_b
                rowCount = int((bound.yMaximum()-bound.yMinimum())/sideLen)
                row = 1
                while y >= bound.yMinimum() - (2 * side_a) - sideLen:
                    if row%2 == 0:
                        x = bound.xMinimum() + sideLen 
                    else:
                        x = bound.xMinimum() - side_a
                    while x <= bound.xMaximum() + sideLen:
                        polygon = self.CreateHexagon(x, y, sideLen)
                        outFeat.setGeometry(outGeom.fromPolygon(polygon))
                        outFeat.addAttribute(0, QtCore.QVariant(idVar))
                        outFeat.addAttribute(1, QtCore.QVariant(1.0))
                        outFeat.addAttribute(2, QtCore.QVariant(0.0))
                        outFeat.addAttribute(3, QtCore.QVariant(1.0))
                        outFeat.addAttribute(4, QtCore.QVariant(puArea))
                        outFeat.addAttribute(5, QtCore.QVariant(puPerimeter))
                        outFeat.addAttribute(6, QtCore.QVariant(sideLen))
                        writer.addFeature(outFeat)
                        idVar = idVar + 1
                        x = x + (2*sideLen) + (2*side_a)
                    y = y - side_b
                    row = row + 1
                    self.ui.progressBar.setValue((row*100)/rowCount)
                    self.ui.progressBar.repaint()
            self.ui.progressBar.setRange( 0, 100 )
        del writer

    def outFile(self):
        
        import ftools_utils
        self.ui.outShape.clear()
        ( self.shapefileName, self.encoding ) = ftools_utils.saveDialog( self )
        if self.shapefileName is None or self.encoding is None:
            return
        self.ui.outShape.setText( QtCore.QString( self.shapefileName ) )

    def setThreadProgress(self, progress):
        self.ui.progressBar.setValue(progress)

    def setThreadRange(self, rangeVals):
        self.ui.progressBar.setRange(rangeVals[0],rangeVals[1])
