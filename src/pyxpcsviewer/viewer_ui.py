# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'xpcs.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .plothandler import ImageViewDev, ImageViewPlotItem, MplCanvasBarV, PlotWidgetDev
from pyqtgraph import DataTreeWidget, GraphicsLayoutWidget, ImageView, PlotWidget
from pyqtgraph.parametertree import ParameterTree
from . import icons_rc


class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName("mainWindow")
        mainWindow.resize(1555, 1013)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(mainWindow.sizePolicy().hasHeightForWidth())
        mainWindow.setSizePolicy(sizePolicy)
        mainWindow.setMinimumSize(QSize(1024, 0))
        icon = QIcon()
        icon.addFile(
            ":/newPrefix/icons8-giraffe-full-body-100.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        icon.addFile(
            ":/icons/icons8-giraffe-full-body-100.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        mainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth()
        )
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName("splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Horizontal)
        self.splitter = QSplitter(self.splitter_3)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.label_2)

        self.work_dir = QLineEdit(self.layoutWidget)
        self.work_dir.setObjectName("work_dir")
        self.work_dir.setMinimumSize(QSize(200, 0))
        self.work_dir.setMaximumSize(QSize(16777215, 16777215))
        self.work_dir.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.work_dir)

        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_56 = QLabel(self.layoutWidget)
        self.label_56.setObjectName("label_56")

        self.horizontalLayout_2.addWidget(self.label_56)

        self.sort_method = QComboBox(self.layoutWidget)
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.addItem("")
        self.sort_method.setObjectName("sort_method")

        self.horizontalLayout_2.addWidget(self.sort_method)

        self.pushButton_11 = QPushButton(self.layoutWidget)
        self.pushButton_11.setObjectName("pushButton_11")
        sizePolicy3 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(
            self.pushButton_11.sizePolicy().hasHeightForWidth()
        )
        self.pushButton_11.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.pushButton_11)

        self.pushButton = QPushButton(self.layoutWidget)
        self.pushButton.setObjectName("pushButton")
        sizePolicy3.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.box_source = QGroupBox(self.layoutWidget)
        self.box_source.setObjectName("box_source")
        sizePolicy4 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy4.setHorizontalStretch(20)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.box_source.sizePolicy().hasHeightForWidth())
        self.box_source.setSizePolicy(sizePolicy4)
        self.box_source.setMinimumSize(QSize(0, 80))
        self.box_source.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_5 = QGridLayout(self.box_source)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.list_view_source = QListView(self.box_source)
        self.list_view_source.setObjectName("list_view_source")
        self.list_view_source.setDragEnabled(True)
        self.list_view_source.setAlternatingRowColors(True)
        self.list_view_source.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.gridLayout_5.addWidget(self.list_view_source, 0, 0, 1, 1)

        self.verticalLayout.addWidget(self.box_source)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.filter_type = QComboBox(self.layoutWidget1)
        self.filter_type.addItem("")
        self.filter_type.addItem("")
        self.filter_type.setObjectName("filter_type")

        self.horizontalLayout_3.addWidget(self.filter_type)

        self.filter_str = QLineEdit(self.layoutWidget1)
        self.filter_str.setObjectName("filter_str")
        sizePolicy3.setHeightForWidth(self.filter_str.sizePolicy().hasHeightForWidth())
        self.filter_str.setSizePolicy(sizePolicy3)
        self.filter_str.setMaximumSize(QSize(16777215, 100))
        self.filter_str.setClearButtonEnabled(True)

        self.horizontalLayout_3.addWidget(self.filter_str)

        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_2 = QPushButton(self.layoutWidget1)
        self.pushButton_2.setObjectName("pushButton_2")
        sizePolicy3.setHeightForWidth(
            self.pushButton_2.sizePolicy().hasHeightForWidth()
        )
        self.pushButton_2.setSizePolicy(sizePolicy3)
        self.pushButton_2.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.layoutWidget1)
        self.pushButton_3.setObjectName("pushButton_3")
        sizePolicy3.setHeightForWidth(
            self.pushButton_3.sizePolicy().hasHeightForWidth()
        )
        self.pushButton_3.setSizePolicy(sizePolicy3)
        self.pushButton_3.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.pushButton_3)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.box_target = QGroupBox(self.layoutWidget1)
        self.box_target.setObjectName("box_target")
        sizePolicy1.setHeightForWidth(self.box_target.sizePolicy().hasHeightForWidth())
        self.box_target.setSizePolicy(sizePolicy1)
        self.box_target.setMinimumSize(QSize(0, 120))
        self.box_target.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_4 = QGridLayout(self.box_target)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.btn_deselect = QPushButton(self.box_target)
        self.btn_deselect.setObjectName("btn_deselect")

        self.horizontalLayout_7.addWidget(self.btn_deselect)

        self.btn_up = QPushButton(self.box_target)
        self.btn_up.setObjectName("btn_up")

        self.horizontalLayout_7.addWidget(self.btn_up)

        self.btn_down = QPushButton(self.box_target)
        self.btn_down.setObjectName("btn_down")

        self.horizontalLayout_7.addWidget(self.btn_down)

        self.gridLayout_4.addLayout(self.horizontalLayout_7, 1, 0, 1, 1)

        self.list_view_target = QListView(self.box_target)
        self.list_view_target.setObjectName("list_view_target")
        self.list_view_target.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.gridLayout_4.addWidget(self.list_view_target, 0, 0, 1, 1)

        self.verticalLayout_2.addWidget(self.box_target)

        self.splitter.addWidget(self.layoutWidget1)
        self.splitter_3.addWidget(self.splitter)
        self.tabWidget = QTabWidget(self.splitter_3)
        self.tabWidget.setObjectName("tabWidget")
        sizePolicy1.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy1)
        self.tabWidget.setMinimumSize(QSize(600, 0))
        self.tabWidget.setMaximumSize(QSize(16777215, 16777215))
        self.tab1_1 = QWidget()
        self.tab1_1.setObjectName("tab1_1")
        self.gridLayout_26 = QGridLayout(self.tab1_1)
        self.gridLayout_26.setObjectName("gridLayout_26")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_38 = QLabel(self.tab1_1)
        self.label_38.setObjectName("label_38")

        self.horizontalLayout_4.addWidget(self.label_38)

        self.saxs2d_display = QLineEdit(self.tab1_1)
        self.saxs2d_display.setObjectName("saxs2d_display")
        self.saxs2d_display.setMinimumSize(QSize(500, 0))
        self.saxs2d_display.setAcceptDrops(False)
        self.saxs2d_display.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.saxs2d_display.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.saxs2d_display)

        self.gridLayout_26.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)

        self.pg_saxs = ImageViewDev(self.tab1_1)
        self.pg_saxs.setObjectName("pg_saxs")
        sizePolicy1.setHeightForWidth(self.pg_saxs.sizePolicy().hasHeightForWidth())
        self.pg_saxs.setSizePolicy(sizePolicy1)

        self.gridLayout_26.addWidget(self.pg_saxs, 1, 0, 1, 2)

        self.groupBox_3 = QGroupBox(self.tab1_1)
        self.groupBox_3.setObjectName("groupBox_3")
        sizePolicy5 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy5)
        self.groupBox_3.setMinimumSize(QSize(0, 100))
        self.gridLayout_40 = QGridLayout(self.groupBox_3)
        self.gridLayout_40.setObjectName("gridLayout_40")
        self.saxs2d_max = QDoubleSpinBox(self.groupBox_3)
        self.saxs2d_max.setObjectName("saxs2d_max")
        self.saxs2d_max.setEnabled(False)
        self.saxs2d_max.setDecimals(4)
        self.saxs2d_max.setMinimum(-99.000000000000000)
        self.saxs2d_max.setMaximum(99999.000000000000000)
        self.saxs2d_max.setValue(1.000000000000000)

        self.gridLayout_40.addWidget(self.saxs2d_max, 0, 8, 1, 1)

        self.cb_saxs2D_cmap = QComboBox(self.groupBox_3)
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.addItem("")
        self.cb_saxs2D_cmap.setObjectName("cb_saxs2D_cmap")

        self.gridLayout_40.addWidget(self.cb_saxs2D_cmap, 0, 1, 1, 1)

        self.label_50 = QLabel(self.groupBox_3)
        self.label_50.setObjectName("label_50")
        sizePolicy2.setHeightForWidth(self.label_50.sizePolicy().hasHeightForWidth())
        self.label_50.setSizePolicy(sizePolicy2)

        self.gridLayout_40.addWidget(self.label_50, 0, 5, 1, 1)

        self.label_13 = QLabel(self.groupBox_3)
        self.label_13.setObjectName("label_13")

        self.gridLayout_40.addWidget(self.label_13, 0, 0, 1, 1)

        self.cb_saxs2D_type = QComboBox(self.groupBox_3)
        self.cb_saxs2D_type.addItem("")
        self.cb_saxs2D_type.addItem("")
        self.cb_saxs2D_type.setObjectName("cb_saxs2D_type")

        self.gridLayout_40.addWidget(self.cb_saxs2D_type, 0, 3, 1, 1)

        self.saxs2d_min = QDoubleSpinBox(self.groupBox_3)
        self.saxs2d_min.setObjectName("saxs2d_min")
        self.saxs2d_min.setEnabled(False)
        self.saxs2d_min.setDecimals(4)
        self.saxs2d_min.setMinimum(-99.000000000000000)
        self.saxs2d_min.setMaximum(99999.000000000000000)

        self.gridLayout_40.addWidget(self.saxs2d_min, 0, 6, 1, 1)

        self.pushButton_plot_saxs2d = QPushButton(self.groupBox_3)
        self.pushButton_plot_saxs2d.setObjectName("pushButton_plot_saxs2d")
        self.pushButton_plot_saxs2d.setMinimumSize(QSize(0, 0))

        self.gridLayout_40.addWidget(self.pushButton_plot_saxs2d, 0, 11, 1, 1)

        self.saxs2d_autorange = QCheckBox(self.groupBox_3)
        self.saxs2d_autorange.setObjectName("saxs2d_autorange")
        self.saxs2d_autorange.setChecked(True)

        self.gridLayout_40.addWidget(self.saxs2d_autorange, 0, 9, 1, 1)

        self.label_12 = QLabel(self.groupBox_3)
        self.label_12.setObjectName("label_12")

        self.gridLayout_40.addWidget(self.label_12, 0, 2, 1, 1)

        self.saxs2d_rotate = QCheckBox(self.groupBox_3)
        self.saxs2d_rotate.setObjectName("saxs2d_rotate")
        self.saxs2d_rotate.setChecked(False)

        self.gridLayout_40.addWidget(self.saxs2d_rotate, 0, 10, 1, 1)

        self.gridLayout_26.addWidget(self.groupBox_3, 2, 0, 1, 1)

        self.groupBox_16 = QGroupBox(self.tab1_1)
        self.groupBox_16.setObjectName("groupBox_16")
        self.gridLayout_3 = QGridLayout(self.groupBox_16)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_58 = QLabel(self.groupBox_16)
        self.label_58.setObjectName("label_58")

        self.gridLayout_3.addWidget(self.label_58, 0, 0, 1, 1)

        self.cb_saxs2D_roi_type = QComboBox(self.groupBox_16)
        self.cb_saxs2D_roi_type.addItem("")
        self.cb_saxs2D_roi_type.addItem("")
        self.cb_saxs2D_roi_type.setObjectName("cb_saxs2D_roi_type")

        self.gridLayout_3.addWidget(self.cb_saxs2D_roi_type, 0, 1, 1, 1)

        self.label_60 = QLabel(self.groupBox_16)
        self.label_60.setObjectName("label_60")

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
        self.cb_saxs2D_roi_color.setObjectName("cb_saxs2D_roi_color")

        self.gridLayout_3.addWidget(self.cb_saxs2D_roi_color, 0, 3, 1, 1)

        self.label_61 = QLabel(self.groupBox_16)
        self.label_61.setObjectName("label_61")

        self.gridLayout_3.addWidget(self.label_61, 0, 4, 1, 1)

        self.sb_saxs2D_roi_width = QDoubleSpinBox(self.groupBox_16)
        self.sb_saxs2D_roi_width.setObjectName("sb_saxs2D_roi_width")
        self.sb_saxs2D_roi_width.setMinimum(0.100000000000000)
        self.sb_saxs2D_roi_width.setSingleStep(0.100000000000000)
        self.sb_saxs2D_roi_width.setValue(1.500000000000000)

        self.gridLayout_3.addWidget(self.sb_saxs2D_roi_width, 0, 5, 1, 1)

        self.pushButton_6 = QPushButton(self.groupBox_16)
        self.pushButton_6.setObjectName("pushButton_6")

        self.gridLayout_3.addWidget(self.pushButton_6, 0, 6, 1, 1)

        self.gridLayout_26.addWidget(self.groupBox_16, 3, 0, 1, 1)

        self.tabWidget.addTab(self.tab1_1, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_25 = QGridLayout(self.tab_2)
        self.gridLayout_25.setObjectName("gridLayout_25")
        self.mp_saxs = PlotWidget(self.tab_2)
        self.mp_saxs.setObjectName("mp_saxs")
        sizePolicy6 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.mp_saxs.sizePolicy().hasHeightForWidth())
        self.mp_saxs.setSizePolicy(sizePolicy6)
        self.mp_saxs.setMinimumSize(QSize(600, 0))

        self.gridLayout_25.addWidget(self.mp_saxs, 0, 0, 1, 1)

        self.groupBox_6 = QGroupBox(self.tab_2)
        self.groupBox_6.setObjectName("groupBox_6")
        sizePolicy5.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy5)
        self.gridLayout_24 = QGridLayout(self.groupBox_6)
        self.gridLayout_24.setObjectName("gridLayout_24")
        self.groupBox_14 = QGroupBox(self.groupBox_6)
        self.groupBox_14.setObjectName("groupBox_14")
        self.gridLayout_34 = QGridLayout(self.groupBox_14)
        self.gridLayout_34.setObjectName("gridLayout_34")
        self.cb_sub_bkg = QCheckBox(self.groupBox_14)
        self.cb_sub_bkg.setObjectName("cb_sub_bkg")

        self.gridLayout_34.addWidget(self.cb_sub_bkg, 0, 0, 1, 1)

        self.le_bkg_fname = QLineEdit(self.groupBox_14)
        self.le_bkg_fname.setObjectName("le_bkg_fname")
        self.le_bkg_fname.setEnabled(False)

        self.gridLayout_34.addWidget(self.le_bkg_fname, 0, 1, 1, 1)

        self.btn_select_bkgfile = QPushButton(self.groupBox_14)
        self.btn_select_bkgfile.setObjectName("btn_select_bkgfile")
        self.btn_select_bkgfile.setEnabled(False)

        self.gridLayout_34.addWidget(self.btn_select_bkgfile, 0, 2, 1, 1)

        self.label_59 = QLabel(self.groupBox_14)
        self.label_59.setObjectName("label_59")

        self.gridLayout_34.addWidget(self.label_59, 0, 3, 1, 1)

        self.bkg_weight = QDoubleSpinBox(self.groupBox_14)
        self.bkg_weight.setObjectName("bkg_weight")
        self.bkg_weight.setEnabled(False)
        self.bkg_weight.setDecimals(4)
        self.bkg_weight.setMaximum(99.999899999999997)
        self.bkg_weight.setValue(1.000000000000000)

        self.gridLayout_34.addWidget(self.bkg_weight, 0, 4, 1, 1)

        self.gridLayout_24.addWidget(self.groupBox_14, 1, 0, 2, 1)

        self.groupBox_13 = QGroupBox(self.groupBox_6)
        self.groupBox_13.setObjectName("groupBox_13")
        self.gridLayout_32 = QGridLayout(self.groupBox_13)
        self.gridLayout_32.setObjectName("gridLayout_32")
        self.box_show_roi = QCheckBox(self.groupBox_13)
        self.box_show_roi.setObjectName("box_show_roi")
        self.box_show_roi.setChecked(True)

        self.gridLayout_32.addWidget(self.box_show_roi, 0, 2, 1, 1)

        self.box_all_phi = QCheckBox(self.groupBox_13)
        self.box_all_phi.setObjectName("box_all_phi")

        self.gridLayout_32.addWidget(self.box_all_phi, 0, 0, 1, 1)

        self.box_show_phi_roi = QCheckBox(self.groupBox_13)
        self.box_show_phi_roi.setObjectName("box_show_phi_roi")

        self.gridLayout_32.addWidget(self.box_show_phi_roi, 0, 3, 1, 1)

        self.btn_export_saxs1d = QPushButton(self.groupBox_13)
        self.btn_export_saxs1d.setObjectName("btn_export_saxs1d")

        self.gridLayout_32.addWidget(self.btn_export_saxs1d, 0, 4, 1, 1)

        self.gridLayout_24.addWidget(self.groupBox_13, 1, 1, 2, 1)

        self.groupBox_15 = QGroupBox(self.groupBox_6)
        self.groupBox_15.setObjectName("groupBox_15")
        self.gridLayout_16 = QGridLayout(self.groupBox_15)
        self.gridLayout_16.setObjectName("gridLayout_16")
        self.label_21 = QLabel(self.groupBox_15)
        self.label_21.setObjectName("label_21")

        self.gridLayout_16.addWidget(self.label_21, 0, 0, 1, 1)

        self.cb_saxs_type = QComboBox(self.groupBox_15)
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.addItem("")
        self.cb_saxs_type.setObjectName("cb_saxs_type")

        self.gridLayout_16.addWidget(self.cb_saxs_type, 0, 1, 1, 2)

        self.label_55 = QLabel(self.groupBox_15)
        self.label_55.setObjectName("label_55")

        self.gridLayout_16.addWidget(self.label_55, 0, 3, 1, 1)

        self.saxs1d_sampling = QSpinBox(self.groupBox_15)
        self.saxs1d_sampling.setObjectName("saxs1d_sampling")
        self.saxs1d_sampling.setMinimum(1)
        self.saxs1d_sampling.setValue(1)

        self.gridLayout_16.addWidget(self.saxs1d_sampling, 0, 4, 1, 1)

        self.label_22 = QLabel(self.groupBox_15)
        self.label_22.setObjectName("label_22")

        self.gridLayout_16.addWidget(self.label_22, 0, 5, 1, 1)

        self.sb_saxs_offset = QDoubleSpinBox(self.groupBox_15)
        self.sb_saxs_offset.setObjectName("sb_saxs_offset")
        self.sb_saxs_offset.setDecimals(4)
        self.sb_saxs_offset.setSingleStep(0.050000000000000)
        self.sb_saxs_offset.setValue(0.000000000000000)

        self.gridLayout_16.addWidget(self.sb_saxs_offset, 0, 6, 1, 1)

        self.label_23 = QLabel(self.groupBox_15)
        self.label_23.setObjectName("label_23")

        self.gridLayout_16.addWidget(self.label_23, 0, 7, 1, 1)

        self.cb_saxs_norm = QComboBox(self.groupBox_15)
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.addItem("")
        self.cb_saxs_norm.setObjectName("cb_saxs_norm")

        self.gridLayout_16.addWidget(self.cb_saxs_norm, 0, 8, 1, 1)

        self.saxs1d_lb_type = QComboBox(self.groupBox_15)
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.addItem("")
        self.saxs1d_lb_type.setObjectName("saxs1d_lb_type")

        self.gridLayout_16.addWidget(self.saxs1d_lb_type, 0, 9, 1, 1)

        self.label_49 = QLabel(self.groupBox_15)
        self.label_49.setObjectName("label_49")

        self.gridLayout_16.addWidget(self.label_49, 1, 0, 1, 2)

        self.saxs1d_qmin = QDoubleSpinBox(self.groupBox_15)
        self.saxs1d_qmin.setObjectName("saxs1d_qmin")
        self.saxs1d_qmin.setDecimals(4)
        self.saxs1d_qmin.setSingleStep(0.002000000000000)

        self.gridLayout_16.addWidget(self.saxs1d_qmin, 1, 2, 1, 2)

        self.saxs1d_qmax = QDoubleSpinBox(self.groupBox_15)
        self.saxs1d_qmax.setObjectName("saxs1d_qmax")
        self.saxs1d_qmax.setDecimals(4)
        self.saxs1d_qmax.setSingleStep(0.000500000000000)
        self.saxs1d_qmax.setValue(1.000000000000000)

        self.gridLayout_16.addWidget(self.saxs1d_qmax, 1, 4, 1, 1)

        self.label_54 = QLabel(self.groupBox_15)
        self.label_54.setObjectName("label_54")

        self.gridLayout_16.addWidget(self.label_54, 1, 5, 1, 1)

        self.sb_saxs_marker_size = QDoubleSpinBox(self.groupBox_15)
        self.sb_saxs_marker_size.setObjectName("sb_saxs_marker_size")
        self.sb_saxs_marker_size.setMinimum(1.000000000000000)
        self.sb_saxs_marker_size.setMaximum(20.000000000000000)
        self.sb_saxs_marker_size.setValue(5.000000000000000)

        self.gridLayout_16.addWidget(self.sb_saxs_marker_size, 1, 6, 1, 1)

        self.label_52 = QLabel(self.groupBox_15)
        self.label_52.setObjectName("label_52")

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
        self.saxs1d_legend_loc.setObjectName("saxs1d_legend_loc")

        self.gridLayout_16.addWidget(self.saxs1d_legend_loc, 1, 8, 1, 1)

        self.cbox_use_abs = QCheckBox(self.groupBox_15)
        self.cbox_use_abs.setObjectName("cbox_use_abs")

        self.gridLayout_16.addWidget(self.cbox_use_abs, 1, 9, 1, 1)

        self.gridLayout_24.addWidget(self.groupBox_15, 0, 0, 1, 3)

        self.pushButton_plot_saxs1d = QPushButton(self.groupBox_6)
        self.pushButton_plot_saxs1d.setObjectName("pushButton_plot_saxs1d")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(
            self.pushButton_plot_saxs1d.sizePolicy().hasHeightForWidth()
        )
        self.pushButton_plot_saxs1d.setSizePolicy(sizePolicy7)

        self.gridLayout_24.addWidget(self.pushButton_plot_saxs1d, 1, 2, 2, 1)

        self.gridLayout_25.addWidget(self.groupBox_6, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_6 = QGridLayout(self.tab_3)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.mp_stab = MplCanvasBarV(self.tab_3)
        self.mp_stab.setObjectName("mp_stab")
        sizePolicy1.setHeightForWidth(self.mp_stab.sizePolicy().hasHeightForWidth())
        self.mp_stab.setSizePolicy(sizePolicy1)

        self.gridLayout_6.addWidget(self.mp_stab, 0, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.tab_3)
        self.groupBox_4.setObjectName("groupBox_4")
        sizePolicy5.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy5)
        self.groupBox_4.setMinimumSize(QSize(0, 0))
        self.gridLayout_17 = QGridLayout(self.groupBox_4)
        self.gridLayout_17.setObjectName("gridLayout_17")
        self.label_14 = QLabel(self.groupBox_4)
        self.label_14.setObjectName("label_14")

        self.gridLayout_17.addWidget(self.label_14, 0, 0, 1, 1)

        self.cb_stab_type = QComboBox(self.groupBox_4)
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.addItem("")
        self.cb_stab_type.setObjectName("cb_stab_type")

        self.gridLayout_17.addWidget(self.cb_stab_type, 0, 1, 1, 1)

        self.label_24 = QLabel(self.groupBox_4)
        self.label_24.setObjectName("label_24")

        self.gridLayout_17.addWidget(self.label_24, 0, 2, 1, 1)

        self.sb_stab_offset = QDoubleSpinBox(self.groupBox_4)
        self.sb_stab_offset.setObjectName("sb_stab_offset")
        self.sb_stab_offset.setDecimals(4)
        self.sb_stab_offset.setSingleStep(0.050000000000000)
        self.sb_stab_offset.setValue(0.000000000000000)

        self.gridLayout_17.addWidget(self.sb_stab_offset, 0, 3, 1, 1)

        self.label_16 = QLabel(self.groupBox_4)
        self.label_16.setObjectName("label_16")

        self.gridLayout_17.addWidget(self.label_16, 0, 4, 1, 1)

        self.cb_stab_norm = QComboBox(self.groupBox_4)
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.addItem("")
        self.cb_stab_norm.setObjectName("cb_stab_norm")

        self.gridLayout_17.addWidget(self.cb_stab_norm, 0, 5, 1, 1)

        self.pushButton_plot_stability = QPushButton(self.groupBox_4)
        self.pushButton_plot_stability.setObjectName("pushButton_plot_stability")

        self.gridLayout_17.addWidget(self.pushButton_plot_stability, 0, 6, 1, 1)

        self.gridLayout_6.addWidget(self.groupBox_4, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gridLayout_27 = QGridLayout(self.tab_4)
        self.gridLayout_27.setObjectName("gridLayout_27")
        self.pg_intt = PlotWidgetDev(self.tab_4)
        self.pg_intt.setObjectName("pg_intt")
        sizePolicy6.setHeightForWidth(self.pg_intt.sizePolicy().hasHeightForWidth())
        self.pg_intt.setSizePolicy(sizePolicy6)

        self.gridLayout_27.addWidget(self.pg_intt, 0, 0, 1, 3)

        self.groupBox_7 = QGroupBox(self.tab_4)
        self.groupBox_7.setObjectName("groupBox_7")
        self.groupBox_7.setMinimumSize(QSize(0, 0))
        self.gridLayout_18 = QGridLayout(self.groupBox_7)
        self.gridLayout_18.setObjectName("gridLayout_18")
        self.label_9 = QLabel(self.groupBox_7)
        self.label_9.setObjectName("label_9")

        self.gridLayout_18.addWidget(self.label_9, 0, 0, 1, 1)

        self.sb_intt_max = QSpinBox(self.groupBox_7)
        self.sb_intt_max.setObjectName("sb_intt_max")
        self.sb_intt_max.setValue(10)

        self.gridLayout_18.addWidget(self.sb_intt_max, 0, 1, 1, 1)

        self.label_31 = QLabel(self.groupBox_7)
        self.label_31.setObjectName("label_31")

        self.gridLayout_18.addWidget(self.label_31, 0, 2, 1, 1)

        self.sb_window = QSpinBox(self.groupBox_7)
        self.sb_window.setObjectName("sb_window")
        self.sb_window.setMaximum(999)
        self.sb_window.setValue(1)

        self.gridLayout_18.addWidget(self.sb_window, 0, 3, 1, 1)

        self.label_11 = QLabel(self.groupBox_7)
        self.label_11.setObjectName("label_11")

        self.gridLayout_18.addWidget(self.label_11, 0, 4, 1, 1)

        self.sb_intt_sampling = QSpinBox(self.groupBox_7)
        self.sb_intt_sampling.setObjectName("sb_intt_sampling")
        self.sb_intt_sampling.setMinimum(1)
        self.sb_intt_sampling.setValue(1)

        self.gridLayout_18.addWidget(self.sb_intt_sampling, 0, 5, 1, 1)

        self.label_34 = QLabel(self.groupBox_7)
        self.label_34.setObjectName("label_34")

        self.gridLayout_18.addWidget(self.label_34, 0, 6, 1, 1)

        self.intt_xlabel = QComboBox(self.groupBox_7)
        self.intt_xlabel.addItem("")
        self.intt_xlabel.addItem("")
        self.intt_xlabel.setObjectName("intt_xlabel")

        self.gridLayout_18.addWidget(self.intt_xlabel, 0, 7, 1, 1)

        self.pushButton_plot_intt = QPushButton(self.groupBox_7)
        self.pushButton_plot_intt.setObjectName("pushButton_plot_intt")

        self.gridLayout_18.addWidget(self.pushButton_plot_intt, 0, 8, 1, 1)

        self.gridLayout_27.addWidget(self.groupBox_7, 1, 0, 1, 3)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName("tab_6")
        self.gridLayout_8 = QGridLayout(self.tab_6)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.scrollArea = QScrollArea(self.tab_6)
        self.scrollArea.setObjectName("scrollArea")
        sizePolicy8 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(30)
        sizePolicy8.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy8)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.scrollArea.setWidgetResizable(True)
        self.g2_scroll_area = QWidget()
        self.g2_scroll_area.setObjectName("g2_scroll_area")
        self.g2_scroll_area.setGeometry(QRect(0, 0, 1134, 741))
        sizePolicy1.setHeightForWidth(
            self.g2_scroll_area.sizePolicy().hasHeightForWidth()
        )
        self.g2_scroll_area.setSizePolicy(sizePolicy1)
        self.gridLayout_10 = QGridLayout(self.g2_scroll_area)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.mp_g2 = PlotWidgetDev(self.g2_scroll_area)
        self.mp_g2.setObjectName("mp_g2")
        sizePolicy5.setHeightForWidth(self.mp_g2.sizePolicy().hasHeightForWidth())
        self.mp_g2.setSizePolicy(sizePolicy5)
        self.mp_g2.setMinimumSize(QSize(0, 0))
        self.mp_g2.setAutoFillBackground(False)

        self.gridLayout_10.addWidget(self.mp_g2, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.g2_scroll_area)

        self.gridLayout_8.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.splitter_2 = QSplitter(self.tab_6)
        self.splitter_2.setObjectName("splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Horizontal)
        self.groupBox = QGroupBox(self.splitter_2)
        self.groupBox.setObjectName("groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QSize(0, 0))
        self.groupBox.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_13 = QGridLayout(self.groupBox)
        self.gridLayout_13.setObjectName("gridLayout_13")
        self.gridLayout_11 = QGridLayout()
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")

        self.gridLayout_11.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")

        self.gridLayout_11.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")

        self.gridLayout_11.addWidget(self.label_7, 2, 0, 1, 1)

        self.g2_qmin = QDoubleSpinBox(self.groupBox)
        self.g2_qmin.setObjectName("g2_qmin")
        sizePolicy9 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.g2_qmin.sizePolicy().hasHeightForWidth())
        self.g2_qmin.setSizePolicy(sizePolicy9)
        self.g2_qmin.setDecimals(4)
        self.g2_qmin.setSingleStep(0.001000000000000)

        self.gridLayout_11.addWidget(self.g2_qmin, 0, 1, 1, 1)

        self.g2_qmax = QDoubleSpinBox(self.groupBox)
        self.g2_qmax.setObjectName("g2_qmax")
        sizePolicy9.setHeightForWidth(self.g2_qmax.sizePolicy().hasHeightForWidth())
        self.g2_qmax.setSizePolicy(sizePolicy9)
        self.g2_qmax.setDecimals(4)
        self.g2_qmax.setSingleStep(0.001000000000000)
        self.g2_qmax.setValue(0.010000000000000)

        self.gridLayout_11.addWidget(self.g2_qmax, 0, 2, 1, 1)

        self.g2_ymin = QDoubleSpinBox(self.groupBox)
        self.g2_ymin.setObjectName("g2_ymin")
        sizePolicy9.setHeightForWidth(self.g2_ymin.sizePolicy().hasHeightForWidth())
        self.g2_ymin.setSizePolicy(sizePolicy9)
        self.g2_ymin.setDecimals(3)
        self.g2_ymin.setMinimum(-1.000000000000000)
        self.g2_ymin.setSingleStep(0.010000000000000)
        self.g2_ymin.setValue(1.000000000000000)

        self.gridLayout_11.addWidget(self.g2_ymin, 2, 1, 1, 1)

        self.g2_ymax = QDoubleSpinBox(self.groupBox)
        self.g2_ymax.setObjectName("g2_ymax")
        sizePolicy9.setHeightForWidth(self.g2_ymax.sizePolicy().hasHeightForWidth())
        self.g2_ymax.setSizePolicy(sizePolicy9)
        self.g2_ymax.setDecimals(3)
        self.g2_ymax.setMinimum(-1.000000000000000)
        self.g2_ymax.setSingleStep(0.010000000000000)
        self.g2_ymax.setValue(1.800000000000000)

        self.gridLayout_11.addWidget(self.g2_ymax, 2, 2, 1, 1)

        self.g2_tmin = QLineEdit(self.groupBox)
        self.g2_tmin.setObjectName("g2_tmin")
        sizePolicy9.setHeightForWidth(self.g2_tmin.sizePolicy().hasHeightForWidth())
        self.g2_tmin.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_tmin, 1, 1, 1, 1)

        self.g2_tmax = QLineEdit(self.groupBox)
        self.g2_tmax.setObjectName("g2_tmax")
        sizePolicy9.setHeightForWidth(self.g2_tmax.sizePolicy().hasHeightForWidth())
        self.g2_tmax.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_tmax, 1, 2, 1, 1)

        self.g2_yauto = QCheckBox(self.groupBox)
        self.g2_yauto.setObjectName("g2_yauto")
        sizePolicy9.setHeightForWidth(self.g2_yauto.sizePolicy().hasHeightForWidth())
        self.g2_yauto.setSizePolicy(sizePolicy9)

        self.gridLayout_11.addWidget(self.g2_yauto, 2, 3, 1, 1)

        self.gridLayout_13.addLayout(self.gridLayout_11, 0, 1, 1, 1)

        self.gridLayout_19 = QGridLayout()
        self.gridLayout_19.setObjectName("gridLayout_19")
        self.pushButton_4 = QPushButton(self.groupBox)
        self.pushButton_4.setObjectName("pushButton_4")
        sizePolicy7.setHeightForWidth(
            self.pushButton_4.sizePolicy().hasHeightForWidth()
        )
        self.pushButton_4.setSizePolicy(sizePolicy7)
        self.pushButton_4.setMinimumSize(QSize(0, 0))

        self.gridLayout_19.addWidget(self.pushButton_4, 0, 0, 1, 2)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")

        self.gridLayout_19.addWidget(self.label, 2, 0, 1, 1)

        self.sb_g2_column = QSpinBox(self.groupBox)
        self.sb_g2_column.setObjectName("sb_g2_column")
        self.sb_g2_column.setMinimum(1)
        self.sb_g2_column.setMaximum(8)
        self.sb_g2_column.setSingleStep(1)
        self.sb_g2_column.setValue(4)

        self.gridLayout_19.addWidget(self.sb_g2_column, 1, 1, 1, 1)

        self.label_53 = QLabel(self.groupBox)
        self.label_53.setObjectName("label_53")

        self.gridLayout_19.addWidget(self.label_53, 3, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox)
        self.label_8.setObjectName("label_8")

        self.gridLayout_19.addWidget(self.label_8, 1, 0, 1, 1)

        self.sb_g2_offset = QDoubleSpinBox(self.groupBox)
        self.sb_g2_offset.setObjectName("sb_g2_offset")
        self.sb_g2_offset.setDecimals(3)
        self.sb_g2_offset.setSingleStep(0.005000000000000)

        self.gridLayout_19.addWidget(self.sb_g2_offset, 2, 1, 1, 1)

        self.g2_marker_size = QDoubleSpinBox(self.groupBox)
        self.g2_marker_size.setObjectName("g2_marker_size")
        self.g2_marker_size.setDecimals(1)
        self.g2_marker_size.setMinimum(1.000000000000000)
        self.g2_marker_size.setMaximum(15.000000000000000)
        self.g2_marker_size.setSingleStep(1.000000000000000)
        self.g2_marker_size.setValue(5.000000000000000)

        self.gridLayout_19.addWidget(self.g2_marker_size, 3, 1, 1, 1)

        self.g2_sub_baseline = QCheckBox(self.groupBox)
        self.g2_sub_baseline.setObjectName("g2_sub_baseline")
        sizePolicy9.setHeightForWidth(
            self.g2_sub_baseline.sizePolicy().hasHeightForWidth()
        )
        self.g2_sub_baseline.setSizePolicy(sizePolicy9)
        self.g2_sub_baseline.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_sub_baseline, 3, 2, 1, 3)

        self.g2_show_fit = QCheckBox(self.groupBox)
        self.g2_show_fit.setObjectName("g2_show_fit")
        sizePolicy9.setHeightForWidth(self.g2_show_fit.sizePolicy().hasHeightForWidth())
        self.g2_show_fit.setSizePolicy(sizePolicy9)
        self.g2_show_fit.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_show_fit, 2, 2, 1, 3)

        self.g2_show_label = QCheckBox(self.groupBox)
        self.g2_show_label.setObjectName("g2_show_label")
        sizePolicy9.setHeightForWidth(
            self.g2_show_label.sizePolicy().hasHeightForWidth()
        )
        self.g2_show_label.setSizePolicy(sizePolicy9)
        self.g2_show_label.setChecked(False)

        self.gridLayout_19.addWidget(self.g2_show_label, 1, 2, 1, 3)

        self.g2_plot_type = QComboBox(self.groupBox)
        self.g2_plot_type.addItem("")
        self.g2_plot_type.addItem("")
        self.g2_plot_type.addItem("")
        self.g2_plot_type.setObjectName("g2_plot_type")
        sizePolicy9.setHeightForWidth(
            self.g2_plot_type.sizePolicy().hasHeightForWidth()
        )
        self.g2_plot_type.setSizePolicy(sizePolicy9)

        self.gridLayout_19.addWidget(self.g2_plot_type, 0, 2, 1, 3)

        self.gridLayout_13.addLayout(self.gridLayout_19, 0, 0, 1, 1)

        self.splitter_2.addWidget(self.groupBox)
        self.groupBox_2 = QGroupBox(self.splitter_2)
        self.groupBox_2.setObjectName("groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setMinimumSize(QSize(0, 0))
        self.groupBox_2.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_14 = QGridLayout(self.groupBox_2)
        self.gridLayout_14.setObjectName("gridLayout_14")
        self.gridLayout_12 = QGridLayout()
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.g2_fmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_fmin.setObjectName("g2_fmin")
        self.g2_fmin.setDecimals(3)
        self.g2_fmin.setMinimum(0.501000000000000)
        self.g2_fmin.setMaximum(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_fmin, 3, 7, 1, 1)

        self.g2_fmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_fmax.setObjectName("g2_fmax")
        self.g2_fmax.setDecimals(3)
        self.g2_fmax.setMinimum(0.501000000000000)
        self.g2_fmax.setMaximum(1.000000000000000)
        self.g2_fmax.setValue(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_fmax, 3, 8, 1, 1)

        self.g2_c2min = QDoubleSpinBox(self.groupBox_2)
        self.g2_c2min.setObjectName("g2_c2min")
        self.g2_c2min.setDecimals(3)
        self.g2_c2min.setValue(0.500000000000000)

        self.gridLayout_12.addWidget(self.g2_c2min, 2, 7, 1, 1)

        self.g2_c2max = QDoubleSpinBox(self.groupBox_2)
        self.g2_c2max.setObjectName("g2_c2max")
        self.g2_c2max.setDecimals(3)
        self.g2_c2max.setValue(2.000000000000000)

        self.gridLayout_12.addWidget(self.g2_c2max, 2, 8, 1, 1)

        self.g2_b2max = QDoubleSpinBox(self.groupBox_2)
        self.g2_b2max.setObjectName("g2_b2max")
        self.g2_b2max.setDecimals(5)
        self.g2_b2max.setMaximum(9999.999900000000707)
        self.g2_b2max.setValue(1.000000000000000)

        self.gridLayout_12.addWidget(self.g2_b2max, 1, 8, 1, 1)

        self.g2_b2min = QDoubleSpinBox(self.groupBox_2)
        self.g2_b2min.setObjectName("g2_b2min")
        self.g2_b2min.setDecimals(5)
        self.g2_b2min.setMinimum(0.000010000000000)
        self.g2_b2min.setMaximum(999.999000000000024)
        self.g2_b2min.setValue(0.000010000000000)

        self.gridLayout_12.addWidget(self.g2_b2min, 1, 7, 1, 1)

        self.label_66 = QLabel(self.groupBox_2)
        self.label_66.setObjectName("label_66")

        self.gridLayout_12.addWidget(self.label_66, 2, 6, 1, 1)

        self.label_48 = QLabel(self.groupBox_2)
        self.label_48.setObjectName("label_48")

        self.gridLayout_12.addWidget(self.label_48, 3, 0, 1, 1)

        self.g2_c2fit = QCheckBox(self.groupBox_2)
        self.g2_c2fit.setObjectName("g2_c2fit")
        self.g2_c2fit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_c2fit, 2, 9, 1, 1)

        self.label_41 = QLabel(self.groupBox_2)
        self.label_41.setObjectName("label_41")

        self.gridLayout_12.addWidget(self.label_41, 3, 1, 1, 1)

        self.g2_dfit = QCheckBox(self.groupBox_2)
        self.g2_dfit.setObjectName("g2_dfit")
        self.g2_dfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_dfit, 3, 4, 1, 1)

        self.label_63 = QLabel(self.groupBox_2)
        self.label_63.setObjectName("label_63")

        self.gridLayout_12.addWidget(self.label_63, 3, 5, 1, 1)

        self.g2_ffit = QCheckBox(self.groupBox_2)
        self.g2_ffit.setObjectName("g2_ffit")
        self.g2_ffit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_ffit, 3, 9, 1, 1)

        self.g2_fitting_function = QComboBox(self.groupBox_2)
        self.g2_fitting_function.addItem("")
        self.g2_fitting_function.addItem("")
        self.g2_fitting_function.setObjectName("g2_fitting_function")

        self.gridLayout_12.addWidget(self.g2_fitting_function, 0, 5, 1, 5)

        self.label_67 = QLabel(self.groupBox_2)
        self.label_67.setObjectName("label_67")

        self.gridLayout_12.addWidget(self.label_67, 3, 6, 1, 1)

        self.g2_amin = QDoubleSpinBox(self.groupBox_2)
        self.g2_amin.setObjectName("g2_amin")
        self.g2_amin.setDecimals(3)
        self.g2_amin.setMaximum(999.999000000000024)
        self.g2_amin.setSingleStep(0.010000000000000)
        self.g2_amin.setValue(0.040000000000000)

        self.gridLayout_12.addWidget(self.g2_amin, 0, 2, 1, 1)

        self.g2_amax = QDoubleSpinBox(self.groupBox_2)
        self.g2_amax.setObjectName("g2_amax")
        self.g2_amax.setDecimals(3)
        self.g2_amax.setMaximum(999.999000000000024)
        self.g2_amax.setSingleStep(0.010000000000000)
        self.g2_amax.setValue(0.800000000000000)

        self.gridLayout_12.addWidget(self.g2_amax, 0, 3, 1, 1)

        self.g2_dmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_dmin.setObjectName("g2_dmin")
        self.g2_dmin.setDecimals(3)
        self.g2_dmin.setSingleStep(0.010000000000000)
        self.g2_dmin.setValue(0.950000000000000)

        self.gridLayout_12.addWidget(self.g2_dmin, 3, 2, 1, 1)

        self.g2_dmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_dmax.setObjectName("g2_dmax")
        self.g2_dmax.setDecimals(3)
        self.g2_dmax.setSingleStep(0.050000000000000)
        self.g2_dmax.setValue(1.050000000000000)

        self.gridLayout_12.addWidget(self.g2_dmax, 3, 3, 1, 1)

        self.g2_cmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_cmin.setObjectName("g2_cmin")
        self.g2_cmin.setDecimals(3)
        self.g2_cmin.setSingleStep(0.010000000000000)
        self.g2_cmin.setValue(0.500000000000000)

        self.gridLayout_12.addWidget(self.g2_cmin, 2, 2, 1, 1)

        self.g2_cmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_cmax.setObjectName("g2_cmax")
        self.g2_cmax.setDecimals(3)
        self.g2_cmax.setSingleStep(0.010000000000000)
        self.g2_cmax.setValue(2.000000000000000)

        self.gridLayout_12.addWidget(self.g2_cmax, 2, 3, 1, 1)

        self.g2_bmin = QDoubleSpinBox(self.groupBox_2)
        self.g2_bmin.setObjectName("g2_bmin")
        self.g2_bmin.setDecimals(5)
        self.g2_bmin.setMinimum(0.000010000000000)
        self.g2_bmin.setMaximum(999.999900000000025)
        self.g2_bmin.setValue(0.000010000000000)

        self.gridLayout_12.addWidget(self.g2_bmin, 1, 2, 1, 1)

        self.g2_bmax = QDoubleSpinBox(self.groupBox_2)
        self.g2_bmax.setObjectName("g2_bmax")
        self.g2_bmax.setDecimals(5)
        self.g2_bmax.setMaximum(9999.999900000000707)
        self.g2_bmax.setValue(100.000000000000000)

        self.gridLayout_12.addWidget(self.g2_bmax, 1, 3, 1, 1)

        self.label_45 = QLabel(self.groupBox_2)
        self.label_45.setObjectName("label_45")

        self.gridLayout_12.addWidget(self.label_45, 0, 0, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")

        self.gridLayout_12.addWidget(self.label_5, 0, 1, 1, 1)

        self.g2_afit = QCheckBox(self.groupBox_2)
        self.g2_afit.setObjectName("g2_afit")
        self.g2_afit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_afit, 0, 4, 1, 1)

        self.label_46 = QLabel(self.groupBox_2)
        self.label_46.setObjectName("label_46")

        self.gridLayout_12.addWidget(self.label_46, 1, 0, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")

        self.gridLayout_12.addWidget(self.label_6, 1, 1, 1, 1)

        self.g2_bfit = QCheckBox(self.groupBox_2)
        self.g2_bfit.setObjectName("g2_bfit")
        self.g2_bfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_bfit, 1, 4, 1, 1)

        self.label_65 = QLabel(self.groupBox_2)
        self.label_65.setObjectName("label_65")

        self.gridLayout_12.addWidget(self.label_65, 1, 5, 1, 1)

        self.label_64 = QLabel(self.groupBox_2)
        self.label_64.setObjectName("label_64")

        self.gridLayout_12.addWidget(self.label_64, 1, 6, 1, 1)

        self.g2_b2fit = QCheckBox(self.groupBox_2)
        self.g2_b2fit.setObjectName("g2_b2fit")
        self.g2_b2fit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_b2fit, 1, 9, 1, 1)

        self.label_47 = QLabel(self.groupBox_2)
        self.label_47.setObjectName("label_47")

        self.gridLayout_12.addWidget(self.label_47, 2, 0, 1, 1)

        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName("label_10")

        self.gridLayout_12.addWidget(self.label_10, 2, 1, 1, 1)

        self.g2_cfit = QCheckBox(self.groupBox_2)
        self.g2_cfit.setObjectName("g2_cfit")
        self.g2_cfit.setChecked(True)

        self.gridLayout_12.addWidget(self.g2_cfit, 2, 4, 1, 1)

        self.label_62 = QLabel(self.groupBox_2)
        self.label_62.setObjectName("label_62")

        self.gridLayout_12.addWidget(self.label_62, 2, 5, 1, 1)

        self.show_g2_fit_summary = QPushButton(self.groupBox_2)
        self.show_g2_fit_summary.setObjectName("show_g2_fit_summary")
        sizePolicy2.setHeightForWidth(
            self.show_g2_fit_summary.sizePolicy().hasHeightForWidth()
        )
        self.show_g2_fit_summary.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.show_g2_fit_summary, 0, 10, 1, 1)

        self.btn_g2_export = QPushButton(self.groupBox_2)
        self.btn_g2_export.setObjectName("btn_g2_export")
        sizePolicy2.setHeightForWidth(
            self.btn_g2_export.sizePolicy().hasHeightForWidth()
        )
        self.btn_g2_export.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.btn_g2_export, 1, 10, 1, 1)

        self.btn_g2_refit = QPushButton(self.groupBox_2)
        self.btn_g2_refit.setObjectName("btn_g2_refit")
        sizePolicy2.setHeightForWidth(
            self.btn_g2_refit.sizePolicy().hasHeightForWidth()
        )
        self.btn_g2_refit.setSizePolicy(sizePolicy2)

        self.gridLayout_12.addWidget(self.btn_g2_refit, 2, 10, 2, 1)

        self.gridLayout_14.addLayout(self.gridLayout_12, 0, 0, 3, 1)

        self.splitter_2.addWidget(self.groupBox_2)

        self.gridLayout_8.addWidget(self.splitter_2, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName("tab_7")
        self.gridLayout_22 = QGridLayout(self.tab_7)
        self.gridLayout_22.setObjectName("gridLayout_22")
        self.mp_tauq = MplCanvasBarV(self.tab_7)
        self.mp_tauq.setObjectName("mp_tauq")
        sizePolicy6.setHeightForWidth(self.mp_tauq.sizePolicy().hasHeightForWidth())
        self.mp_tauq.setSizePolicy(sizePolicy6)

        self.gridLayout_22.addWidget(self.mp_tauq, 0, 0, 1, 1)

        self.mp_tauq_pre = MplCanvasBarV(self.tab_7)
        self.mp_tauq_pre.setObjectName("mp_tauq_pre")
        sizePolicy6.setHeightForWidth(self.mp_tauq_pre.sizePolicy().hasHeightForWidth())
        self.mp_tauq_pre.setSizePolicy(sizePolicy6)

        self.gridLayout_22.addWidget(self.mp_tauq_pre, 0, 1, 1, 1)

        self.groupBox_5 = QGroupBox(self.tab_7)
        self.groupBox_5.setObjectName("groupBox_5")
        sizePolicy5.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy5)
        self.groupBox_5.setMinimumSize(QSize(0, 0))
        self.groupBox_5.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_39 = QGridLayout(self.groupBox_5)
        self.gridLayout_39.setObjectName("gridLayout_39")
        self.gridLayout_38 = QGridLayout()
        self.gridLayout_38.setObjectName("gridLayout_38")
        self.gridLayout_15 = QGridLayout()
        self.gridLayout_15.setObjectName("gridLayout_15")
        self.label_15 = QLabel(self.groupBox_5)
        self.label_15.setObjectName("label_15")

        self.gridLayout_15.addWidget(self.label_15, 0, 0, 1, 1)

        self.cb_tauq_type = QComboBox(self.groupBox_5)
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.addItem("")
        self.cb_tauq_type.setObjectName("cb_tauq_type")

        self.gridLayout_15.addWidget(self.cb_tauq_type, 0, 1, 1, 1)

        self.label_18 = QLabel(self.groupBox_5)
        self.label_18.setObjectName("label_18")

        self.gridLayout_15.addWidget(self.label_18, 1, 0, 1, 1)

        self.sb_tauq_offset = QDoubleSpinBox(self.groupBox_5)
        self.sb_tauq_offset.setObjectName("sb_tauq_offset")
        self.sb_tauq_offset.setMinimum(-2.000000000000000)
        self.sb_tauq_offset.setMaximum(2.000000000000000)
        self.sb_tauq_offset.setSingleStep(0.200000000000000)
        self.sb_tauq_offset.setValue(0.000000000000000)

        self.gridLayout_15.addWidget(self.sb_tauq_offset, 1, 1, 1, 1)

        self.gridLayout_38.addLayout(self.gridLayout_15, 1, 1, 1, 1)

        self.gridLayout_21 = QGridLayout()
        self.gridLayout_21.setObjectName("gridLayout_21")
        self.tauq_amax = QLineEdit(self.groupBox_5)
        self.tauq_amax.setObjectName("tauq_amax")

        self.gridLayout_21.addWidget(self.tauq_amax, 0, 2, 1, 1)

        self.tauq_qmax = QLineEdit(self.groupBox_5)
        self.tauq_qmax.setObjectName("tauq_qmax")

        self.gridLayout_21.addWidget(self.tauq_qmax, 2, 2, 1, 1)

        self.tauq_bfit = QCheckBox(self.groupBox_5)
        self.tauq_bfit.setObjectName("tauq_bfit")
        self.tauq_bfit.setChecked(True)

        self.gridLayout_21.addWidget(self.tauq_bfit, 1, 3, 1, 1)

        self.label_44 = QLabel(self.groupBox_5)
        self.label_44.setObjectName("label_44")

        self.gridLayout_21.addWidget(self.label_44, 0, 0, 1, 1)

        self.tauq_bmin = QLineEdit(self.groupBox_5)
        self.tauq_bmin.setObjectName("tauq_bmin")

        self.gridLayout_21.addWidget(self.tauq_bmin, 1, 1, 1, 1)

        self.label_42 = QLabel(self.groupBox_5)
        self.label_42.setObjectName("label_42")

        self.gridLayout_21.addWidget(self.label_42, 1, 0, 1, 1)

        self.tauq_amin = QLineEdit(self.groupBox_5)
        self.tauq_amin.setObjectName("tauq_amin")

        self.gridLayout_21.addWidget(self.tauq_amin, 0, 1, 1, 1)

        self.tauq_afit = QCheckBox(self.groupBox_5)
        self.tauq_afit.setObjectName("tauq_afit")
        self.tauq_afit.setChecked(True)

        self.gridLayout_21.addWidget(self.tauq_afit, 0, 3, 1, 1)

        self.tauq_bmax = QLineEdit(self.groupBox_5)
        self.tauq_bmax.setObjectName("tauq_bmax")

        self.gridLayout_21.addWidget(self.tauq_bmax, 1, 2, 1, 1)

        self.tauq_qmin = QLineEdit(self.groupBox_5)
        self.tauq_qmin.setObjectName("tauq_qmin")

        self.gridLayout_21.addWidget(self.tauq_qmin, 2, 1, 1, 1)

        self.label_43 = QLabel(self.groupBox_5)
        self.label_43.setObjectName("label_43")

        self.gridLayout_21.addWidget(self.label_43, 2, 0, 1, 1)

        self.gridLayout_38.addLayout(self.gridLayout_21, 0, 0, 1, 2)

        self.pushButton_8 = QPushButton(self.groupBox_5)
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_8.setMinimumSize(QSize(120, 80))

        self.gridLayout_38.addWidget(self.pushButton_8, 1, 0, 1, 1)

        self.gridLayout_39.addLayout(self.gridLayout_38, 0, 0, 1, 1)

        self.tauq_msg = DataTreeWidget(self.groupBox_5)
        self.tauq_msg.setObjectName("tauq_msg")

        self.gridLayout_39.addWidget(self.tauq_msg, 0, 1, 1, 1)

        self.gridLayout_22.addWidget(self.groupBox_5, 1, 0, 1, 2)

        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName("tab_8")
        self.gridLayout_33 = QGridLayout(self.tab_8)
        self.gridLayout_33.setObjectName("gridLayout_33")
        self.splitter_4 = QSplitter(self.tab_8)
        self.splitter_4.setObjectName("splitter_4")
        self.splitter_4.setOrientation(Qt.Orientation.Vertical)
        self.mp_2t_map = GraphicsLayoutWidget(self.splitter_4)
        self.mp_2t_map.setObjectName("mp_2t_map")
        sizePolicy10 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(1)
        sizePolicy10.setHeightForWidth(self.mp_2t_map.sizePolicy().hasHeightForWidth())
        self.mp_2t_map.setSizePolicy(sizePolicy10)
        self.mp_2t_map.setMinimumSize(QSize(300, 300))
        self.splitter_4.addWidget(self.mp_2t_map)
        self.mp_2t = ImageViewPlotItem(self.splitter_4)
        self.mp_2t.setObjectName("mp_2t")
        sizePolicy11 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(2)
        sizePolicy11.setHeightForWidth(self.mp_2t.sizePolicy().hasHeightForWidth())
        self.mp_2t.setSizePolicy(sizePolicy11)
        self.mp_2t.setMinimumSize(QSize(300, 300))
        self.splitter_4.addWidget(self.mp_2t)

        self.gridLayout_33.addWidget(self.splitter_4, 0, 0, 1, 1)

        self.groupBox_11 = QGroupBox(self.tab_8)
        self.groupBox_11.setObjectName("groupBox_11")
        sizePolicy5.setHeightForWidth(self.groupBox_11.sizePolicy().hasHeightForWidth())
        self.groupBox_11.setSizePolicy(sizePolicy5)
        self.groupBox_11.setMinimumSize(QSize(0, 0))
        self.groupBox_11.setMaximumSize(QSize(16777215, 65536))
        self.gridLayout_37 = QGridLayout(self.groupBox_11)
        self.gridLayout_37.setObjectName("gridLayout_37")
        self.horizontalSpacer_5 = QSpacerItem(
            279, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.gridLayout_37.addItem(self.horizontalSpacer_5, 0, 0, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.cb_twotime_saxs_cmap = QComboBox(self.groupBox_11)
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.addItem("")
        self.cb_twotime_saxs_cmap.setObjectName("cb_twotime_saxs_cmap")

        self.gridLayout_2.addWidget(self.cb_twotime_saxs_cmap, 0, 2, 1, 3)

        self.pushButton_12 = QPushButton(self.groupBox_11)
        self.pushButton_12.setObjectName("pushButton_12")

        self.gridLayout_2.addWidget(self.pushButton_12, 1, 9, 1, 3)

        self.label_35 = QLabel(self.groupBox_11)
        self.label_35.setObjectName("label_35")

        self.gridLayout_2.addWidget(self.label_35, 0, 0, 1, 2)

        self.label_28 = QLabel(self.groupBox_11)
        self.label_28.setObjectName("label_28")

        self.gridLayout_2.addWidget(self.label_28, 1, 0, 1, 2)

        self.twotime_autocrop = QCheckBox(self.groupBox_11)
        self.twotime_autocrop.setObjectName("twotime_autocrop")
        self.twotime_autocrop.setChecked(True)

        self.gridLayout_2.addWidget(self.twotime_autocrop, 0, 8, 1, 1)

        self.cb_twotime_cmap = QComboBox(self.groupBox_11)
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.addItem("")
        self.cb_twotime_cmap.setObjectName("cb_twotime_cmap")
        sizePolicy9.setHeightForWidth(
            self.cb_twotime_cmap.sizePolicy().hasHeightForWidth()
        )
        self.cb_twotime_cmap.setSizePolicy(sizePolicy9)
        self.cb_twotime_cmap.setMinimumSize(QSize(0, 0))

        self.gridLayout_2.addWidget(self.cb_twotime_cmap, 1, 2, 1, 3)

        self.c2_min = QDoubleSpinBox(self.groupBox_11)
        self.c2_min.setObjectName("c2_min")
        self.c2_min.setMinimum(-1.000000000000000)
        self.c2_min.setValue(0.800000000000000)

        self.gridLayout_2.addWidget(self.c2_min, 1, 7, 1, 1)

        self.twotime_correct_diag = QCheckBox(self.groupBox_11)
        self.twotime_correct_diag.setObjectName("twotime_correct_diag")

        self.gridLayout_2.addWidget(self.twotime_correct_diag, 0, 9, 1, 3)

        self.c2_max = QDoubleSpinBox(self.groupBox_11)
        self.c2_max.setObjectName("c2_max")
        self.c2_max.setMinimum(-1.000000000000000)
        self.c2_max.setValue(2.200000000000000)

        self.gridLayout_2.addWidget(self.c2_max, 1, 8, 1, 1)

        self.label_57 = QLabel(self.groupBox_11)
        self.label_57.setObjectName("label_57")

        self.gridLayout_2.addWidget(self.label_57, 1, 5, 1, 2)

        self.gridLayout_37.addLayout(self.gridLayout_2, 0, 1, 1, 1)

        self.horizontalSpacer_10 = QSpacerItem(
            278, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.gridLayout_37.addItem(self.horizontalSpacer_10, 0, 3, 1, 1)

        self.gridLayout_33.addWidget(self.groupBox_11, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_8, "")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_9 = QGridLayout(self.tab)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.comboBox_qmap_target = QComboBox(self.tab)
        self.comboBox_qmap_target.addItem("")
        self.comboBox_qmap_target.addItem("")
        self.comboBox_qmap_target.addItem("")
        self.comboBox_qmap_target.setObjectName("comboBox_qmap_target")

        self.gridLayout_9.addWidget(self.comboBox_qmap_target, 1, 1, 1, 1)

        self.label_27 = QLabel(self.tab)
        self.label_27.setObjectName("label_27")

        self.gridLayout_9.addWidget(self.label_27, 1, 0, 1, 1)

        self.pg_qmap = ImageView(self.tab)
        self.pg_qmap.setObjectName("pg_qmap")

        self.gridLayout_9.addWidget(self.pg_qmap, 0, 0, 1, 2)

        self.tabWidget.addTab(self.tab, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName("tab_5")
        self.gridLayout_36 = QGridLayout(self.tab_5)
        self.gridLayout_36.setObjectName("gridLayout_36")
        self.groupBox_10 = QGroupBox(self.tab_5)
        self.groupBox_10.setObjectName("groupBox_10")
        self.gridLayout_31 = QGridLayout(self.groupBox_10)
        self.gridLayout_31.setObjectName("gridLayout_31")
        self.mp_avg_g2 = PlotWidgetDev(self.groupBox_10)
        self.mp_avg_g2.setObjectName("mp_avg_g2")
        sizePolicy1.setHeightForWidth(self.mp_avg_g2.sizePolicy().hasHeightForWidth())
        self.mp_avg_g2.setSizePolicy(sizePolicy1)
        self.mp_avg_g2.setMinimumSize(QSize(0, 300))

        self.gridLayout_31.addWidget(self.mp_avg_g2, 0, 0, 1, 1)

        self.gridLayout_36.addWidget(self.groupBox_10, 0, 0, 1, 3)

        self.groupBox_8 = QGroupBox(self.tab_5)
        self.groupBox_8.setObjectName("groupBox_8")
        self.gridLayout_30 = QGridLayout(self.groupBox_8)
        self.gridLayout_30.setObjectName("gridLayout_30")
        self.gridLayout_28 = QGridLayout()
        self.gridLayout_28.setObjectName("gridLayout_28")
        self.max_thread_count = QSpinBox(self.groupBox_8)
        self.max_thread_count.setObjectName("max_thread_count")
        self.max_thread_count.setMinimum(1)
        self.max_thread_count.setMaximum(32)
        self.max_thread_count.setSingleStep(1)
        self.max_thread_count.setValue(4)

        self.gridLayout_28.addWidget(self.max_thread_count, 0, 5, 1, 2)

        self.avg_blmax = QDoubleSpinBox(self.groupBox_8)
        self.avg_blmax.setObjectName("avg_blmax")
        self.avg_blmax.setDecimals(3)
        self.avg_blmax.setMinimum(0.900000000000000)
        self.avg_blmax.setMaximum(10.000000000000000)
        self.avg_blmax.setSingleStep(0.010000000000000)
        self.avg_blmax.setValue(1.050000000000000)

        self.gridLayout_28.addWidget(self.avg_blmax, 2, 5, 1, 2)

        self.avg_save_path = QLineEdit(self.groupBox_8)
        self.avg_save_path.setObjectName("avg_save_path")
        self.avg_save_path.setClearButtonEnabled(True)

        self.gridLayout_28.addWidget(self.avg_save_path, 6, 2, 1, 4)

        self.label_39 = QLabel(self.groupBox_8)
        self.label_39.setObjectName("label_39")

        self.gridLayout_28.addWidget(self.label_39, 2, 4, 1, 1)

        self.btn_set_average_save_name = QPushButton(self.groupBox_8)
        self.btn_set_average_save_name.setObjectName("btn_set_average_save_name")
        self.btn_set_average_save_name.setMinimumSize(QSize(10, 0))

        self.gridLayout_28.addWidget(self.btn_set_average_save_name, 7, 6, 1, 1)

        self.label_17 = QLabel(self.groupBox_8)
        self.label_17.setObjectName("label_17")

        self.gridLayout_28.addWidget(self.label_17, 0, 0, 1, 2)

        self.label_32 = QLabel(self.groupBox_8)
        self.label_32.setObjectName("label_32")

        self.gridLayout_28.addWidget(self.label_32, 1, 0, 1, 1)

        self.label_25 = QLabel(self.groupBox_8)
        self.label_25.setObjectName("label_25")

        self.gridLayout_28.addWidget(self.label_25, 2, 0, 1, 1)

        self.label_19 = QLabel(self.groupBox_8)
        self.label_19.setObjectName("label_19")

        self.gridLayout_28.addWidget(self.label_19, 7, 0, 1, 2)

        self.bx_avg_G2IPIF = QCheckBox(self.groupBox_8)
        self.bx_avg_G2IPIF.setObjectName("bx_avg_G2IPIF")

        self.gridLayout_28.addWidget(self.bx_avg_G2IPIF, 3, 5, 3, 2)

        self.avg_window = QSpinBox(self.groupBox_8)
        self.avg_window.setObjectName("avg_window")
        self.avg_window.setMinimum(1)
        self.avg_window.setValue(10)

        self.gridLayout_28.addWidget(self.avg_window, 1, 5, 1, 2)

        self.bx_avg_g2g2err = QCheckBox(self.groupBox_8)
        self.bx_avg_g2g2err.setObjectName("bx_avg_g2g2err")
        self.bx_avg_g2g2err.setChecked(True)

        self.gridLayout_28.addWidget(self.bx_avg_g2g2err, 3, 4, 3, 1)

        self.avg_save_name = QLineEdit(self.groupBox_8)
        self.avg_save_name.setObjectName("avg_save_name")
        self.avg_save_name.setClearButtonEnabled(True)

        self.gridLayout_28.addWidget(self.avg_save_name, 7, 2, 1, 4)

        self.label_20 = QLabel(self.groupBox_8)
        self.label_20.setObjectName("label_20")

        self.gridLayout_28.addWidget(self.label_20, 6, 0, 1, 2)

        self.btn_set_average_save_path = QPushButton(self.groupBox_8)
        self.btn_set_average_save_path.setObjectName("btn_set_average_save_path")
        self.btn_set_average_save_path.setMinimumSize(QSize(10, 0))

        self.gridLayout_28.addWidget(self.btn_set_average_save_path, 6, 6, 1, 1)

        self.bx_avg_saxs = QCheckBox(self.groupBox_8)
        self.bx_avg_saxs.setObjectName("bx_avg_saxs")
        self.bx_avg_saxs.setChecked(True)

        self.gridLayout_28.addWidget(self.bx_avg_saxs, 3, 3, 3, 1)

        self.label_26 = QLabel(self.groupBox_8)
        self.label_26.setObjectName("label_26")

        self.gridLayout_28.addWidget(self.label_26, 3, 0, 3, 3)

        self.label_33 = QLabel(self.groupBox_8)
        self.label_33.setObjectName("label_33")

        self.gridLayout_28.addWidget(self.label_33, 1, 4, 1, 1)

        self.label_40 = QLabel(self.groupBox_8)
        self.label_40.setObjectName("label_40")

        self.gridLayout_28.addWidget(self.label_40, 0, 4, 1, 1)

        self.cb_avg_chunk_size = QComboBox(self.groupBox_8)
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.addItem("")
        self.cb_avg_chunk_size.setObjectName("cb_avg_chunk_size")
        self.cb_avg_chunk_size.setMaximumSize(QSize(80, 16777215))

        self.gridLayout_28.addWidget(self.cb_avg_chunk_size, 0, 2, 1, 2)

        self.avg_qindex = QSpinBox(self.groupBox_8)
        self.avg_qindex.setObjectName("avg_qindex")
        self.avg_qindex.setMaximum(999)
        self.avg_qindex.setValue(5)

        self.gridLayout_28.addWidget(self.avg_qindex, 1, 1, 1, 3)

        self.avg_blmin = QDoubleSpinBox(self.groupBox_8)
        self.avg_blmin.setObjectName("avg_blmin")
        self.avg_blmin.setDecimals(3)
        self.avg_blmin.setMaximum(10.000000000000000)
        self.avg_blmin.setSingleStep(0.010000000000000)
        self.avg_blmin.setValue(0.950000000000000)

        self.gridLayout_28.addWidget(self.avg_blmin, 2, 1, 1, 3)

        self.gridLayout_30.addLayout(self.gridLayout_28, 0, 0, 1, 1)

        self.gridLayout_36.addWidget(self.groupBox_8, 1, 0, 1, 1)

        self.groupBox_12 = QGroupBox(self.tab_5)
        self.groupBox_12.setObjectName("groupBox_12")
        sizePolicy12 = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        sizePolicy12.setHorizontalStretch(0)
        sizePolicy12.setVerticalStretch(0)
        sizePolicy12.setHeightForWidth(
            self.groupBox_12.sizePolicy().hasHeightForWidth()
        )
        self.groupBox_12.setSizePolicy(sizePolicy12)
        self.gridLayout_35 = QGridLayout(self.groupBox_12)
        self.gridLayout_35.setObjectName("gridLayout_35")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.btn_submit_job = QPushButton(self.groupBox_12)
        self.btn_submit_job.setObjectName("btn_submit_job")
        sizePolicy7.setHeightForWidth(
            self.btn_submit_job.sizePolicy().hasHeightForWidth()
        )
        self.btn_submit_job.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_submit_job)

        self.avg_job_pop = QPushButton(self.groupBox_12)
        self.avg_job_pop.setObjectName("avg_job_pop")
        sizePolicy7.setHeightForWidth(self.avg_job_pop.sizePolicy().hasHeightForWidth())
        self.avg_job_pop.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.avg_job_pop)

        self.btn_avg_jobinfo = QPushButton(self.groupBox_12)
        self.btn_avg_jobinfo.setObjectName("btn_avg_jobinfo")
        sizePolicy7.setHeightForWidth(
            self.btn_avg_jobinfo.sizePolicy().hasHeightForWidth()
        )
        self.btn_avg_jobinfo.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_avg_jobinfo)

        self.btn_avg_kill = QPushButton(self.groupBox_12)
        self.btn_avg_kill.setObjectName("btn_avg_kill")

        self.verticalLayout_3.addWidget(self.btn_avg_kill)

        self.btn_start_avg_job = QPushButton(self.groupBox_12)
        self.btn_start_avg_job.setObjectName("btn_start_avg_job")
        sizePolicy7.setHeightForWidth(
            self.btn_start_avg_job.sizePolicy().hasHeightForWidth()
        )
        self.btn_start_avg_job.setSizePolicy(sizePolicy7)

        self.verticalLayout_3.addWidget(self.btn_start_avg_job)

        self.gridLayout_35.addLayout(self.verticalLayout_3, 0, 0, 1, 1)

        self.gridLayout_36.addWidget(self.groupBox_12, 1, 1, 1, 1)

        self.groupBox_9 = QGroupBox(self.tab_5)
        self.groupBox_9.setObjectName("groupBox_9")
        sizePolicy5.setHeightForWidth(self.groupBox_9.sizePolicy().hasHeightForWidth())
        self.groupBox_9.setSizePolicy(sizePolicy5)
        self.gridLayout_29 = QGridLayout(self.groupBox_9)
        self.gridLayout_29.setObjectName("gridLayout_29")
        self.avg_job_table = QTableView(self.groupBox_9)
        self.avg_job_table.setObjectName("avg_job_table")
        sizePolicy5.setHeightForWidth(
            self.avg_job_table.sizePolicy().hasHeightForWidth()
        )
        self.avg_job_table.setSizePolicy(sizePolicy5)
        self.avg_job_table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.avg_job_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.avg_job_table.horizontalHeader().setMinimumSectionSize(19)
        self.avg_job_table.horizontalHeader().setDefaultSectionSize(100)
        self.avg_job_table.horizontalHeader().setStretchLastSection(True)
        self.avg_job_table.verticalHeader().setDefaultSectionSize(30)

        self.gridLayout_29.addWidget(self.avg_job_table, 0, 0, 1, 2)

        self.gridLayout_36.addWidget(self.groupBox_9, 1, 2, 1, 1)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName("tab_9")
        self.gridLayout_7 = QGridLayout(self.tab_9)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.hdf_info = ParameterTree(self.tab_9)
        self.hdf_info.setObjectName("hdf_info")
        sizePolicy13 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
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
        self.statusbar.setObjectName("statusbar")
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
        QWidget.setTabOrder(self.cb_saxs2D_type, self.pushButton_plot_saxs2d)
        QWidget.setTabOrder(self.pushButton_plot_saxs2d, self.cb_saxs_type)
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
        QWidget.setTabOrder(self.cb_stab_norm, self.sb_intt_max)
        QWidget.setTabOrder(self.sb_intt_max, self.sb_window)
        QWidget.setTabOrder(self.sb_window, self.sb_intt_sampling)
        QWidget.setTabOrder(self.sb_intt_sampling, self.intt_xlabel)
        QWidget.setTabOrder(self.intt_xlabel, self.pushButton_4)
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
        QWidget.setTabOrder(self.saxs2d_display, self.cb_twotime_saxs_cmap)
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
        self.sb_window.valueChanged.connect(self.pushButton_plot_intt.click)
        self.sb_intt_sampling.valueChanged.connect(self.pushButton_plot_intt.click)
        self.sb_stab_offset.valueChanged.connect(self.pushButton_plot_stability.click)
        self.pushButton_3.clicked.connect(mainWindow.remove_target)
        self.cb_saxs2D_type.currentIndexChanged.connect(
            self.pushButton_plot_saxs2d.click
        )
        self.cb_stab_type.currentIndexChanged.connect(
            self.pushButton_plot_stability.click
        )
        self.sb_saxs_offset.valueChanged.connect(self.pushButton_plot_saxs1d.click)
        self.pushButton.clicked.connect(mainWindow.load_path)
        self.cb_saxs2D_cmap.currentIndexChanged.connect(
            self.pushButton_plot_saxs2d.click
        )
        self.pushButton_2.clicked.connect(mainWindow.add_target)
        self.cb_saxs_norm.currentIndexChanged.connect(self.pushButton_plot_saxs1d.click)
        self.saxs2d_rotate.stateChanged.connect(self.pushButton_plot_saxs2d.click)
        self.intt_xlabel.currentIndexChanged.connect(self.pushButton_plot_intt.click)
        self.pushButton_11.clicked.connect(mainWindow.reload_source)
        self.cb_saxs_type.currentIndexChanged.connect(self.pushButton_plot_saxs1d.click)
        self.cb_stab_norm.currentIndexChanged.connect(
            self.pushButton_plot_stability.click
        )
        self.pushButton_12.clicked["bool"].connect(mainWindow.plot_twotime)
        self.sb_intt_max.valueChanged.connect(self.pushButton_plot_intt.click)
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
        self.saxs1d_qmin.valueChanged.connect(self.pushButton_plot_saxs1d.click)
        self.saxs1d_qmax.valueChanged.connect(self.pushButton_plot_saxs1d.click)
        self.g2_show_fit.toggled.connect(self.g2_sub_baseline.setEnabled)
        self.g2_sub_baseline.stateChanged.connect(self.pushButton_4.click)
        self.saxs1d_legend_loc.currentIndexChanged.connect(
            self.pushButton_plot_saxs1d.click
        )
        self.box_target.clicked.connect(self.list_view_target.clearSelection)
        self.sb_saxs_marker_size.valueChanged.connect(self.pushButton_plot_saxs1d.click)
        self.saxs1d_sampling.valueChanged.connect(self.pushButton_plot_saxs1d.click)
        self.g2_afit.toggled.connect(self.g2_amin.setEnabled)
        self.g2_bfit.toggled.connect(self.g2_bmin.setEnabled)
        self.g2_cfit.toggled.connect(self.g2_cmin.setEnabled)
        self.g2_dfit.toggled.connect(self.g2_dmin.setEnabled)
        self.g2_b2fit.toggled.connect(self.g2_b2min.setEnabled)
        self.g2_c2fit.toggled.connect(self.g2_c2min.setEnabled)
        self.g2_ffit.toggled.connect(self.g2_fmin.setEnabled)
        self.box_all_phi.stateChanged.connect(self.pushButton_plot_saxs1d.click)
        self.saxs1d_lb_type.currentIndexChanged.connect(
            self.pushButton_plot_saxs1d.click
        )
        self.cb_sub_bkg.toggled.connect(self.le_bkg_fname.setEnabled)
        self.cb_sub_bkg.toggled.connect(self.btn_select_bkgfile.setEnabled)
        self.cb_sub_bkg.toggled.connect(self.bkg_weight.setEnabled)
        self.box_show_phi_roi.toggled.connect(self.box_show_roi.setDisabled)
        self.box_show_phi_roi.toggled.connect(self.box_all_phi.setDisabled)
        self.filter_str.textChanged.connect(mainWindow.apply_filter_to_source)

        self.tabWidget.setCurrentIndex(1)
        self.cb_saxs_type.setCurrentIndex(3)
        self.cb_stab_type.setCurrentIndex(3)
        self.cb_stab_norm.setCurrentIndex(0)
        self.cb_tauq_type.setCurrentIndex(3)
        self.cb_avg_chunk_size.setCurrentIndex(2)

        QMetaObject.connectSlotsByName(mainWindow)

    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(
            QCoreApplication.translate("mainWindow", "pyXPCSViewer", None)
        )
        self.label_2.setText(QCoreApplication.translate("mainWindow", "Path:", None))
        self.label_56.setText(QCoreApplication.translate("mainWindow", "Sort:", None))
        self.sort_method.setItemText(
            0, QCoreApplication.translate("mainWindow", "Filename", None)
        )
        self.sort_method.setItemText(
            1, QCoreApplication.translate("mainWindow", "Filename-reverse", None)
        )
        self.sort_method.setItemText(
            2, QCoreApplication.translate("mainWindow", "Index", None)
        )
        self.sort_method.setItemText(
            3, QCoreApplication.translate("mainWindow", "Index-reverse", None)
        )
        self.sort_method.setItemText(
            4, QCoreApplication.translate("mainWindow", "Time", None)
        )
        self.sort_method.setItemText(
            5, QCoreApplication.translate("mainWindow", "Time-reverse", None)
        )

        self.pushButton_11.setText(
            QCoreApplication.translate("mainWindow", "reload", None)
        )
        self.pushButton.setText(
            QCoreApplication.translate("mainWindow", "browse", None)
        )
        self.box_source.setTitle(
            QCoreApplication.translate("mainWindow", "Source:", None)
        )
        self.filter_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "prefix is", None)
        )
        self.filter_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "contains", None)
        )

        self.filter_str.setPlaceholderText(
            QCoreApplication.translate(
                "mainWindow", "filter, press enter to add files", None
            )
        )
        self.pushButton_2.setText(QCoreApplication.translate("mainWindow", "add", None))
        self.pushButton_3.setText(
            QCoreApplication.translate("mainWindow", "remove", None)
        )
        self.box_target.setTitle(
            QCoreApplication.translate("mainWindow", "Target:", None)
        )
        self.btn_deselect.setText(
            QCoreApplication.translate("mainWindow", "de-select", None)
        )
        self.btn_up.setText(QCoreApplication.translate("mainWindow", "up", None))
        self.btn_down.setText(QCoreApplication.translate("mainWindow", "down", None))
        self.label_38.setText(
            QCoreApplication.translate("mainWindow", "coordinates:", None)
        )
        self.groupBox_3.setTitle(
            QCoreApplication.translate("mainWindow", "SAXS 2D Plot Setting", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            0, QCoreApplication.translate("mainWindow", "jet", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            1, QCoreApplication.translate("mainWindow", "hot", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            2, QCoreApplication.translate("mainWindow", "plasma", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            3, QCoreApplication.translate("mainWindow", "viridis", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            4, QCoreApplication.translate("mainWindow", "magma", None)
        )
        self.cb_saxs2D_cmap.setItemText(
            5, QCoreApplication.translate("mainWindow", "gray", None)
        )

        self.label_50.setText(
            QCoreApplication.translate("mainWindow", "min-max:", None)
        )
        self.label_13.setText(QCoreApplication.translate("mainWindow", "cmap:", None))
        self.cb_saxs2D_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "log", None)
        )
        self.cb_saxs2D_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "linear", None)
        )

        self.pushButton_plot_saxs2d.setText(
            QCoreApplication.translate("mainWindow", "Plot 2D SAXS", None)
        )
        self.saxs2d_autorange.setText(
            QCoreApplication.translate("mainWindow", "auto-range", None)
        )
        self.label_12.setText(QCoreApplication.translate("mainWindow", "type:", None))
        self.saxs2d_rotate.setText(
            QCoreApplication.translate("mainWindow", "rotate", None)
        )
        self.groupBox_16.setTitle(QCoreApplication.translate("mainWindow", "ROI", None))
        self.label_58.setText(QCoreApplication.translate("mainWindow", "type:", None))
        self.cb_saxs2D_roi_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "Q-Wedge", None)
        )
        self.cb_saxs2D_roi_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "Phi-Ring", None)
        )

        self.label_60.setText(QCoreApplication.translate("mainWindow", "color:", None))
        self.cb_saxs2D_roi_color.setItemText(
            0, QCoreApplication.translate("mainWindow", "green", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            1, QCoreApplication.translate("mainWindow", "yellow", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            2, QCoreApplication.translate("mainWindow", "blue", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            3, QCoreApplication.translate("mainWindow", "red", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            4, QCoreApplication.translate("mainWindow", "cyan", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            5, QCoreApplication.translate("mainWindow", "magenta", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            6, QCoreApplication.translate("mainWindow", "black", None)
        )
        self.cb_saxs2D_roi_color.setItemText(
            7, QCoreApplication.translate("mainWindow", "white", None)
        )

        self.label_61.setText(
            QCoreApplication.translate("mainWindow", "linewidth:", None)
        )
        self.pushButton_6.setText(QCoreApplication.translate("mainWindow", "Add", None))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab1_1),
            QCoreApplication.translate("mainWindow", "SAXS-2D", None),
        )
        self.groupBox_6.setTitle(
            QCoreApplication.translate("mainWindow", "SAXS 1D Plot Setting", None)
        )
        self.groupBox_14.setTitle(
            QCoreApplication.translate("mainWindow", "Background", None)
        )
        self.cb_sub_bkg.setText(
            QCoreApplication.translate("mainWindow", "subtract background", None)
        )
        self.btn_select_bkgfile.setText(
            QCoreApplication.translate("mainWindow", "select", None)
        )
        self.label_59.setText(QCoreApplication.translate("mainWindow", "weight", None))
        self.groupBox_13.setTitle(
            QCoreApplication.translate("mainWindow", "Display", None)
        )
        self.box_show_roi.setText(
            QCoreApplication.translate("mainWindow", "q-I_ROIs", None)
        )
        # if QT_CONFIG(tooltip)
        self.box_all_phi.setToolTip(
            QCoreApplication.translate(
                "mainWindow",
                "<html><head/><body><p>show saxs_1d lines for  all phi partitions.</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.box_all_phi.setText(
            QCoreApplication.translate("mainWindow", "q-I_Phi", None)
        )
        self.box_show_phi_roi.setText(
            QCoreApplication.translate("mainWindow", "phi-I ROIs", None)
        )
        self.btn_export_saxs1d.setText(
            QCoreApplication.translate("mainWindow", "Export profiles", None)
        )
        self.groupBox_15.setTitle(
            QCoreApplication.translate("mainWindow", "Basic", None)
        )
        self.label_21.setText(QCoreApplication.translate("mainWindow", "type:", None))
        self.cb_saxs_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "I - q", None)
        )
        self.cb_saxs_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "I - log(q)", None)
        )
        self.cb_saxs_type.setItemText(
            2, QCoreApplication.translate("mainWindow", "log(I) - q", None)
        )
        self.cb_saxs_type.setItemText(
            3, QCoreApplication.translate("mainWindow", "log(I) - log(q)", None)
        )

        self.label_55.setText(
            QCoreApplication.translate("mainWindow", "sampling:", None)
        )
        self.label_22.setText(QCoreApplication.translate("mainWindow", "offset:", None))
        self.label_23.setText(
            QCoreApplication.translate("mainWindow", "normalization:", None)
        )
        self.cb_saxs_norm.setItemText(
            0, QCoreApplication.translate("mainWindow", "none", None)
        )
        self.cb_saxs_norm.setItemText(
            1, QCoreApplication.translate("mainWindow", "I' = Iq2", None)
        )
        self.cb_saxs_norm.setItemText(
            2, QCoreApplication.translate("mainWindow", "I' = Iq4", None)
        )
        self.cb_saxs_norm.setItemText(
            3, QCoreApplication.translate("mainWindow", "I' = I/Io", None)
        )

        self.saxs1d_lb_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "no drawing", None)
        )
        self.saxs1d_lb_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "slope drawing", None)
        )
        self.saxs1d_lb_type.setItemText(
            2, QCoreApplication.translate("mainWindow", "horizontal line", None)
        )

        self.label_49.setText(
            QCoreApplication.translate(
                "mainWindow", "q range (\u00c5\u207b\u00b9)", None
            )
        )
        self.label_54.setText(
            QCoreApplication.translate("mainWindow", "marker_size:", None)
        )
        self.label_52.setText(
            QCoreApplication.translate("mainWindow", "legend loc:", None)
        )
        self.saxs1d_legend_loc.setItemText(
            0, QCoreApplication.translate("mainWindow", "best", None)
        )
        self.saxs1d_legend_loc.setItemText(
            1, QCoreApplication.translate("mainWindow", "outside", None)
        )
        self.saxs1d_legend_loc.setItemText(
            2, QCoreApplication.translate("mainWindow", "upper right", None)
        )
        self.saxs1d_legend_loc.setItemText(
            3, QCoreApplication.translate("mainWindow", "upper left", None)
        )
        self.saxs1d_legend_loc.setItemText(
            4, QCoreApplication.translate("mainWindow", "lower left", None)
        )
        self.saxs1d_legend_loc.setItemText(
            5, QCoreApplication.translate("mainWindow", "lower right", None)
        )
        self.saxs1d_legend_loc.setItemText(
            6, QCoreApplication.translate("mainWindow", "right", None)
        )
        self.saxs1d_legend_loc.setItemText(
            7, QCoreApplication.translate("mainWindow", "center left", None)
        )
        self.saxs1d_legend_loc.setItemText(
            8, QCoreApplication.translate("mainWindow", "center right", None)
        )
        self.saxs1d_legend_loc.setItemText(
            9, QCoreApplication.translate("mainWindow", "lower center", None)
        )
        self.saxs1d_legend_loc.setItemText(
            10, QCoreApplication.translate("mainWindow", "upper center", None)
        )
        self.saxs1d_legend_loc.setItemText(
            11, QCoreApplication.translate("mainWindow", "center", None)
        )

        self.cbox_use_abs.setText(
            QCoreApplication.translate(
                "mainWindow", "using absolute cross section", None
            )
        )
        self.pushButton_plot_saxs1d.setText(
            QCoreApplication.translate("mainWindow", "Plot", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2),
            QCoreApplication.translate("mainWindow", "SAXS-1D", None),
        )
        self.groupBox_4.setTitle(
            QCoreApplication.translate("mainWindow", "Stability Plot Setting", None)
        )
        self.label_14.setText(QCoreApplication.translate("mainWindow", "type:", None))
        self.cb_stab_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "I - q", None)
        )
        self.cb_stab_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "I - log(q)", None)
        )
        self.cb_stab_type.setItemText(
            2, QCoreApplication.translate("mainWindow", "log(I) - q", None)
        )
        self.cb_stab_type.setItemText(
            3, QCoreApplication.translate("mainWindow", "log(I) - log(q)", None)
        )

        self.label_24.setText(QCoreApplication.translate("mainWindow", "offset:", None))
        self.label_16.setText(
            QCoreApplication.translate("mainWindow", "normalization:", None)
        )
        self.cb_stab_norm.setItemText(
            0, QCoreApplication.translate("mainWindow", "none", None)
        )
        self.cb_stab_norm.setItemText(
            1, QCoreApplication.translate("mainWindow", "I' = Iq2", None)
        )
        self.cb_stab_norm.setItemText(
            2, QCoreApplication.translate("mainWindow", "I' = Iq4", None)
        )
        self.cb_stab_norm.setItemText(
            3, QCoreApplication.translate("mainWindow", "I' = I/Io", None)
        )

        self.pushButton_plot_stability.setText(
            QCoreApplication.translate("mainWindow", "Plot Stability Data", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_3),
            QCoreApplication.translate("mainWindow", "Stability", None),
        )
        self.groupBox_7.setTitle(
            QCoreApplication.translate(
                "mainWindow", "Intensity-Time Plot Setting", None
            )
        )
        self.label_9.setText(
            QCoreApplication.translate("mainWindow", "max datasets:", None)
        )
        self.label_31.setText(
            QCoreApplication.translate("mainWindow", "moving average:", None)
        )
        self.label_11.setText(
            QCoreApplication.translate("mainWindow", "sampling:", None)
        )
        self.label_34.setText(QCoreApplication.translate("mainWindow", "xlabel:", None))
        self.intt_xlabel.setItemText(
            0, QCoreApplication.translate("mainWindow", "Time (second)", None)
        )
        self.intt_xlabel.setItemText(
            1, QCoreApplication.translate("mainWindow", "Frame Index", None)
        )

        self.pushButton_plot_intt.setText(
            QCoreApplication.translate("mainWindow", "plot Intensity-T", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_4),
            QCoreApplication.translate("mainWindow", "Intensity-Time", None),
        )
        self.groupBox.setTitle(
            QCoreApplication.translate("mainWindow", "Data Selection:", None)
        )
        self.label_4.setText(
            QCoreApplication.translate("mainWindow", "t range (s):", None)
        )
        self.label_3.setText(
            QCoreApplication.translate("mainWindow", "q (1/\u00c5):", None)
        )
        self.label_7.setText(QCoreApplication.translate("mainWindow", "y range", None))
        self.g2_tmin.setText(QCoreApplication.translate("mainWindow", "1e-6", None))
        self.g2_tmax.setText(QCoreApplication.translate("mainWindow", "100.0", None))
        self.g2_yauto.setText(QCoreApplication.translate("mainWindow", "auto", None))
        self.pushButton_4.setText(
            QCoreApplication.translate("mainWindow", "plot", None)
        )
        self.label.setText(QCoreApplication.translate("mainWindow", "offset:", None))
        self.label_53.setText(
            QCoreApplication.translate("mainWindow", "marker size:", None)
        )
        self.label_8.setText(QCoreApplication.translate("mainWindow", "column:", None))
        self.g2_sub_baseline.setText(
            QCoreApplication.translate("mainWindow", "subtract baseline", None)
        )
        self.g2_show_fit.setText(
            QCoreApplication.translate("mainWindow", "do fitting", None)
        )
        self.g2_show_label.setText(
            QCoreApplication.translate("mainWindow", "show labels", None)
        )
        self.g2_plot_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "multiple", None)
        )
        self.g2_plot_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "single", None)
        )
        self.g2_plot_type.setItemText(
            2, QCoreApplication.translate("mainWindow", "single-combined", None)
        )

        self.groupBox_2.setTitle(
            QCoreApplication.translate("mainWindow", "g2 fitting", None)
        )
        self.label_66.setText(QCoreApplication.translate("mainWindow", "c2", None))
        self.label_48.setText(
            QCoreApplication.translate("mainWindow", "baseline:", None)
        )
        self.g2_c2fit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_41.setText(QCoreApplication.translate("mainWindow", "d", None))
        self.g2_dfit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_63.setText(QCoreApplication.translate("mainWindow", "ratio:", None))
        self.g2_ffit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.g2_fitting_function.setItemText(
            0, QCoreApplication.translate("mainWindow", "Single Exponential", None)
        )
        self.g2_fitting_function.setItemText(
            1, QCoreApplication.translate("mainWindow", "Double Exponential", None)
        )

        self.label_67.setText(QCoreApplication.translate("mainWindow", "f", None))
        self.label_45.setText(
            QCoreApplication.translate("mainWindow", "contrast:", None)
        )
        self.label_5.setText(QCoreApplication.translate("mainWindow", "a", None))
        self.g2_afit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_46.setText(
            QCoreApplication.translate("mainWindow", "tau (s):", None)
        )
        self.label_6.setText(QCoreApplication.translate("mainWindow", "b", None))
        self.g2_bfit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_65.setText(
            QCoreApplication.translate("mainWindow", "tau2 (s):", None)
        )
        self.label_64.setText(QCoreApplication.translate("mainWindow", "b2", None))
        self.g2_b2fit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_47.setText(
            QCoreApplication.translate("mainWindow", "stretch:", None)
        )
        self.label_10.setText(QCoreApplication.translate("mainWindow", "c", None))
        self.g2_cfit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_62.setText(
            QCoreApplication.translate("mainWindow", "stretch2:", None)
        )
        self.show_g2_fit_summary.setText(
            QCoreApplication.translate("mainWindow", "values", None)
        )
        self.btn_g2_export.setText(
            QCoreApplication.translate("mainWindow", "export", None)
        )
        self.btn_g2_refit.setText(
            QCoreApplication.translate("mainWindow", "refit", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_6),
            QCoreApplication.translate("mainWindow", "g2", None),
        )
        self.groupBox_5.setTitle(
            QCoreApplication.translate(
                "mainWindow", "Power Law Fitting: y = a\u00b7x^b", None
            )
        )
        self.label_15.setText(
            QCoreApplication.translate("mainWindow", "plot_type:", None)
        )
        self.cb_tauq_type.setItemText(
            0, QCoreApplication.translate("mainWindow", "t-q", None)
        )
        self.cb_tauq_type.setItemText(
            1, QCoreApplication.translate("mainWindow", "\u03c4-log(q)", None)
        )
        self.cb_tauq_type.setItemText(
            2, QCoreApplication.translate("mainWindow", "log(\u03c4)-q", None)
        )
        self.cb_tauq_type.setItemText(
            3, QCoreApplication.translate("mainWindow", "log(\u03c4)-log(q)", None)
        )

        self.label_18.setText(QCoreApplication.translate("mainWindow", "Offset:", None))
        self.tauq_amax.setText(
            QCoreApplication.translate("mainWindow", "1.00e-3", None)
        )
        self.tauq_amax.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "max", None)
        )
        self.tauq_qmax.setText(QCoreApplication.translate("mainWindow", "0.0092", None))
        self.tauq_qmax.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "max", None)
        )
        self.tauq_bfit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.label_44.setText(QCoreApplication.translate("mainWindow", "a", None))
        self.tauq_bmin.setText(QCoreApplication.translate("mainWindow", "-2.5", None))
        self.tauq_bmin.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "min", None)
        )
        self.label_42.setText(QCoreApplication.translate("mainWindow", "b", None))
        self.tauq_amin.setText(
            QCoreApplication.translate("mainWindow", "1.00e-12", None)
        )
        self.tauq_amin.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "min", None)
        )
        self.tauq_afit.setText(QCoreApplication.translate("mainWindow", "fit", None))
        self.tauq_bmax.setText(QCoreApplication.translate("mainWindow", "-0.5", None))
        self.tauq_bmax.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "max", None)
        )
        self.tauq_qmin.setText(QCoreApplication.translate("mainWindow", "0.001", None))
        self.tauq_qmin.setPlaceholderText(
            QCoreApplication.translate("mainWindow", "min", None)
        )
        self.label_43.setText(
            QCoreApplication.translate("mainWindow", "q (\u00c5\u207b\u00b9)", None)
        )
        self.pushButton_8.setText(
            QCoreApplication.translate("mainWindow", "fit plot", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_7),
            QCoreApplication.translate("mainWindow", "Diffusion", None),
        )
        self.groupBox_11.setTitle(
            QCoreApplication.translate(
                "mainWindow", "Twotime Visualization Setting", None
            )
        )
        self.cb_twotime_saxs_cmap.setItemText(
            0, QCoreApplication.translate("mainWindow", "jet", None)
        )
        self.cb_twotime_saxs_cmap.setItemText(
            1, QCoreApplication.translate("mainWindow", "hot", None)
        )
        self.cb_twotime_saxs_cmap.setItemText(
            2, QCoreApplication.translate("mainWindow", "plasma", None)
        )
        self.cb_twotime_saxs_cmap.setItemText(
            3, QCoreApplication.translate("mainWindow", "viridis", None)
        )
        self.cb_twotime_saxs_cmap.setItemText(
            4, QCoreApplication.translate("mainWindow", "magma", None)
        )
        self.cb_twotime_saxs_cmap.setItemText(
            5, QCoreApplication.translate("mainWindow", "gray", None)
        )

        self.pushButton_12.setText(
            QCoreApplication.translate("mainWindow", "Plot", None)
        )
        self.label_35.setText(
            QCoreApplication.translate("mainWindow", "sax2d_cmap:", None)
        )
        self.label_28.setText(
            QCoreApplication.translate("mainWindow", "twotime_cmap:", None)
        )
        self.twotime_autocrop.setText(
            QCoreApplication.translate("mainWindow", "auto-crop", None)
        )
        self.cb_twotime_cmap.setItemText(
            0, QCoreApplication.translate("mainWindow", "jet", None)
        )
        self.cb_twotime_cmap.setItemText(
            1, QCoreApplication.translate("mainWindow", "hot", None)
        )
        self.cb_twotime_cmap.setItemText(
            2, QCoreApplication.translate("mainWindow", "plasma", None)
        )
        self.cb_twotime_cmap.setItemText(
            3, QCoreApplication.translate("mainWindow", "viridis", None)
        )
        self.cb_twotime_cmap.setItemText(
            4, QCoreApplication.translate("mainWindow", "magma", None)
        )
        self.cb_twotime_cmap.setItemText(
            5, QCoreApplication.translate("mainWindow", "gray", None)
        )

        self.twotime_correct_diag.setText(
            QCoreApplication.translate("mainWindow", "correct-diag", None)
        )
        self.label_57.setText(
            QCoreApplication.translate("mainWindow", "min-max:", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_8),
            QCoreApplication.translate("mainWindow", "Two Time", None),
        )
        self.comboBox_qmap_target.setItemText(
            0, QCoreApplication.translate("mainWindow", "dynamic_roi_map", None)
        )
        self.comboBox_qmap_target.setItemText(
            1, QCoreApplication.translate("mainWindow", "static_roi_map", None)
        )
        self.comboBox_qmap_target.setItemText(
            2, QCoreApplication.translate("mainWindow", "scattering", None)
        )

        self.label_27.setText(QCoreApplication.translate("mainWindow", "Target", None))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab),
            QCoreApplication.translate("mainWindow", "QMap", None),
        )
        self.groupBox_10.setTitle(
            QCoreApplication.translate("mainWindow", "g2 outlier", None)
        )
        self.groupBox_8.setTitle(
            QCoreApplication.translate("mainWindow", "Averaging Setting:", None)
        )
        self.label_39.setText(QCoreApplication.translate("mainWindow", "g2 max:", None))
        self.btn_set_average_save_name.setText(
            QCoreApplication.translate("mainWindow", "...", None)
        )
        self.label_17.setText(
            QCoreApplication.translate("mainWindow", "batch size:", None)
        )
        self.label_32.setText(
            QCoreApplication.translate("mainWindow", "q_index:", None)
        )
        self.label_25.setText(QCoreApplication.translate("mainWindow", "g2 min:", None))
        self.label_19.setText(
            QCoreApplication.translate("mainWindow", "save name:", None)
        )
        self.bx_avg_G2IPIF.setText(
            QCoreApplication.translate("mainWindow", "G2/IP/IF", None)
        )
        self.bx_avg_g2g2err.setText(
            QCoreApplication.translate("mainWindow", "g2/g2err", None)
        )
        self.label_20.setText(
            QCoreApplication.translate("mainWindow", "save path:", None)
        )
        self.btn_set_average_save_path.setText(
            QCoreApplication.translate("mainWindow", "...", None)
        )
        self.bx_avg_saxs.setText(
            QCoreApplication.translate("mainWindow", "saxs 1d/2d", None)
        )
        self.label_26.setText(
            QCoreApplication.translate("mainWindow", "selection:", None)
        )
        self.label_33.setText(
            QCoreApplication.translate("mainWindow", "avg_window:", None)
        )
        self.label_40.setText(
            QCoreApplication.translate("mainWindow", "max_thread:", None)
        )
        self.cb_avg_chunk_size.setItemText(
            0, QCoreApplication.translate("mainWindow", "32", None)
        )
        self.cb_avg_chunk_size.setItemText(
            1, QCoreApplication.translate("mainWindow", "64", None)
        )
        self.cb_avg_chunk_size.setItemText(
            2, QCoreApplication.translate("mainWindow", "128", None)
        )
        self.cb_avg_chunk_size.setItemText(
            3, QCoreApplication.translate("mainWindow", "256", None)
        )
        self.cb_avg_chunk_size.setItemText(
            4, QCoreApplication.translate("mainWindow", "512", None)
        )

        self.avg_blmin.setSpecialValueText("")
        self.groupBox_12.setTitle(
            QCoreApplication.translate("mainWindow", "Action:", None)
        )
        self.btn_submit_job.setText(
            QCoreApplication.translate("mainWindow", "submit", None)
        )
        self.avg_job_pop.setText(
            QCoreApplication.translate("mainWindow", "delete", None)
        )
        self.btn_avg_jobinfo.setText(
            QCoreApplication.translate("mainWindow", "info", None)
        )
        self.btn_avg_kill.setText(
            QCoreApplication.translate("mainWindow", "kill", None)
        )
        self.btn_start_avg_job.setText(
            QCoreApplication.translate("mainWindow", "start", None)
        )
        self.groupBox_9.setTitle(
            QCoreApplication.translate("mainWindow", "Averaging Job List", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_5),
            QCoreApplication.translate("mainWindow", "Average", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_9),
            QCoreApplication.translate("mainWindow", "Metadata", None),
        )

    # retranslateUi
