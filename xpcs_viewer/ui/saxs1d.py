# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'saxs1d.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1199, 845)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.mp_saxs = MplCanvas(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mp_saxs.sizePolicy().hasHeightForWidth())
        self.mp_saxs.setSizePolicy(sizePolicy)
        self.mp_saxs.setMinimumSize(QtCore.QSize(600, 0))
        self.mp_saxs.setMaximumSize(QtCore.QSize(16777215, 600))
        self.mp_saxs.setObjectName("mp_saxs")
        self.gridLayout.addWidget(self.mp_saxs, 0, 0, 1, 1)
        self.groupBox_6 = QtWidgets.QGroupBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy)
        self.groupBox_6.setObjectName("groupBox_6")
        self.gridLayout_16 = QtWidgets.QGridLayout(self.groupBox_6)
        self.gridLayout_16.setObjectName("gridLayout_16")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_16.addItem(spacerItem, 0, 0, 1, 1)
        self.gridLayout_24 = QtWidgets.QGridLayout()
        self.gridLayout_24.setObjectName("gridLayout_24")
        self.label_21 = QtWidgets.QLabel(self.groupBox_6)
        self.label_21.setObjectName("label_21")
        self.gridLayout_24.addWidget(self.label_21, 0, 0, 1, 1)
        self.pa_type = QtWidgets.QComboBox(self.groupBox_6)
        self.pa_type.setObjectName("pa_type")
        self.pa_type.addItem("")
        self.pa_type.addItem("")
        self.pa_type.addItem("")
        self.pa_type.addItem("")
        self.gridLayout_24.addWidget(self.pa_type, 0, 1, 1, 1)
        self.label_22 = QtWidgets.QLabel(self.groupBox_6)
        self.label_22.setObjectName("label_22")
        self.gridLayout_24.addWidget(self.label_22, 0, 2, 1, 1)
        self.pa_offset = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.pa_offset.setDecimals(4)
        self.pa_offset.setSingleStep(0.05)
        self.pa_offset.setProperty("value", 0.0)
        self.pa_offset.setObjectName("pa_offset")
        self.gridLayout_24.addWidget(self.pa_offset, 0, 3, 1, 1)
        self.label_23 = QtWidgets.QLabel(self.groupBox_6)
        self.label_23.setObjectName("label_23")
        self.gridLayout_24.addWidget(self.label_23, 0, 4, 1, 1)
        self.pa_norm = QtWidgets.QComboBox(self.groupBox_6)
        self.pa_norm.setObjectName("pa_norm")
        self.pa_norm.addItem("")
        self.pa_norm.addItem("")
        self.pa_norm.addItem("")
        self.pa_norm.addItem("")
        self.gridLayout_24.addWidget(self.pa_norm, 0, 5, 1, 1)
        self.pushButton_10 = QtWidgets.QPushButton(self.groupBox_6)
        self.pushButton_10.setObjectName("pushButton_10")
        self.gridLayout_24.addWidget(self.pushButton_10, 1, 0, 1, 6)
        self.gridLayout_16.addLayout(self.gridLayout_24, 0, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_16.addItem(spacerItem1, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.groupBox_6, 1, 0, 1, 1)

        self.retranslateUi(Form)
        self.pa_type.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_6.setTitle(_translate("Form", "SAXS 1D Plot Setting"))
        self.label_21.setText(_translate("Form", "type:"))
        self.pa_type.setItemText(0, _translate("Form", "I - q"))
        self.pa_type.setItemText(1, _translate("Form", "I - log(q)"))
        self.pa_type.setItemText(2, _translate("Form", "log(I) - q"))
        self.pa_type.setItemText(3, _translate("Form", "log(I) - log(q)"))
        self.label_22.setText(_translate("Form", "offset:"))
        self.label_23.setText(_translate("Form", "normalization:"))
        self.pa_norm.setItemText(0, _translate("Form", "none"))
        self.pa_norm.setItemText(1, _translate("Form", "I\' = Iq2"))
        self.pa_norm.setItemText(2, _translate("Form", "I\' = Iq4"))
        self.pa_norm.setItemText(3, _translate("Form", "I\' = I/Io"))
        self.pushButton_10.setText(_translate("Form", "Plot 1D SAXS"))

from matplot_qt import MplCanvas

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

