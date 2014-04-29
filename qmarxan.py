"""
/***************************************************************************
 Qmarxan
                                 A QGIS plugin
Create grid, calculate grid values, export Marxan input layers, import results                              
                             ----------------------
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Initialize Qt resources from file resources_rc.py
import resources_rc

# Import the code for the dialog
from qm_about import qmAbout
from qm_mkgrid import qmMkGrid
from qm_calc import qmCalc
from qm_export import qmExport
from qm_import import qmImport
from qm_input import qmInput

class Qmarxan:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
    
    def initGui(self):
    
        # MkGrid
        # define
        self.show_mkgrid = QAction(QIcon(":/icons/qm_mkgrid.png"),\
            "Create Planning Grid", self.iface.mainWindow())
        # hint
        self.show_mkgrid.setWhatsThis("Tool to create your planning grid")
        # connect 
        QObject.connect(self.show_mkgrid, SIGNAL("triggered()"), self.mkgrid)
    
        # Calc
        # define
        self.show_calc = QAction(QIcon(":/icons/qm_calc.png"),\
            "Calculate Conservation Values", self.iface.mainWindow())
        # hint
        self.show_calc.setWhatsThis("Tool to measure factors to be conserved")
        # connect
        QObject.connect(self.show_calc, SIGNAL("triggered()"), self.calc)
        
        # Export
        self.show_export = QAction(QIcon(":/icons/qm_export.png"),\
            "Export to Marxan", self.iface.mainWindow())
        # hint
        self.show_export.setWhatsThis("Tool to create Marxan input files")
        # connect
        QObject.connect(self.show_export, SIGNAL("triggered()"), self.export)
        
        # Import
        self.show_import = QAction(QIcon(":/icons/qm_import.png"),\
            "Import Marxan Results", self.iface.mainWindow())
        # hint
        self.show_import.setWhatsThis("Tool to import Marxan results")
        # connect
        QObject.connect(self.show_import, SIGNAL("triggered()"), self.results_import)
        
        # Input
        self.show_input = QAction(QIcon(":/icons/qm_icon.png"),\
            "Configure Scenario", self.iface.mainWindow())
        # hint
        self.show_input.setWhatsThis("Edit / create input.dat file")
        # connect
        QObject.connect(self.show_input, SIGNAL("triggered()"), self.configure)

        # About
        self.show_about = QAction(QIcon(":/icons/qm_icon.png"), \
            "About Qmarxan", self.iface.mainWindow())
        self.show_about.setWhatsThis("Description of Qmarxan")
        # connect the action to the about method
        QObject.connect(self.show_about, SIGNAL("triggered()"), self.about)

        self.iface.addPluginToMenu("Qmar&xan", self.show_mkgrid)
        self.iface.addPluginToMenu("Qmar&xan", self.show_calc)
        self.iface.addPluginToMenu("Qmar&xan", self.show_export)
        self.iface.addPluginToMenu("Qmar&xan", self.show_import)
        self.iface.addPluginToMenu("Qmar&xan", self.show_input)
        self.iface.addPluginToMenu("Qmar&xan", self.show_about)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("Qmar&xan", self.show_mkgrid)
        self.iface.removePluginMenu("Qmar&xan", self.show_calc)
        self.iface.removePluginMenu("Qmar&xan", self.show_export)
        self.iface.removePluginMenu("Qmar&xan", self.show_import)
        self.iface.removePluginMenu("Qmar&xan", self.show_input)
        self.iface.removePluginMenu("Qmar&xan", self.show_about)

    # about method that opens the mkgrid dialog
    def mkgrid(self):

        # create and show the dialog
        dlg = qmMkGrid(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

    # about method that opens the calc dialog
    def calc(self):

        # create and show the dialog
        dlg = qmCalc(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

    # about method that opens the export dialog
    def export(self):

        # create and show the dialog
        dlg = qmExport(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

    # about method that opens the import dialog
    def results_import(self):

        # create and show the dialog
        dlg = qmImport(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

    # about method that opens the configure dialog
    def configure(self):

        # create and show the dialog
        dlg = qmInput(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

    # about method that opens the about dialog
    def about(self):

        # create and show the dialog
        dlg = qmAbout(self.iface)
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass

