"""
/***************************************************************************
 qmInput - create and edit Marxan input.dat file
                             -------------------
        begin                : 2011-12-13
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
from ui_qm_input import Ui_qm_input
import sys, os, csv, math, string

commandlist = ['VERSION','BLM','PROP','NUMITNS','STARTTEMP','COOLFAC','NUMTEMP', \
    'RANDSEED','BESTSCORE','COSTTHRESH','THRESHPEN1','THRESHPEN2','NUMREPS',\
    'SAVERUN','SAVEBEST','SAVESUM','SAVESCEN','SAVETARGMET','SAVESUMSOLN',\
    'SAVELOG','SAVESNAPSTEPS','SAVESNAPFREQUENCY','SCENNAME','INPUTDIR','OUTPUTDIR',\
    'SPECNAME','PUNAME','PUVSPRNAME','BOUNDNAME','BLOCKDEFNAME','MATRIXSPORDERNAME',\
    'RUNMODE','CLUMPTYPE','MISSLEVEL','ITIMPTYPE','HEURTYPE','VERBOSITY',\
    'SAVESUMMARY','SAVESNAPCHANGES','SAVESOLUTIONSMATRIX']
    
class qmInput(QtGui.QDialog):
    def __init__(self, iface):
        self.iface = iface
        self.progress = 0
        self.step = 0
        self.scenarioDir = "."
        self.inputDir = "input"
        self.outputDir = "ouput"

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
        self.ui = Ui_qm_input()
        self.ui.setupUi(self)
        self.setFixedSize(653,674)
        self.setWindowTitle(self.tr("Configure Scenario (input.dat)"))
        self.ui.buttonOk = self.ui.buttonBox.button( QtGui.QDialogButtonBox.Ok )
        self.setModeOptions()
        # enable selection of output directory
        QtCore.QObject.connect(self.ui.pbScenarioDirectory, QtCore.SIGNAL("clicked()"), self.setScenarioDir)
        # enable input and output dir buttons
        QtCore.QObject.connect(self.ui.pbINPUTDIR, QtCore.SIGNAL("clicked()"), self.setInputDir)
        QtCore.QObject.connect(self.ui.pbOUTPUTDIR, QtCore.SIGNAL("clicked()"), self.setOutputDir)
        # enable input file buttons
        QtCore.QObject.connect(self.ui.pbSPECNAME, QtCore.SIGNAL("clicked()"), self.setSpecName)
        QtCore.QObject.connect(self.ui.pbPUNAME, QtCore.SIGNAL("clicked()"), self.setPUName)
        QtCore.QObject.connect(self.ui.pbBOUNDNAME, QtCore.SIGNAL("clicked()"), self.setBoundName)
        QtCore.QObject.connect(self.ui.pbPUVSPRNAME, QtCore.SIGNAL("clicked()"), self.setPUvSPRName)
        QtCore.QObject.connect(self.ui.pbBLOCKDEFNAME, QtCore.SIGNAL("clicked()"), self.setBlockDefName)
        QtCore.QObject.connect(self.ui.pbMATRIXSPORDERNAME, QtCore.SIGNAL("clicked()"), self.setMatrixSpOrderName)
        # enable the enabling and disabling of heuristic and iterative improvement
        # combo boxes 
        QtCore.QObject.connect(self.ui.cbxRUNMODE, QtCore.SIGNAL("currentIndexChanged(QString)"), self.setModeOptions)
        
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
    # setModeOptions - control enabling and disabling of heuristic type
    #                  and iterative improvement combo boxes
    #

    def setModeOptions(self):
        rmidx = self.ui.cbxRUNMODE.currentIndex()
        if rmidx == 0 or rmidx == 7:
            self.ui.lblHEURTYPE.setDisabled(True)
            self.ui.cbxHEURTYPE.setDisabled(True)
            self.ui.lblITIMPTYPE.setDisabled(True)
            self.ui.cbxITIMPTYPE.setDisabled(True)
        elif rmidx == 1 or rmidx == 4:
            self.ui.lblHEURTYPE.setEnabled(True)
            self.ui.cbxHEURTYPE.setEnabled(True)
            self.ui.lblITIMPTYPE.setDisabled(True)
            self.ui.cbxITIMPTYPE.setDisabled(True)
        elif rmidx == 2 or rmidx == 5:
            self.ui.lblHEURTYPE.setDisabled(True)
            self.ui.cbxHEURTYPE.setDisabled(True)
            self.ui.lblITIMPTYPE.setEnabled(True)
            self.ui.cbxITIMPTYPE.setEnabled(True)
        elif rmidx == 3 or rmidx == 6:
            self.ui.lblHEURTYPE.setEnabled(True)
            self.ui.cbxHEURTYPE.setEnabled(True)
            self.ui.lblITIMPTYPE.setEnabled(True)
            self.ui.cbxITIMPTYPE.setEnabled(True)
        else:
            QtGui.QMessageBox.information(self, self.tr("DEBUG"), 
                        self.tr('cbxRUNMODE.currentIndex() == %d' % rmidx))
            
    #
    # setScenarioDir - provide linkage between browse button and text box
    #                  and read input.dat if file found
    #

    def setScenarioDir(self):
        temp = QtGui.QFileDialog.getExistingDirectory( self,
            self.tr( "Select directory to write Marxan input.dat file" ), self.scenarioDir)
        if temp != "":
            self.scenarioDir = str(temp)
            self.ui.leScenarioDirectory.setText(str(temp))
            self.readInputFile()
    #
    # setInputDir - provide linkage between browse button and text box
    #

    def setInputDir(self):
        temp = QtGui.QFileDialog.getExistingDirectory( self,
            self.tr( "Select directory for Marxan input files" ), self.scenarioDir)
        if temp != "":
            self.inputDir = os.path.basename(str(temp))
            self.ui.leINPUTDIR.setText(self.inputDir)
            inList = os.listdir(temp)
            for fN in inList:
                if 'spec.dat' == fN:
                    self.ui.leSPECNAME.setText(fN)
                if 'pu.dat' == fN:
                    self.ui.lePUNAME.setText(fN)
                if 'puvspr.dat' == fN:
                    self.ui.lePUVSPRNAME.setText(fN)
                if 'puvspr_sporder.dat' == fN:
                    self.ui.leMATRIXSPORDERNAME.setText(fN)
                if 'bound.dat' == fN:
                    self.ui.leBOUNDNAME.setText(fN)
        

    #
    # setOutputDir - provide linkage between browse button and text box
    #

    def setOutputDir(self):
        temp = QtGui.QFileDialog.getExistingDirectory( self,
            self.tr( "Select directory for Marxan output files" ), self.scenarioDir)
        if temp != "":
            self.ouputDir = os.path.basename(str(temp))
            self.ui.leOUTPUTDIR.setText(self.ouputDir)

    #
    # setSpecName - provide linkage between browse button and text box
    #

    def setSpecName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan species file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.leSPECNAME.setText(temp)

    #
    # setPUName - provide linkage between browse button and text box
    #

    def setPUName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan planning unit file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.lePUNAME.setText(temp)

    #
    # setBoundName - provide linkage between browse button and text box
    #

    def setBoundName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan boundary file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.leBOUNDNAME.setText(temp)

    #
    # setPUvSPRName - provide linkage between browse button and text box
    #

    def setPUvSPRName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan pu vs species file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.lePUVSPRNAME.setText(temp)

    #
    # setBlockDefName - provide linkage between browse button and text box
    #

    def setBlockDefName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan species group file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.leBLOCKDEFNAME.setText(temp)
    #
    # setMatrixSpOrderName - provide linkage between browse button and text box
    #

    def setMatrixSpOrderName(self):
        temp = QtGui.QFileDialog.getOpenFileName( self,
            self.tr( "Select Marxan species ordered pu vs species file" ), self.scenarioDir,
            "*.dat" )
        if temp != "":
            temp = os.path.basename(str(temp))
            self.ui.leMATRIXSPORDERNAME.setText(temp)
    
    #
    # readInputFile - attempts to read input.dat file
    #

    def readInputFile(self):
        global commandlist
        fname = os.path.join(self.scenarioDir, 'input.dat')
        if not os.path.isfile(fname):
            return()
        nl = os.linesep
        tmpf = file(fname, 'rb')
        for line in tmpf:
            temp = line.replace('  ',' ')
            temp = temp.replace('\t',' ')
            lc = temp.split(' ')
            if len(lc) > 1 and lc[0] in commandlist:
                # GENERAL TAB
                if lc[0] == 'VERSION':
                    self.ui.leVERSION.setText(lc[1])
                if lc[0] == 'BLM':
                    self.ui.spnBLM.setValue(float(lc[1]))
                if lc[0] == 'MISSLEVEL':
                    self.ui.spnMISSLEVEL.setValue(float(lc[1]))
                if lc[0] == 'PROP':
                    self.ui.spnPROP.setValue(float(lc[1]))
                if lc[0] == 'NUMREPS':
                    self.ui.spnNUMREPS.setValue(float(lc[1]))
                if lc[0] == 'CLUMPTYPE':
                    temp = int(lc[1])
                    if temp <= 2:
                        self.ui.cbxCLUMPTYPE.setCurrentIndex(temp)
                    else:
                        self.ui.cbxCLUMPTYPE.setCurrentIndex(0)
                if lc[0] == 'RANDSEED':
                    self.ui.spnRANDSEED.setValue(float(lc[1]))
                if lc[0] == 'BESTSCORE':
                    self.ui.spnBESTSCORE.setValue(float(lc[1]))
                # RUN AND ANNEALING TAB 
                if lc[0] == 'NUMITNS':
                    self.ui.spnNUMITNS.setValue(float(lc[1]))
                if lc[0] == 'NUMTEMP':
                    self.ui.spnNUMTEMP.setValue(float(lc[1]))
                if lc[0] == 'RUNMODE':
                    # note addition of 1 because this one starts at -1
                    temp = int(lc[1]) + 1
                    if temp <= 7: 
                        self.ui.cbxRUNMODE.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxRUNMODE.setCurrentIndex(2)
                if lc[0] == 'HEURTYPE':
                    temp = int(lc[1])
                    if temp <= 7:
                        self.ui.cbxHEURTYPE.setCurrentIndex(temp)
                    else:
                        self.ui.cbxHEURTYPE.setCurrentIndex(0)
                if lc[0] == 'ITIMPTYPE':
                    temp = int(lc[1])
                    if temp <= 3:
                        self.ui.cbxITIMPTYPE.setCurrentIndex(temp)
                    else:
                        self.ui.cbxITIMPTYPE.setCurrentIndex(0)
                if lc[0] == 'STARTTEMP':
                    self.ui.spnSTARTTEMP.setValue(float(lc[1]))
                if lc[0] == 'COOLFAC':
                    self.ui.spnCOOLFAC.setValue(float(lc[1]))
                if lc[0] == 'VERBOSITY':
                    temp = int(lc[1])
                    if temp <= 3:
                        self.ui.cbxVERBOSITY.setCurrentIndex(temp)
                    else:
                        self.ui.cbxVERBOSITY.setCurrentIndex(0)
                # FILES AND COSTS TAB
                if lc[0] == 'INPUTDIR':
                    self.ui.leINPUTDIR.setText(lc[1])
                if lc[0] == 'OUTPUTDIR':
                    self.ui.leOUTPUTDIR.setText(lc[1])
                if lc[0] == 'SPECNAME':
                    self.ui.leSPECNAME.setText(lc[1])
                if lc[0] == 'PUNAME':
                    self.ui.lePUNAME.setText(lc[1])
                if lc[0] == 'BOUNDNAME':
                    self.ui.leBOUNDNAME.setText(lc[1])
                if lc[0] == 'PUVSPRNAME':
                    self.ui.lePUVSPRNAME.setText(lc[1])
                if lc[0] == 'BLOCKDEFNAME':
                    self.ui.leBLOCKDEFNAME.setText(lc[1])
                if lc[0] == 'MATRIXSPORDERNAME':
                    self.ui.leMATRIXSPORDERNAME.setText(lc[1])
                if lc[0] == 'COSTTHRESH':
                    self.ui.spnCOSTTHRESH.setValue(float(lc[1]))
                if lc[0] == 'THRESHPEN1':
                    self.ui.spnTHRESHPEN1.setValue(float(lc[1]))
                if lc[0] == 'THRESHPEN2':
                    self.ui.spnTHRESHPEN2.setValue(float(lc[1]))
                # MARXAN OUTPUT TAB   
                if lc[0] == 'SCENNAME':
                    self.ui.leSCENNAME.setText(lc[1])
                if lc[0] == 'SAVESCEN':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVESCEN.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVESCEN.setCurrentIndex(2)
                if lc[0] == 'SAVESUM' or lc[0] == 'SAVESUMMARY':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVESUM.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVESUM.setCurrentIndex(2)
                if lc[0] == 'SAVERUN':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVERUN.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVERUN.setCurrentIndex(2)
                if lc[0] == 'SAVEBEST':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVEBEST.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVEBEST.setCurrentIndex(2)
                if lc[0] == 'SAVESUMSOLN':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVESUMSOLN.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVESUMSOLN.setCurrentIndex(2)
                if lc[0] == 'SAVETARGMET':
                    temp = int(lc[1])
                    if temp <= 2: 
                        self.ui.cbxSAVETARGMET.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVETARGMET.setCurrentIndex(2)
                if lc[0] == 'SAVELOG':
                    temp = int(lc[1])
                    if temp <= 1: 
                        self.ui.cbxSAVELOG.setCurrentIndex(temp)
                    elif temp == 0:
                        self.ui.cbxSAVELOG.setCurrentIndex(2)
                if lc[0] == 'SAVESNAPSTEPS':
                    self.ui.spnSAVESNAPSTEPS.setValue(float(lc[1]))
                if lc[0] == 'SAVESNAPCHANGES':
                    self.ui.spnSAVESNAPCHANGES.setValue(float(lc[1]))
                if lc[0] == 'SAVESNAPFREQUENCY':
                    self.ui.spnSAVESNAPFREQUENCY.setValue(float(lc[1]))
                if lc[0] == 'SAVESOLUTIONSMATRIX':
                    temp = int(lc[1])
                    if temp <= 3:
                        self.ui.cbxSAVESOLUTIONSMATRIX.setCurrentIndex(temp)
                    else:
                        self.ui.cbxSAVESOLUTIONSMATRIX.setCurrentIndex(0)
                
        tmpf.close()
        
    #
    # accept - links clicking OK to writing file
    #

    def accept(self):
        self.writeInputFile()
        
        
    #
    # writeInputFile - write input.dat in the selected directory
    #        

    def writeInputFile(self):
        
        #
        # stripCR - strip newline characters from line edit text
        #
        def stripCR(inStr):
            outStr = string.replace(inStr,'\r','')
            outStr = string.replace(outStr,'\n','')
            return(outStr)
        
        #
        # formatAsME - format as Marxan Exponent format like 
        #              Input File Editor
        #
        def formatAsME(inVal):
            outStr = "%.14E" % inVal
            parts = outStr.split('E')
            sign = parts[1][:1]
            exponent = "%04d" % float(parts[1][1:])
            outStr = parts[0] + 'E' +  sign + exponent
            return(outStr)
            
        # disable OK button
        self.ui.buttonOk.setDisabled(True)
        # get file name
        fname = os.path.join(self.scenarioDir, 'input.dat')
        nl = os.linesep
        tmpf = file(fname, 'w')
        credits = "Input file for Annealing program.%s%s" % (nl,nl)
        credits = credits + "This file generated by Qmarxan%s" % nl
        credits = credits + "created by Apropos Information Systems Inc.%s%s" % (nl,nl)
        tmpf.write(credits)
        self.progressStatus('update',15)
        tmpf.write("General Parameters%s" % nl)
        tmpf.write("VERSION %s%s" % (stripCR(self.ui.leVERSION.text()),nl))
        tmpf.write("BLM %s%s" % (formatAsME(self.ui.spnBLM.value()),nl))
        tmpf.write("PROP %s%s" % (formatAsME(self.ui.spnPROP.value()),nl))
        tmpf.write("RANDSEED %d%s" % (self.ui.spnRANDSEED.value(),nl))
        tmpf.write("BESTSCORE %s%s" % (formatAsME(self.ui.spnBESTSCORE.value()),nl))
        tmpf.write("NUMREPS %d%s" % (self.ui.spnNUMREPS.value(),nl))
        self.progressStatus('update',30)
        tmpf.write("%sAnnealing Parameters%s" % (nl,nl))
        tmpf.write("NUMITNS %d%s" % (self.ui.spnNUMITNS.value(),nl))
        tmpf.write("STARTTEMP %s%s" % (formatAsME(self.ui.spnSTARTTEMP.value()),nl))
        tmpf.write("COOLFAC %s%s" % (formatAsME(self.ui.spnCOOLFAC.value()),nl))
        tmpf.write("NUMTEMP %d%s" % (self.ui.spnNUMTEMP.value(),nl))
        self.progressStatus('update',45)
        tmpf.write("%sCost Threshold%s" % (nl,nl))
        tmpf.write("COSTTHRESH %s%s" % (formatAsME(self.ui.spnCOSTTHRESH.value()),nl))
        tmpf.write("THRESHPEN1 %s%s" % (formatAsME(self.ui.spnTHRESHPEN1.value()),nl))
        tmpf.write("THRESHPEN2 %s%s" % (formatAsME(self.ui.spnTHRESHPEN2.value()),nl))
        self.progressStatus('update',60)
        tmpf.write("%sInput File%s" % (nl,nl))
        tmpf.write("INPUTDIR %s%s" % (stripCR(self.ui.leINPUTDIR.text()),nl))
        tmpf.write("SPECNAME %s%s" % (stripCR(self.ui.leSPECNAME.text()),nl))
        if self.ui.leBLOCKDEFNAME.text() != "":
            tmpf.write("BLOCKDEFNAME %s%s" % (stripCR(self.ui.leBLOCKDEFNAME.text()),nl))
        tmpf.write("PUNAME %s%s" % (stripCR(self.ui.lePUNAME.text()),nl))
        tmpf.write("PUVSPRNAME %s%s" % (stripCR(self.ui.lePUVSPRNAME.text()),nl))
        if self.ui.leBOUNDNAME.text() != "":
            tmpf.write("BOUNDNAME %s%s" % (stripCR(self.ui.leBOUNDNAME.text()),nl))
        if self.ui.leMATRIXSPORDERNAME.text() != "":
            tmpf.write("MATRIXSPORDERNAME %s%s" % (stripCR(self.ui.leMATRIXSPORDERNAME.text()),nl))
        self.progressStatus('update',75)
        tmpf.write("%sSave Files%s" % (nl,nl))
        tmpf.write("SCENNAME %s%s" % (stripCR(self.ui.leSCENNAME.text()),nl))
        tmpf.write("SAVERUN %d%s" % (self.ui.cbxSAVERUN.currentIndex(),nl))
        tmpf.write("SAVEBEST %d%s" % (self.ui.cbxSAVEBEST.currentIndex(),nl))
        tmpf.write("SAVESUMMARY %d%s" % (self.ui.cbxSAVESUM.currentIndex(),nl))
        tmpf.write("SAVESCEN %d%s" % (self.ui.cbxSAVESCEN.currentIndex(),nl))
        tmpf.write("SAVETARGMET %d%s" % (self.ui.cbxSAVETARGMET.currentIndex(),nl))
        tmpf.write("SAVESUMSOLN %d%s" % (self.ui.cbxSAVESUMSOLN.currentIndex(),nl))
        tmpf.write("SAVELOG %d%s" % (self.ui.cbxSAVELOG.currentIndex(),nl))
        tmpf.write("SAVESNAPSTEPS %d%s" % (self.ui.spnSAVESNAPSTEPS.value(),nl))
        tmpf.write("SAVESNAPCHANGES %d%s" % (self.ui.spnSAVESNAPCHANGES.value(),nl))
        tmpf.write("SAVESNAPFREQUENCY %d%s" % (self.ui.spnSAVESNAPFREQUENCY.value(),nl))
        tmpf.write("OUTPUTDIR %s%s" % (stripCR(self.ui.leOUTPUTDIR.text()),nl))
        self.progressStatus('update',90)
        tmpf.write("%sProgram control.%s" % (nl,nl))
        tmpf.write("RUNMODE %d%s" % (self.ui.cbxRUNMODE.currentIndex()-1,nl))
        tmpf.write("MISSLEVEL %s%s" % (formatAsME(self.ui.spnMISSLEVEL.value()),nl))
        tmpf.write("ITIMPTYPE %d%s" % (self.ui.cbxITIMPTYPE.currentIndex(),nl))
        tmpf.write("HEURTYPE %d%s" % (self.ui.cbxHEURTYPE.currentIndex(),nl))
        tmpf.write("CLUMPTYPE %d%s" % (self.ui.cbxCLUMPTYPE.currentIndex(),nl))
        tmpf.write("VERBOSITY %d%s" % (self.ui.cbxVERBOSITY.currentIndex(),nl))
        tmpf.write("SAVESOLUTIONSMATRIX %d%s" % (self.ui.cbxSAVESOLUTIONSMATRIX.currentIndex(),nl))
        tmpf.write("%s" % nl)
        
        self.progressStatus('update',100)
        tmpf.close()
        QtGui.QMessageBox.information(self, self.tr("Configure Scenario"), 
                        self.tr("input.dat written"))
        # reset progress bar
        self.progressStatus('reset')
        # reset system
        self.ui.buttonOk.setEnabled(True)
    
