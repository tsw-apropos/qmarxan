# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_qm_import.ui'
#
# Created: Tue Sep  3 19:20:47 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_qm_import(object):
    def setupUi(self, qm_import):
        qm_import.setObjectName(_fromUtf8("qm_import"))
        qm_import.resize(465, 398)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/qm_import.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        qm_import.setWindowIcon(icon)
        self.verticalLayoutWidget = QtGui.QWidget(qm_import)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 441, 371))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblPlanningGrid = QtGui.QLabel(self.verticalLayoutWidget)
        self.lblPlanningGrid.setObjectName(_fromUtf8("lblPlanningGrid"))
        self.verticalLayout.addWidget(self.lblPlanningGrid)
        self.cbxPlanningGrid = QtGui.QComboBox(self.verticalLayoutWidget)
        self.cbxPlanningGrid.setObjectName(_fromUtf8("cbxPlanningGrid"))
        self.verticalLayout.addWidget(self.cbxPlanningGrid)
        self.lbIdField = QtGui.QLabel(self.verticalLayoutWidget)
        self.lbIdField.setObjectName(_fromUtf8("lbIdField"))
        self.verticalLayout.addWidget(self.lbIdField)
        self.cbxIdField = QtGui.QComboBox(self.verticalLayoutWidget)
        self.cbxIdField.setObjectName(_fromUtf8("cbxIdField"))
        self.verticalLayout.addWidget(self.cbxIdField)
        self.lblInputFile = QtGui.QLabel(self.verticalLayoutWidget)
        self.lblInputFile.setObjectName(_fromUtf8("lblInputFile"))
        self.verticalLayout.addWidget(self.lblInputFile)
        self.vlMeasureLayer = QtGui.QVBoxLayout()
        self.vlMeasureLayer.setObjectName(_fromUtf8("vlMeasureLayer"))
        self._2 = QtGui.QHBoxLayout()
        self._2.setObjectName(_fromUtf8("_2"))
        self.leInputFile = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.leInputFile.setReadOnly(False)
        self.leInputFile.setObjectName(_fromUtf8("leInputFile"))
        self._2.addWidget(self.leInputFile)
        self.pbInputFile = QtGui.QToolButton(self.verticalLayoutWidget)
        self.pbInputFile.setObjectName(_fromUtf8("pbInputFile"))
        self._2.addWidget(self.pbInputFile)
        self.vlMeasureLayer.addLayout(self._2)
        self.verticalLayout.addLayout(self.vlMeasureLayer)
        self.vlOutput = QtGui.QVBoxLayout()
        self.vlOutput.setObjectName(_fromUtf8("vlOutput"))
        self.lblSelectField = QtGui.QLabel(self.verticalLayoutWidget)
        self.lblSelectField.setObjectName(_fromUtf8("lblSelectField"))
        self.vlOutput.addWidget(self.lblSelectField)
        self.cbxSelectField = QtGui.QComboBox(self.verticalLayoutWidget)
        self.cbxSelectField.setObjectName(_fromUtf8("cbxSelectField"))
        self.vlOutput.addWidget(self.cbxSelectField)
        self.lblNewField = QtGui.QLabel(self.verticalLayoutWidget)
        self.lblNewField.setEnabled(False)
        self.lblNewField.setObjectName(_fromUtf8("lblNewField"))
        self.vlOutput.addWidget(self.lblNewField)
        self.leNewResultsField = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.leNewResultsField.setEnabled(False)
        self.leNewResultsField.setMaxLength(10)
        self.leNewResultsField.setReadOnly(False)
        self.leNewResultsField.setObjectName(_fromUtf8("leNewResultsField"))
        self.vlOutput.addWidget(self.leNewResultsField)
        self.verticalLayout.addLayout(self.vlOutput)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.progressBar = QtGui.QProgressBar(self.verticalLayoutWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.horizontalLayout.addWidget(self.progressBar)
        self.buttonBox = QtGui.QDialogButtonBox(self.verticalLayoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(qm_import)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), qm_import.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), qm_import.accept)
        QtCore.QMetaObject.connectSlotsByName(qm_import)

    def retranslateUi(self, qm_import):
        qm_import.setWindowTitle(QtGui.QApplication.translate("qm_import", "Import Marxan Results", None, QtGui.QApplication.UnicodeUTF8))
        self.lblPlanningGrid.setText(QtGui.QApplication.translate("qm_import", "Planning Grid", None, QtGui.QApplication.UnicodeUTF8))
        self.lbIdField.setText(QtGui.QApplication.translate("qm_import", "Planning Unit Id Field", None, QtGui.QApplication.UnicodeUTF8))
        self.lblInputFile.setText(QtGui.QApplication.translate("qm_import", "Select Marxan Results File To Import", None, QtGui.QApplication.UnicodeUTF8))
        self.pbInputFile.setText(QtGui.QApplication.translate("qm_import", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.lblSelectField.setText(QtGui.QApplication.translate("qm_import", "Select Results Field Name", None, QtGui.QApplication.UnicodeUTF8))
        self.lblNewField.setText(QtGui.QApplication.translate("qm_import", "Enter New Results Field Name", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
