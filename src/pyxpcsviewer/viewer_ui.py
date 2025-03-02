# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'xpcs.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QComboBox, QDoubleSpinBox, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListView, QMainWindow, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QSplitter,
    QStatusBar, QTabWidget, QTableView, QVBoxLayout,
    QWidget)

from .plothandler import (ImageViewDev, ImageViewPlotItem, MplCanvasBarV, PlotWidgetDev)
from pyqtgraph import (DataTreeWidget, GraphicsLayoutWidget)
from pyqtgraph.parametertree import ParameterTree
from . import icons_rc

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName(u"mainWindow")
        mainWindow.resize(1555, 1013)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(mainWindow.sizePolicy().hasHeightForWidth())
        mainWindow.setSizePolicy(sizePolicy)
        mainWindow.setMinimumSize(QSize(1024, 0))
        icon = QIcon()
        icon.addFile(u":/newPrefix/icons8-giraffe-full-body-100.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u":/icons/icons8-giraffe-full-body-100.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        mainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(mainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Horizontal)
        self.splitter = QSplitter(self.splitter_3)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.label_2)

        self.work_dir = QLineEdit(self.layoutWidget)
        self.work_dir.setObjectName(u"work_dir")
        self.work_dir.setMinimumSize(QSize(200, 0))
        self.work_dir.setMaximumSize(QSize(16777215, 16777215))
        self.work_dir.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.work_dir)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_56 = QLabel(self.layoutWidget)
        self.label_56.setObjectName(u"label_56")

        self.horizontalLayout_2.addWidget(self.label_56)

        self.sort_method = QComboBox(self.layoutWidget)
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.setObjectName(u"sort_method")

        self.horizontalLayout_2.addWidget(self.sort_method)

        self.pushButton_11 = QPushButton(self.layoutWidget)
        self.pushButton_11.setObjectName(u"pushButton_11")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_11.sizePolicy().hasHeightForWidth())
        self.pushButton_11.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.pushButton_11)

        self.pushButton = QPushButton(self.layoutWidget)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy3.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.box_source = QGroupBox(self.layoutWidget)
        self.box_source.setObjectName(u"box_source")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(20)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.box_source.sizePolicy().hasHeightForWidth())
        self.box_source.setSizePolicy(sizePolicy4)
        self.box_source.setMinimumSize(QSize(0, 80))
        self.box_source.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_5 = QGridLayout(self.box_source)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.list_view_source = QListView(self.box_source)
        self.list_view_source.setObjectName(u"list_view_source")
        self.list_view_source.setDragEnabled(True)
        self.list_view_source.setAlternatingRowColors(True)
        self.list_view_source.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.gridLayout_5.addWidget(self.list_view_source, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.box_source)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.filter_type = QComboBox(self.layoutWidget1)
        self.filter_type.addItem("")
        self.filter_type.addItem("")
        self.filter_type.setObjectName(u"filter_type")

        self.horizontalLayout_3.addWidget(self.filter_type)

        self.filter_str = QLineEdit(self.layoutWidget1)
        self.filter_str.setObjectName(u"filter_str")
        sizePolicy3.setHeightForWidth(self.filter_str.sizePolicy().hasHeightForWidth())
        self.filter_str.setSizePolicy(sizePolicy3)
        self.filter_str.setMaximumSize(QSize(16777215, 100))
        self.filter_str.setClearButtonEnabled(True)

        self.horizontalLayout_3.addWidget(self.filter_str)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_2 = QPushButton(self.layoutWidget1)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy3.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy3)
        self.pushButton_2.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.layoutWidget1)
        self.pushButton_3.setObjectName(u"pushButton_3")
        sizePolicy3.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy3)
        self.pushButton_3.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.pushButton_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.box_target = QGroupBox(self.layoutWidget1)
        self.box_target.setObjectName(u"box_target")
        sizePolicy1.setHeightForWidth(self.box_target.sizePolicy().hasHeightForWidth())
        self.box_target.setSizePolicy(sizePolicy1)
        self.box_target.setMinimumSize(QSize(0, 120))
        self.box_target.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_4 = QGridLayout(self.box_target)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.btn_deselect = QPushButton(self.box_target)
        self.btn_deselect.setObjectName(u"btn_deselect")

        self.horizontalLayout_7.addWidget(self.btn_deselect)

        self.btn_up = QPushButton(self.box_target)
        self.btn_up.setObjectName(u"btn_up")

        self.horizontalLayout_7.addWidget(self.btn_up)

        self.btn_down = QPushButton(self.box_target)
        self.btn_down.setObjectName(u"btn_down")

        self.horizontalLayout_7.addWidget(self.btn_down)


        self.gridLayout_4.addLayout(self.horizontalLayout_7, 1, 0, 1, 1)

        self.list_view_target = QListView(self.box_target)
        self.list_view_target.setObjectName(u"list_view_target")
        self.list_view_target.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.gridLayout_4.addWidget(self.list_view_target, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.box_target)

        self.splitter.addWidget(self.layoutWidget1)
        self.splitter_3.addWidget(self.splitter)
        self.tabWidget = QTabWidget(self.splitter_3)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy1.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy1)
        self.tabWidget.setMinimumSize(QSize(600, 0))
        self.tabWidget.setMaximumSize(QSize(16777215, 16777215))
        self.tab1_1 = QWidget()
        self.tab1_1.setObjectName(u"tab1_1")
        self.gridLayout_26 = QGridLayout(self.tab1_1)
        self.gridLayout_26.setObjectName(u"gridLayout_26")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_38 = QLabel(self.tab1_1)
        self.label_38.setObjectName(u"label_38")

        self.horizontalLayout_4.addWidget(self.label_38)

        self.saxs2d_display = QLineEdit(self.tab1_1)
        self.saxs2d_display.setObjectName(u"saxs2d_display")
        self.saxs2d_display.setMinimumSize(QSize(500, 0))
        self.saxs2d_display.setAcceptDrops(False)
        self.saxs2d_display.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.saxs2d_display.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.saxs2d_display)


        self.gridLayout_26.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)

        self.pg_saxs = ImageViewDev(self.tab1_1)
        self.pg_saxs.setObjectName(u"pg_saxs")
        sizePolicy1.setHeightForWidth(self.pg_saxs.sizePolicy().hasHeightForWidth())
        self.pg_saxs.setSizePolicy(sizePolicy1)

        self.gridLayout_26.addWidget(self.pg_saxs, 1, 0, 1, 2)

        self.groupBox_3 = QGroupBox(self.tab1_1)
        self.groupBox_3.setObjectName(u"groupBox_3")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy5)
        self.groupBox_3.setMinimumSize(QSize(0, 100))
        self.gridLayout_40 = QGridLayout(self.groupBox_3)
        self.gridLayout_40.setObjectName(u"gridLayout_40")
        self.cb_saxs2D_cmap = QComboBox(self.groupBox_3)
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.setObjectName(u"cb_saxs2D_cmap")

        self.gridLayout_40.addWidget(self.cb_saxs2D_cmap, 0, 1, 1, 1)

        self.cb_saxs2D_type = QComboBox(self.groupBox_3)
        self.cb_saxs2D_type.addItem("")
        self.cb_saxs2D_type.addItem("")
        self.cb_saxs2D_type.setObjectName(u"cb_saxs2D_type")

        self.gridLayout_40.addWidget(self.cb_saxs2D_type, 0, 3, 1, 1)

        self.label_51 = QLabel(self.groupBox_3)
        self.label_51.setObjectName(u"label_51")

        self.gridLayout_40.addWidget(self.label_51, 0, 7, 1, 1)

        self.label_50 = QLabel(self.groupBox_3)
        self.label_50.setObjectName(u"label_50")

        self.gridLayout_40.addWidget(self.label_50, 0, 5, 1, 1)

        self.saxs2d_max = QDoubleSpinBox(self.groupBox_3)
        self.saxs2d_max.setObjectName(u"saxs2d_max")
        self.saxs2d_max.setEnabled(False)
        self.saxs2d_max.setDecimals(4)
        self.saxs2d_max.setMinimum(-99.000000000000000)
        self.saxs2d_max.setMaximum(99999.000000000000000)
        self.saxs2d_max.setValue(1.000000000000000)

        self.gridLayout_40.addWidget(self.saxs2d_max, 0, 8, 1, 1)

        self.label_13 = QLabel(self.groupBox_3)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_40.addWidget(self.label_13, 0, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_3)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_40.addWidget(self.label_12, 0, 2, 1, 1)

        self.saxs2d_rotate = QCheckBox(self.groupBox_3)
        self.saxs2d_rotate.setObjectName(u"saxs2d_rotate")
        self.saxs2d_rotate.setChecked(False)

        self.gridLayout_40.addWidget(self.saxs2d_rotate, 0, 4, 1, 1)

        self.saxs2d_min = QDoubleSpinBox(self.groupBox_3)
        self.saxs2d_min.setObjectName(u"saxs2d_min")
        self.saxs2d_min.setEnabled(False)
        self.saxs2d_min.setDecimals(4)
        self.saxs2d_min.setMinimum(-99.000000000000000)
        self.saxs2d_min.setMaximum(99999.000000000000000)

        self.gridLayout_40.addWidget(self.saxs2d_min, 0, 6, 1, 1)

        self.saxs2d_autorange = QCheckBox(self.groupBox_3)
        self.saxs2d_autorange.setObjectName(u"saxs2d_autorange")
        self.saxs2d_autorange.setChecked(True)

        self.gridLayout_40.addWidget(self.saxs2d_autorange, 0, 9, 1, 1)

        self.pushButton_5 = QPushButton(self.groupBox_3)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setMinimumSize(QSize(0, 0))

        self.gridLayout_40.addWidget(self.pushButton_5, 0, 10, 1, 1)


        self.gridLayout_26.addWidget(self.groupBox_3, 2, 0, 1, 1)

        self.groupBox_16 = QGroupBox(self.tab1_1)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.gridLayout_3 = QGridLayout(self.groupBox_16)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_58 = QLabel(self.groupBox_16)
        self.label_58.setObjectName(u"label_58")

        self.gridLayout_3.addWidget(self.label_58, 0, 0, 1, 1)

        self.cb_saxs2D_roi_type = QComboBox(self.groupBox_16)
        self.cb_saxs2D_roi_type.addItem("")
        self.cb_saxs2D_roi_type.addItem("")
        self.cb_saxs2D_roi_type.setObjectName(u"cb_saxs2D_roi_type")

        self.gridLayout_3.addWidget(self.cb_saxs2D_roi_type, 0, 1, 1, 1)

        self.label_60 = QLabel(self.groupBox_16)
        self.label_60.setObjectName(u"label_60")

        self.gridLayout_3.addWidget(self.label_60, 0, 2, 1, 1)

        self.cb_saxs2D_roi_color = QComboBox(self.groupBox_16)
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.addItem("")
        self.cb_saxs2D_roi_color.setObjectName(u"cb_saxs2D_roi_color")

        self.gridLayout_3.addWidget(self.cb_saxs2D_roi_color, 0, 3, 1, 1)

        self.label_61 = QLabel(self.groupBox_16)
        self.label_61.setObjectName(u"label_61")

        self.gridLayout_3.addWidget(self.label_61, 0, 4, 1, 1)

        self.sb_saxs2D_roi_width = QDoubleSpinBox(self.groupBox_16)
        self.sb_saxs2D_roi_width.setObjectName(u"sb_saxs2D_roi_width")
        self.sb_saxs2D_roi_width.setMinimum(0.100000000000000)
        self.sb_saxs2D_roi_width.setSingleStep(0.100000000000000)
        self.sb_saxs2D_roi_width.setValue(1.500000000000000)

        self.gridLayout_3.addWidget(self.sb_saxs2D_roi_width, 0, 5, 1, 1)

        self.btn_saxs2d_roi_add = QPushButton(self.groupBox_16)
        self.btn_saxs2d_roi_add.setObjectName(u"btn_saxs2d_roi_add")

        self.gridLayout_3.addWidget(self.btn_saxs2d_roi_add, 0, 6, 1, 1)


        self.gridLayout_26.addWidget(self.groupBox_16, 3, 0, 1, 1)

        self.tabWidget.addTab(self.tab1_1, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.gridLayout_25 = QGridLayout(self.tab_2)
        self.gridLayout_25.setObjectName(u"gridLayout_25")
        self.mp_saxs = MplCanvasBarV(self.tab_2)
        self.mp_saxs.setObjectName(u"mp_saxs")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.mp_saxs.sizePolicy().hasHeightForWidth())
        self.mp_saxs.setSizePolicy(sizePolicy6)
        self.mp_saxs.setMinimumSize(QSize(600, 0))

        self.gridLayout_25.addWidget(self.mp_saxs, 0, 0, 1, 1)

        self.groupBox_6 = QGroupBox(self.tab_2)
        self.groupBox_6.setObjectName(u"groupBox_6")
        sizePolicy5.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy5)
        self.gridLayout_24 = QGridLayout(self.groupBox_6)
        self.gridLayout_24.setObjectName(u"gridLayout_24")
        self.groupBox_14 = QGroupBox(self.groupBox_6)
        self.groupBox_14.setObjectName(u"groupBox_14")
        self.gridLayout_34 = QGridLayout(self.groupBox_14)
        self.gridLayout_34.setObjectName(u"gridLayout_34")
        self.cb_sub_bkg = QCheckBox(self.groupBox_14)
        self.cb_sub_bkg.setObjectName(u"cb_sub_bkg")

        self.gridLayout_34.addWidget(self.cb_sub_bkg, 0, 0, 1, 1)

        self.le_bkg_fname = QLineEdit(self.groupBox_14)
        self.le_bkg_fname.setObjectName(u"le_bkg_fname")
        self.le_bkg_fname.setEnabled(False)

        self.gridLayout_34.addWidget(self.le_bkg_fname, 0, 1, 1, 1)

        self.btn_select_bkgfile = QPushButton(self.groupBox_14)
        self.btn_select_bkgfile.setObjectName(u"btn_select_bkgfile")
        self.btn_select_bkgfile.setEnabled(False)

        self.gridLayout_34.addWidget(self.btn_select_bkgfile, 0, 2, 1, 1)

        self.label_59 = QLabel(self.groupBox_14)
        self.label_59.setObjectName(u"label_59")

        self.gridLayout_34.addWidget(self.label_59, 0, 3, 1, 1)

        self.bkg_weight = QDoubleSpinBox(self.groupBox_14)
        self.bkg_weight.setObjectName(u"bkg_weight")
        self.bkg_weight.setEnabled(False)
        self.bkg_weight.setDecimals(4)
        self.bkg_weight.setMaximum(99.999899999999997)
        self.bkg_weight.setValue(1.000000000000000)

        self.gridLayout_34.addWidget(self.bkg_weight, 0, 4, 1, 1)


        self.gridLayout_24.addWidget(self.groupBox_14, 1, 0, 2, 1)

        self.groupBox_13 = QGroupBox(self.groupBox_6)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.gridLayout_32 = QGridLayout(self.groupBox_13)
        self.gridLayout_32.setObjectName(u"gridLayout_32")
        self.box_show_roi = QCheckBox(self.groupBox_13)
        self.box_show_roi.setObjectName(u"box_show_roi")
        self.box_show_roi.setChecked(True)

        self.gridLayout_32.addWidget(self.box_show_roi, 0, 2, 1, 1)

        self.box_all_phi = QCheckBox(self.groupBox_13)
        self.box_all_phi.setObjectName(u"box_all_phi")

        self.gridLayout_32.addWidget(self.box_all_phi, 0, 0, 1, 1)

        self.box_show_phi_roi = QCheckBox(self.groupBox_13)
        self.box_show_phi_roi.setObjectName(u"box_show_phi_roi")

        self.gridLayout_32.addWidget(self.box_show_phi_roi, 0, 3, 1, 1)

        self.btn_export_saxs1d = QPushButton(self.groupBox_13)
        self.btn_export_saxs1d.setObjectName(u"btn_export_saxs1d")

        self.gridLayout_32.addWidget(self.btn_export_saxs1d, 0, 4, 1, 1)


        self.gridLayout_24.addWidget(self.groupBox_13, 1, 1, 2, 1)

        self.groupBox_15 = QGroupBox(self.groupBox_6)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.gridLayout_16 = QGridLayout(self.groupBox_15)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.label_21 = QLabel(self.groupBox_15)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_16.addWidget(self.label_21, 0, 0, 1, 1)

        self.cb_saxs_type = QComboBox(self.groupBox_15)
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.setObjectName(u"cb_saxs_type")

        self.gridLayout_16.addWidget(self.cb_saxs_type, 0, 1, 1, 2)

        self.label_55 = QLabel(self.groupBox_15)
        self.label_55.setObjectName(u"label_55")

        self.gridLayout_16.addWidget(self.label_55, 0, 3, 1, 1)

        self.saxs1d_sampling = QSpinBox(self.groupBox_15)
        self.saxs1d_sampling.setObjectName(u"saxs1d_sampling")
        self.saxs1d_sampling.setMinimum(1)
        self.saxs1d_sampling.setValue(1)

        self.gridLayout_16.addWidget(self.saxs1d_sampling, 0, 4, 1, 1)

        self.label_22 = QLabel(self.groupBox_15)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_16.addWidget(self.label_22, 0, 5, 1, 1)

        self.sb_saxs_offset = QDoubleSpinBox(self.groupBox_15)
        self.sb_saxs_offset.setObjectName(u"sb_saxs_offset")
        self.sb_saxs_offset.setDecimals(4)
        self.sb_saxs_offset.setSingleStep(0.050000000000000)
        self.sb_saxs_offset.setValue(0.000000000000000)

        self.gridLayout_16.addWidget(self.sb_saxs_offset, 0, 6, 1, 1)

        self.label_23 = QLabel(self.groupBox_15)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_16.addWidget(self.label_23, 0, 7, 1, 1)

        self.cb_saxs_norm = QComboBox(self.groupBox_15)
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.setObjectName(u"cb_saxs_norm")

        self.gridLayout_16.addWidget(self.cb_saxs_norm, 0, 8, 1, 1)

        self.saxs1d_lb_type = QComboBox(self.groupBox_15)
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.setObjectName(u"saxs1d_lb_type")

        self.gridLayout_16.addWidget(self.saxs1d_lb_type, 0, 9, 1, 1)

        self.label_49 = QLabel(self.groupBox_15)
        self.label_49.setObjectName(u"label_49")

        self.gridLayout_16.addWidget(self.label_49, 1, 0, 1, 2)

        self.saxs1d_qmin = QDoubleSpinBox(self.groupBox_15)
        self.saxs1d_qmin.setObjectName(u"saxs1d_qmin")
        self.saxs1d_qmin.setDecimals(4)
        self.saxs1d_qmin.setSingleStep(0.002000000000000)

        self.gridLayout_16.addWidget(self.saxs1d_qmin, 1, 2, 1, 2)

        self.saxs1d_qmax = QDoubleSpinBox(self.groupBox_15)
        self.saxs1d_qmax.setObjectName(u"saxs1d_qmax")
        self.saxs1d_qmax.setDecimals(4)
        self.saxs1d_qmax.setSingleStep(0.000500000000000)
        self.saxs1d_qmax.setValue(1.000000000000000)

        self.gridLayout_16.addWidget(self.saxs1d_qmax, 1, 4, 1, 1)

        self.label_54 = QLabel(self.groupBox_15)
        self.label_54.setObjectName(u"label_54")

        self.gridLayout_16.addWidget(self.label_54, 1, 5, 1, 1)

        self.sb_saxs_marker_size = QDoubleSpinBox(self.groupBox_15)
        self.sb_saxs_marker_size.setObjectName(u"sb_saxs_marker_size")
        self.sb_saxs_marker_size.setMinimum(1.000000000000000)
        self.sb_saxs_marker_size.setMaximum(20.000000000000000)
        self.sb_saxs_marker_size.setValue(5.000000000000000)

        self.gridLayout_16.addWidget(self.sb_saxs_marker_size, 1, 6, 1, 1)

        self.label_52 = QLabel(self.groupBox_15)
        self.label_52.setObjectName(u"label_52")

        self.gridLayout_16.addWidget(self.label_52, 1, 7, 1, 1)

        self.saxs1d_legend_loc = QComboBox(self.groupBox_15)
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.addItem("")
        self.saxs1d_legend_loc.setObjectName(u"saxs1d_legend_loc")

        self.gridLayout_16.addWidget(self.saxs1d_legend_loc, 1, 8, 1, 1)

        self.cbox_use_abs = QCheckBox(self.groupBox_15)
        self.cbox_use_abs.setObjectName(u"cbox_use_abs")

        self.gridLayout_16.addWidget(self.cbox_use_abs, 1, 9, 1, 1)


        self.gridLayout_24.addWidget(self.groupBox_15, 0, 0, 1, 3)

        self.pushButton_10 = QPushButton(self.groupBox_6)
        self.pushButton_10.setObjectName(u"pushButton_10")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.pushButton_10.sizePolicy().hasHeightForWidth())
        self.pushButton_10.setSizePolicy(sizePolicy7)

        self.gridLayout_24.addWidget(self.pushButton_10, 1, 2, 2, 1)


        self.gridLayout_25.addWidget(self.groupBox_6, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_6 = QGridLayout(self.tab_3)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.mp_stab = MplCanvasBarV(self.tab_3)
        self.mp_stab.setObjectName(u"mp_stab")
        sizePolicy1.setHeightForWidth(self.mp_stab.sizePolicy().hasHeightForWidth())
        self.mp_stab.setSizePolicy(sizePolicy1)

        self.gridLayout_6.addWidget(self.mp_stab, 0, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.tab_3)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy5.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy5)
        self.groupBox_4.setMinimumSize(QSize(0, 0))
        self.gridLayout_20 = QGridLayout(self.groupBox_4)
        self.gridLayout_20.setObjectName(u"gridLayout_20")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_20.addItem(self.horizontalSpacer_6, 0, 0, 1, 1)

        self.gridLayout_17 = QGridLayout()
        self.gridLayout_17.setObjectName(u"gridLayout_17")
        self.label_14 = QLabel(self.groupBox_4)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_17.addWidget(self.label_14, 0, 0, 1, 1)

        self.cb_stab_type = QComboBox(self.groupBox_4)
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.setObjectName(u"cb_stab_type")

        self.gridLayout_17.addWidget(self.cb_stab_type, 0, 1, 1, 1)

        self.label_24 = QLabel(self.groupBox_4)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout_17.addWidget(self.label_24, 0, 2, 1, 1)

        self.sb_stab_offset = QDoubleSpinBox(self.groupBox_4)
        self.sb_stab_offset.setObjectName(u"sb_stab_offset")
        self.sb_stab_offset.setDecimals(4)
        self.sb_stab_offset.setSingleStep(0.050000000000000)
        self.sb_stab_offset.setValue(0.000000000000000)

        self.gridLayout_17.addWidget(self.sb_stab_offset, 0, 3, 1, 1)

        self.label_16 = QLabel(self.groupBox_4)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_17.addWidget(self.label_16, 0, 4, 1, 2)

        self.pushButton_7 = QPushButton(self.groupBox_4)
        self.pushButton_7.setObjectName(u"pushButton_7")

        self.gridLayout_17.addWidget(self.pushButton_7, 1, 6, 1, 1)

        self.cb_stab = QComboBox(self.groupBox_4)
        self.cb_stab.setObjectName(u"cb_stab")

        self.gridLayout_17.addWidget(self.cb_stab, 1, 0, 1, 6)

        self.cb_stab_norm = QComboBox(self.groupBox_4)
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.setObjectName(u"cb_stab_norm")

        self.gridLayout_17.addWidget(self.cb_stab_norm, 0, 6, 1, 1)


        self.gridLayout_20.addLayout(self.gridLayout_17, 0, 1, 1, 1)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_20.addItem(self.horizontalSpacer_9, 0, 2, 1, 1)


        self.gridLayout_6.addWidget(self.groupBox_4, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.gridLayout_27 = QGridLayout(self.tab_4)
        self.gridLayout_27.setObjectName(u"gridLayout_27")
        self.pg_intt = PlotWidgetDev(self.tab_4)
        self.pg_intt.setObjectName(u"pg_intt")
        sizePolicy6.setHeightForWidth(self.pg_intt.sizePolicy().hasHeightForWidth())
        self.pg_intt.setSizePolicy(sizePolicy6)

        self.gridLayout_27.addWidget(self.pg_intt, 0, 0, 1, 3)

        self.groupBox_7 = QGroupBox(self.tab_4)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setMinimumSize(QSize(0, 0))
        self.gridLayout_23 = QGridLayout(self.groupBox_7)
        self.gridLayout_23.setObjectName(u"gridLayout_23")
        self.horizontalSpacer_12 = QSpacerItem(344, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_23.addItem(self.horizontalSpacer_12, 0, 0, 1, 1)

        self.gridLayout_18 = QGridLayout()
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.label_9 = QLabel(self.groupBox_7)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_18.addWidget(self.label_9, 0, 0, 1, 1)

        self.sb_intt_max = QSpinBox(self.groupBox_7)
        self.sb_intt_max.setObjectName(u"sb_intt_max")
        self.sb_intt_max.setValue(10)

        self.gridLayout_18.addWidget(self.sb_intt_max, 0, 1, 1, 1)

        self.label_31 = QLabel(self.groupBox_7)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout_18.addWidget(self.label_31, 0, 2, 1, 1)

        self.sb_window = QSpinBox(self.groupBox_7)
        self.sb_window.setObjectName(u"sb_window")
        self.sb_window.setMaximum(999)
        self.sb_window.setValue(1)

        self.gridLayout_18.addWidget(self.sb_window, 0, 3, 1, 1)

        self.label_11 = QLabel(self.groupBox_7)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_18.addWidget(self.label_11, 0, 4, 1, 1)

        self.sb_intt_sampling = QSpinBox(self.groupBox_7)
        self.sb_intt_sampling.setObjectName(u"sb_intt_sampling")
        self.sb_intt_sampling.setMinimum(1)
        self.sb_intt_sampling.setValue(1)

        self.gridLayout_18.addWidget(self.sb_intt_sampling, 0, 5, 1, 1)

        self.label_34 = QLabel(self.groupBox_7)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_18.addWidget(self.label_34, 0, 6, 1, 1)

        self.intt_xlabel = QComboBox(self.groupBox_7)
        self.intt_xlabel.addItem("")
        self.intt_xlabel.addItem("")
        self.intt_xlabel.setObjectName(u"intt_xlabel")

        self.gridLayout_18.addWidget(self.intt_xlabel, 0, 7, 1, 1)

        self.btn_intt = QPushButton(self.groupBox_7)
        self.btn_intt.setObjectName(u"btn_intt")

        self.gridLayout_18.addWidget(self.btn_intt, 1, 0, 1, 8)


        self.gridLayout_23.addLayout(self.gridLayout_18, 0, 1, 1, 1)

        self.horizontalSpacer_11 = QSpacerItem(343, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_23.addItem(self.horizontalSpacer_11, 0, 2, 1, 1)


        self.gridLayout_27.addWidget(self.groupBox_7, 1, 0, 1, 3)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.gridLayout_8 = QGridLayout(self.tab_6)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.scrollArea = QScrollArea(self.tab_6)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(30)
        sizePolicy8.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy8)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.g2_scroll_area = QWidget()
        self.g2_scroll_area.setObjectName(u"g2_scroll_area")
        self.g2_scroll_area.setGeometry(QRect(0, 0, 1122, 717))
        sizePolicy1.setHeightForWidth(self.g2_scroll_area.sizePolicy().hasHeightForWidth())
        self.g2_scroll_area.setSizePolicy(sizePolicy1)
        self.gridLayout_10 = QGridLayout(self.g2_scroll_area)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.mp_g2 = PlotWidgetDev(self.g2_scroll_area)
        self.mp_g2.setObjectName(u"mp_g2")
        sizePolicy5.setHeightForWidth(self.mp_g2.sizePolicy().hasHeightForWidth())
        self.mp_g2.setSizePolicy(sizePolicy5)
        self.mp_g2.setMinimumSize(QSize(0, 0))
        self.mp_g2.setAutoFillBackground(False)

        self.gridLayout_10.addWidget(self.mp_g2, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.g2_scroll_area)

        self.gridLayout_8.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.splitter_2 = QSplitter(self.tab_6)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Horizontal)
        self.groupBox = QGroupBox(self.splitter_2)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QSize(0, 0))
        self.groupBox.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_13 = QGridLayout(self.groupBox)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gridLayout_11 = QGridLayout()
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_11.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_11.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_11.addWidget(self.label_7, 2, 0, 1, 1)

        self.g2_qmin = QDoubleSpinBox(self.groupBox)
        self.g2_qmin.setObjectName(u"g2_qmin")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.g2_qmin.sizePolicy().hasHeightForWidth())
        self.g2_qmin.setSizePolicy(sizePolicy9)
        self.g2_qmin.setDecimals(4)
        self.g2_qmin.setSingleStep(0.001000000000000)

        self.gridLayout_11.addWidget(self.g2_qmin, 0, 1, 1, 1)

        self.g2_qmax = QDoubleSpinBox(self.groupBox)
        self.g2_qmax.setObjectName(u"g2_qmax")
        sizePolicy9.setHeightForWidth(self.g2_qmax.sizePolicy().hasHeightForWidth())
        self.g2_qmax.setSizePolicy(sizePolicy9)
        self.g2_qmax.setDecimals(4)
        self.g2_qmax.setSingleStep(0.001000000000000)
        self.g2_qmax.setValue(0.010000000000000)

        self.gridLayout_11.addWidget(self.g2_qmax, 0, 2, 1, 1)

        self.g2_ymin = QDoubleSpinBox(self.groupBox)
        self.g2_ymin.setObjectName(u"g2_ymin")
        sizePolicy9.setHeightForWidth(self.g2_ymin.sizePolicy().hasHeightForWidth())
        self.g2_ymin.setSizePolicy(sizePolicy9)
        self.g2_ymin.setDecimals(3)
        self.g2_ymin.setMinimum(-1.000000000000000)
        self.g2_ymin.setSingleStep(0.010000000000000)
        self.g2_ymin.setValue(1.000000000000000)

        self.gridLayout_11.addWidget(self.g2_ymin, 2, 1, 1, 1)

        self.g2_ymax = QDoubleSpinBox(self.groupBox)
        self.g2_ymax.setObjectName(u"g2_ymax")
        sizePolicy9.setHeightForWidth(self.g2_ymax.sizePolicy().hasHeightForWidth())
        self.g2_ymax.setSizePolicy(sizePolicy9)
        self.g2_ymax.setDecimals(3)
        self.g2_ymax.setMinimum(-1.000000000000000)
        self.g2_ymax.setSingleStep(0.010000000000000)
        self.g2_ymax.setValue(1.800000000000000)

        self.gridLayout_11.addWidget(self.g2_ymax, 2, 2, 1, 1)

        self.g2_tmin = QLineEdit(self.groupBox)
        self.g2_tmin.setObjectName(u"g2_tmin")
        sizePolicy9.setHeightForWidth(self.g2_tmin.sizePolicy().hasHeightForWidth())
        self.g2_tmin.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_tmin, 1, 1, 1, 1)

        self.g2_tmax = QLineEdit(self.groupBox)
        self.g2_tmax.setObjectName(u"g2_tmax")
        sizePolicy9.setHeightForWidth(self.g2_tmax.sizePolicy().hasHeightForWidth())
        self.g2_tmax.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_tmax, 1, 2, 1, 1)

        self.g2_yauto = QCheckBox(self.groupBox)
        self.g2_yauto.setObjectName(u"g2_yauto")
        sizePolicy9.setHeightForWidth(self.g2_yauto.sizePolicy().hasHeightForWidth())
        self.g2_yauto.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_yauto, 2, 3, 1, 1)


        self.gridLayout_13.addLayout(self.gridLayout_11, 0, 1, 1, 1)

        self.gridLayout_19 = QGridLayout()
        self.gridLayout_19.setObjectName(u"gridLayout_19")
        self.pushButton_4 = QPushButton(self.groupBox)
        self.pushButton_4.setObjectName(u"pushButton_4")
        sizePolicy7.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy7)
        self.pushButton_4.setMinimumSize(QSize(0, 0))

        self.gridLayout_19.addWidget(self.pushButton_4, 0, 0, 1, 2)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout_19.addWidget(self.label, 2, 0, 1, 1)

        self.sb_g2_column = QSpinBox(self.groupBox)
        self.sb_g2_column.setObjectName(u"sb_g2_column")
        self.sb_g2_column.setMinimum(1)
        self.sb_g2_column.setMaximum(8)
        self.sb_g2_column.setSingleStep(1)
        self.sb_g2_column.setValue(4)

        self.gridLayout_19.addWidget(self.sb_g2_column, 1, 1, 1, 1)

        self.label_53 = QLabel(self.groupBox)
        self.label_53.setObjectName(u"label_53")

        self.gridLayout_19.addWidget(self.label_53, 3, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_19.addWidget(self.label_8, 1, 0, 1, 1)

        self.sb_g2_offset = QDoubleSpinBox(self.groupBox)
        self.sb_g2_offset.setObjectName(u"sb_g2_offset")
        self.sb_g2_offset.setDecimals(3)
        self.sb_g2_offset.setSingleStep(0.005000000000000)

        self.gridLayout_19.addWidget(self.sb_g2_offset, 2, 1, 1, 1)

        self.g2_marker_size = QDoubleSpinBox(self.groupBox)
        self.g2_marker_size.setObjectName(u"g2_marker_size")
        self.g2_marker_size.setDecimals(1)
        self.g2_marker_size.setMinimum(1.000000000000000)
        self.g2_marker_size.setMaximum(15.000000000000000)
        self.g2_marker_size.setSingleStep(1.000000000000000)
        self.g2_marker_size.setValue(5.000000000000000)

        self.gridLayout_19.addWidget(self.g2_marker_size, 3, 1, 1, 1)

        self.g2_sub_baseline = QCheckBox(self.groupBox)
        self.g2_sub_baseline.setObjectName(u"g2_sub_baseline")
        sizePolicy9.setHeightForWidth(self.g2_sub_baseline.sizePolicy().hasHeightForWidth())
        self.g2_sub_baseline.setSizePolicy(sizePolicy9)
        self.g2_sub_baseline.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_sub_baseline, 3, 2, 1, 3)

        self.g2_show_fit = QCheckBox(self.groupBox)
        self.g2_show_fit.setObjectName(u"g2_show_fit")
        sizePolicy9.setHeightForWidth(self.g2_show_fit.sizePolicy().hasHeightForWidth())
        self.g2_show_fit.setSizePolicy(sizePolicy9)
        self.g2_show_fit.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_show_fit, 2, 2, 1, 3)

        self.g2_show_label = QCheckBox(self.groupBox)
        self.g2_show_label.setObjectName(u"g2_show_label")
        sizePolicy9.setHeightForWidth(self.g2_show_label.sizePolicy().hasHeightForWidth())
        self.g2_show_label.setSizePolicy(sizePolicy9)
        self.g2_show_label.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_show_label, 1, 2, 1, 3)

        self.g2_plot_type = QComboBox(self.groupBox)
        self.g2_plot_type.addItem("")
        self.g2_plot_type.addItem("")
        self.g2_plot_type.addItem("")
        self.g2_plot_type.setObjectName(u"g2_plot_type")
        sizePolicy9.setHeightForWidth(self.g2_plot_type.sizePolicy().hasHeightForWidth())
        self.g2_plot_type.setSizePolicy(sizePolicy9)

        self.gridLayout_19.addWidget(self.g2_plot_type, 0, 2, 1, 3)


        self.gridLayout_13.addLayout(self.gridLayout_19, 0, 0, 1, 1)

        self.splitter_2.addWidget(self.groupBox)
        self.groupBox_2 = QGroupBox(self.splitter_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setMinimumSize(QSize(0, 0))
        self.groupBox_2.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_14 = QGridLayout(self.groupBox_2)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gridLayout_12 = QGridLayout()
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.g2_fmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_fmin.setObjectName(u"g2_fmin")
        self.g2_fmin.setDecimals(3)
        self.g2_fmin.setMinimum(0.501000000000000)
        self.g2_fmin.setMaximum(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_fmin, 3, 7, 1, 1)

        self.g2_fmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_fmax.setObjectName(u"g2_fmax")
        self.g2_fmax.setDecimals(3)
        self.g2_fmax.setMinimum(0.501000000000000)
        self.g2_fmax.setMaximum(1.000000000000000)
        self.g2_fmax.setValue(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_fmax, 3, 8, 1, 1)

        self.g2_c2min = QDoubleSpinBox(self.groupBox_2)
        self.g2_c2min.setObjectName(u"g2_c2min")
        self.g2_c2min.setDecimals(3)
        self.g2_c2min.setValue(0.500000000000000)

        self.gridLayout_12.addWidget(self.g2_c2min, 2, 7, 1, 1)

        self.g2_c2max = QDoubleSpinBox(self.groupBox_2)
        self.g2_c2max.setObjectName(u"g2_c2max")
        self.g2_c2max.setDecimals(3)
        self.g2_c2max.setValue(2.000000000000000)

        self.gridLayout_12.addWidget(self.g2_c2max, 2, 8, 1, 1)

        self.g2_b2max = QDoubleSpinBox(self.groupBox_2)
        self.g2_b2max.setObjectName(u"g2_b2max")
        self.g2_b2max.setDecimals(5)
        self.g2_b2max.setMaximum(9999.999900000000707)
        self.g2_b2max.setValue(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_b2max, 1, 8, 1, 1)

        self.g2_b2min = QDoubleSpinBox(self.groupBox_2)
        self.g2_b2min.setObjectName(u"g2_b2min")
        self.g2_b2min.setDecimals(5)
        self.g2_b2min.setMinimum(0.000010000000000)
        self.g2_b2min.setMaximum(999.999000000000024)
        self.g2_b2min.setValue(0.000010000000000)

        self.gridLayout_12.addWidget(self.g2_b2min, 1, 7, 1, 1)

        self.label_66 = QLabel(self.groupBox_2)
        self.label_66.setObjectName(u"label_66")

        self.gridLayout_12.addWidget(self.label_66, 2, 6, 1, 1)

        self.label_48 = QLabel(self.groupBox_2)
        self.label_48.setObjectName(u"label_48")

        self.gridLayout_12.addWidget(self.label_48, 3, 0, 1, 1)

        self.g2_c2fit = QCheckBox(self.groupBox_2)
        self.g2_c2fit.setObjectName(u"g2_c2fit")
        self.g2_c2fit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_c2fit, 2, 9, 1, 1)

        self.label_41 = QLabel(self.groupBox_2)
        self.label_41.setObjectName(u"label_41")

        self.gridLayout_12.addWidget(self.label_41, 3, 1, 1, 1)

        self.g2_dfit = QCheckBox(self.groupBox_2)
        self.g2_dfit.setObjectName(u"g2_dfit")
        self.g2_dfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_dfit, 3, 4, 1, 1)

        self.label_63 = QLabel(self.groupBox_2)
        self.label_63.setObjectName(u"label_63")

        self.gridLayout_12.addWidget(self.label_63, 3, 5, 1, 1)

        self.g2_ffit = QCheckBox(self.groupBox_2)
        self.g2_ffit.setObjectName(u"g2_ffit")
        self.g2_ffit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_ffit, 3, 9, 1, 1)

        self.g2_fitting_function = QComboBox(self.groupBox_2)
        self.g2_fitting_function.addItem("")
        self.g2_fitting_function.addItem("")
        self.g2_fitting_function.setObjectName(u"g2_fitting_function")

        self.gridLayout_12.addWidget(self.g2_fitting_function, 0, 5, 1, 5)

        self.label_67 = QLabel(self.groupBox_2)
        self.label_67.setObjectName(u"label_67")

        self.gridLayout_12.addWidget(self.label_67, 3, 6, 1, 1)

        self.g2_amin = QDoubleSpinBox(self.groupBox_2)
        self.g2_amin.setObjectName(u"g2_amin")
        self.g2_amin.setDecimals(3)
        self.g2_amin.setMaximum(999.999000000000024)
        self.g2_amin.setSingleStep(0.010000000000000)
        self.g2_amin.setValue(0.040000000000000)

        self.gridLayout_12.addWidget(self.g2_amin, 0, 2, 1, 1)

        self.g2_amax = QDoubleSpinBox(self.groupBox_2)
        self.g2_amax.setObjectName(u"g2_amax")
        self.g2_amax.setDecimals(3)
        self.g2_amax.setMaximum(999.999000000000024)
        self.g2_amax.setSingleStep(0.010000000000000)
        self.g2_amax.setValue(0.800000000000000)

        self.gridLayout_12.addWidget(self.g2_amax, 0, 3, 1, 1)

        self.g2_dmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_dmin.setObjectName(u"g2_dmin")
        self.g2_dmin.setDecimals(3)
        self.g2_dmin.setSingleStep(0.010000000000000)
        self.g2_dmin.setValue(0.950000000000000)

        self.gridLayout_12.addWidget(self.g2_dmin, 3, 2, 1, 1)

        self.g2_dmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_dmax.setObjectName(u"g2_dmax")
        self.g2_dmax.setDecimals(3)
        self.g2_dmax.setSingleStep(0.050000000000000)
        self.g2_dmax.setValue(1.050000000000000)

        self.gridLayout_12.addWidget(self.g2_dmax, 3, 3, 1, 1)

        self.g2_cmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_cmin.setObjectName(u"g2_cmin")
        self.g2_cmin.setDecimals(3)
        self.g2_cmin.setSingleStep(0.010000000000000)
        self.g2_cmin.setValue(0.500000000000000)

        self.gridLayout_12.addWidget(self.g2_cmin, 2, 2, 1, 1)

        self.g2_cmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_cmax.setObjectName(u"g2_cmax")
        self.g2_cmax.setDecimals(3)
        self.g2_cmax.setSingleStep(0.010000000000000)
        self.g2_cmax.setValue(2.000000000000000)

        self.gridLayout_12.addWidget(self.g2_cmax, 2, 3, 1, 1)

        self.g2_bmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_bmin.setObjectName(u"g2_bmin")
        self.g2_bmin.setDecimals(5)
        self.g2_bmin.setMinimum(0.000010000000000)
        self.g2_bmin.setMaximum(999.999900000000025)
        self.g2_bmin.setValue(0.000010000000000)

        self.gridLayout_12.addWidget(self.g2_bmin, 1, 2, 1, 1)

        self.g2_bmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_bmax.setObjectName(u"g2_bmax")
        self.g2_bmax.setDecimals(5)
        self.g2_bmax.setMaximum(9999.999900000000707)
        self.g2_bmax.setValue(100.000000000000000)

        self.gridLayout_12.addWidget(self.g2_bmax, 1, 3, 1, 1)

        self.label_45 = QLabel(self.groupBox_2)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout_12.addWidget(self.label_45, 0, 0, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_12.addWidget(self.label_5, 0, 1, 1, 1)

        self.g2_afit = QCheckBox(self.groupBox_2)
        self.g2_afit.setObjectName(u"g2_afit")
        self.g2_afit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_afit, 0, 4, 1, 1)

        self.label_46 = QLabel(self.groupBox_2)
        self.label_46.setObjectName(u"label_46")

        self.gridLayout_12.addWidget(self.label_46, 1, 0, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_12.addWidget(self.label_6, 1, 1, 1, 1)

        self.g2_bfit = QCheckBox(self.groupBox_2)
        self.g2_bfit.setObjectName(u"g2_bfit")
        self.g2_bfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_bfit, 1, 4, 1, 1)

        self.label_65 = QLabel(self.groupBox_2)
        self.label_65.setObjectName(u"label_65")

        self.gridLayout_12.addWidget(self.label_65, 1, 5, 1, 1)

        self.label_64 = QLabel(self.groupBox_2)
        self.label_64.setObjectName(u"label_64")

        self.gridLayout_12.addWidget(self.label_64, 1, 6, 1, 1)

        self.g2_b2fit = QCheckBox(self.groupBox_2)
        self.g2_b2fit.setObjectName(u"g2_b2fit")
        self.g2_b2fit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_b2fit, 1, 9, 1, 1)

        self.label_47 = QLabel(self.groupBox_2)
        self.label_47.setObjectName(u"label_47")

        self.gridLayout_12.addWidget(self.label_47, 2, 0, 1, 1)

        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_12.addWidget(self.label_10, 2, 1, 1, 1)

        self.g2_cfit = QCheckBox(self.groupBox_2)
        self.g2_cfit.setObjectName(u"g2_cfit")
        self.g2_cfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_cfit, 2, 4, 1, 1)

        self.label_62 = QLabel(self.groupBox_2)
        self.label_62.setObjectName(u"label_62")

        self.gridLayout_12.addWidget(self.label_62, 2, 5, 1, 1)

        self.show_g2_fit_summary = QPushButton(self.groupBox_2)
        self.show_g2_fit_summary.setObjectName(u"show_g2_fit_summary")
        sizePolicy2.setHeightForWidth(self.show_g2_fit_summary.sizePolicy().hasHeightForWidth())
        self.show_g2_fit_summary.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.show_g2_fit_summary, 0, 10, 1, 1)

        self.btn_g2_export = QPushButton(self.groupBox_2)
        self.btn_g2_export.setObjectName(u"btn_g2_export")
        sizePolicy2.setHeightForWidth(self.btn_g2_export.sizePolicy().hasHeightForWidth())
        self.btn_g2_export.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.btn_g2_export, 1, 10, 1, 1)

        self.btn_g2_refit = QPushButton(self.groupBox_2)
        self.btn_g2_refit.setObjectName(u"btn_g2_refit")
        sizePolicy2.setHeightForWidth(self.btn_g2_refit.sizePolicy().hasHeightForWidth())
        self.btn_g2_refit.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.btn_g2_refit, 2, 10, 2, 1)


        self.gridLayout_14.addLayout(self.gridLayout_12, 0, 0, 3, 1)

        self.splitter_2.addWidget(self.groupBox_2)

        self.gridLayout_8.addWidget(self.splitter_2, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.gridLayout_22 = QGridLayout(self.tab_7)
        self.gridLayout_22.setObjectName(u"gridLayout_22")
        self.mp_tauq = MplCanvasBarV(self.tab_7)
        self.mp_tauq.setObjectName(u"mp_tauq")
        sizePolicy6.setHeightForWidth(self.mp_tauq.sizePolicy().hasHeightForWidth())
        self.mp_tauq.setSizePolicy(sizePolicy6)

        self.gridLayout_22.addWidget(self.mp_tauq, 0, 0, 1, 1)

        self.mp_tauq_pre = MplCanvasBarV(self.tab_7)
        self.mp_tauq_pre.setObjectName(u"mp_tauq_pre")
        sizePolicy6.setHeightForWidth(self.mp_tauq_pre.sizePolicy().hasHeightForWidth())
        self.mp_tauq_pre.setSizePolicy(sizePolicy6)

        self.gridLayout_22.addWidget(self.mp_tauq_pre, 0, 1, 1, 1)

        self.groupBox_5 = QGroupBox(self.tab_7)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy5.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy5)
        self.groupBox_5.setMinimumSize(QSize(0, 0))
        self.groupBox_5.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_39 = QGridLayout(self.groupBox_5)
        self.gridLayout_39.setObjectName(u"gridLayout_39")
        self.gridLayout_38 = QGridLayout()
        self.gridLayout_38.setObjectName(u"gridLayout_38")
        self.gridLayout_15 = QGridLayout()
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.label_15 = QLabel(self.groupBox_5)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_15.addWidget(self.label_15, 0, 0, 1, 1)

        self.cb_tauq_type = QComboBox(self.groupBox_5)
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.setObjectName(u"cb_tauq_type")

        self.gridLayout_15.addWidget(self.cb_tauq_type, 0, 1, 1, 1)

        self.label_18 = QLabel(self.groupBox_5)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_15.addWidget(self.label_18, 1, 0, 1, 1)

        self.sb_tauq_offset = QDoubleSpinBox(self.groupBox_5)
        self.sb_tauq_offset.setObjectName(u"sb_tauq_offset")
        self.sb_tauq_offset.setMinimum(-2.000000000000000)
        self.sb_tauq_offset.setMaximum(2.000000000000000)
        self.sb_tauq_offset.setSingleStep(0.200000000000000)
        self.sb_tauq_offset.setValue(0.000000000000000)

        self.gridLayout_15.addWidget(self.sb_tauq_offset, 1, 1, 1, 1)


        self.gridLayout_38.addLayout(self.gridLayout_15, 1, 1, 1, 1)

        self.gridLayout_21 = QGridLayout()
        self.gridLayout_21.setObjectName(u"gridLayout_21")
        self.tauq_amax = QLineEdit(self.groupBox_5)
        self.tauq_amax.setObjectName(u"tauq_amax")

        self.gridLayout_21.addWidget(self.tauq_amax, 0, 2, 1, 1)

        self.tauq_qmax = QLineEdit(self.groupBox_5)
        self.tauq_qmax.setObjectName(u"tauq_qmax")

        self.gridLayout_21.addWidget(self.tauq_qmax, 2, 2, 1, 1)

        self.tauq_bfit = QCheckBox(self.groupBox_5)
        self.tauq_bfit.setObjectName(u"tauq_bfit")
        self.tauq_bfit.setChecked(True)

        self.gridLayout_21.addWidget(self.tauq_bfit, 1, 3, 1, 1)

        self.label_44 = QLabel(self.groupBox_5)
        self.label_44.setObjectName(u"label_44")

        self.gridLayout_21.addWidget(self.label_44, 0, 0, 1, 1)

        self.tauq_bmin = QLineEdit(self.groupBox_5)
        self.tauq_bmin.setObjectName(u"tauq_bmin")

        self.gridLayout_21.addWidget(self.tauq_bmin, 1, 1, 1, 1)

        self.label_42 = QLabel(self.groupBox_5)
        self.label_42.setObjectName(u"label_42")

        self.gridLayout_21.addWidget(self.label_42, 1, 0, 1, 1)

        self.tauq_amin = QLineEdit(self.groupBox_5)
        self.tauq_amin.setObjectName(u"tauq_amin")

        self.gridLayout_21.addWidget(self.tauq_amin, 0, 1, 1, 1)

        self.tauq_afit = QCheckBox(self.groupBox_5)
        self.tauq_afit.setObjectName(u"tauq_afit")
        self.tauq_afit.setChecked(True)

        self.gridLayout_21.addWidget(self.tauq_afit, 0, 3, 1, 1)

        self.tauq_bmax = QLineEdit(self.groupBox_5)
        self.tauq_bmax.setObjectName(u"tauq_bmax")

        self.gridLayout_21.addWidget(self.tauq_bmax, 1, 2, 1, 1)

        self.tauq_qmin = QLineEdit(self.groupBox_5)
        self.tauq_qmin.setObjectName(u"tauq_qmin")

        self.gridLayout_21.addWidget(self.tauq_qmin, 2, 1, 1, 1)

        self.label_43 = QLabel(self.groupBox_5)
        self.label_43.setObjectName(u"label_43")

        self.gridLayout_21.addWidget(self.label_43, 2, 0, 1, 1)


        self.gridLayout_38.addLayout(self.gridLayout_21, 0, 0, 1, 2)

        self.pushButton_8 = QPushButton(self.groupBox_5)
        self.pushButton_8.setObjectName(u"pushButton_8")
        self.pushButton_8.setMinimumSize(QSize(120, 80))

        self.gridLayout_38.addWidget(self.pushButton_8, 1, 0, 1, 1)


        self.gridLayout_39.addLayout(self.gridLayout_38, 0, 0, 1, 1)

        self.tauq_msg = DataTreeWidget(self.groupBox_5)
        self.tauq_msg.setObjectName(u"tauq_msg")

        self.gridLayout_39.addWidget(self.tauq_msg, 0, 1, 1, 1)


        self.gridLayout_22.addWidget(self.groupBox_5, 1, 0, 1, 2)

        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName(u"tab_8")
        self.gridLayout_33 = QGridLayout(self.tab_8)
        self.gridLayout_33.setObjectName(u"gridLayout_33")
        self.mp_2t = ImageViewPlotItem(self.tab_8)
        self.mp_2t.setObjectName(u"mp_2t")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(2)
        sizePolicy10.setHeightForWidth(self.mp_2t.sizePolicy().hasHeightForWidth())
        self.mp_2t.setSizePolicy(sizePolicy10)
        self.mp_2t.setMinimumSize(QSize(300, 200))

        self.gridLayout_33.addWidget(self.mp_2t, 1, 0, 1, 1)

        self.groupBox_11 = QGroupBox(self.tab_8)
        self.groupBox_11.setObjectName(u"groupBox_11")
        sizePolicy5.setHeightForWidth(self.groupBox_11.sizePolicy().hasHeightForWidth())
        self.groupBox_11.setSizePolicy(sizePolicy5)
        self.groupBox_11.setMinimumSize(QSize(0, 0))
        self.groupBox_11.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_37 = QGridLayout(self.groupBox_11)
        self.gridLayout_37.setObjectName(u"gridLayout_37")
        self.horizontalSpacer_5 = QSpacerItem(279, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_37.addItem(self.horizontalSpacer_5, 0, 0, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.c2_min = QDoubleSpinBox(self.groupBox_11)
        self.c2_min.setObjectName(u"c2_min")
        self.c2_min.setMinimum(-1.000000000000000)
        self.c2_min.setValue(0.800000000000000)

        self.gridLayout_2.addWidget(self.c2_min, 1, 11, 1, 1)

        self.c2_max = QDoubleSpinBox(self.groupBox_11)
        self.c2_max.setObjectName(u"c2_max")
        self.c2_max.setMinimum(-1.000000000000000)
        self.c2_max.setValue(2.200000000000000)

        self.gridLayout_2.addWidget(self.c2_max, 1, 12, 1, 1)

        self.label_35 = QLabel(self.groupBox_11)
        self.label_35.setObjectName(u"label_35")

        self.gridLayout_2.addWidget(self.label_35, 0, 3, 1, 2)

        self.label_36 = QLabel(self.groupBox_11)
        self.label_36.setObjectName(u"label_36")

        self.gridLayout_2.addWidget(self.label_36, 0, 0, 1, 1)

        self.cb_twotime_type = QComboBox(self.groupBox_11)
        self.cb_twotime_type.addItem("")
        self.cb_twotime_type.addItem("")
        self.cb_twotime_type.setObjectName(u"cb_twotime_type")

        self.gridLayout_2.addWidget(self.cb_twotime_type, 0, 1, 1, 2)

        self.label_28 = QLabel(self.groupBox_11)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout_2.addWidget(self.label_28, 1, 3, 1, 2)

        self.pushButton_12 = QPushButton(self.groupBox_11)
        self.pushButton_12.setObjectName(u"pushButton_12")

        self.gridLayout_2.addWidget(self.pushButton_12, 1, 13, 1, 2)

        self.twotime_autocrop = QCheckBox(self.groupBox_11)
        self.twotime_autocrop.setObjectName(u"twotime_autocrop")
        self.twotime_autocrop.setChecked(True)

        self.gridLayout_2.addWidget(self.twotime_autocrop, 0, 14, 1, 1)

        self.twotime_autorotate = QCheckBox(self.groupBox_11)
        self.twotime_autorotate.setObjectName(u"twotime_autorotate")
        self.twotime_autorotate.setChecked(True)

        self.gridLayout_2.addWidget(self.twotime_autorotate, 0, 13, 1, 1)

        self.twotime_showbox = QCheckBox(self.groupBox_11)
        self.twotime_showbox.setObjectName(u"twotime_showbox")

        self.gridLayout_2.addWidget(self.twotime_showbox, 1, 0, 1, 3)

        self.cb_twotime_saxs_cmap = QComboBox(self.groupBox_11)
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.setObjectName(u"cb_twotime_saxs_cmap")

        self.gridLayout_2.addWidget(self.cb_twotime_saxs_cmap, 0, 5, 1, 3)

        self.cb_twotime_cmap = QComboBox(self.groupBox_11)
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.setObjectName(u"cb_twotime_cmap")
        sizePolicy9.setHeightForWidth(self.cb_twotime_cmap.sizePolicy().hasHeightForWidth())
        self.cb_twotime_cmap.setSizePolicy(sizePolicy9)
        self.cb_twotime_cmap.setMinimumSize(QSize(0, 0))

        self.gridLayout_2.addWidget(self.cb_twotime_cmap, 1, 5, 1, 3)

        self.twotime_correct_diag = QCheckBox(self.groupBox_11)
        self.twotime_correct_diag.setObjectName(u"twotime_correct_diag")

        self.gridLayout_2.addWidget(self.twotime_correct_diag, 0, 8, 1, 3)

        self.label_57 = QLabel(self.groupBox_11)
        self.label_57.setObjectName(u"label_57")

        self.gridLayout_2.addWidget(self.label_57, 1, 8, 1, 3)


        self.gridLayout_37.addLayout(self.gridLayout_2, 0, 1, 1, 1)

        self.horizontalSpacer_10 = QSpacerItem(278, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_37.addItem(self.horizontalSpacer_10, 0, 3, 1, 1)


        self.gridLayout_33.addWidget(self.groupBox_11, 2, 0, 1, 1)

        self.mp_2t_map = GraphicsLayoutWidget(self.tab_8)
        self.mp_2t_map.setObjectName(u"mp_2t_map")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(1)
        sizePolicy11.setHeightForWidth(self.mp_2t_map.sizePolicy().hasHeightForWidth())
        self.mp_2t_map.setSizePolicy(sizePolicy11)
        self.mp_2t_map.setMinimumSize(QSize(300, 100))

        self.gridLayout_33.addWidget(self.mp_2t_map, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_8, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayout_36 = QGridLayout(self.tab_5)
        self.gridLayout_36.setObjectName(u"gridLayout_36")
        self.groupBox_10 = QGroupBox(self.tab_5)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.gridLayout_31 = QGridLayout(self.groupBox_10)
        self.gridLayout_31.setObjectName(u"gridLayout_31")
        self.mp_avg_g2 = PlotWidgetDev(self.groupBox_10)
        self.mp_avg_g2.setObjectName(u"mp_avg_g2")
        sizePolicy1.setHeightForWidth(self.mp_avg_g2.sizePolicy().hasHeightForWidth())
        self.mp_avg_g2.setSizePolicy(sizePolicy1)
        self.mp_avg_g2.setMinimumSize(QSize(0, 300))

        self.gridLayout_31.addWidget(self.mp_avg_g2, 0, 0, 1, 1)


        self.gridLayout_36.addWidget(self.groupBox_10, 0, 0, 1, 3)

        self.groupBox_8 = QGroupBox(self.tab_5)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.gridLayout_30 = QGridLayout(self.groupBox_8)
        self.gridLayout_30.setObjectName(u"gridLayout_30")
        self.gridLayout_28 = QGridLayout()
        self.gridLayout_28.setObjectName(u"gridLayout_28")
        self.max_thread_count = QSpinBox(self.groupBox_8)
        self.max_thread_count.setObjectName(u"max_thread_count")
        self.max_thread_count.setMinimum(1)
        self.max_thread_count.setMaximum(32)
        self.max_thread_count.setSingleStep(1)
        self.max_thread_count.setValue(4)

        self.gridLayout_28.addWidget(self.max_thread_count, 0, 5, 1, 2)

        self.avg_blmax = QDoubleSpinBox(self.groupBox_8)
        self.avg_blmax.setObjectName(u"avg_blmax")
        self.avg_blmax.setDecimals(3)
        self.avg_blmax.setMinimum(0.900000000000000)
        self.avg_blmax.setMaximum(10.000000000000000)
        self.avg_blmax.setSingleStep(0.010000000000000)
        self.avg_blmax.setValue(1.050000000000000)

        self.gridLayout_28.addWidget(self.avg_blmax, 2, 5, 1, 2)

        self.avg_save_path = QLineEdit(self.groupBox_8)
        self.avg_save_path.setObjectName(u"avg_save_path")
        self.avg_save_path.setClearButtonEnabled(True)

        self.gridLayout_28.addWidget(self.avg_save_path, 6, 2, 1, 4)

        self.label_39 = QLabel(self.groupBox_8)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout_28.addWidget(self.label_39, 2, 4, 1, 1)

        self.btn_set_average_save_name = QPushButton(self.groupBox_8)
        self.btn_set_average_save_name.setObjectName(u"btn_set_average_save_name")
        self.btn_set_average_save_name.setMinimumSize(QSize(10, 0))

        self.gridLayout_28.addWidget(self.btn_set_average_save_name, 7, 6, 1, 1)

        self.label_17 = QLabel(self.groupBox_8)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_28.addWidget(self.label_17, 0, 0, 1, 2)

        self.label_32 = QLabel(self.groupBox_8)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_28.addWidget(self.label_32, 1, 0, 1, 1)

        self.label_25 = QLabel(self.groupBox_8)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_28.addWidget(self.label_25, 2, 0, 1, 1)

        self.label_19 = QLabel(self.groupBox_8)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_28.addWidget(self.label_19, 7, 0, 1, 2)

        self.bx_avg_G2IPIF = QCheckBox(self.groupBox_8)
        self.bx_avg_G2IPIF.setObjectName(u"bx_avg_G2IPIF")

        self.gridLayout_28.addWidget(self.bx_avg_G2IPIF, 3, 5, 3, 2)

        self.avg_window = QSpinBox(self.groupBox_8)
        self.avg_window.setObjectName(u"avg_window")
        self.avg_window.setMinimum(1)
        self.avg_window.setValue(10)

        self.gridLayout_28.addWidget(self.avg_window, 1, 5, 1, 2)

        self.bx_avg_g2g2err = QCheckBox(self.groupBox_8)
        self.bx_avg_g2g2err.setObjectName(u"bx_avg_g2g2err")
        self.bx_avg_g2g2err.setChecked(True)

        self.gridLayout_28.addWidget(self.bx_avg_g2g2err, 3, 4, 3, 1)

        self.avg_save_name = QLineEdit(self.groupBox_8)
        self.avg_save_name.setObjectName(u"avg_save_name")
        self.avg_save_name.setClearButtonEnabled(True)

        self.gridLayout_28.addWidget(self.avg_save_name, 7, 2, 1, 4)

        self.label_20 = QLabel(self.groupBox_8)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_28.addWidget(self.label_20, 6, 0, 1, 2)

        self.btn_set_average_save_path = QPushButton(self.groupBox_8)
        self.btn_set_average_save_path.setObjectName(u"btn_set_average_save_path")
        self.btn_set_average_save_path.setMinimumSize(QSize(10, 0))

        self.gridLayout_28.addWidget(self.btn_set_average_save_path, 6, 6, 1, 1)

        self.bx_avg_saxs = QCheckBox(self.groupBox_8)
        self.bx_avg_saxs.setObjectName(u"bx_avg_saxs")
        self.bx_avg_saxs.setChecked(True)

        self.gridLayout_28.addWidget(self.bx_avg_saxs, 3, 3, 3, 1)

        self.label_26 = QLabel(self.groupBox_8)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout_28.addWidget(self.label_26, 3, 0, 3, 3)

        self.label_33 = QLabel(self.groupBox_8)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_28.addWidget(self.label_33, 1, 4, 1, 1)

        self.label_40 = QLabel(self.groupBox_8)
        self.label_40.setObjectName(u"label_40")

        self.gridLayout_28.addWidget(self.label_40, 0, 4, 1, 1)

        self.cb_avg_chunk_size = QComboBox(self.groupBox_8)
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.setObjectName(u"cb_avg_chunk_size")
        self.cb_avg_chunk_size.setMaximumSize(QSize(80, 16777215))

        self.gridLayout_28.addWidget(self.cb_avg_chunk_size, 0, 2, 1, 2)

        self.avg_qindex = QSpinBox(self.groupBox_8)
        self.avg_qindex.setObjectName(u"avg_qindex")
        self.avg_qindex.setMaximum(999)
        self.avg_qindex.setValue(5)

        self.gridLayout_28.addWidget(self.avg_qindex, 1, 1, 1, 3)

        self.avg_blmin = QDoubleSpinBox(self.groupBox_8)
        self.avg_blmin.setObjectName(u"avg_blmin")
        self.avg_blmin.setDecimals(3)
        self.avg_blmin.setMaximum(10.000000000000000)
        self.avg_blmin.setSingleStep(0.010000000000000)
        self.avg_blmin.setValue(0.950000000000000)

        self.gridLayout_28.addWidget(self.avg_blmin, 2, 1, 1, 3)


        self.gridLayout_30.addLayout(self.gridLayout_28, 0, 0, 1, 1)


        self.gridLayout_36.addWidget(self.groupBox_8, 1, 0, 1, 1)

        self.groupBox_12 = QGroupBox(self.tab_5)
        self.groupBox_12.setObjectName(u"groupBox_12")
        sizePolicy12 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy12.setHorizontalStretch(0)
        sizePolicy12.setVerticalStretch(0)
        sizePolicy12.setHeightForWidth(self.groupBox_12.sizePolicy().hasHeightForWidth())
        self.groupBox_12.setSizePolicy(sizePolicy12)
        self.gridLayout_35 = QGridLayout(self.groupBox_12)
        self.gridLayout_35.setObjectName(u"gridLayout_35")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.btn_submit_job = QPushButton(self.groupBox_12)
        self.btn_submit_job.setObjectName(u"btn_submit_job")
        sizePolicy7.setHeightForWidth(self.btn_submit_job.sizePolicy().hasHeightForWidth())
        self.btn_submit_job.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_submit_job)

        self.avg_job_pop = QPushButton(self.groupBox_12)
        self.avg_job_pop.setObjectName(u"avg_job_pop")
        sizePolicy7.setHeightForWidth(self.avg_job_pop.sizePolicy().hasHeightForWidth())
        self.avg_job_pop.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.avg_job_pop)

        self.btn_avg_jobinfo = QPushButton(self.groupBox_12)
        self.btn_avg_jobinfo.setObjectName(u"btn_avg_jobinfo")
        sizePolicy7.setHeightForWidth(self.btn_avg_jobinfo.sizePolicy().hasHeightForWidth())
        self.btn_avg_jobinfo.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_avg_jobinfo)

        self.btn_avg_kill = QPushButton(self.groupBox_12)
        self.btn_avg_kill.setObjectName(u"btn_avg_kill")

        self.verticalLayout_3.addWidget(self.btn_avg_kill)

        self.btn_start_avg_job = QPushButton(self.groupBox_12)
        self.btn_start_avg_job.setObjectName(u"btn_start_avg_job")
        sizePolicy7.setHeightForWidth(self.btn_start_avg_job.sizePolicy().hasHeightForWidth())
        self.btn_start_avg_job.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_start_avg_job)


        self.gridLayout_35.addLayout(self.verticalLayout_3, 0, 0, 1, 1)


        self.gridLayout_36.addWidget(self.groupBox_12, 1, 1, 1, 1)

        self.groupBox_9 = QGroupBox(self.tab_5)
        self.groupBox_9.setObjectName(u"groupBox_9")
        sizePolicy5.setHeightForWidth(self.groupBox_9.sizePolicy().hasHeightForWidth())
        self.groupBox_9.setSizePolicy(sizePolicy5)
        self.gridLayout_29 = QGridLayout(self.groupBox_9)
        self.gridLayout_29.setObjectName(u"gridLayout_29")
        self.avg_job_table = QTableView(self.groupBox_9)
        self.avg_job_table.setObjectName(u"avg_job_table")
        sizePolicy5.setHeightForWidth(self.avg_job_table.sizePolicy().hasHeightForWidth())
        self.avg_job_table.setSizePolicy(sizePolicy5)
        self.avg_job_table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.avg_job_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.avg_job_table.horizontalHeader().setMinimumSectionSize(19)
        self.avg_job_table.horizontalHeader().setDefaultSectionSize(100)
        self.avg_job_table.horizontalHeader().setStretchLastSection(True)
        self.avg_job_table.verticalHeader().setDefaultSectionSize(30)

        self.gridLayout_29.addWidget(self.avg_job_table, 0, 0, 1, 2)


        self.gridLayout_36.addWidget(self.groupBox_9, 1, 2, 1, 1)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.gridLayout_7 = QGridLayout(self.tab_9)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.hdf_info = ParameterTree(self.tab_9)
        self.hdf_info.setObjectName(u"hdf_info")
        sizePolicy13 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy13.setHorizontalStretch(1)
        sizePolicy13.setVerticalStretch(1)
        sizePolicy13.setHeightForWidth(self.hdf_info.sizePolicy().hasHeightForWidth())
        self.hdf_info.setSizePolicy(sizePolicy13)

        self.gridLayout_7.addWidget(self.hdf_info, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_9, "")
        self.splitter_3.addWidget(self.tabWidget)

        self.gridLayout.addWidget(self.splitter_3, 0, 0, 1, 1)

        mainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(mainWindow)
        self.statusbar.setObjectName(u"statusbar")
        mainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.cb_saxs2D_cmap, self.g2_c2min)
        QWidget.setTabOrder(self.g2_c2min, self.cb_avg_chunk_size)
        QWidget.setTabOrder(self.cb_avg_chunk_size, self.list_view_target)
        QWidget.setTabOrder(self.list_view_target, self.max_thread_count)
        QWidget.setTabOrder(self.max_thread_count, self.avg_qindex)
        QWidget.setTabOrder(self.avg_qindex, self.avg_window)
        QWidget.setTabOrder(self.avg_window, self.avg_blmin)
        QWidget.setTabOrder(self.avg_blmin, self.avg_blmax)
        QWidget.setTabOrder(self.avg_blmax, self.bx_avg_saxs)
        QWidget.setTabOrder(self.bx_avg_saxs, self.bx_avg_g2g2err)
        QWidget.setTabOrder(self.bx_avg_g2g2err, self.bx_avg_G2IPIF)
        QWidget.setTabOrder(self.bx_avg_G2IPIF, self.avg_save_path)
        QWidget.setTabOrder(self.avg_save_path, self.btn_set_average_save_path)
        QWidget.setTabOrder(self.btn_set_average_save_path, self.avg_save_name)
        QWidget.setTabOrder(self.avg_save_name, self.btn_set_average_save_name)
        QWidget.setTabOrder(self.btn_set_average_save_name, self.btn_submit_job)
        QWidget.setTabOrder(self.btn_submit_job, self.avg_job_pop)
        QWidget.setTabOrder(self.avg_job_pop, self.btn_avg_jobinfo)
        QWidget.setTabOrder(self.btn_avg_jobinfo, self.btn_avg_kill)
        QWidget.setTabOrder(self.btn_avg_kill, self.btn_start_avg_job)
        QWidget.setTabOrder(self.btn_start_avg_job, self.avg_job_table)
        QWidget.setTabOrder(self.avg_job_table, self.work_dir)
        QWidget.setTabOrder(self.work_dir, self.sort_method)
        QWidget.setTabOrder(self.sort_method, self.pushButton_11)
        QWidget.setTabOrder(self.pushButton_11, self.pushButton)
        QWidget.setTabOrder(self.pushButton, self.list_view_source)
        QWidget.setTabOrder(self.list_view_source, self.filter_type)
        QWidget.setTabOrder(self.filter_type, self.filter_str)
        QWidget.setTabOrder(self.filter_str, self.pushButton_2)
        QWidget.setTabOrder(self.pushButton_2, self.pushButton_3)
        QWidget.setTabOrder(self.pushButton_3, self.btn_deselect)
        QWidget.setTabOrder(self.btn_deselect, self.btn_up)
        QWidget.setTabOrder(self.btn_up, self.btn_down)
        QWidget.setTabOrder(self.btn_down, self.cb_saxs2D_type)
        QWidget.setTabOrder(self.cb_saxs2D_type, self.saxs2d_rotate)
        QWidget.setTabOrder(self.saxs2d_rotate, self.pushButton_5)
        QWidget.setTabOrder(self.pushButton_5, self.cb_saxs_type)
        QWidget.setTabOrder(self.cb_saxs_type, self.saxs1d_sampling)
        QWidget.setTabOrder(self.saxs1d_sampling, self.sb_saxs_offset)
        QWidget.setTabOrder(self.sb_saxs_offset, self.cb_saxs_norm)
        QWidget.setTabOrder(self.cb_saxs_norm, self.saxs1d_lb_type)
        QWidget.setTabOrder(self.saxs1d_lb_type, self.g2_show_label)
        QWidget.setTabOrder(self.g2_show_label, self.saxs1d_qmin)
        QWidget.setTabOrder(self.saxs1d_qmin, self.saxs1d_qmax)
        QWidget.setTabOrder(self.saxs1d_qmax, self.sb_saxs_marker_size)
        QWidget.setTabOrder(self.sb_saxs_marker_size, self.saxs1d_legend_loc)
        QWidget.setTabOrder(self.saxs1d_legend_loc, self.cb_stab_type)
        QWidget.setTabOrder(self.cb_stab_type, self.sb_stab_offset)
        QWidget.setTabOrder(self.sb_stab_offset, self.cb_stab_norm)
        QWidget.setTabOrder(self.cb_stab_norm, self.cb_stab)
        QWidget.setTabOrder(self.cb_stab, self.pushButton_7)
        QWidget.setTabOrder(self.pushButton_7, self.sb_intt_max)
        QWidget.setTabOrder(self.sb_intt_max, self.sb_window)
        QWidget.setTabOrder(self.sb_window, self.sb_intt_sampling)
        QWidget.setTabOrder(self.sb_intt_sampling, self.intt_xlabel)
        QWidget.setTabOrder(self.intt_xlabel, self.btn_intt)
        QWidget.setTabOrder(self.btn_intt, self.pushButton_4)
        QWidget.setTabOrder(self.pushButton_4, self.g2_plot_type)
        QWidget.setTabOrder(self.g2_plot_type, self.g2_qmin)
        QWidget.setTabOrder(self.g2_qmin, self.g2_qmax)
        QWidget.setTabOrder(self.g2_qmax, self.g2_tmin)
        QWidget.setTabOrder(self.g2_tmin, self.g2_tmax)
        QWidget.setTabOrder(self.g2_tmax, self.g2_ymin)
        QWidget.setTabOrder(self.g2_ymin, self.g2_ymax)
        QWidget.setTabOrder(self.g2_ymax, self.g2_yauto)
        QWidget.setTabOrder(self.g2_yauto, self.tabWidget)
        QWidget.setTabOrder(self.tabWidget, self.g2_amin)
        QWidget.setTabOrder(self.g2_amin, self.g2_amax)
        QWidget.setTabOrder(self.g2_amax, self.g2_afit)
        QWidget.setTabOrder(self.g2_afit, self.g2_bmin)
        QWidget.setTabOrder(self.g2_bmin, self.g2_bmax)
        QWidget.setTabOrder(self.g2_bmax, self.g2_bfit)
        QWidget.setTabOrder(self.g2_bfit, self.g2_cmin)
        QWidget.setTabOrder(self.g2_cmin, self.g2_cmax)
        QWidget.setTabOrder(self.g2_cmax, self.g2_cfit)
        QWidget.setTabOrder(self.g2_cfit, self.g2_dmin)
        QWidget.setTabOrder(self.g2_dmin, self.g2_dmax)
        QWidget.setTabOrder(self.g2_dmax, self.g2_dfit)
        QWidget.setTabOrder(self.g2_dfit, self.g2_show_fit)
        QWidget.setTabOrder(self.g2_show_fit, self.tauq_amin)
        QWidget.setTabOrder(self.tauq_amin, self.tauq_amax)
        QWidget.setTabOrder(self.tauq_amax, self.tauq_afit)
        QWidget.setTabOrder(self.tauq_afit, self.sb_g2_column)
        QWidget.setTabOrder(self.sb_g2_column, self.g2_sub_baseline)
        QWidget.setTabOrder(self.g2_sub_baseline, self.tauq_bmin)
        QWidget.setTabOrder(self.tauq_bmin, self.tauq_bmax)
        QWidget.setTabOrder(self.tauq_bmax, self.tauq_bfit)
        QWidget.setTabOrder(self.tauq_bfit, self.tauq_qmin)
        QWidget.setTabOrder(self.tauq_qmin, self.tauq_qmax)
        QWidget.setTabOrder(self.tauq_qmax, self.pushButton_8)
        QWidget.setTabOrder(self.pushButton_8, self.g2_c2max)
        QWidget.setTabOrder(self.g2_c2max, self.g2_b2fit)
        QWidget.setTabOrder(self.g2_b2fit, self.cb_tauq_type)
        QWidget.setTabOrder(self.cb_tauq_type, self.sb_tauq_offset)
        QWidget.setTabOrder(self.sb_tauq_offset, self.g2_b2max)
        QWidget.setTabOrder(self.g2_b2max, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.g2_marker_size)
        QWidget.setTabOrder(self.g2_marker_size, self.saxs2d_display)
        QWidget.setTabOrder(self.saxs2d_display, self.cb_twotime_type)
        QWidget.setTabOrder(self.cb_twotime_type, self.cb_twotime_saxs_cmap)
        QWidget.setTabOrder(self.cb_twotime_saxs_cmap, self.g2_c2fit)
        QWidget.setTabOrder(self.g2_c2fit, self.g2_fmin)
        QWidget.setTabOrder(self.g2_fmin, self.g2_fmax)
        QWidget.setTabOrder(self.g2_fmax, self.g2_ffit)
        QWidget.setTabOrder(self.g2_ffit, self.show_g2_fit_summary)
        QWidget.setTabOrder(self.show_g2_fit_summary, self.btn_g2_export)
        QWidget.setTabOrder(self.btn_g2_export, self.btn_g2_refit)
        QWidget.setTabOrder(self.btn_g2_refit, self.sb_g2_offset)
        QWidget.setTabOrder(self.sb_g2_offset, self.g2_b2min)
        QWidget.setTabOrder(self.g2_b2min, self.g2_fitting_function)

        self.retranslateUi(mainWindow)
        self.pushButton_4.clicked.connect(mainWindow.plot_g2)
        self.sb_window.valueChanged.connect(self.btn_intt.click)
        self.sb_intt_sampling.valueChanged.connect(self.btn_intt.click)
        self.sb_stab_offset.valueChanged.connect(self.pushButton_7.click)
        self.pushButton_3.clicked.connect(mainWindow.remove_target)
        self.cb_stab.currentIndexChanged.connect(self.pushButton_7.click)
        self.cb_saxs2D_type.currentIndexChanged.connect(self.pushButton_5.click)
        self.pushButton_8.clicked.connect(mainWindow.plot_tauq)
        self.cb_stab_type.currentIndexChanged.connect(self.pushButton_7.click)
        self.sb_saxs_offset.valueChanged.connect(self.pushButton_10.click)
        self.pushButton.clicked.connect(mainWindow.load_path)
        self.cb_saxs2D_cmap.currentIndexChanged.connect(self.pushButton_5.click)
        self.pushButton_2.clicked.connect(mainWindow.add_target)
        self.cb_saxs_norm.currentIndexChanged.connect(self.pushButton_10.click)
        self.saxs2d_rotate.stateChanged.connect(self.pushButton_5.click)
        self.intt_xlabel.currentIndexChanged.connect(self.btn_intt.click)
        self.pushButton_11.clicked.connect(mainWindow.reload_source)
        self.cb_saxs_type.currentIndexChanged.connect(self.pushButton_10.click)
        self.cb_stab_norm.currentIndexChanged.connect(self.pushButton_7.click)
        self.pushButton_12.clicked["bool"].connect(mainWindow.plot_twotime)
        self.sb_intt_max.valueChanged.connect(self.btn_intt.click)
        self.cb_twotime_cmap.currentIndexChanged.connect(mainWindow.plot_twotime)
        self.filter_str.returnPressed.connect(self.pushButton_2.click)
        self.sb_g2_column.editingFinished.connect(self.pushButton_4.click)
        self.sb_g2_offset.editingFinished.connect(self.pushButton_4.click)
        self.g2_show_label.stateChanged.connect(self.pushButton_4.click)
        self.g2_show_fit.stateChanged.connect(self.pushButton_4.click)
        self.g2_plot_type.currentIndexChanged.connect(self.pushButton_4.click)
        self.tauq_afit.toggled.connect(self.tauq_amin.setEnabled)
        self.tauq_bfit.toggled.connect(self.tauq_bmin.setEnabled)
        self.cb_tauq_type.currentIndexChanged.connect(self.pushButton_8.click)
        self.sb_tauq_offset.editingFinished.connect(self.pushButton_8.click)
        self.saxs1d_qmin.valueChanged.connect(self.pushButton_10.click)
        self.saxs1d_qmax.valueChanged.connect(self.pushButton_10.click)
        self.g2_show_fit.toggled.connect(self.g2_sub_baseline.setEnabled)
        self.g2_sub_baseline.stateChanged.connect(self.pushButton_4.click)
        self.saxs1d_legend_loc.currentIndexChanged.connect(self.pushButton_10.click)
        self.box_target.clicked.connect(self.list_view_target.clearSelection)
        self.sb_saxs_marker_size.valueChanged.connect(self.pushButton_10.click)
        self.saxs1d_sampling.valueChanged.connect(self.pushButton_10.click)
        self.g2_afit.toggled.connect(self.g2_amin.setEnabled)
        self.g2_bfit.toggled.connect(self.g2_bmin.setEnabled)
        self.g2_cfit.toggled.connect(self.g2_cmin.setEnabled)
        self.g2_dfit.toggled.connect(self.g2_dmin.setEnabled)
        self.g2_b2fit.toggled.connect(self.g2_b2min.setEnabled)
        self.g2_c2fit.toggled.connect(self.g2_c2min.setEnabled)
        self.g2_ffit.toggled.connect(self.g2_fmin.setEnabled)
        self.box_all_phi.stateChanged.connect(self.pushButton_10.click)
        self.saxs1d_lb_type.currentIndexChanged.connect(self.pushButton_10.click)
        self.cb_sub_bkg.toggled.connect(self.le_bkg_fname.setEnabled)
        self.cb_sub_bkg.toggled.connect(self.btn_select_bkgfile.setEnabled)
        self.cb_sub_bkg.toggled.connect(self.bkg_weight.setEnabled)
        self.box_show_phi_roi.toggled.connect(self.box_show_roi.setDisabled)
        self.box_show_phi_roi.toggled.connect(self.box_all_phi.setDisabled)
        self.filter_str.textChanged.connect(mainWindow.apply_filter_to_source)

        self.tabWidget.setCurrentIndex(0)
        self.cb_saxs_type.setCurrentIndex(3)
        self.cb_stab_type.setCurrentIndex(3)
        self.cb_stab_norm.setCurrentIndex(0)
        self.cb_tauq_type.setCurrentIndex(3)
        self.cb_avg_chunk_size.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(mainWindow)
    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(QCoreApplication.translate("mainWindow", u"pyXPCSViewer", None))
        self.label_2.setText(QCoreApplication.translate("mainWindow", u"Path:", None))
        self.label_56.setText(QCoreApplication.translate("mainWindow", u"Sort:", None))
        self.sort_method.setItemText(0, QCoreApplication.translate("mainWindow", u"Filename", None))
        self.sort_method.setItemText(1, QCoreApplication.translate("mainWindow", u"Filename-reverse", None))
        self.sort_method.setItemText(2, QCoreApplication.translate("mainWindow", u"Index", None))
        self.sort_method.setItemText(3, QCoreApplication.translate("mainWindow", u"Index-reverse", None))
        self.sort_method.setItemText(4, QCoreApplication.translate("mainWindow", u"Time", None))
        self.sort_method.setItemText(5, QCoreApplication.translate("mainWindow", u"Time-reverse", None))

        self.pushButton_11.setText(QCoreApplication.translate("mainWindow", u"reload", None))
        self.pushButton.setText(QCoreApplication.translate("mainWindow", u"browse", None))
        self.box_source.setTitle(QCoreApplication.translate("mainWindow", u"Source:", None))
        self.filter_type.setItemText(0, QCoreApplication.translate("mainWindow", u"prefix is", None))
        self.filter_type.setItemText(1, QCoreApplication.translate("mainWindow", u"contains", None))

        self.filter_str.setPlaceholderText(QCoreApplication.translate("mainWindow", u"filter, press enter to add files", None))
        self.pushButton_2.setText(QCoreApplication.translate("mainWindow", u"add", None))
        self.pushButton_3.setText(QCoreApplication.translate("mainWindow", u"remove", None))
        self.box_target.setTitle(QCoreApplication.translate("mainWindow", u"Target:", None))
        self.btn_deselect.setText(QCoreApplication.translate("mainWindow", u"de-select", None))
        self.btn_up.setText(QCoreApplication.translate("mainWindow", u"up", None))
        self.btn_down.setText(QCoreApplication.translate("mainWindow", u"down", None))
        self.label_38.setText(QCoreApplication.translate("mainWindow", u"coordinates:", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("mainWindow", u"SAXS 2D Plot Setting", None))
        self.cb_saxs2D_cmap.setItemText(0, QCoreApplication.translate("mainWindow", u"jet", None))
        self.cb_saxs2D_cmap.setItemText(1, QCoreApplication.translate("mainWindow", u"hot", None))
        self.cb_saxs2D_cmap.setItemText(2, QCoreApplication.translate("mainWindow", u"plasma", None))
        self.cb_saxs2D_cmap.setItemText(3, QCoreApplication.translate("mainWindow", u"viridis", None))
        self.cb_saxs2D_cmap.setItemText(4, QCoreApplication.translate("mainWindow", u"magma", None))
        self.cb_saxs2D_cmap.setItemText(5, QCoreApplication.translate("mainWindow", u"gray", None))

        self.cb_saxs2D_type.setItemText(0, QCoreApplication.translate("mainWindow", u"log", None))
        self.cb_saxs2D_type.setItemText(1, QCoreApplication.translate("mainWindow", u"linear", None))

        self.label_51.setText(QCoreApplication.translate("mainWindow", u"max:", None))
        self.label_50.setText(QCoreApplication.translate("mainWindow", u"min:", None))
        self.label_13.setText(QCoreApplication.translate("mainWindow", u"cmap:", None))
        self.label_12.setText(QCoreApplication.translate("mainWindow", u"type:", None))
        self.saxs2d_rotate.setText(QCoreApplication.translate("mainWindow", u"rotate", None))
        self.saxs2d_autorange.setText(QCoreApplication.translate("mainWindow", u"auto-range", None))
        self.pushButton_5.setText(QCoreApplication.translate("mainWindow", u"Plot 2D SAXS", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("mainWindow", u"ROI", None))
        self.label_58.setText(QCoreApplication.translate("mainWindow", u"type:", None))
        self.cb_saxs2D_roi_type.setItemText(0, QCoreApplication.translate("mainWindow", u"Q-Wedge", None))
        self.cb_saxs2D_roi_type.setItemText(1, QCoreApplication.translate("mainWindow", u"Phi-Ring", None))

        self.label_60.setText(QCoreApplication.translate("mainWindow", u"color:", None))
        self.cb_saxs2D_roi_color.setItemText(0, QCoreApplication.translate("mainWindow", u"green", None))
        self.cb_saxs2D_roi_color.setItemText(1, QCoreApplication.translate("mainWindow", u"yellow", None))
        self.cb_saxs2D_roi_color.setItemText(2, QCoreApplication.translate("mainWindow", u"blue", None))
        self.cb_saxs2D_roi_color.setItemText(3, QCoreApplication.translate("mainWindow", u"red", None))
        self.cb_saxs2D_roi_color.setItemText(4, QCoreApplication.translate("mainWindow", u"cyan", None))
        self.cb_saxs2D_roi_color.setItemText(5, QCoreApplication.translate("mainWindow", u"magenta", None))
        self.cb_saxs2D_roi_color.setItemText(6, QCoreApplication.translate("mainWindow", u"black", None))
        self.cb_saxs2D_roi_color.setItemText(7, QCoreApplication.translate("mainWindow", u"white", None))

        self.label_61.setText(QCoreApplication.translate("mainWindow", u"linewidth:", None))
        self.btn_saxs2d_roi_add.setText(QCoreApplication.translate("mainWindow", u"Add", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab1_1), QCoreApplication.translate("mainWindow", u"SAXS-2D", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("mainWindow", u"SAXS 1D Plot Setting", None))
        self.groupBox_14.setTitle(QCoreApplication.translate("mainWindow", u"Background", None))
        self.cb_sub_bkg.setText(QCoreApplication.translate("mainWindow", u"subtract background", None))
        self.btn_select_bkgfile.setText(QCoreApplication.translate("mainWindow", u"select", None))
        self.label_59.setText(QCoreApplication.translate("mainWindow", u"weight", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("mainWindow", u"Display", None))
        self.box_show_roi.setText(QCoreApplication.translate("mainWindow", u"q-I_ROIs", None))
#if QT_CONFIG(tooltip)
        self.box_all_phi.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>show saxs_1d lines for  all phi partitions.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.box_all_phi.setText(QCoreApplication.translate("mainWindow", u"q-I_Phi", None))
        self.box_show_phi_roi.setText(QCoreApplication.translate("mainWindow", u"phi-I ROIs", None))
        self.btn_export_saxs1d.setText(QCoreApplication.translate("mainWindow", u"Export profiles", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("mainWindow", u"Basic", None))
        self.label_21.setText(QCoreApplication.translate("mainWindow", u"type:", None))
        self.cb_saxs_type.setItemText(0, QCoreApplication.translate("mainWindow", u"I - q", None))
        self.cb_saxs_type.setItemText(1, QCoreApplication.translate("mainWindow", u"I - log(q)", None))
        self.cb_saxs_type.setItemText(2, QCoreApplication.translate("mainWindow", u"log(I) - q", None))
        self.cb_saxs_type.setItemText(3, QCoreApplication.translate("mainWindow", u"log(I) - log(q)", None))

        self.label_55.setText(QCoreApplication.translate("mainWindow", u"sampling:", None))
        self.label_22.setText(QCoreApplication.translate("mainWindow", u"offset:", None))
        self.label_23.setText(QCoreApplication.translate("mainWindow", u"normalization:", None))
        self.cb_saxs_norm.setItemText(0, QCoreApplication.translate("mainWindow", u"none", None))
        self.cb_saxs_norm.setItemText(1, QCoreApplication.translate("mainWindow", u"I' = Iq2", None))
        self.cb_saxs_norm.setItemText(2, QCoreApplication.translate("mainWindow", u"I' = Iq4", None))
        self.cb_saxs_norm.setItemText(3, QCoreApplication.translate("mainWindow", u"I' = I/Io", None))

        self.saxs1d_lb_type.setItemText(0, QCoreApplication.translate("mainWindow", u"no drawing", None))
        self.saxs1d_lb_type.setItemText(1, QCoreApplication.translate("mainWindow", u"slope drawing", None))
        self.saxs1d_lb_type.setItemText(2, QCoreApplication.translate("mainWindow", u"horizontal line", None))

        self.label_49.setText(QCoreApplication.translate("mainWindow", u"q range (\u00c5\u207b\u00b9)", None))
        self.label_54.setText(QCoreApplication.translate("mainWindow", u"marker_size:", None))
        self.label_52.setText(QCoreApplication.translate("mainWindow", u"legend loc:", None))
        self.saxs1d_legend_loc.setItemText(0, QCoreApplication.translate("mainWindow", u"best", None))
        self.saxs1d_legend_loc.setItemText(1, QCoreApplication.translate("mainWindow", u"outside", None))
        self.saxs1d_legend_loc.setItemText(2, QCoreApplication.translate("mainWindow", u"upper right", None))
        self.saxs1d_legend_loc.setItemText(3, QCoreApplication.translate("mainWindow", u"upper left", None))
        self.saxs1d_legend_loc.setItemText(4, QCoreApplication.translate("mainWindow", u"lower left", None))
        self.saxs1d_legend_loc.setItemText(5, QCoreApplication.translate("mainWindow", u"lower right", None))
        self.saxs1d_legend_loc.setItemText(6, QCoreApplication.translate("mainWindow", u"right", None))
        self.saxs1d_legend_loc.setItemText(7, QCoreApplication.translate("mainWindow", u"center left", None))
        self.saxs1d_legend_loc.setItemText(8, QCoreApplication.translate("mainWindow", u"center right", None))
        self.saxs1d_legend_loc.setItemText(9, QCoreApplication.translate("mainWindow", u"lower center", None))
        self.saxs1d_legend_loc.setItemText(10, QCoreApplication.translate("mainWindow", u"upper center", None))
        self.saxs1d_legend_loc.setItemText(11, QCoreApplication.translate("mainWindow", u"center", None))

        self.cbox_use_abs.setText(QCoreApplication.translate("mainWindow", u"using absolute cross section", None))
        self.pushButton_10.setText(QCoreApplication.translate("mainWindow", u"Plot", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("mainWindow", u"SAXS-1D", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("mainWindow", u"Stability Plot Setting", None))
        self.label_14.setText(QCoreApplication.translate("mainWindow", u"type:", None))
        self.cb_stab_type.setItemText(0, QCoreApplication.translate("mainWindow", u"I - q", None))
        self.cb_stab_type.setItemText(1, QCoreApplication.translate("mainWindow", u"I - log(q)", None))
        self.cb_stab_type.setItemText(2, QCoreApplication.translate("mainWindow", u"log(I) - q", None))
        self.cb_stab_type.setItemText(3, QCoreApplication.translate("mainWindow", u"log(I) - log(q)", None))

        self.label_24.setText(QCoreApplication.translate("mainWindow", u"offset:", None))
        self.label_16.setText(QCoreApplication.translate("mainWindow", u"normalization:", None))
        self.pushButton_7.setText(QCoreApplication.translate("mainWindow", u"Plot Iq Stability Data", None))
        self.cb_stab_norm.setItemText(0, QCoreApplication.translate("mainWindow", u"none", None))
        self.cb_stab_norm.setItemText(1, QCoreApplication.translate("mainWindow", u"I' = Iq2", None))
        self.cb_stab_norm.setItemText(2, QCoreApplication.translate("mainWindow", u"I' = Iq4", None))
        self.cb_stab_norm.setItemText(3, QCoreApplication.translate("mainWindow", u"I' = I/Io", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("mainWindow", u"Stability", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("mainWindow", u"Intensity-Time Plot Setting", None))
        self.label_9.setText(QCoreApplication.translate("mainWindow", u"max datasets:", None))
        self.label_31.setText(QCoreApplication.translate("mainWindow", u"moving average:", None))
        self.label_11.setText(QCoreApplication.translate("mainWindow", u"sampling:", None))
        self.label_34.setText(QCoreApplication.translate("mainWindow", u"xlabel:", None))
        self.intt_xlabel.setItemText(0, QCoreApplication.translate("mainWindow", u"Time (second)", None))
        self.intt_xlabel.setItemText(1, QCoreApplication.translate("mainWindow", u"Frame Index", None))

        self.btn_intt.setText(QCoreApplication.translate("mainWindow", u"plot Intensity-T", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("mainWindow", u"Intensity-Time", None))
        self.groupBox.setTitle(QCoreApplication.translate("mainWindow", u"Data Selection:", None))
        self.label_4.setText(QCoreApplication.translate("mainWindow", u"t range (s):", None))
        self.label_3.setText(QCoreApplication.translate("mainWindow", u"q (1/\u00c5):", None))
        self.label_7.setText(QCoreApplication.translate("mainWindow", u"y range", None))
        self.g2_tmin.setText(QCoreApplication.translate("mainWindow", u"1e-6", None))
        self.g2_tmax.setText(QCoreApplication.translate("mainWindow", u"100.0", None))
        self.g2_yauto.setText(QCoreApplication.translate("mainWindow", u"auto", None))
        self.pushButton_4.setText(QCoreApplication.translate("mainWindow", u"plot", None))
        self.label.setText(QCoreApplication.translate("mainWindow", u"offset:", None))
        self.label_53.setText(QCoreApplication.translate("mainWindow", u"marker size:", None))
        self.label_8.setText(QCoreApplication.translate("mainWindow", u"column:", None))
        self.g2_sub_baseline.setText(QCoreApplication.translate("mainWindow", u"subtract baseline", None))
        self.g2_show_fit.setText(QCoreApplication.translate("mainWindow", u"do fitting", None))
        self.g2_show_label.setText(QCoreApplication.translate("mainWindow", u"show labels", None))
        self.g2_plot_type.setItemText(0, QCoreApplication.translate("mainWindow", u"multiple", None))
        self.g2_plot_type.setItemText(1, QCoreApplication.translate("mainWindow", u"single", None))
        self.g2_plot_type.setItemText(2, QCoreApplication.translate("mainWindow", u"single-combined", None))

        self.groupBox_2.setTitle(QCoreApplication.translate("mainWindow", u"g2 fitting", None))
        self.label_66.setText(QCoreApplication.translate("mainWindow", u"c2", None))
        self.label_48.setText(QCoreApplication.translate("mainWindow", u"baseline:", None))
        self.g2_c2fit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_41.setText(QCoreApplication.translate("mainWindow", u"d", None))
        self.g2_dfit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_63.setText(QCoreApplication.translate("mainWindow", u"ratio:", None))
        self.g2_ffit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.g2_fitting_function.setItemText(0, QCoreApplication.translate("mainWindow", u"Single Exponential", None))
        self.g2_fitting_function.setItemText(1, QCoreApplication.translate("mainWindow", u"Double Exponential", None))

        self.label_67.setText(QCoreApplication.translate("mainWindow", u"f", None))
        self.label_45.setText(QCoreApplication.translate("mainWindow", u"contrast:", None))
        self.label_5.setText(QCoreApplication.translate("mainWindow", u"a", None))
        self.g2_afit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_46.setText(QCoreApplication.translate("mainWindow", u"tau (s):", None))
        self.label_6.setText(QCoreApplication.translate("mainWindow", u"b", None))
        self.g2_bfit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_65.setText(QCoreApplication.translate("mainWindow", u"tau2 (s):", None))
        self.label_64.setText(QCoreApplication.translate("mainWindow", u"b2", None))
        self.g2_b2fit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_47.setText(QCoreApplication.translate("mainWindow", u"stretch:", None))
        self.label_10.setText(QCoreApplication.translate("mainWindow", u"c", None))
        self.g2_cfit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_62.setText(QCoreApplication.translate("mainWindow", u"stretch2:", None))
        self.show_g2_fit_summary.setText(QCoreApplication.translate("mainWindow", u"values", None))
        self.btn_g2_export.setText(QCoreApplication.translate("mainWindow", u"export", None))
        self.btn_g2_refit.setText(QCoreApplication.translate("mainWindow", u"refit", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("mainWindow", u"g2", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("mainWindow", u"Power Law Fitting: y = a\u00b7x^b", None))
        self.label_15.setText(QCoreApplication.translate("mainWindow", u"plot_type:", None))
        self.cb_tauq_type.setItemText(0, QCoreApplication.translate("mainWindow", u"t-q", None))
        self.cb_tauq_type.setItemText(1, QCoreApplication.translate("mainWindow", u"\u03c4-log(q)", None))
        self.cb_tauq_type.setItemText(2, QCoreApplication.translate("mainWindow", u"log(\u03c4)-q", None))
        self.cb_tauq_type.setItemText(3, QCoreApplication.translate("mainWindow", u"log(\u03c4)-log(q)", None))

        self.label_18.setText(QCoreApplication.translate("mainWindow", u"Offset:", None))
        self.tauq_amax.setText(QCoreApplication.translate("mainWindow", u"1.00e-3", None))
        self.tauq_amax.setPlaceholderText(QCoreApplication.translate("mainWindow", u"max", None))
        self.tauq_qmax.setText(QCoreApplication.translate("mainWindow", u"0.0092", None))
        self.tauq_qmax.setPlaceholderText(QCoreApplication.translate("mainWindow", u"max", None))
        self.tauq_bfit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.label_44.setText(QCoreApplication.translate("mainWindow", u"a", None))
        self.tauq_bmin.setText(QCoreApplication.translate("mainWindow", u"-2.5", None))
        self.tauq_bmin.setPlaceholderText(QCoreApplication.translate("mainWindow", u"min", None))
        self.label_42.setText(QCoreApplication.translate("mainWindow", u"b", None))
        self.tauq_amin.setText(QCoreApplication.translate("mainWindow", u"1.00e-12", None))
        self.tauq_amin.setPlaceholderText(QCoreApplication.translate("mainWindow", u"min", None))
        self.tauq_afit.setText(QCoreApplication.translate("mainWindow", u"fit", None))
        self.tauq_bmax.setText(QCoreApplication.translate("mainWindow", u"-0.5", None))
        self.tauq_bmax.setPlaceholderText(QCoreApplication.translate("mainWindow", u"max", None))
        self.tauq_qmin.setText(QCoreApplication.translate("mainWindow", u"0.001", None))
        self.tauq_qmin.setPlaceholderText(QCoreApplication.translate("mainWindow", u"min", None))
        self.label_43.setText(QCoreApplication.translate("mainWindow", u"q (\u00c5\u207b\u00b9)", None))
        self.pushButton_8.setText(QCoreApplication.translate("mainWindow", u"fit plot", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), QCoreApplication.translate("mainWindow", u"Diffusion", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("mainWindow", u"Twotime Visualization Setting", None))
        self.label_35.setText(QCoreApplication.translate("mainWindow", u"sax2d_cmap:", None))
        self.label_36.setText(QCoreApplication.translate("mainWindow", u"type:", None))
        self.cb_twotime_type.setItemText(0, QCoreApplication.translate("mainWindow", u"log", None))
        self.cb_twotime_type.setItemText(1, QCoreApplication.translate("mainWindow", u"linear", None))

        self.label_28.setText(QCoreApplication.translate("mainWindow", u"twotime_cmap:", None))
        self.pushButton_12.setText(QCoreApplication.translate("mainWindow", u"Plot", None))
        self.twotime_autocrop.setText(QCoreApplication.translate("mainWindow", u"auto-crop", None))
        self.twotime_autorotate.setText(QCoreApplication.translate("mainWindow", u"auto-rotate", None))
        self.twotime_showbox.setText(QCoreApplication.translate("mainWindow", u"show-partial-box", None))
        self.cb_twotime_saxs_cmap.setItemText(0, QCoreApplication.translate("mainWindow", u"jet", None))
        self.cb_twotime_saxs_cmap.setItemText(1, QCoreApplication.translate("mainWindow", u"hot", None))
        self.cb_twotime_saxs_cmap.setItemText(2, QCoreApplication.translate("mainWindow", u"plasma", None))
        self.cb_twotime_saxs_cmap.setItemText(3, QCoreApplication.translate("mainWindow", u"viridis", None))
        self.cb_twotime_saxs_cmap.setItemText(4, QCoreApplication.translate("mainWindow", u"magma", None))
        self.cb_twotime_saxs_cmap.setItemText(5, QCoreApplication.translate("mainWindow", u"gray", None))

        self.cb_twotime_cmap.setItemText(0, QCoreApplication.translate("mainWindow", u"jet", None))
        self.cb_twotime_cmap.setItemText(1, QCoreApplication.translate("mainWindow", u"hot", None))
        self.cb_twotime_cmap.setItemText(2, QCoreApplication.translate("mainWindow", u"plasma", None))
        self.cb_twotime_cmap.setItemText(3, QCoreApplication.translate("mainWindow", u"viridis", None))
        self.cb_twotime_cmap.setItemText(4, QCoreApplication.translate("mainWindow", u"magma", None))
        self.cb_twotime_cmap.setItemText(5, QCoreApplication.translate("mainWindow", u"gray", None))

        self.twotime_correct_diag.setText(QCoreApplication.translate("mainWindow", u"correct-diag", None))
        self.label_57.setText(QCoreApplication.translate("mainWindow", u"min-max:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_8), QCoreApplication.translate("mainWindow", u"Two Time", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("mainWindow", u"g2 outlier", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("mainWindow", u"Averaging Setting:", None))
        self.label_39.setText(QCoreApplication.translate("mainWindow", u"g2 max:", None))
        self.btn_set_average_save_name.setText(QCoreApplication.translate("mainWindow", u"...", None))
        self.label_17.setText(QCoreApplication.translate("mainWindow", u"batch size:", None))
        self.label_32.setText(QCoreApplication.translate("mainWindow", u"q_index:", None))
        self.label_25.setText(QCoreApplication.translate("mainWindow", u"g2 min:", None))
        self.label_19.setText(QCoreApplication.translate("mainWindow", u"save name:", None))
        self.bx_avg_G2IPIF.setText(QCoreApplication.translate("mainWindow", u"G2/IP/IF", None))
        self.bx_avg_g2g2err.setText(QCoreApplication.translate("mainWindow", u"g2/g2err", None))
        self.label_20.setText(QCoreApplication.translate("mainWindow", u"save path:", None))
        self.btn_set_average_save_path.setText(QCoreApplication.translate("mainWindow", u"...", None))
        self.bx_avg_saxs.setText(QCoreApplication.translate("mainWindow", u"saxs 1d/2d", None))
        self.label_26.setText(QCoreApplication.translate("mainWindow", u"selection:", None))
        self.label_33.setText(QCoreApplication.translate("mainWindow", u"avg_window:", None))
        self.label_40.setText(QCoreApplication.translate("mainWindow", u"max_thread:", None))
        self.cb_avg_chunk_size.setItemText(0, QCoreApplication.translate("mainWindow", u"32", None))
        self.cb_avg_chunk_size.setItemText(1, QCoreApplication.translate("mainWindow", u"64", None))
        self.cb_avg_chunk_size.setItemText(2, QCoreApplication.translate("mainWindow", u"128", None))
        self.cb_avg_chunk_size.setItemText(3, QCoreApplication.translate("mainWindow", u"256", None))
        self.cb_avg_chunk_size.setItemText(4, QCoreApplication.translate("mainWindow", u"512", None))

        self.avg_blmin.setSpecialValueText("")
        self.groupBox_12.setTitle(QCoreApplication.translate("mainWindow", u"Action:", None))
        self.btn_submit_job.setText(QCoreApplication.translate("mainWindow", u"submit", None))
        self.avg_job_pop.setText(QCoreApplication.translate("mainWindow", u"delete", None))
        self.btn_avg_jobinfo.setText(QCoreApplication.translate("mainWindow", u"info", None))
        self.btn_avg_kill.setText(QCoreApplication.translate("mainWindow", u"kill", None))
        self.btn_start_avg_job.setText(QCoreApplication.translate("mainWindow", u"start", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("mainWindow", u"Averaging Job List", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("mainWindow", u"Average", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("mainWindow", u"Metadata", None))
    # retranslateUi

