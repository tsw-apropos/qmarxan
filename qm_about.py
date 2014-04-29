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
from ui_qm_about import Ui_qm_about

# create the dialog for zoom to point
class qmAbout(QtGui.QDialog):
    def __init__(self, iface):
        self.iface = iface
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_qm_about()
        self.ui.setupUi(self)
        self.setFixedSize(537,364)
        self.ui.lblVersion.setText("Version 1.4.0")

