# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'reportviewer.ui'
#
# Created: Sat Dec  6 23:21:02 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_ReportViewer(object):
    def setupUi(self, ReportViewer):
        ReportViewer.setObjectName(_fromUtf8("ReportViewer"))
        ReportViewer.resize(1024, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ReportViewer.sizePolicy().hasHeightForWidth())
        ReportViewer.setSizePolicy(sizePolicy)
        ReportViewer.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.centralwidget = QtWidgets.QWidget(ReportViewer)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.fileopen = QtWidgets.QPushButton(self.centralwidget)
        self.fileopen.setObjectName(_fromUtf8("fileopen"))
        self.horizontalLayout.addWidget(self.fileopen)
        self.excel = QtWidgets.QPushButton(self.centralwidget)
        self.excel.setObjectName(_fromUtf8("excel"))
        self.horizontalLayout.addWidget(self.excel)
        self.printer = QtWidgets.QPushButton(self.centralwidget)
        self.printer.setObjectName(_fromUtf8("printer"))
        self.horizontalLayout.addWidget(self.printer)
        self.email = QtWidgets.QPushButton(self.centralwidget)
        self.email.setObjectName(_fromUtf8("email"))
        self.horizontalLayout.addWidget(self.email)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        ReportViewer.setCentralWidget(self.centralwidget)

        self.retranslateUi(ReportViewer)
        QtCore.QMetaObject.connectSlotsByName(ReportViewer)

    def retranslateUi(self, ReportViewer):
        ReportViewer.setWindowTitle(_translate("ReportViewer", "ReportViewer", None))
        self.fileopen.setText(_translate("ReportViewer", "Открыть", None))
        self.excel.setText(_translate("ReportViewer", "Excel", None))
        self.printer.setText(_translate("ReportViewer", "Печать", None))
        self.email.setText(_translate("ReportViewer", "E-Mail", None))

