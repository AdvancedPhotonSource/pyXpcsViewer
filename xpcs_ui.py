# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'xpcs.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        mainwindow.setObjectName("mainwindow")
        mainwindow.resize(1920, 980)
        mainwindow.setMinimumSize(QtCore.QSize(1024, 800))
        self.centralwidget = QtWidgets.QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.file_panel = QtWidgets.QFrame(self.centralwidget)
        self.file_panel.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.file_panel.setFrameShadow(QtWidgets.QFrame.Raised)
        self.file_panel.setObjectName("file_panel")
        self.gridLayout = QtWidgets.QGridLayout(self.file_panel)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.file_panel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QtCore.QSize(1280, 0))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.graphWidget = ImageView(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(120)
        sizePolicy.setVerticalStretch(120)
        sizePolicy.setHeightForWidth(self.graphWidget.sizePolicy().hasHeightForWidth())
        self.graphWidget.setSizePolicy(sizePolicy)
        self.graphWidget.setObjectName("graphWidget")
        self.gridLayout_3.addWidget(self.graphWidget, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.f0 = PlotWidget(self.tab_2)
        self.f0.setObjectName("f0")
        self.horizontalLayout_4.addWidget(self.f0)
        self.f1 = PlotWidget(self.tab_2)
        self.f1.setObjectName("f1")
        self.horizontalLayout_4.addWidget(self.f1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.f2 = PlotWidget(self.tab_2)
        self.f2.setObjectName("f2")
        self.horizontalLayout_3.addWidget(self.f2)
        self.f3 = PlotWidget(self.tab_2)
        self.f3.setObjectName("f3")
        self.horizontalLayout_3.addWidget(self.f3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.gridLayout_6.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.mf1 = MplCanvas(self.tab_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mf1.sizePolicy().hasHeightForWidth())
        self.mf1.setSizePolicy(sizePolicy)
        self.mf1.setObjectName("mf1")
        self.gridLayout_7.addWidget(self.mf1, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName("widget")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.scrollArea = QtWidgets.QScrollArea(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QtCore.QSize(0, 800))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1232, 1624))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.mf2 = MplCanvas(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mf2.sizePolicy().hasHeightForWidth())
        self.mf2.setSizePolicy(sizePolicy)
        self.mf2.setMinimumSize(QtCore.QSize(0, 1600))
        self.mf2.setObjectName("mf2")
        self.gridLayout_9.addWidget(self.mf2, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_8.addWidget(self.scrollArea, 0, 0, 1, 1)
        self.tabWidget.addTab(self.widget, "")
        self.gridLayout.addWidget(self.tabWidget, 2, 1, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.file_panel)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.work_dir = QtWidgets.QLineEdit(self.file_panel)
        self.work_dir.setObjectName("work_dir")
        self.horizontalLayout_2.addWidget(self.work_dir)
        self.pushButton = QtWidgets.QPushButton(self.file_panel)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.box_source = QtWidgets.QGroupBox(self.file_panel)
        self.box_source.setMinimumSize(QtCore.QSize(0, 80))
        self.box_source.setObjectName("box_source")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.box_source)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.list_view_source = QtWidgets.QListWidget(self.box_source)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_view_source.sizePolicy().hasHeightForWidth())
        self.list_view_source.setSizePolicy(sizePolicy)
        self.list_view_source.setMinimumSize(QtCore.QSize(0, 120))
        self.list_view_source.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.list_view_source.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.list_view_source.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.list_view_source.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.list_view_source.setObjectName("list_view_source")
        self.gridLayout_5.addWidget(self.list_view_source, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.box_source)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.file_panel)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.filter_str = QtWidgets.QLineEdit(self.file_panel)
        self.filter_str.setMaximumSize(QtCore.QSize(16777215, 100))
        self.filter_str.setObjectName("filter_str")
        self.horizontalLayout.addWidget(self.filter_str)
        self.pushButton_2 = QtWidgets.QPushButton(self.file_panel)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.file_panel)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout.addWidget(self.pushButton_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.box_target = QtWidgets.QGroupBox(self.file_panel)
        self.box_target.setMinimumSize(QtCore.QSize(0, 120))
        self.box_target.setObjectName("box_target")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.box_target)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.list_view_target = QtWidgets.QListWidget(self.box_target)
        self.list_view_target.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.list_view_target.setObjectName("list_view_target")
        self.gridLayout_4.addWidget(self.list_view_target, 0, 0, 1, 1)
        self.btn_load_data = QtWidgets.QPushButton(self.box_target)
        self.btn_load_data.setObjectName("btn_load_data")
        self.gridLayout_4.addWidget(self.btn_load_data, 1, 0, 1, 1)
        self.verticalLayout.addWidget(self.box_target)
        self.gridLayout.addLayout(self.verticalLayout, 2, 0, 1, 1)
        self.gridLayout_2.addWidget(self.file_panel, 0, 0, 1, 1)
        mainwindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(mainwindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1920, 22))
        self.menubar.setObjectName("menubar")
        mainwindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainwindow)
        self.tabWidget.setCurrentIndex(3)
        self.pushButton_2.clicked.connect(mainwindow.add_target)
        self.pushButton_3.clicked.connect(mainwindow.remove_target)
        self.pushButton.clicked.connect(mainwindow.load_path)
        self.filter_str.textChanged['QString'].connect(mainwindow.trie_search)
        self.filter_str.returnPressed.connect(self.pushButton_2.click)
        self.btn_load_data.clicked.connect(mainwindow.load_data)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)

    def retranslateUi(self, mainwindow):
        _translate = QtCore.QCoreApplication.translate
        mainwindow.setWindowTitle(_translate("mainwindow", "XPCS_GUI"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("mainwindow", "SAXS"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("mainwindow", "Tab 2"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("mainwindow", "Page"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.widget), _translate("mainwindow", "g2"))
        self.label_2.setText(_translate("mainwindow", "Path:"))
        self.pushButton.setText(_translate("mainwindow", "browse"))
        self.box_source.setTitle(_translate("mainwindow", "Source:"))
        self.label.setText(_translate("mainwindow", "Filter:"))
        self.pushButton_2.setText(_translate("mainwindow", "add"))
        self.pushButton_3.setText(_translate("mainwindow", "remove"))
        self.box_target.setTitle(_translate("mainwindow", "Target:"))
        self.btn_load_data.setText(_translate("mainwindow", "Finalize"))

from matplot_qt import MplCanvas
from pyqtgraph import ImageView, PlotWidget

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = QtWidgets.QMainWindow()
    ui = Ui_mainwindow()
    ui.setupUi(mainwindow)
    mainwindow.show()
    sys.exit(app.exec_())

