# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_qm_about.ui'
#
# Created: Mon Mar 12 16:01:29 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_qm_about(object):
    def setupUi(self, qm_about):
        qm_about.setObjectName(_fromUtf8("qm_about"))
        qm_about.resize(537, 364)
        qm_about.setWindowTitle(QtGui.QApplication.translate("qm_about", "About Qmarxan", None, QtGui.QApplication.UnicodeUTF8))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/qm_icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        qm_about.setWindowIcon(icon)
        self.layoutWidget = QtGui.QWidget(qm_about)
        self.layoutWidget.setGeometry(QtCore.QRect(20, 19, 501, 331))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_2 = QtGui.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setText(QtGui.QApplication.translate("qm_about", "Qmarxan ", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.lblVersion = QtGui.QLabel(self.layoutWidget)
        self.lblVersion.setText(QtGui.QApplication.translate("qm_about", "Version x.x", None, QtGui.QApplication.UnicodeUTF8))
        self.lblVersion.setAlignment(QtCore.Qt.AlignCenter)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.verticalLayout.addWidget(self.lblVersion)
        self.textBrowser = QtGui.QTextBrowser(self.layoutWidget)
        self.textBrowser.setHtml(QtGui.QApplication.translate("qm_about", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Qmarxan allows QGIS users to create Marxan input files and display Marxan results. Qmarxan was created by Apropos Information Systems Inc. For help information about Qmarxan please go to:</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">http://www.aproposinfosystems.com/products/qmarxan/</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Marxan is freely available conservation planning software. For more information please visit:</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">http://www.uq.edu.au/marxan</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        self.buttonBox = QtGui.QDialogButtonBox(self.layoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(qm_about)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), qm_about.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), qm_about.reject)
        QtCore.QMetaObject.connectSlotsByName(qm_about)

    def retranslateUi(self, qm_about):
        pass

import resources_rc
