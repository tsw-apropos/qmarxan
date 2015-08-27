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
from ui_qm_import import Ui_qm_import
import csv,sys,os

class qmImport(QtGui.QDialog):
    def __init__(self, iface):
        self.iface = iface
        self.searchDir = '.'
        
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
        self.ui = Ui_qm_import()
        self.ui.setupUi(self)
        self.setFixedSize(465,398)
        self.setWindowTitle(self.tr("Import Marxan Results"))
        layers = ftools_utils.getLayerNames([QGis.Polygon])
        self.ui.cbxPlanningGrid.addItems(layers)
        self.setFields(self.ui.cbxPlanningGrid.currentText())
        self.setOutputField()
        self.ui.buttonOk = self.ui.buttonBox.button( QtGui.QDialogButtonBox.Ok )

        QtCore.QObject.connect(self.ui.pbInputFile, QtCore.SIGNAL("clicked()"), self.selectInputFile)
        # selecting measure layer
        QtCore.QObject.connect(self.ui.cbxPlanningGrid, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setFields)
        # selecting field name
        QtCore.QObject.connect(self.ui.cbxSelectField, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setOutputField)

    #
    # progressStatus - update progress bar
    #
    
    def progressStatus(self,action='update',pval=0):
        if action in ('start','reset'):
            self.progress = 0
            self.step = 0
        elif action == 'finish':
            self.progress = 100
            self.step = 0
        elif action == 'step':
            self.step = self.step + pval
            self.progress = self.step
        elif action =='update':
            self.progress = self.step + pval
        self.ui.progressBar.setValue(self.progress)
        self.ui.progressBar.repaint()
    
    #
    # setFields - set fields to select based on selected planning units file
    #
    
    def setFields(self, planningGrid):
        import ftools_utils
        self.ui.cbxSelectField.clear()
        self.ui.cbxIdField.clear()
        selectedLayer = ftools_utils.getVectorLayerByName(unicode(planningGrid))
        if selectedLayer != None:
            self.ui.cbxSelectField.addItem(unicode("--Create New--"))
            fields = ftools_utils.getFieldList(selectedLayer)
            for i in fields:
                if fields[i].type() == QtCore.QVariant.Int or \
                fields[i].type() == QtCore.QVariant.Double:
                    self.ui.cbxSelectField.addItem(unicode(fields[i].name()))
                    self.ui.cbxIdField.addItem(unicode(fields[i].name()))
    
    #
    # setOutputField - control enabled / disabled status of fields if
    #                  the user selects create new or an existing field
    #
    
    def setOutputField(self):
        if self.ui.cbxSelectField.currentIndex() == 0:
            self.ui.lblNewField.setEnabled(True)
            self.ui.leNewResultsField.setEnabled(True)
        else:
            self.ui.lblNewField.setDisabled(True)
            self.ui.leNewResultsField.setDisabled(True)

    #
    # selectInputFile - provide linkage between browse button and line edit
    #
    
    def selectInputFile(self):
        sFile = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan results file" ), self.searchDir,
            "*.csv *.txt" )
        if sFile != "":
            self.searchDir = sFile
            self.ui.leInputFile.setText(sFile)
 
    #
    # accept - provide action on clicking "OK"
    #          temporarily disable interface and try to import file
    #          provide notice if success or failure
    #
 
    def accept(self):       
        status = False  
        message = "Failure!"   
        import ftools_utils
        self.ui.buttonOk.setEnabled(False)
        self.progressStatus('start')
        puFile = self.ui.cbxPlanningGrid.currentText()
        inFile = self.ui.leInputFile.text()
        if inFile != "":
            proceed = True
        else:
            proceed = False
        if proceed and self.ui.cbxSelectField.currentIndex() == 0:
            if self.ui.leNewResultsField.text() != "":
                fName = self.ui.leNewResultsField.text()
                proceed = True
            else:
                proceed = False
        else:
            fName = self.ui.cbxSelectField.currentText()
        if proceed:
            status, message = self.do_import(puFile, inFile, fName)

        if status:
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.repaint()
            QtGui.QMessageBox.information(self, self.tr("Planning Unit Calculation"), 
                        self.tr(message))
        else:
            QtGui.QMessageBox.warning(self, self.tr("Planning Unit Calculation"), 
                        self.tr(message))

        # reset progress bar
        self.progressStatus('reset')
        # reset system
        self.ui.buttonOk.setEnabled(True)
        
    #
    # do_import - check file format and call import function
    #
        
    def do_import(self, puFile, inFile, fName):
        import ftools_utils, string
        success = True
        message = "Import Successful"
        puLayer = ftools_utils.getVectorLayerByName(unicode(puFile))
        # convert input layer into list for easy searching
        f = open(inFile,'rb')
        inputVals = {}
        reader = csv.reader(f, delimiter = ',')
        header = reader.next()
#         QtGui.QMessageBox.warning(self, self.tr("pu_id"), 
#                     self.tr("col1:%s,col2:%s" % (header[0],header[1])))
        if (string.upper(header[0]) == 'PUID' or string.upper(header[0]) == 'PLANNING_UNIT') and \
            (string.upper(header[1]) == 'SOLUTION' or string.upper(header[1]) == 'NUMBER'):
            for row in reader:
                # convert values into float when saving to list
                inputVals[float(row[0])] = [float(row[0]), float(row[1])]
        else:
            return(False, 'Invalid or unsupported input format')
        f.close()
        success, message = self.updateLayer(puLayer, fName, inputVals)
        return (success, message)
        
    #
    # The updateLayer function is modelled very closely after the Carson Farmer
    # code used in qm_calc. See qm_calc.py for more details
    # TSW - updated 2012-03-22 to speed matching by use of dictionary
    #
        
    def updateLayer(self, polygonLayer, fieldName = "", updateVals = {}):
        import ftools_utils
        message = "Calculation Complete!"
        feature = QgsFeature()
        polygonLayer.blockSignals(True)
        wasEditing = polygonLayer.isEditable() 
        # if it is editable, then we must be in edit mode
        if not wasEditing:
            polygonLayer.startEditing()
            if not polygonLayer.isEditable():
                message = "Unable to edit input polygon layer: Please choose a layer with edit capabilities."
                return (False, message)
        fieldMap = polygonLayer.pendingFields()
        fieldMap = dict([(field.name(), index) for index, field in fieldMap.iteritems()])
        attributeId = -1
        if fieldName.toUpper() in fieldMap: 
            # update existing uppercase field
            attributeId = fieldMap[fieldName.toUpper()]
        elif fieldName in fieldMap: 
            # update existing lower or mixed case field
            attributeId = fieldMap[fieldName]
        else: 
            # create new field
            if not polygonLayer.dataProvider().capabilities() > 7: # can't add attributes
                message = "Data provider does not support adding attributes: " + \
                    "Cannot add required field."
                if not wasEditing:
                    polygonLayer.rollBack()
                return (False, message)
            newField = QgsField(fieldName, QtCore.QVariant.Double, "real", 10, 5)
            polygonLayer.beginEditCommand("Attribute added")
            if not polygonLayer.addAttribute(newField):
                message = "Could not add the new field to the polygon layer."
                polygonLayer.destroyEditCommand()
                if not wasEditing:
                    polygonLayer.rollBack()
                return (False, message)
            polygonLayer.endEditCommand()
            # get index of the new field
            fieldMap = polygonLayer.pendingFields()
            fieldMap = dict([(field.name(), index) for index, field in fieldMap.iteritems()])
            if not fieldName in fieldMap:
                message =  "Could not find the newly created field."
                if not wasEditing:
                    polygonLayer.rollBack()
                return (False, message)
            attributeId = fieldMap[fieldName]
        # get index of planning unit id field
        puidIdx = fieldMap[self.ui.cbxIdField.currentText()]
        if attributeId == -1:
            message= "Error writing to the new attribute."
            if not wasEditing:
                polygonLayer.rollBack()
            return (False, message)
        if puidIdx == -1:
            message = "Could not find %s" % self.ui.cbxIdField.currentText()
        pAA = polygonLayer.pendingAllAttributesList()
        polygonLayer.select(pAA, QgsRectangle(), False, False)
        polygonLayer.beginEditCommand("Updated marxan results field")
        fCount = polygonLayer.dataProvider().featureCount()
        x = 0
        try:
            while polygonLayer.nextFeature(feature):
                match = False
                pbVal = (x*100)/fCount
                self.progressStatus('update',pbVal)
                # retrieve attributes for current feature
                atMap = feature.attributeMap()
                pu_id = -1
                pu_id = float(atMap[puidIdx].toString())
                if pu_id in updateVals:
                    commitValue = updateVals[pu_id][1]
                    match = True
                if pu_id > -1 and match:
                    polygonLayer.changeAttributeValue(feature.id(), attributeId, commitValue, False)
                x = x + 1
            polygonLayer.endEditCommand()
        except Exception, err:
            message = "An error occured while adding measure:%s%s" % (os.linesep,str(err))
            if not wasEditing:
                polygonLayer.rollBack()
                return (False, message)

        # stop blocking layerModified signals and make sure that one layerModified signal is emitted
        polygonLayer.blockSignals(False)
        polygonLayer.setModified(True, False)

        if not wasEditing:
            polygonLayer.commitChanges()
        return (True, message)        
