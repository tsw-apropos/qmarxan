"""
/***************************************************************************
 QMarxanDialog
                                 A QGIS plugin
 Create grid, measure input layers, create Marxan input layers, import results
                             -------------------
        begin                : 2011-10-11
        copyright            : (C) 2011 by Apropos Information Systems Inc.
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

from PyQt4 import QtCore, QtGui
from qgis.core import *
import qgis.utils
from ui_qm_calc import Ui_qm_calc
from qm_utils import qmCalculateThread
import os, time, datetime
import sys

  
# create the dialog for zoom to point
class qmCalc(QtGui.QDialog):

    # class initiation
    def __init__(self, iface):
        self.iface = iface

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

        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_qm_calc()
        self.ui.setupUi(self)
        self.setFixedSize(809,714)
        #
        self.setWindowTitle(self.tr("Calculate Planning Grid Conservation Factor Values"))
        # add input layers to select planning grid
        self.allLayers = ftools_utils.getLayerNames([QGis.Polygon, QGis.Line, QGis.Point])
        layers = ftools_utils.getLayerNames([QGis.Polygon])
        self.ui.cbxPlanningGrid.addItems(layers)
        self.setMeasurePoints()
        self.setIdAndMeasureFields(self.ui.cbxPlanningGrid.currentText())
        self.setOutputField()
        self.ui.rdoSum.setChecked(True)
        self.ui.rdoMeasure.setChecked(True)
        # setup calculations list
        self.setCalculations()
        
        # connect methods to button interactions
        # selecting type of layer to measure
        QtCore.QObject.connect(self.ui.rdoPoints, QtCore.SIGNAL("clicked()"), self.setMeasurePoints)
        QtCore.QObject.connect(self.ui.rdoLines, QtCore.SIGNAL("clicked()"), self.setMeasureLines)
        QtCore.QObject.connect(self.ui.rdoAreas, QtCore.SIGNAL("clicked()"), self.setMeasurePolygons)
        QtCore.QObject.connect(self.ui.rdoRaster, QtCore.SIGNAL("clicked()"), self.setMeasureRasters)
        # selecting measure layer
        QtCore.QObject.connect(self.ui.cbxPlanningGrid, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setIdAndMeasureFields)
        # select single or multiple variale output
        QtCore.QObject.connect(self.ui.rdoCalcSingle, QtCore.SIGNAL("clicked()"), self.setSingle)
        QtCore.QObject.connect(self.ui.rdoCalcMulti, QtCore.SIGNAL("clicked()"), self.setMulti)
        # selecting measure or calculation
        QtCore.QObject.connect(self.ui.rdoMeasure, QtCore.SIGNAL("clicked()"), self.setMeasure)
        QtCore.QObject.connect(self.ui.rdoCalculate, QtCore.SIGNAL("clicked()"), self.setCalculate)
        QtCore.QObject.connect(self.ui.rdoPresence, QtCore.SIGNAL("clicked()"), self.setPresence)
        QtCore.QObject.connect(self.ui.cbxMeasureLayer, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setCalcFields)
        # selecting field name
        QtCore.QObject.connect(self.ui.cbxSelectField, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setOutputField)
        # calculation list actions
        QtCore.QObject.connect(self.ui.twCalculations, QtCore.SIGNAL("itemSelectionChanged()"), self.selectCalcForEdit)
        QtCore.QObject.connect(self.ui.pbCancel, QtCore.SIGNAL('clicked()'), self.cancelCalcEdit)
        QtCore.QObject.connect(self.ui.pbNew, QtCore.SIGNAL('clicked()'), self.newCalculation)
        QtCore.QObject.connect(self.ui.pbDelete, QtCore.SIGNAL('clicked()'), self.deleteCalculation)
        QtCore.QObject.connect(self.ui.pbSave, QtCore.SIGNAL('clicked()'), self.saveCalculation)
        # set main form buttons
        QtCore.QObject.connect(self.ui.pbOpenList, QtCore.SIGNAL('clicked()'), self.loadCalculationList)
        QtCore.QObject.connect(self.ui.pbSaveList, QtCore.SIGNAL('clicked()'), self.saveCalculationList)
        QtCore.QObject.connect(self.ui.pbClose, QtCore.SIGNAL('clicked()'), self.close)
        QtCore.QObject.connect(self.ui.pbRun, QtCore.SIGNAL('clicked()'), self.doCalculations)

    #
    # control list of calculations
    #
    
    # create table header
    def setCalculations(self):
        # clear the grid    
        self.ui.twCalculations.clear()
        self.ui.twCalculations.repaint()
        # prepare the grid
        self.ui.twCalculations.setColumnCount(8)
        header = QtCore.QStringList()
        header.append('pu_layer')
        header.append('puid')
        header.append('measure_layer')
        header.append('field_output')
        header.append('measure_type')
        header.append('calc_field')
        header.append('operator')
        header.append('out_name')
        self.ui.twCalculations.setHorizontalHeaderLabels(header)
        self.ui.frCalcEdit.setDisabled(True)
        self.ui.pbNew.setEnabled(True)

    # control functional state of interface elements and then load content
    def selectCalcForEdit(self):

        selItems = self.ui.twCalculations.selectedItems()
        if len(selItems) == 0:
            self.ui.frProcessManagement.setEnabled(True)
            self.ui.pbOpenList.setEnabled(True)
            self.ui.pbSaveList.setEnabled(True)
            self.ui.pbNew.setEnabled(True)
            self.ui.pbSave.setDisabled(True)
            self.ui.pbDelete.setDisabled(True)
            self.ui.pbCancel.setDisabled(True)
            self.ui.frCalcEdit.setDisabled(True)
        else:
            self.ui.frProcessManagement.setDisabled(True)
            self.ui.pbOpenList.setDisabled(True)
            self.ui.pbSaveList.setDisabled(True)
            self.ui.pbNew.setDisabled(True)
            self.ui.pbSave.setEnabled(True)
            self.ui.pbDelete.setEnabled(True)
            self.ui.pbCancel.setEnabled(True)
            self.ui.frCalcEdit.setEnabled(True)
            self.ui.twCalculations.setDisabled(True)
            self.loadCalculation()

    # cancel an edit
    def cancelCalcEdit(self):

        selected = self.ui.twCalculations.selectedItems()
        for item in selected:
            self.ui.twCalculations.setItemSelected(item, False)
        self.ui.frCalcEdit.setDisabled(True)
        self.ui.twCalculations.setEnabled(True)
        self.ui.frProcessManagement.setEnabled(True)
        if self.ui.twCalculations.rowCount() > 0:
            self.ui.pbRun.setEnabled(True)

    # create a new calculation record
    def newCalculation(self):
        # determine how many rows
        x = self.ui.twCalculations.rowCount()+1
        self.ui.twCalculations.setRowCount(x)
        # pu layer: col 0
        item = QtGui.QTableWidgetItem()
        item.setText('')
        item.setToolTip('PU Layer')
        self.ui.twCalculations.setItem(x-1,0,item)
        # pu id: col 1
        item = QtGui.QTableWidgetItem()
        item.setText('')
        item.setToolTip('PuId')
        self.ui.twCalculations.setItem(x-1,1,item)
        # measure layer: col 2
        item = QtGui.QTableWidgetItem()
        item.setText('')
        item.setToolTip('Measure Layer')
        self.ui.twCalculations.setItem(x-1,2,item)
        # single vs multi field output: col 3
        item = QtGui.QTableWidgetItem()
        item.setText('single')
        item.setToolTip('Field Output')
        self.ui.twCalculations.setItem(x-1,3,item)
        # measure type: col 4
        item = QtGui.QTableWidgetItem()
        item.setText('measure')
        item.setToolTip('Measure Type')
        self.ui.twCalculations.setItem(x-1,4,item)
        # calculation field: col 5
        item = QtGui.QTableWidgetItem()
        item.setText('')
        item.setToolTip('Calculation Field')
        self.ui.twCalculations.setItem(x-1,5,item)
        # Operator: col 6
        item = QtGui.QTableWidgetItem()
        item.setText('sum')
        item.setToolTip('Operator')
        self.ui.twCalculations.setItem(x-1,6,item)
        # output name or prefix: col 7
        item = QtGui.QTableWidgetItem()
        item.setText('')
        item.setToolTip('Output Name')
        self.ui.twCalculations.setItem(x-1,7,item)
        self.ui.twCalculations.selectRow(x-1)
        
    # load a calculation
    def loadCalculation(self):
        import ftools_utils
        message = ''
        selected = self.ui.twCalculations.selectedItems()
        for item in selected:
            iText = str(item.text())
            if item.column() == 0:
                layerList = ftools_utils.getLayerNames([QGis.Polygon])
                cbIndex = -1
                for lName in layerList:
                    cLyr = ftools_utils.getVectorLayerByName(lName)
                    if cLyr.source() == iText:
                        cbIndex = self.ui.cbxPlanningGrid.findText(cLyr.name())
                if cbIndex > -1:
                    self.ui.cbxPlanningGrid.setCurrentIndex(cbIndex)
                else:
                    self.ui.cbxPlanningGrid.setCurrentIndex(0)
            elif item.column() == 1:
                fldIndex = self.ui.cbxPuId.findText(iText)
                if fldIndex > -1:
                    self.ui.cbxPuId.setCurrentIndex(fldIndex)
            elif item.column() == 2:
                self.setMeasurePoints()
                self.ui.rdoPoints.setChecked(True)
                layerList = ftools_utils.getLayerNames([QGis.Point])
                cbIndex = -1
                for lName in layerList:
                    cLyr = ftools_utils.getVectorLayerByName(lName)
                    if cLyr.source() == iText:
                        cbIndex = self.ui.cbxMeasureLayer.findText(cLyr.name())
                if cbIndex > -1:
                    self.ui.cbxMeasureLayer.setCurrentIndex(cbIndex)
                else:
                    self.setMeasureLines()
                    self.ui.rdoLines.setChecked(True)
                    layerList = ftools_utils.getLayerNames([QGis.Line])
                    cbIndex = -1
                    for lName in layerList:
                        cLyr = ftools_utils.getVectorLayerByName(lName)
                        if cLyr.source() == iText:
                            cbIndex = self.ui.cbxMeasureLayer.findText(cLyr.name())
                    if cbIndex > -1:
                        self.ui.cbxMeasureLayer.setCurrentIndex(cbIndex)
                    else:
                        self.setMeasurePolygons()
                        self.ui.rdoAreas.setChecked(True)
                        layerList = ftools_utils.getLayerNames([QGis.Polygon])
                        cbIndex = -1
                        for lName in layerList:
                            cLyr = ftools_utils.getVectorLayerByName(lName)
                            if cLyr.source() == iText:
                                cbIndex = self.ui.cbxMeasureLayer.findText(cLyr.name())
                        if cbIndex > -1:
                            self.ui.cbxMeasureLayer.setCurrentIndex(cbIndex)
                        else:
                            self.setMeasureRasters()
                            self.ui.rdoRaster.setChecked(True)
                            layerList = []
                            layers = []
                            for key, value in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                                if 'raster' in str(value.__class__).lower():
                                    layerList.append(str(value.name()))
                                    layers.append(value)
                            cbIndex = -1
                            for q in range(len(layers)):
                                if layers[q] == iText:
                                    cbIndex = self.ui.cbxMeasureLayer.findText(layerList[q])
                            if cbIndex > -1:
                                self.ui.cbxMeasureLayer.setCurrentIndex(cbIndex)
            elif item.column() == 3:
                if iText == 'single':
                    self.ui.rdoCalcSingle.setChecked(True)
                    self.setSingle()
                else:
                    self.ui.rdoCalcMulti.setChecked(True)
                    self.setMulti()
            elif item.column() == 4:
                if iText == 'measure':
                    self.ui.rdoMeasure.setChecked(True)
                    self.setMeasure()
                elif iText == 'calculate':
                    self.ui.rdoCalculate.setChecked(True)
                    self.setCalculate()
                else:
                    self.ui.rdoPresence.setChecked(True)
                    self.setPresence()
            elif item.column() == 5:
                if self.ui.rdoMeasure.isChecked() == False:
                    fldIndex = self.ui.cbxCalcField.findText(iText)
                    if fldIndex > -1:
                        self.ui.cbxCalcField.setCurrentIndex(fldIndex)
            elif item.column() == 6:
                if iText == 'sum':
                    self.ui.rdoSum.setChecked(True)
                elif iText == 'mean':
                    self.ui.rdoMean.setChecked(True)
                elif iText == 'max':
                    self.ui.rdoMax.setChecked(True)
                elif iText == 'min':
                    self.ui.rdoMin.setChecked(True)
                elif iText == 'count':
                    self.ui.rdoCount.setChecked(True)
            elif item.column() == 7:
                outIndex = self.ui.cbxSelectField.findText(iText)
                if outIndex > -1:
                    self.ui.cbxSelectField.setCurrentIndex(outIndex)
                    self.ui.leNewField.setText('')
                else:
                    self.ui.cbxSelectField.setCurrentIndex(0)
                    self.ui.leNewField.setText(iText)

    # save a calculation
    def saveCalculation(self):
        import ftools_utils
        selected = self.ui.twCalculations.selectedItems()
        for item in selected:
            if item.column() == 0:
                cLyr = ftools_utils.getVectorLayerByName(self.ui.cbxPlanningGrid.currentText())
                item.setText(cLyr.source())
            elif item.column() == 1:
                item.setText(self.ui.cbxPuId.currentText())
            elif item.column() == 2:
                if self.ui.rdoRaster.isChecked() == True:
                    for key, value in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                        if ('raster' in str(value.__class__).lower()) and \
                        (str(value.name()) == self.ui.cbxMeasureLayer.currentText()):
                            item.setText(str(value.source()))
                else:
                    cLyr = ftools_utils.getVectorLayerByName(self.ui.cbxMeasureLayer.currentText())
                    item.setText(cLyr.source())
            elif item.column() == 3:
                if self.ui.rdoCalcSingle.isChecked() == True:
                    item.setText('single')
                else:
                    item.setText('multiple')
            elif item.column() == 4:
                if self.ui.rdoMeasure.isChecked() == True:
                    item.setText('measure')
                elif self.ui.rdoCalculate.isChecked() == True:
                    item.setText('calculate')
                else:
                    item.setText('presence')
            elif item.column() == 5:
                if self.ui.cbxCalcField.isEnabled():
                    item.setText(self.ui.cbxCalcField.currentText())
                else:
                    item.setText = ''
            elif item.column() == 6:
                if self.ui.rdoSum.isChecked() == True:
                    item.setText('sum')
                elif self.ui.rdoMean.isChecked() == True:
                    item.setText('mean')
                elif self.ui.rdoMax.isChecked() == True:
                    item.setText('max')
                elif self.ui.rdoMin.isChecked() == True:
                    item.setText('min')
                else:
                    item.setText('count')
            elif item.column() == 7:
                outText = self.ui.cbxSelectField.currentText()
                if outText == "--Create New--":
                    item.setText(self.ui.leNewField.text())
                else:
                    item.setText(outText)
        self.cancelCalcEdit()
        if self.ui.twCalculations.rowCount() > 0:
            self.ui.pbRun.setEnabled(True)

    # delete a calculation
    def deleteCalculation(self):
        selected = self.ui.twCalculations.selectedItems()
        row = self.ui.twCalculations.row(selected[0])
        self.ui.twCalculations.removeRow(row)
        self.cancelCalcEdit()
        if self.ui.twCalculations.rowCount() == 0:
            self.ui.pbRun.setDisabled(True)
        else:
            self.ui.pbRun.setEnabled(True)

    # load a list of calculations and if files available and not loaded,
    # load them
    def loadCalculationList(self):
        import ftools_utils
        newLayersLoaded = False
        message = ''
        cFile = ""
        cFile = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select calculations file" ), '.',
            "*.csv" )
        if cFile != "":
            tf = open(cFile,'rU')
            calcData = tf.readlines()
            tf.close()
            rCnt = self.ui.twCalculations.rowCount()
            for i in range(rCnt):
                self.ui.twCalculations.removeRow(i)
            warnUser = False
            for i in range(len(calcData)):
                loadError = 0
                fields = calcData[i].strip().split(',')
                if i == 0:
                    if not fields[0] == 'pu_layer':
                        return
                elif len(fields) == 8:
                    # grid layer check
                    # remove extra quotation marks
                    fGText = fields[0].replace("'",'').replace("'",'')
                    # get polygon layers
                    layerList = ftools_utils.getLayerNames([QGis.Polygon])
                    cbIndex = -1
                    glName = ''
                    for lName in layerList:
                        cLyr = ftools_utils.getVectorLayerByName(lName)
                        if cLyr.source() == fGText:
                            glName = cLyr.name()
                    if glName == '':
                        # get default layer name
                        glName = os.path.splitext(os.path.basename(fGText))[0]
                        srcLyr = QgsVectorLayer(fGText, glName, 'ogr')
                        if srcLyr.isValid():
                            if srcLyr.geometryType() == QGis.Polygon:
                                self.allLayers.append(glName)
                                QgsMapLayerRegistry.instance().addMapLayer(srcLyr)
                                newLayersLoaded = True
                            else:
                                message = message + '%s is not an area layer and can not be used a PU layer%s' % (glName, os.linesep)
                                loadError += 1
                                warnUser = True
                        else:
                            message = message + '%s failed to load%s' % (glName, os.linesep)
                            loadError += 1
                            warnUser = True
                    # measure layer check
                    # remove extra quotation marks
                    fMText = fields[2].replace("'",'').replace("'",'')
                    # get all vector layers
                    layerList = ftools_utils.getLayerNames([QGis.Polygon, QGis.Line, QGis.Point])
                    cbIndex = -1
                    mlName = ''
                    for lName in layerList:
                        cLyr = ftools_utils.getVectorLayerByName(lName)
                        if cLyr.source() == fMText:
                            mlName = cLyr.name()
                    if mlName == '':
                        # get layer name from path
                        extension = os.path.splitext(os.path.basename(fMText))[1]
                        if extension == '.shp':
                            mlName = os.path.splitext(os.path.basename(fMText))[0]
                            srcLyr = QgsVectorLayer(fMText, mlName, 'ogr')
                            if srcLyr.isValid():
                                #self.allLayers.append(mlName)
                                QgsMapLayerRegistry.instance().addMapLayer(srcLyr)
                                newLayersLoaded = True
                            else:
                                message = message + '%s failed to load%s' % (mlName, os.linesep)
                                loadError += 1
                                warnUser = True
                        else:
                            # measure raster layer check
                            layerList = []
                            layers = []
                            for key, value in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                                if 'raster' in str(value.__class__).lower():
                                    layerList.append(str(value.name()))
                                    layers.append(value)
                            for q in range(len(layers)):
                                if layers[q] == fMText:
                                    mlName = layerList[q]
                            if mlName == '':
                                # get layer name from path
                                mlName = os.path.splitext(os.path.basename(fMText))[0]
                                srcLyr = QgsRasterLayer(fMText, mlName)
                                if srcLyr.isValid():
                                    self.allLayers.append(mlName)
                                    QgsMapLayerRegistry.instance().addMapLayer(srcLyr)
                                    newLayersLoaded = True
                                else:
                                    message = message + '%s failed to load%s' % (mlName, os.linesep)
                                    loadError += 1
                                    warnUser = True
                    if loadError == 0:
                        # create row and populate it
                        self.newCalculation()
                        self.ui.twCalculations.item(i-1,0).setText(fGText)
                        self.ui.twCalculations.item(i-1,1).setText(fields[1].replace("'",'').replace("'",''))
                        self.ui.twCalculations.item(i-1,2).setText(fMText)
                        self.ui.twCalculations.item(i-1,3).setText(fields[3].replace("'",'').replace("'",''))
                        self.ui.twCalculations.item(i-1,4).setText(fields[4].replace("'",'').replace("'",''))
                        self.ui.twCalculations.item(i-1,5).setText(fields[5].replace("'",'').replace("'",''))
                        self.ui.twCalculations.item(i-1,6).setText(fields[6].replace("'",'').replace("'",''))
                        self.ui.twCalculations.item(i-1,7).setText(fields[7].replace("'",'').replace("'",''))
            # check for weird rows
            rCnt = self.ui.twCalculations.rowCount()
            for i in range(rCnt):
                if self.ui.twCalculations.item(i,0).text() == '':
                    self.ui.twCalculations.removeRow(i)
            if warnUser:
                QtGui.QMessageBox.warning(self, self.tr("Load Error"), 
                        self.tr(message))
        if newLayersLoaded:
            layers = ftools_utils.getLayerNames([QGis.Polygon])
            self.ui.cbxPlanningGrid.addItems(layers)
            self.ui.pbRun.setEnabled(True)
        
        self.cancelCalcEdit()

    # save calculation list
    def saveCalculationList(self):
        cFile = ""
        cFile = QtGui.QFileDialog.getSaveFileName( self,
            self.tr( "Select calculations file name" ), '.',
            "*.csv" )
        if cFile != "":
            if os.path.splitext(str(cFile))[1] != '.csv':
                cFile = str(cFile) + '.csv'
            cf = file(cFile,'w')
            cf.write('pu_layer,puid,measure_layer,field_output,measure_type,calculation_field,operator,output_name'+os.linesep)
            rCnt = self.ui.twCalculations.rowCount()
            for i in range(rCnt):
                outline = ''
                outline += self.ui.twCalculations.item(i,0).text() + ','
                outline += self.ui.twCalculations.item(i,1).text() + ','
                outline += self.ui.twCalculations.item(i,2).text() + ','
                outline += self.ui.twCalculations.item(i,3).text() + ','
                outline += self.ui.twCalculations.item(i,4).text() + ','
                outline += self.ui.twCalculations.item(i,5).text() + ','
                outline += self.ui.twCalculations.item(i,6).text() + ','
                outline += self.ui.twCalculations.item(i,7).text() + os.linesep
                cf.write(outline)
            cf.close()
            QtGui.QMessageBox.information(self, self.tr("Saved"), 
                    self.tr("%s saved" % cFile))

    #
    # control visibility and functioning of calculation content elements
    #

    # measured geometry type
    # adjust interface if points choosen
    def setMeasurePoints(self):
        import ftools_utils
        layers = ftools_utils.getLayerNames([QGis.Point])
        self.updateMeasureLayer(layers)
        self.setSingle()
        
    # measured geometry type
    # adjust interface if lines choosen
    def setMeasureLines(self):
        import ftools_utils
        layers = ftools_utils.getLayerNames([QGis.Line])
        self.updateMeasureLayer(layers)
        self.setSingle()
        
    # measured geometry type
    # adjust interface if areas choosen
    def setMeasurePolygons(self):
        import ftools_utils
        layers = ftools_utils.getLayerNames([QGis.Polygon])
        self.updateMeasureLayer(layers)
        self.setSingle()

    # measured geometry type
    # adjust interface if raster choosen
    def setMeasureRasters(self):
        layers = []
        for key, value in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if 'raster' in str(value.__class__).lower():
                layers.append(str(value.name()))
        self.updateMeasureLayer(layers)
        self.disableIntersectionOptions()

    # measure layer
    # update measure layer options
    def updateMeasureLayer(self, layers):
        self.ui.cbxMeasureLayer.clear()
        self.ui.cbxMeasureLayer.addItems(layers)
        self.setCalcFields()

    # measure layer
    # update calculated field options
    def setCalcFields(self):
        import ftools_utils
        self.ui.cbxCalcField.clear()
        calcLayer = self.ui.cbxMeasureLayer.currentText()
        selectedLayer = ftools_utils.getVectorLayerByName(unicode(calcLayer))
        if selectedLayer != None:
            fields = ftools_utils.getFieldList(selectedLayer)
            for i in fields:
                if fields[i].type() == QtCore.QVariant.Int or \
                fields[i].type() == QtCore.QVariant.Double:
                    self.ui.cbxCalcField.addItem(unicode(fields[i].name()))
    
    # number of output fields
    # adjust interface if single output field is choosen
    def setSingle(self):
        # switch buttons
        self.ui.rdoCalcSingle.setChecked(True)
        self.ui.rdoCalcMulti.setChecked(False)
        if self.ui.rdoRaster.isChecked() == False:
            # enable insection action options
            self.ui.lblMeasureOrCalc.setEnabled(True)
            self.ui.rdoMeasure.setEnabled(True)
            self.ui.rdoPresence.setEnabled(True)
            self.ui.rdoCalculate.setEnabled(True)
            self.setMeasure()
            self.ui.lblCalcField.setText('Select Field for Calculation')
        self.ui.lblSelectField.setEnabled(True)
        self.ui.cbxSelectField.setEnabled(True)
        self.ui.cbxSelectField.setCurrentIndex(0)
        self.ui.lblNewField.setText('Enter New Field Name')
        self.ui.leNewField.setMaxLength(10)
        self.ui.leNewField.setEnabled(True)

    # number of output fields
    # adjust interface if multiple output fields are choosen
    def setMulti(self):
        self.ui.rdoCalcSingle.setChecked(False)
        self.ui.rdoCalcMulti.setChecked(True)
        self.disableIntersectionOptions()
        # enable selection of calculation field if vector
        self.ui.lblCalcField.setText('Select Field for Calculation (Create new fields for each unique value)')
        if self.ui.rdoRaster.isChecked() == False:
            self.ui.lblCalcField.setEnabled(True)
            self.ui.cbxCalcField.setEnabled(True)
        else:
            self.ui.lblCalcField.setDisabled(True)
            self.ui.cbxCalcField.setDisabled(True)
        # disable re-use of an existing field
        self.ui.lblSelectField.setEnabled(False)
        self.ui.cbxSelectField.setEnabled(False)
        self.ui.cbxSelectField.setCurrentIndex(0)
        self.ui.lblNewField.setText('Enter field prefix (up to 6 characters)')
        self.ui.leNewField.setMaxLength(6)
        self.ui.leNewField.setEnabled(True)

    # measure type
    # disable intersection options for multiple and raster calculations
    def disableIntersectionOptions(self):
        # disable insection action options
        self.ui.lblMeasureOrCalc.setEnabled(False)
        self.ui.rdoMeasure.setChecked(True)
        self.ui.rdoMeasure.setEnabled(False)
        self.ui.rdoPresence.setChecked(False)
        self.ui.rdoPresence.setEnabled(False)
        self.ui.rdoCalculate.setChecked(False)
        self.ui.rdoCalculate.setEnabled(False)
        # disable multi select options
        self.setPresence()
        self.ui.rdoSum.setChecked(True)

    # measure type
    # adjust interface if measure option is choosen
    def setMeasure(self):
        self.ui.lblCalcField.setDisabled(True)
        self.ui.cbxCalcField.setDisabled(True)
        if not self.ui.lblMultipleAction.isEnabled():
            self.ui.lblMultipleAction.setEnabled(True)
            self.ui.rdoSum.setEnabled(True)
            self.ui.rdoMean.setEnabled(True)
            self.ui.rdoMax.setEnabled(True)
            self.ui.rdoMin.setEnabled(True)
            self.ui.rdoCount.setEnabled(True)

    # measure type
    # adjust interface if calculate option is choosen
    def setCalculate(self):
        self.ui.lblCalcField.setEnabled(True)
        self.ui.cbxCalcField.setEnabled(True)
        if not self.ui.lblMultipleAction.isEnabled():
            self.ui.lblMultipleAction.setEnabled(True)
            self.ui.rdoSum.setEnabled(True)
            self.ui.rdoMean.setEnabled(True)
            self.ui.rdoMax.setEnabled(True)
            self.ui.rdoMin.setEnabled(True)
            self.ui.rdoCount.setEnabled(True)
    
    # measure type
    # adjust interface if presence option is choosen
    def setPresence(self):
        self.ui.lblCalcField.setDisabled(True)
        self.ui.cbxCalcField.setDisabled(True)
        if self.ui.lblMultipleAction.isEnabled():
            self.ui.lblMultipleAction.setDisabled(True)
            self.ui.rdoSum.setDisabled(True)
            self.ui.rdoMean.setDisabled(True)
            self.ui.rdoMax.setDisabled(True)
            self.ui.rdoMin.setDisabled(True)
            self.ui.rdoCount.setDisabled(True)

    # output field
    # update output field options
    def setIdAndMeasureFields(self, planningGrid):
        import ftools_utils
        self.ui.cbxSelectField.clear()
        self.ui.cbxPuId.clear()
        selectedLayer = ftools_utils.getVectorLayerByName(unicode(planningGrid))
        if selectedLayer != None:
            self.ui.cbxSelectField.addItem(unicode("--Create New--"))
            fields = ftools_utils.getFieldList(selectedLayer)
            for i in fields:
                if fields[i].type() == QtCore.QVariant.Int or \
                fields[i].type() == QtCore.QVariant.Double:
                    self.ui.cbxSelectField.addItem(unicode(fields[i].name()))
                    self.ui.cbxPuId.addItem(unicode(fields[i].name()))

    # output field
    # set output field
    def setOutputField(self):
        if self.ui.cbxSelectField.currentIndex() == 0:
            self.ui.lblNewField.setEnabled(True)
            self.ui.leNewField.setEnabled(True)
        else:
            self.ui.lblNewField.setDisabled(True)
            self.ui.leNewField.setDisabled(True)

    #
    # do the calculations
    #

    # main control function
    def doCalculations(self):
        self.ui.pbRun.setDisabled(True)
        # zoom out to make sure nothing gets oddly clipped
        canvas = qgis.utils.iface.mapCanvas()
        canvas.zoomToFullExtent()
        # start processing
        rCnt = self.ui.twCalculations.rowCount()
        calculationList = []
        for i in range(rCnt):
            entry = []
            entry.append(self.ui.twCalculations.item(i,0).text())
            entry.append(self.ui.twCalculations.item(i,1).text())
            entry.append(self.ui.twCalculations.item(i,2).text())
            entry.append(self.ui.twCalculations.item(i,3).text())
            entry.append(self.ui.twCalculations.item(i,4).text())
            entry.append(self.ui.twCalculations.item(i,5).text())
            entry.append(self.ui.twCalculations.item(i,6).text())
            entry.append(self.ui.twCalculations.item(i,7).text())
            calculationList.append(entry)
        cl = qmCalculateListThread(calculationList,self.ui)
        QtCore.QObject.connect(cl,QtCore.SIGNAL("runProgress(PyQt_PyObject)"),self.setThreadProgress)
        QtCore.QObject.connect(cl,QtCore.SIGNAL("runRange(PyQt_PyObject)"),self.setThreadRange)
        cl.run()
        if len(cl.warningTypes) > 0:
            QtGui.QMessageBox.warning(self, self.tr("Calculations"), self.tr(cl.wMessage))
        else:
            QtGui.QMessageBox.information(self, self.tr("Calculations"), 
                    self.tr("Calculations completed. No errors detected."))
        # reset progress bar
        self.ui.pbListProgress.setValue(0)
        self.ui.pbCalculationProgress.setValue(0)
        # reset system
        self.ui.pbRun.setEnabled(True)

    def setThreadProgress(self, progress):
        self.ui.pbListProgress.setValue(progress)

    def setThreadRange(self, rangeVals):
        self.ui.pbListProgress.setRange(rangeVals[0],rangeVals[1])

class qmCalculateListThread(QtCore.QThread):

    # initialize class
    def __init__(self,calculationList,guiLink):
        super(qmCalculateListThread, self).__init__()
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
        self.warningTypes = []
        self.calcList = calculationList
        self.ui = guiLink
        self.wMessage = ''
        self.logText = ''

    def run(self):
        self.running = True
        warningTypes = []
        self.emit(QtCore.SIGNAL("runProgress(PyQt_PyObject)"),0)
        rCnt = len(self.calcList)
        self.emit(QtCore.SIGNAL("runRange(PyQt_PyObject)" ),(0,rCnt))
        puFile = self.calcList[0][0]
        logFile = os.path.join(os.path.dirname(str(puFile)), 'qcalc_'+datetime.datetime.now().isoformat()[:19].replace('-','').replace(':','') + '_err.log')
        redoFile = os.path.join(os.path.dirname(str(puFile)), 'qcalc_'+datetime.datetime.now().isoformat()[:19].replace('-','').replace(':','') + '_redo.csv')
        if self.ui.rdoWLyr.isChecked() == True:
            writeToCSV = False
        else:
            writeToCSV = True
        for i in range(rCnt):
            warnType = 0
            self.emit(QtCore.SIGNAL("runProgress(PyQt_PyObject)"),i+1)
            # do some basic validation
            puFile = self.calcList[i][0]
            puId = self.calcList[i][1]
            srcFile = self.calcList[i][2]
            outCnt = self.calcList[i][3]
            measType = self.calcList[i][4]
            calcField = self.calcList[i][5]
            operator = self.calcList[i][6]
            outFldName = self.calcList[i][7]
            if puFile == '' or srcFile == '' or puId == '' or outCnt == '' \
                or operator == '' or outFldName == '' :
                warnType = 2
                self.warningTypes.append(2)
            if calcField == '' and measType == 'calculate':
                warnType = 3
                self.warningTypes.append(3)
            if warnType == 0:
                d = qmCalculateThread(puFile,puId,srcFile,outCnt,measType,
                                     calcField,operator,outFldName,writeToCSV)
                QtCore.QObject.connect(d,QtCore.SIGNAL("runSubProgress(PyQt_PyObject)"),self.setSubThreadProgress)
                QtCore.QObject.connect(d,QtCore.SIGNAL("runSubRange(PyQt_PyObject)"),self.setSubThreadRange)
                QtCore.QObject.connect(d,QtCore.SIGNAL("runSubStep(PyQt_PyObject)"),self.setSubThreadStep)
                d.run()
                if d.issueWarning:
                    warnType = 1
                    self.warningTypes.append(1)
                    # write log
                    f = open(logFile,'a')
                    f.write(d.logText)
                    f.close()
                    # write redo calc list
                    if not os.path.exists(redoFile):
                        f = open(redoFile,'a')
                        f.write('pu_layer,puid,measure_layer,field_output,measure_type,calculation_field,operator,output_name'+os.linesep)
                    else:
                        f = open(redoFile,'a')
                    f.write(str(puFile)+','+str(puId)+','+str(srcFile)+','+str(outCnt)+','\
                        +str(measType)+','+str(calcField)+','+str(operator)+','+str(outFldName)+os.linesep)
                    f.close()
        # notify user of success or errors
        self.wMessage = ''
        if 1 in self.warningTypes:
            self.wMessage = "Errors detected. Check process logs in folder with PU file."
        elif 2 in self.warningTypes:
            if self.wMessage == '':
                self.wMessage = "Not all required fields set for a calculation. Not all calculations may have been completed."
            else:
                self.wMessage = self.wMessage + '\n' + "Not all required fields set for a calculation. Not all calculations may have been completed."
        elif 3 in self.warningTypes:
            if self.wMessage == '':
                self.wMessage = "Field calculation selected but calculation field not selected. Not all calculations may have been completed."
            else:
                self.wMessage = self.wMessage + '\n' + "Field calculation selected but calculation field not selected. Not all calculations may have been completed."

    def stop(self):
        self.running = False
                    
    def setSubThreadProgress(self, progress):
        self.ui.pbCalculationProgress.setValue(progress)

    def setSubThreadRange(self, rangeVals):
        self.ui.pbCalculationProgress.setRange(rangeVals[0],rangeVals[1])

    def setSubThreadStep(self, step):
        self.ui.lblCPAction.setText(step)

