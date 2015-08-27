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
from ui_qm_export import Ui_qm_export
import sys, os, csv, math
from batch_sort import batch_sort
import datetime

# create the dialog for zoom to point
class qmExport(QtGui.QDialog):
    def __init__(self, iface):
        self.iface = iface
        self.progress = 0
        self.step = 0
        self.exportCount = 0
        self.outDir = "."

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
        self.ui = Ui_qm_export()
        self.ui.setupUi(self)
        self.setFixedSize(725,712)
        self.setWindowTitle(self.tr("Export data to Marxan Input Files"))
        # add input layers to select planning grid
        layers = ftools_utils.getLayerNames([QGis.Polygon])
        self.ui.cbxPlanningGrid.addItems(layers)
        self.ui.cbxTolerance.addItems(['100','10','1','0.1','0.01','0.001','0.0001','0.00001'])
        self.ui.cbxTolerance.setCurrentIndex(2)
        self.setExportFields(self.ui.cbxPlanningGrid.currentText())
        self.ui.buttonOk = self.ui.buttonBox.button( QtGui.QDialogButtonBox.Ok )
        # enabled automatic refresh of fields window
        QtCore.QObject.connect(self.ui.cbxPlanningGrid, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setExportFields)
        # enable buttons under fields window
        QtCore.QObject.connect(self.ui.pbSelectAll, QtCore.SIGNAL("clicked()"), self.selectAll)
        QtCore.QObject.connect(self.ui.pbSelectNone, QtCore.SIGNAL("clicked()"), self.selectNone)
        QtCore.QObject.connect(self.ui.pbInvertSelection, QtCore.SIGNAL("clicked()"), self.invertSelection)
        QtCore.QObject.connect(self.ui.pbReadSpecFile, QtCore.SIGNAL("clicked()"), self.readSpecFile)
        # enable selection of output directory
        QtCore.QObject.connect(self.ui.pbOutputDir, QtCore.SIGNAL("clicked()"), self.setOutputDir)
        # enable accessiblity of boundary cost field selection
        QtCore.QObject.connect(self.ui.rdoLength, QtCore.SIGNAL("clicked()"), self.disableBCF)
        QtCore.QObject.connect(self.ui.rdoField, QtCore.SIGNAL("clicked()"), self.enableBCF)
        QtCore.QObject.connect(self.ui.rdoLengthnField, QtCore.SIGNAL("clicked()"), self.enableBCF)

    def disableBCF(self):
        self.ui.lblBoundaryCost.setDisabled(True)
        self.ui.cbxBoundaryCost.setDisabled(True)

    def enableBCF(self):
        self.ui.lblBoundaryCost.setEnabled(True)
        self.ui.cbxBoundaryCost.setEnabled(True)
        
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
        if self.progress == 100 and action != 'finish':
            self.progress = 99
        self.ui.progressBar.setValue(self.progress)
        self.ui.progressBar.repaint()

    def adjBound(self,inVal,id1,id2):
        if id1 == id2:
            if self.ui.rdoFullValue.isChecked():
                retVal = inVal
            elif self.ui.rdoHalfValue.isChecked():
                retVal = inVal/2.0
            else:
                retVal = 0.0
        else:
            retVal = inVal
        return(retVal)
        
    def textRound(self,inputValue):
        if inputValue > 0:
            roundString = '%0.5f' % inputValue
        elif inputValue < 0.0001:
            roundString = '%0.10f' % inputValue
        elif inputValue < 0.000000001:
            roundString = '%0.15f' % inputValue
        elif inputValue < 0.0000000000001:
            roundString = '%0.20f' % inputValue
        else:
            roundString = '%0.30f' % inputValue
        return(roundString)
        
    def setExportFields(self, planningGrid):
        import ftools_utils
        def setCheckState(item):
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
        def setEditState(item):
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        def setViewState(item):
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        def addField(fName, x):
            # field no
            item = QtGui.QTableWidgetItem()
            setCheckState(item)
            item.setText(str(x))
            item.setToolTip('Field Number')
            self.ui.twFields.setItem(x,0,item)
            # id
            item = QtGui.QTableWidgetItem()
            setEditState(item)
            item.setText(str(x))
            item.setToolTip('Custom Id')
            self.ui.twFields.setItem(x,1,item)
            # prop
            item = QtGui.QTableWidgetItem(str(1.0), type=QtCore.QVariant.Double)
            setEditState(item)
            item.setToolTip('Target Proportion')
            self.ui.twFields.setItem(x,2,item)
            # target
            item = QtGui.QTableWidgetItem(str(0.0), type=QtCore.QVariant.Double)
            setEditState(item)
            item.setToolTip('Target Value')
            self.ui.twFields.setItem(x,3,item)
            # target2
            item = QtGui.QTableWidgetItem(str(0), type=QtCore.QVariant.Int)
            setEditState(item)
            item.setToolTip('Minimum Clump Size')
            self.ui.twFields.setItem(x,4,item)
            # spf
            item = QtGui.QTableWidgetItem(str(1.0), type=QtCore.QVariant.Double)
            setEditState(item)
            item.setToolTip('Penalty Factor')
            self.ui.twFields.setItem(x,5,item)
            # field name
            item = QtGui.QTableWidgetItem()
            setViewState(item)
            item.setText(fName)
            item.setToolTip('Field Name')
            self.ui.twFields.setItem(x,6,item)
        # clear the grid    
        self.ui.twFields.clear()
        self.ui.twFields.repaint()
        # prepare the grid
        self.ui.twFields.setColumnCount(7)
        selectedLayer = ftools_utils.getVectorLayerByName(unicode(planningGrid))
        if selectedLayer != None:
            fields = ftools_utils.getFieldList(selectedLayer)
        else:
            return()
        fcount = len(fields)
        self.ui.twFields.setRowCount(fcount)
        header = QtCore.QStringList()
        header.append('field_no')
        header.append('id')
        header.append('prop')
        header.append('target')
        header.append('target2')
        header.append('spf')
        header.append('name')
        self.ui.twFields.setHorizontalHeaderLabels(header)
        x = 0
        for i in fields.values():
            addField(i.name(),x)
            x = x + 1
        # set drop down boxes
        self.ui.cbxIdField.clear()
        self.ui.cbxCostField.clear()
        self.ui.cbxStatusField.clear()
        self.ui.cbxBoundaryCost.clear()
        fidx = -1
        for i in fields:
            if fields[i].type() == QtCore.QVariant.Int or \
            fields[i].type() == QtCore.QVariant.Double:
                self.ui.cbxIdField.addItem(fields[i].name())
                self.ui.cbxCostField.addItem(fields[i].name())
                self.ui.cbxStatusField.addItem(fields[i].name())
                self.ui.cbxBoundaryCost.addItem(fields[i].name())
                fidx = fidx + 1
            if fields[i].name() in ('pu_id', 'puid'):
                self.ui.cbxIdField.setCurrentIndex(fidx)
            if fields[i].name() in ('pu_cost', 'pucost'):
                self.ui.cbxCostField.setCurrentIndex(fidx)
            if fields[i].name() in ('pu_status', 'pustatus'):
                self.ui.cbxStatusField.setCurrentIndex(fidx)
            if fields[i].name() in ('bnd_cost', 'bndcost'):
                self.ui.cbxBoundaryCost.setCurrentIndex(fidx)

    def selectAll(self):
        rcount = self.ui.twFields.rowCount()
        for i in range(rcount):
            item = self.ui.twFields.item(i,0)
            item.setCheckState(QtCore.Qt.Checked)
    
    def selectNone(self):
        rcount = self.ui.twFields.rowCount()
        for i in range(rcount):
            item = self.ui.twFields.item(i,0)
            item.setCheckState(QtCore.Qt.Unchecked)
    
    def invertSelection(self):
        rcount = self.ui.twFields.rowCount()
        for i in range(rcount):
            item = self.ui.twFields.item(i,0)
            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
    
    def readSpecFile(self):
        searchDir = self.outDir
        sFile = ""
        sFile = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select spec.dat file" ), searchDir,
            "*.dat" )
        if sFile != "":
            self.parseSpecFile(sFile)
            
    def parseSpecFile(self,sFile):
        tf = open(sFile,'r')
        reader = csv.reader(tf, delimiter = '\t', quoting=csv.QUOTE_NONE)
        # find matching fields and adjust 
        # targets and spf values
        r_id = -1
        r_prop = -1
        r_target = -1
        r_target2 = -1
        r_spf = -1
        r_name = -1
        for row in reader:
            if row[0] == 'id':
                for j in range(len(row)):
                    if row[j] == 'id':
                        r_id = j
                    elif row[j] == 'prop':
                        r_prop = j
                    elif row[j] == 'target':
                        r_target = j
                    elif row[j] == 'target2':
                        r_target2 = j
                    elif row[j] == 'spf':
                        r_spf = j
                    elif row[j] == 'name':
                        r_name = j
                continue
            rcount = self.ui.twFields.rowCount()
            for i in range(rcount):
                item = self.ui.twFields.item(i,6)
                if item.text() == row[r_name]:
                    self.ui.twFields.item(i,0).setCheckState(QtCore.Qt.Checked)
                    if r_id <> -1:
                        self.ui.twFields.item(i,1).setText(row[r_id])
                    if r_prop <> -1:
                        self.ui.twFields.item(i,2).setText(row[r_prop])
                    if r_target <> -1:
                        self.ui.twFields.item(i,3).setText(row[r_target])
                    if r_target2 <> -1:
                        self.ui.twFields.item(i,4).setText(row[r_target2])
                    if r_spf <> -1:
                        self.ui.twFields.item(i,5).setText(row[r_spf])
        tf.close() 
                        
    def setOutputDir(self):
        temp = QtGui.QFileDialog.getExistingDirectory( self,
            self.tr( "Select directory to write Marxan input files" ), self.outDir)
        if temp != "":
            self.outDir = str(temp)
            self.ui.outDirectory.setText(self.outDir)
            sFile = os.path.join(self.outDir,'spec.dat')
            if os.path.isfile(sFile):
                self.parseSpecFile(sFile)

    def accept(self):
        # check that information is provided
        self.ui.buttonOk.setEnabled( False )
        self.exportCount = 0
        if self.ui.chkSpecies.isChecked() == True:
            exportSpec = True
            self.exportCount = self.exportCount + 1
        else:
            exportSpec = False
        if self.ui.chkPlanningUnits.isChecked() == True:
            exportPu = True
            self.exportCount = self.exportCount + 1
        else:
            exportPu = False
        if self.ui.chkPUvsSPC.isChecked() == True:
            exportPuSpc2 = True
            self.exportCount = self.exportCount + 1
        else:
            exportPuSpc2 = False
        if self.ui.chkBoundary.isChecked() == True:
            exportBound = True
            self.exportCount = self.exportCount + 1
        else:
            exportBound = False
        if self.exportCount == 0:
            QtGui.QMessageBox.warning(self, self.tr("Export Error"), 
                        self.tr("No export files selected"))
            self.ui.buttonOk.setEnabled( True )
            return()
        # check that an export directory has been selected 
        # and that it exists
        if self.outDir == "":
            QtGui.QMessageBox.warning(self, self.tr("Export Error"), 
                        self.tr("No export directory selected"))
            self.ui.buttonOk.setEnabled( True )
            return()
        # check that some fields have been marked as conservation factors
        # if anything more than boundary file export has been selected
        if exportPuSpc2 or exportSpec:
            someSelected = False
            rcount = self.ui.twFields.rowCount()
            for i in range(rcount):
                item = self.ui.twFields.item(i,0)
                if item.checkState() == QtCore.Qt.Checked:
                    someSelected = True
            if someSelected == False:
                QtGui.QMessageBox.warning(self, self.tr("Export Error"), 
                            self.tr("No fields marked for export"))
                self.ui.buttonOk.setEnabled( True )
                return()
        # set progress bar
        self.progressStatus('start')
        if exportSpec:
            self.exportSpeciesFile()
        if exportPu:
            self.exportPlanningUnitFile()
        if exportPuSpc2:
            self.exportSpeciesVsPlanningFile()
        if exportBound:
            self.exportBoundaryFile()
        self.progressStatus('finish')
        # notify success
        QtGui.QMessageBox.information(self, self.tr("Marxan Export"), 
                        self.tr("File(s) export complete"))
        # reset progress bar
        self.progressStatus('reset')
        # reset system
        self.ui.buttonOk.setEnabled( True )

    def exportSpeciesFile(self):
        fname = os.path.join(self.outDir, 'spec.dat')
        nl = os.linesep
        tmpf = file(fname, 'w')
        tmpf.write("id\tprop\ttarget\ttarget2\tspf\tname%s" % nl)
        self.ui.lbExportAction.setText('Writing spec file')
        rcount = self.ui.twFields.rowCount()
        for i in range(rcount):
            item = self.ui.twFields.item(i,0)
            if item.checkState() == QtCore.Qt.Checked:
                outText = self.ui.twFields.item(i,1).text() + '\t' + \
                    self.ui.twFields.item(i,2).text() + '\t' + \
                    self.ui.twFields.item(i,3).text() + '\t' + \
                    self.ui.twFields.item(i,4).text() + '\t' + \
                    self.ui.twFields.item(i,5).text() + '\t' + \
                    self.ui.twFields.item(i,6).text() + nl
                tmpf.write(outText)       
            pval = (i*100)/rcount/self.exportCount
            self.progressStatus('update',pval)
        self.progressStatus('step',pval)
        tmpf.close()
    
    def exportPlanningUnitFile(self):
        import ftools_utils
        fname = os.path.join(self.outDir, 'pu.dat')
        nl = os.linesep
        tmpf = file(fname, 'w')
        tmpf.write("id\tcost\tstatus\txloc\tyloc%s" % nl)
        lname = self.ui.cbxPlanningGrid.currentText()
        plProv = ftools_utils.getVectorLayerByName(lname).dataProvider()
        # get count for posting progress
        fCount = plProv.featureCount()
        # get value indexes
        fidx = plProv.fieldNameIndex(self.ui.cbxIdField.currentText())
        cidx = plProv.fieldNameIndex(self.ui.cbxCostField.currentText())
        sidx = plProv.fieldNameIndex(self.ui.cbxStatusField.currentText())
        x = 0
        feature = QgsFeature()
        allAttrs = plProv.attributeIndexes()
        plProv.select(allAttrs)
        outVals = []
        self.ui.lbExportAction.setText('Calculating PU values')
        while plProv.nextFeature(feature):
            # get id
            fidValue = feature.attributeMap()[fidx].toString()
            # get cost
            costValue = feature.attributeMap()[cidx].toString()
            # get status
            statusValue = feature.attributeMap()[sidx].toString()
            # get coords
            coords = feature.geometry().centroid().asPoint()
            outVals.append([int(fidValue),costValue,statusValue,coords])
            # write records
            # progress update
            pval = (x*100/2)/fCount/self.exportCount
            self.progressStatus('update',pval)
            # increment counter
            x = x + 1
        self.progressStatus('step',pval)
        outVals.sort()
        x = 0
        self.ui.lbExportAction.setText('Writing PU file')
        for row in outVals:
            outText = str(row[0]) + '\t' + row[1] + '\t' + \
                row[2] + '\t' + str(row[3][0]) + '\t' + \
                str(row[3][1]) + nl
            tmpf.write(outText)
            x = x + 1
            pval = (x*100/2)/fCount/self.exportCount
            self.progressStatus('update',pval)
        tmpf.close()
        self.progressStatus('step',pval)

    def exportSpeciesVsPlanningFile(self):
    
        #
        # NOTE: 2011-12-08 - NEW FEATURE
        # read to array export as two files - puvspr.dat (planning unit id order)
        #                                   - puvspr_sporder.dat (species order)
        #
        import ftools_utils
        fname1 = os.path.join(self.outDir,'puvspr.dat')
        fname2 = os.path.join(self.outDir,'puvspr_sporder.dat')
        nl = os.linesep
        tmpf1 = file(fname1, 'w')
        tmpf1.write("species\tpu\tamount%s" % nl)
        tmpf2 = file(fname2, 'w')
        tmpf2.write("species\tpu\tamount%s" % nl)
        lname = self.ui.cbxPlanningGrid.currentText()
        plProv = ftools_utils.getVectorLayerByName(lname).dataProvider()
        # get count for posting progress
        fCount = plProv.featureCount()
        # get selected species
        # field indexes
        fidx = plProv.fieldNameIndex(self.ui.cbxIdField.currentText())
        # feature indexes
        idsx = []
        # species indexes
        sids = []
        # max values for species
        maxsx = []
        srcount = self.ui.twFields.rowCount()
        for i in range(srcount):
            item = self.ui.twFields.item(i,0)
            if item.checkState() == QtCore.Qt.Checked:
                temp = self.ui.twFields.item(i,6).text()
                idsx.append(plProv.fieldNameIndex(temp))
                sids.append(int(self.ui.twFields.item(i,1).text()))
                maxsx.append(0.0)
        sCount = len(idsx)
        feature = QgsFeature()
        allAttrs = plProv.attributeIndexes()
        # check if outputs are scaled
        self.ui.lbExportAction.setText('Starting PU vs SP')
        
        if self.ui.rdoScale.isChecked() == True:
            scaleOutput = True
            # get max values to scale output
            y = 0
            plProv.select(allAttrs)
            while plProv.nextFeature(feature):
                for x in range(sCount):
                    # get id
                    cVal = feature.attributeMap()[idsx[x]].toString()
                    if float(cVal) > 0 and maxsx[x] < float(cVal):
                        maxsx[x] = float(cVal)
                # increment counter
                y = y + 1        
                # progress update
                pval = y*100/3.0/fCount/self.exportCount
                self.progressStatus('update',pval)
        else:
            scaleOutput = False
            pval = fCount*100/3.0/fCount/self.exportCount
            self.progressStatus('update',pval)
        self.progressStatus('step',pval)
        
        # calculate values
        self.ui.lbExportAction.setText('Calculating PU vs SP')
        puorder = []
        sporder = []

        y = 0
        plProv.select(allAttrs)
        while plProv.nextFeature(feature):
            for x in range(sCount):
                # get id
                cVal = feature.attributeMap()[idsx[x]].toString()
                if float(cVal) > 0:
                    species = str(sids[x])
                    pu = feature.attributeMap()[fidx].toString()
                    if scaleOutput == True:
                        # scaled ouptut
                        amountText = self.textRound(float(cVal) / maxsx[x])
                    else:
                        # raw output
                        amountText = self.textRound(float(cVal))
                    # save records to array
                    sporder.append([int(species),int(pu),amountText])
                    puorder.append([int(pu),int(species),amountText])
            # increment counter
            y = y + 1        
            # progress update
            pval = y*100/3.0/fCount/self.exportCount
            self.progressStatus('update',pval)
        self.progressStatus('step',pval)

        # sort results
        sporder.sort()
        puorder.sort()
        # write results
        self.ui.lbExportAction.setText('Writing PU vs SP files')
        x = 0
        while x < len(sporder):
            outText = str(puorder[x][1]) + '\t' + str(puorder[x][0]) + '\t' + \
                puorder[x][2] + nl
            tmpf1.write(outText)
            outText = str(sporder[x][0]) + '\t' + str(sporder[x][1]) + '\t' + \
                sporder[x][2] + nl
            tmpf2.write(outText)
            pval = x*100/3.0/len(sporder)/self.exportCount
            self.progressStatus('update',pval)
            x = x + 1
        tmpf1.close()
        tmpf2.close()
        self.progressStatus('step',pval)
        
    def exportBoundaryFile(self):
        import ftools_utils

        def LineLength(p1,p2):
            ll = math.sqrt( (float(p1[0]) - float(p2[0]))**2 + \
                (float(p1[1]) - float(p2[1]))**2 )
            return(ll)

        # track # of possible topological errors
        topoErrorCount = 0
        
        # change to output directory
        os.chdir(str(self.outDir))
        nl = os.linesep
        
        # create temporary file names 
        tempsegfile = 'tempsegfile_%s.txt' % os.getpid()
        tempsortedfile = 'tempsortedfile_%s.txt' % os.getpid()
        tempadjfile = 'tempadjfile_%s.txt' % os.getpid()
        tempsortedadjfile = 'tempsortedadjfile_%s.txt' % os.getpid()
        errorlog = 'topo_error_log_%s.txt' % datetime.date.today().isoformat()
        
        # get planning unit layer
        lname = self.ui.cbxPlanningGrid.currentText()
        plProv = ftools_utils.getVectorLayerByName(lname).dataProvider()
        # get feature count
        fCount = plProv.featureCount()
        # set tolerance setting
        if self.ui.cbxTolerance.currentIndex() == 0:
            # round to 100
            tol = -2
        elif self.ui.cbxTolerance.currentIndex() == 1:
            # round to 10
            tol = -1
        elif self.ui.cbxTolerance.currentIndex() == 3:
            # round to 0.1
            tol = 1
        elif self.ui.cbxTolerance.currentIndex() == 4:
            # round to 0.01
            tol = 2
        elif self.ui.cbxTolerance.currentIndex() == 5:
            # round to 0.001
            tol = 3
        elif self.ui.cbxTolerance.currentIndex() == 6:
            # round to 0.0001
            tol = 4
        elif self.ui.cbxTolerance.currentIndex() == 7:
            # round to 0.00001
            tol = 5
        else:
            # round to 1
            tol = 0
            
        # set action for cost differences
        if self.ui.rdoGreatest.isChecked() == True:
            cAction = 'greatest'
        elif self.ui.rdoLeast.isChecked() == True:
            cAction = 'least'
        else:
            cAction = 'average'

        # boundary type
        if self.ui.rdoLength.isChecked() == True:
            bType = 'length'
        elif self.ui.rdoField.isChecked() == True:
            bType = 'field_value'
        else:
            bType = 'lxf'

        # get field indexes for id and cost fields
        fidx = plProv.fieldNameIndex(self.ui.cbxIdField.currentText())
        if self.ui.rdoLength.isChecked() == True:
            bcidx = -1
        else:
            bcidx = plProv.fieldNameIndex(self.ui.cbxBoundaryCost.currentText())
            
        # build temporary segment file and dictionary
        tsf = open(tempsegfile,'w')
        inGeom = QgsGeometry()
        feature = QgsFeature()
        allAttrs = plProv.attributeIndexes()
        plProv.select(allAttrs)
        x = 0
        segLineCnt = 0
        self.ui.lbExportAction.setText('Extracting Segments')

        while plProv.nextFeature(feature):
            pid = feature.attributeMap()[fidx].toString()
            if bcidx != -1:
                cost = feature.attributeMap()[bcidx].toString()
            else:
                cost = '1.0'
            inGeom = feature.geometry()
            pointList = ftools_utils.extractPoints(inGeom)
            prevPoint = 0
            for i in pointList:
                if prevPoint == 0:
                    prevPoint = i
                else:
                    # write line segment
                    segLen = LineLength([prevPoint[0],prevPoint[1]], [i[0],i[1]])
                    # make spatial key to segment file
                    if round(float(prevPoint[0]),tol) < round(float(i[0]),tol) or \
                        (round(float(prevPoint[0]),tol) == round(float(i[0]),tol) \
                        and round(float(prevPoint[1]),tol) < round(float(i[1]),tol) ):
                        skey = str(round(float(prevPoint[0]),tol)) + '|' + \
                            str(round(float(prevPoint[1]),tol)) + '|' + \
                            str(round(float(i[0]),tol)) + '|' +  \
                            str(round(float(i[1]),tol))
                    else:
                        skey = str(round(float(i[0]),tol)) + '|' +  \
                            str(round(float(i[1]),tol)) + '|' + \
                            str(round(float(prevPoint[0]),tol)) + '|' + \
                            str(round(float(prevPoint[1]),tol))
                    if segLen > 0:
                        tsf.write('%s,%d,%f,%f %s' %  \
                            (skey, int(pid), float(cost), segLen, nl ) )
                    prevPoint = i
            # progress update
            pval = (x*100/3)/fCount/self.exportCount
            self.progressStatus('update',pval)
            # increment counter for progress bar
            x = x + 1
        # clean up
        tsf.close()
        # notify users
        self.ui.lbExportAction.setText('Sorting Segments')
        self.progressStatus('step',pval)
        pval = (50/3)/self.exportCount
        self.progressStatus('update',pval)
        # sort the file
        batch_sort(tempsegfile, tempsortedfile)
        os.remove(tempsegfile)
        # update progress notification 
        self.ui.lbExportAction.setText('Calculating Adjacency')
        pval = (100/3)/self.exportCount
        self.progressStatus('step',pval)
        

        # loop through sorted file and create adjacency file
        tsf = open(tempsortedfile,'r')
        taf = open(tempadjfile,'w')
        # notify users
        pval = (40/3)/self.exportCount
        self.progressStatus('update',pval)
        done = False
        pl = ''
        while not done:
            line = tsf.readline()
            if line == '':
                done = True
            else:
                cl = line.rstrip().split(',')
            if pl != '' and pl != ['']:
                if cl != '' and pl[0] == cl[0]:
                    fCost = 1
                    if bType == 'field_value':
                        bCost = 1
                        if float(pl[2])== float(cl[2]):
                            bCost = float(pl[2])
                        else:
                            if cAction == 'greatest':
                                bCost = max([float(pl[2]),float(cl[2])])
                            elif cAction == 'least':
                                bCost = min([float(pl[2]),float(cl[2])])
                            else:
                                bCost = (float(pl[2]) + float(cl[2]))/2.0
                        fCost = str(bCost)
                    elif bType == 'lxf':
                        bCost = 1
                        if float(pl[2])== float(cl[2]):
                            bCost = float(pl[2])
                        else:
                            if cAction == 'greatest':
                                bCost = max([float(pl[2]),float(cl[2])])
                            elif cAction == 'least':
                                bCost = min([float(pl[2]),float(cl[2])])
                            else:
                                bCost = sum([float(pl[2]),float(cl[2])])/2.0
                        fCost = str(float(pl[3]) * bCost)
                    else:
                        fCost = str(pl[3])
                    # topology error test
                    # check for more matching lines
                    errorLines = True
                    topologyErrorFound = False
                    pids = ''
                    while errorLines:
                        line = tsf.readline()
                        chkLine = line.rstrip().split(',')
                        if chkLine != '' and chkLine[0] == pl[0]:
                            topologyErrorFound = True
                            # an error exists
                            if pids == '':
                                pids = str(pl[1]) + ',' + str(cl[1]) + ',' + str(chkLine[1])
                            else:
                                pids = pids + ',' + str(chkLine[1])
                        else:
                            errorLines = False
                    if topologyErrorFound:
                        if topoErrorCount == 0:
                            el = open(errorlog, 'w')
                            outline = 'There should never be more than 2 overlapping ' + \
                                'line segments. ' + nl + \
                                'Below are listed cases where more than 2 have ' + \
                                'been identified. ' +  nl + 'These should all be ' + \
                                'corrected before using the boundary file' + nl + \
                                '-------' + nl
                            el.write(outline)
                        outline = 'Line segments defined as %s may be topologically invalid.%s' % (str(pl[0]),nl)
                        outline = outline + 'Area ids %s appear to overlap.%s--%s' % (pids,nl,nl) 
                        el.write(outline)
                        topoErrorCount += 1
                    else:
                        # no error proceed
                        if int(pl[1]) < int(cl[1]):
                            taf.write('%020d,%020d,%s %s' % (int(pl[1]),int(cl[1]),fCost,nl))
                        else:
                            taf.write('%020d,%020d,%s %s' % (int(cl[1]),int(pl[1]),fCost,nl))
                elif type(pl) == list:
                    fCost = 1
                    if bType == 'field_value':
                        fCost = str(pl[2])
                    elif bType == 'lxf':
                        fCost = str(float(pl[3]) * float(pl[2]))
                    else:
                        fCost = str(pl[3])
                    taf.write('%020d,%020d,%s %s' % (int(pl[1]),int(pl[1]),fCost,nl))
            pl = line.rstrip().split(',')
        tsf.close()
        taf.close()
        os.remove(tempsortedfile)
        
        # sort adjacency file
        batch_sort(tempadjfile, tempsortedadjfile)
        os.remove(tempadjfile)
        
        # write boundary file
        self.ui.lbExportAction.setText('Writing Boundary File')
        pval = (80/3)/self.exportCount
        self.progressStatus('update',pval)
        
        saf = open(tempsortedadjfile,'r')
        fname = os.path.join(self.outDir, 'bound.dat')
        faf = open(fname,'w')
        faf.write("id1\tid2\tboundary%s" % nl)
        
        done = False
        pl = ''
        while not done:
            line = saf.readline()
            if line == '':
                done = True
                cl = ''
            else:
                cl = line.rstrip().split(',')
            if pl != '':
                if cl != '' and pl[0] == cl[0] and pl[1] == cl[1]:
                    if bType != 'field_value':
                        # note that if field value don't sum the line segments
                        pl = [pl[0],pl[1],sum([float(pl[2]),float(cl[2])])]
                else:
                    bound = self.adjBound(float(pl[2]),pl[0],pl[1])
                    if bType in ('field_value','lxf'):
                        boundStr = str(bound)
                    else:
                        boundStr = str(round(float(bound),tol))
                    if float(bound) > 0.0:
                        faf.write('%d\t%d\t%s%s' % (int(pl[0]),int(pl[1]),boundStr,nl))
                    pl = line.rstrip().split(',')
            else:
                pl = cl
        saf.close()
        faf.close()
        os.remove(tempsortedadjfile)
        self.ui.lbExportAction.setText('')
        if topoErrorCount > 0:
            el.close()
            warningText = '%d possible topological error(s) found. ' % topoErrorCount
            warningText = warningText + \
                'Please check error log in same directory as boundary file.'
            QtGui.QMessageBox.warning(self, self.tr("Export Error"), 
                        self.tr(warningText))
            
