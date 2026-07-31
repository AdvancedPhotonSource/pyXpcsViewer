# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import os
import sys
import traceback

import numpy as np
import psutil
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, qInstallMessageHandler
from PySide6.QtWidgets import QMessageBox

from pyxpcsviewer.core.g2_utils import has_G2_field
from pyxpcsviewer.gui.control.job_manager import JobManager
from pyxpcsviewer.gui.control.plot_controller import PlotController
from pyxpcsviewer.gui.model.file_locator import FileLocator

from .viewer_ui import Ui_mainWindow as Ui

home_dir = os.path.join(os.path.expanduser("~"), ".pyxpcsviewer")
if not os.path.isdir(home_dir):
    os.mkdir(home_dir)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-24s: %(message)s")

logger = logging.getLogger(__name__)


def exception_hook(exc_type, exc_value, exc_traceback) -> None:
    """Global uncaught-exception handler that logs errors to the application logger."""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = exception_hook


tab_mapping = {
    0: "saxs_2d",
    1: "saxs_1d",
    2: "stability",
    3: "intensity_t",
    4: "g2",
    5: "diffusion",
    6: "twotime",
    7: "qmap",
    8: "average",
    9: "metadata",
    10: "g2map",
    11: "g2_stability",
    12: "G2_regroup",
}


def create_param_tree(data_dict):
    """Convert a dictionary into PyQtGraph's ParameterTree format."""
    params = []
    for key, value in data_dict.items():
        if isinstance(value, dict):  # If value is a nested dictionary
            params.append({"name": key, "type": "group", "children": create_param_tree(value)})
        elif isinstance(value, (float, np.floating)):  # Numeric types
            params.append(
                {
                    "name": key,
                    "type": "float",
                    "value": float(value),
                    "format": "{value:.10g}",
                }
            )
        elif isinstance(value, (int, np.integer)):  # Integer types
            params.append({"name": key, "type": "int", "value": int(value)})
        elif isinstance(value, str):  # String types
            params.append({"name": key, "type": "str", "value": value})
        elif isinstance(value, np.ndarray):  # Numpy arrays
            params.append({"name": key, "type": "text", "value": str(value.tolist())})
        else:  # Default fallback
            params.append({"name": key, "type": "text", "value": str(value)})
    return params


class XpcsViewer(QtWidgets.QMainWindow, Ui):
    """Main application window for the pyXPCSViewer GUI.

    Combines the generated Qt UI (:class:`Ui_mainWindow`) with the model/
    controllers: ``self.model`` (:class:`~pyxpcsviewer.gui.model.file_locator.FileLocator`),
    ``self.plots`` (:class:`~pyxpcsviewer.gui.control.plot_controller.PlotController`),
    and ``self.jobs`` (:class:`~pyxpcsviewer.gui.control.job_manager.JobManager`).
    """

    def __init__(self, path=None, label_style=None):
        """Initialize the main window, set up the viewer kernel and connect signals.

        Args:
            path: Starting directory for file browsing.
            label_style: Comma-separated index string for deriving short file labels.
        """
        super().__init__()
        self.setupUi(self)
        self.home_dir = home_dir
        self.label_style = label_style

        self.tabWidget.setCurrentIndex(0)  # show scattering 2d
        self.plot_kwargs_record = {}
        for _, v in tab_mapping.items():
            self.plot_kwargs_record[v] = {}

        # explicit tab -> plot method table for update_plot(); every
        # plot_<tab> method follows the same (dryrun: bool) -> dict | None
        # contract. "average" is handled separately by update_plot itself.
        self._tab_plotters = {
            "saxs_2d": self.plot_saxs_2d,
            "saxs_1d": self.plot_saxs_1d,
            "stability": self.plot_stability,
            "intensity_t": self.plot_intensity_t,
            "g2": self.plot_g2,
            "diffusion": self.plot_diffusion,
            "twotime": self.plot_twotime,
            "qmap": self.plot_qmap,
            "metadata": self.plot_metadata,
            "g2map": self.plot_g2map,
            "g2_stability": self.plot_g2_stability,
            "G2_regroup": self.plot_G2_regroup,
        }

        self.thread_pool = QtCore.QThreadPool()
        logger.info("Maximal threads: %d", self.thread_pool.maxThreadCount())

        self.model = None
        self.plots = None
        self.jobs = None
        # list widget models
        self.source_model = None
        self.target_model = None
        self.timer = QtCore.QTimer()
        # g2 tau-bound (g2_bmin/g2_bmax) auto-population is a one-shot per
        # target list: True once it's been set for the current (non-empty)
        # target list, so later replots/reselections don't clobber a
        # manually-tightened bound. Unlocked again in add_target() whenever
        # the list starts out empty.
        self._g2_bounds_initialized = False

        if path is not None:
            self.start_wd = path
            self.load_path(path)
        else:
            # use home directory
            self.start_wd = os.path.expanduser("~")

        self.start_wd = os.path.abspath(self.start_wd)
        logger.info(f"Start up directory is [{self.start_wd}]")

        self.pushButton_plot_saxs2d.clicked.connect(self.plot_saxs_2d)
        self.pushButton_plot_saxs1d.clicked.connect(self.plot_saxs_1d)
        self.pushButton_plot_stability.clicked.connect(self.plot_stability)
        self.pushButton_plot_intt.clicked.connect(self.plot_intensity_t)
        # self.saxs1d_lb_type.currentIndexChanged.connect(self.switch_saxs1d_line)

        self.tabWidget.currentChanged.connect(self.update_plot)
        self.list_view_target.clicked.connect(self.update_plot)

        self.mp_2t_hdls = None
        self.init_twotime_plot_handler()
        self.init_g2map_handler()
        self._set_plot_backgrounds()
        self.pushButton_plot_g2map.clicked.connect(self.plot_g2map)

        # self.avg_job_pop.clicked.connect(self.remove_avg_job)
        self.btn_submit_job.clicked.connect(self.submit_job)
        # self.btn_start_avg_job.clicked.connect(self.start_avg_job)
        self.btn_set_average_save_path.clicked.connect(self.set_average_save_path)
        self.btn_set_average_save_name.clicked.connect(self.set_average_save_name)
        # self.btn_avg_kill.clicked.connect(self.avg_kill_job)
        # self.btn_avg_jobinfo.clicked.connect(self.show_avg_jobinfo)
        self.show_g2_fit_summary.clicked.connect(self.show_g2_fit_summary_func)
        self.btn_g2_refit.clicked.connect(self.plot_g2)
        self.saxs2d_autolevel.stateChanged.connect(self.update_saxs2d_level)
        self.btn_deselect.clicked.connect(self.clear_target_selection)
        self.list_view_target.doubleClicked.connect(self.show_dataset)
        self.btn_select_bkgfile.clicked.connect(self.select_bkgfile)
        self.spinBox_saxs2d_selection.valueChanged.connect(self.plot_saxs_2d_selection)
        self.comboBox_twotime_selection.currentIndexChanged.connect(self.update_plot)
        self.pushButton_4.clicked.connect(self.update_plot)
        self.pushButton_5.clicked.connect(self.update_plot)
        self.comboBox_qmap_target.currentIndexChanged.connect(self.update_plot)
        self.cb_qmap_cmap.currentIndexChanged.connect(self.update_plot)
        self.comboBox_G2_target.currentIndexChanged.connect(self.update_plot)
        self.horizontalSlider_G2_delay.valueChanged.connect(self.update_plot)
        self.pushButton_G2_regroup.clicked.connect(self.process_G2_regroup)
        self.pushButton_G2_savefile.clicked.connect(self.savefile_G2_regroup)
        self.pushButton_G2_loadQMap.clicked.connect(self.load_external_qmap_for_G2_regroup)

        self.g2_fitting_function.currentIndexChanged.connect(self.update_g2_fitting_function)
        self.btn_up.clicked.connect(lambda: self.reorder_target("up"))
        self.btn_down.clicked.connect(lambda: self.reorder_target("down"))

        self.btn_export_saxs1d.clicked.connect(self.saxs1d_export)

        self.comboBox_qmap_target.currentIndexChanged.connect(self.update_plot)
        self.update_g2_fitting_function()

        self.pg_saxs.getView().scene().sigMouseMoved.connect(self.saxs2d_mouseMoved)

        self.load_default_setting()
        self.show()

    def closeEvent(self, event) -> None:
        """Release background resources (e.g. the pre-warmed fit process pool) on window close."""
        if self.jobs is not None:
            self.jobs.shutdown()
        super().closeEvent(event)

    def load_default_setting(self) -> None:
        """Set the default window size."""
        self.resize(1400, 1200)

    def get_selected_rows(self) -> list[int]:
        """Return the currently selected row indices from the target file list."""
        selected_index = self.list_view_target.selectedIndexes()
        selected_row = [x.row() for x in selected_index]
        # the selected index is ordered;
        selected_row.sort()
        return selected_row

    def update_plot(self):
        """Update the current tab's plot using dry-run diff against recorded kwargs."""
        idx = self.tabWidget.currentIndex()
        tab_name = tab_mapping[idx]
        if tab_name == "average":
            return
        func = self._tab_plotters[tab_name]
        try:
            kwargs = func(dryrun=True)
            if not kwargs:
                return
            kwargs["target_timestamp"] = self.model.timestamp
            if self.plot_kwargs_record[tab_name] != kwargs:
                self.plot_kwargs_record[tab_name] = kwargs
                func(dryrun=False)
                if tab_name == "g2":  # reset diffusion plot on new g2 plot
                    logger.info("g2 updated; reset diffusion plot settings")
                    self.plot_kwargs_record["diffusion"] = {}
        except Exception as e:
            logger.error(f"update selection in [{tab_name}] failed")
            logger.error(e)
            traceback.print_exc()

    def init_g2map_handler(self) -> None:
        """Create and configure the pyqtgraph ``ImageView`` widgets for G2-map display.

        Sets up three panels: G2 correlation image (with colour bar), Q-map overlay,
        and a G2-vs-time profile plot with histogram LUT.
        """
        self.widget_g2map_profile_plot = self.widget_g2map_profile.addPlot()
        cmap = pg.colormap.getFromMatplotlib("tab20b")  # from matplotlib.cm.tab20b
        self.widget_g2map_qmap.setColorMap(cmap)

        plot = self.widget_g2map_all.addPlot(row=0, col=0)
        plot.setLabel("bottom", "tau index")
        plot.setLabel("left", "qbin index")
        # Optional: grid and aspect ratio
        plot.showGrid(x=True, y=True)
        plot.getViewBox().setAspectLocked(False)

        # --- Add the ImageItem ---
        self.g2map_all_img = pg.ImageItem()
        plot.addItem(self.g2map_all_img)
        # Example image data

        # Optional: colorbar
        hist = pg.HistogramLUTItem()
        hist.setImageItem(self.g2map_all_img)
        hist.vb.setBackgroundColor("w")
        self.widget_g2map_all.addItem(hist, row=0, col=1)
        # Optional: apply a matplotlib colormap
        cmap = pg.colormap.getFromMatplotlib("viridis")
        self.g2map_all_img.setLookupTable(cmap.getLookupTable())
        hist.gradient.setColorMap(cmap)

    def _set_plot_backgrounds(self) -> None:
        """Force white backgrounds on all plot widgets.

        PlotWidgetDev already sets white in its own __init__, so this only
        covers the raw PlotWidget / GraphicsLayoutWidget / ImageView instances
        that the generated UI creates without any background.
        """
        for widget in (
            self.mp_saxs,  # SAXS 1D tab (PlotWidget)
            self.mp_stab,  # Stability tab (PlotWidget)
            self.mp_tauq,  # Tau-q tab (PlotWidget)
            self.mp_tauq_pre,  # Tau-q pre tab (GraphicsLayoutWidget)
            self.pg_intt,  # Intensity vs Time (GraphicsLayoutWidget)
            self.widget_g2map_all,  # G2-map image (GraphicsLayoutWidget)
            self.widget_g2map_profile,  # G2-map profile (GraphicsLayoutWidget)
        ):
            widget.setBackground("w")

        # ImageView instances: set the main ViewBox and the embedded HistogramLUTItem's
        # ViewBox (the vertical colour-bar / histogram strip on the side) to white.
        for iv in (
            self.pg_saxs,  # SAXS 2D tab (ImageViewDev)
            self.pg_qmap,  # QMap tab (ImageView)
            self.widget_g2map_qmap,  # G2-map qmap (ImageView)
            self.pg_regroup_G2,  # G2 Regroup tab (ImageView)
            self.mp_2t,  # Two Time tab (ImageViewPlotItem)
        ):
            # iv.getView() is a ViewBox for plain ImageView, but a PlotItem for
            # ImageViewPlotItem (mp_2t) — PlotItem has no setBackgroundColor of
            # its own, so reach into its wrapped ViewBox via .vb when present.
            view = iv.getView()
            vb = view.vb if hasattr(view, "vb") else view
            vb.setBackgroundColor("w")
            # iv.ui.histogram is a HistogramLUTWidget: a GraphicsView (own scene/
            # background) wrapping a HistogramLUTItem. Its inner .vb has no
            # background of its own by default (transparent), so whitening the
            # enclosing widget's scene is sufficient -- no need to also touch .vb.
            iv.ui.histogram.setBackground("w")

    def plot_g2map(self, dryrun: bool = False) -> dict | None:
        """Display the G2 correlation image with Q-map overlay and profile trace.

        Returns keyword arguments for dry-run comparison in :meth:`update_plot`.
        """
        kwargs = {
            "rows": self.get_selected_rows(),
            "qbin": self.spinBox_qbin.value(),
            "normalization": self.checkBox_g2map_normalization.isChecked(),
        }

        if dryrun:
            return kwargs
        self.plots.plot_g2map(
            self.g2map_all_img,
            self.widget_g2map_qmap,
            self.widget_g2map_profile_plot,
            **kwargs,
        )

    def load_external_qmap_for_G2_regroup(self) -> None:
        """Open a file dialog to select an external Q-map HDF5 file for G2 regrouping."""
        f = QtWidgets.QFileDialog.getOpenFileName(
            self, caption="select the external qmap file for G2 regrouping", dir=None
        )[0]
        if os.path.isfile(f):
            self.label_G2_external_qmapfname.setText(f)

    def savefile_G2_regroup(self):
        """Prompt the user to choose a save location and delegate to :meth:`PlotController.savefile_G2_regroup`."""
        kwargs = {
            "rows": self.get_selected_rows(),
        }
        if len(kwargs["rows"]) == 0:
            return None

        save_fname = QtWidgets.QFileDialog.getSaveFileName(
            self, caption="select the save file for G2 regrouping", dir=None
        )[0]

        if save_fname:
            kwargs["save_fname"] = save_fname
        else:
            kwargs["save_fname"] = None

        flag = self.plots.savefile_G2_regroup(**kwargs)
        if flag:
            QMessageBox.information(self, "Save G2 regrouping", "G2 regrouping saved successfully.")
        else:
            QMessageBox.critical(self, "Save G2 regrouping", "Failed to save G2 regrouping.")

    def process_G2_regroup(self) -> None:
        """Re-group G2 correlations using internal, external, or drawn Q-map (delegates to ``self.plots``)."""
        kwargs = {
            "rows": self.get_selected_rows(),
        }
        if len(kwargs["rows"]) == 0:
            return None

        qmap_method = {0: "internal", 1: "external", 2: "draw"}[self.tabWidget_G2_regroup.currentIndex()]

        if qmap_method == "internal":
            kwargs["qmap_fname"] = None
        elif qmap_method == "external":
            fname = self.label_G2_external_qmapfname.text()
            if not os.path.isfile(fname):
                QMessageBox.critical(
                    self,
                    "No QMap file found",
                    "No QMap file found in the selected dataset.",
                )
                return
            kwargs["qmap_fname"] = fname
        elif qmap_method == "draw":
            # kwargs["external_qmap"] = None
            raise NotImplementedError("draw qmap is not implemented yet")
            return

        self.plots.process_G2_regroup(**kwargs)

        g2_plot_kwargs = self.plot_g2(dryrun=True)
        self.plots.plot_g2(self.pg_regroup_g2, **g2_plot_kwargs)

    def plot_G2_regroup(self, dryrun: bool = False) -> dict | None:
        """Display the G2 correlation data from regrouped results (or returns kwargs in dry-run mode)."""
        kwargs = {
            "rows": self.get_selected_rows(),
            "target": self.comboBox_G2_target.currentText(),
            "delay_index": self.horizontalSlider_G2_delay.value(),
            "cmap": self.cb_saxs2D_cmap.currentText(),
            "vmin": self.doubleSpinBox_G2_vmin.value(),
            "vmax": self.doubleSpinBox_G2_vmax.value(),
        }
        if len(kwargs["rows"]) == 0:
            # no dataset selected
            return

        if dryrun:
            return kwargs

        if not has_G2_field(self.model.target[kwargs["rows"][0]]):
            QMessageBox.critical(self, "No G2 data found", "No G2 data found in the selected dataset.")
            return

        self.progress = QtWidgets.QProgressDialog("Loading data, please wait...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)  # Blocks interaction with main window
        self.progress.setRange(0, 0)  # Setting 0,0 makes it an infinite "spinner"
        self.progress.show()
        self.plots.plot_G2_regroup(self.pg_regroup_G2, **kwargs)
        self.progress.close()

        return

    def plot_metadata(self, dryrun: bool = False) -> dict | None:
        """Display HDF5 metadata in a ParameterTree widget (or return kwargs in dry-run)."""
        kwargs = {"rows": self.get_selected_rows()}
        if dryrun:
            return kwargs
        if len(self.model.target) == 0:
            return
        msg = self.model.get_xf_list(**kwargs)[0].get_hdf_info()
        hdf_info_data = create_param_tree(msg)
        hdf_params = Parameter.create(name="Settings", type="group", children=hdf_info_data)
        self.hdf_info.setParameters(hdf_params, showTop=True)

    def saxs2d_mouseMoved(self, pos) -> None:
        """Update the SAXS-2D display with Q-map info at the cursor position."""
        if self.pg_saxs.view.sceneBoundingRect().contains(pos):
            mouse_point = self.pg_saxs.getView().mapSceneToView(pos)
            x, y = int(mouse_point.x()), int(mouse_point.y())
            rows = self.get_selected_rows()
            payload = self.plots.get_info_at_mouse(rows, x, y)
            if payload:
                self.saxs2d_display.setText(payload)

    def plot_saxs_2d_selection(self) -> None:
        """Re-plot SAXS-2D with the currently selected q-bin."""
        selection = self.spinBox_saxs2d_selection.value()
        self.plot_saxs_2d(selection=selection)

    def plot_saxs_2d(self, selection=None, dryrun: bool = False):
        """Display SAXS 2D image with optional q-bin selection and dry-run kwargs."""
        kwargs = {
            "plot_type": self.cb_saxs2D_type.currentText(),
            "cmap": self.cb_saxs2D_cmap.currentText(),
            "rotate": self.saxs2d_rotate.isChecked(),
            "autolevel": self.saxs2d_autolevel.isChecked(),
            "vmin": self.saxs2d_min.value(),
            "vmax": self.saxs2d_max.value(),
        }
        if selection and selection >= 0:
            kwargs["rows"] = [selection]
        else:
            kwargs["rows"] = self.get_selected_rows()

        if dryrun:
            return kwargs
        else:
            self.plots.plot_saxs_2d(pg_hdl=self.pg_saxs, **kwargs)

    def plot_saxs_1d(self, dryrun: bool = False):
        """Display SAXS 1D intensity curves with optional normalization and offset."""
        kwargs = {
            "plot_type": self.cb_saxs_type.currentIndex(),
            "plot_offset": self.sb_saxs_offset.value(),
            "plot_norm": self.cb_saxs_norm.currentIndex(),
            "rows": self.get_selected_rows(),
            "qmin": self.saxs1d_qmin.value(),
            "qmax": self.saxs1d_qmax.value(),
            "loc": self.saxs1d_legend_loc.currentText(),
            "marker_size": self.sb_saxs_marker_size.value(),
            "sampling": self.saxs1d_sampling.value(),
            "all_phi": self.box_all_phi.isChecked(),
            "absolute_crosssection": self.cbox_use_abs.isChecked(),
            "subtract_background": self.cb_sub_bkg.isChecked(),
            "weight": self.bkg_weight.value(),
            "show_roi": self.box_show_roi.isChecked(),
            "show_phi_roi": self.box_show_phi_roi.isChecked(),
        }
        if kwargs["qmin"] >= kwargs["qmax"]:
            self.statusbar.showMessage("check qmin and qmax")
            return

        if dryrun:
            return kwargs
        else:
            self.plots.plot_saxs_1d(self.pg_saxs, self.mp_saxs, **kwargs)
            # adjust the line behavior
            self.switch_saxs1d_line()

    def switch_saxs1d_line(self) -> None:
        """Switch the matplotlib line-builder mode (slope/hline)."""
        lb_type = self.saxs1d_lb_type.currentIndex()
        lb_type = [None, "slope", "hline"][lb_type]
        self.plots.switch_saxs1d_line(self.mp_saxs, lb_type)

    def saxs1d_export(self) -> None:
        """Export SAXS-1D ROI data to the user-selected folder via :meth:`PlotController.export_saxs_1d`."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, caption="select a folder to export SAXS profiles")

        if folder in [None, ""]:
            return

        self.plots.export_saxs_1d(self.pg_saxs, folder)

    def init_twotime_plot_handler(self) -> None:
        """Create the two-time analysis display widgets: SAXS background, Q-map overlay."""
        # self.mp_2t.setBackground('w')
        self.mp_2t_hdls = {}
        labels = ["saxs", "dqmap"]
        titles = ["scattering", "dynamic_qmap"]
        cmaps = ["viridis", "tab20"]
        self.mp_2t_map.setBackground("w")
        for n in range(2):
            plot_item = self.mp_2t_map.addPlot(row=0, col=n)
            # Remove axes
            plot_item.hideAxis("left")
            plot_item.hideAxis("bottom")
            plot_item.getViewBox().setDefaultPadding(0)

            plot_item.setMouseEnabled(x=False, y=False)
            image_item = pg.ImageItem(np.ones((128, 128)))
            image_item.setOpts(axisOrder="row-major")  # Set to row-major order

            plot_item.setTitle(titles[n])
            plot_item.addItem(image_item)
            plot_item.setAspectLocked(True)

            cmap = pg.colormap.getFromMatplotlib(cmaps[n])
            if n == 1:
                positions = cmap.pos
                colors = cmap.color
                new_color = [0, 0, 1, 1.0]
                colors[-1] = new_color
                # need to convert to 0-255 range for pyqtgraph ColorMap
                cmap = pg.ColorMap(positions, colors * 255)
            colorbar = plot_item.addColorBar(image_item, colorMap=cmap)
            self.mp_2t_hdls[labels[n]] = image_item
            self.mp_2t_hdls[labels[n] + "_colorbar"] = colorbar

        c2g2_plot = self.mp_2t_map.addPlot(row=0, col=2)
        self.mp_2t_hdls["c2g2"] = c2g2_plot

        self.mp_2t_hdls["dqmap"].mouseClickEvent = self.pick_twotime_index
        self.mp_2t_hdls["saxs"].mouseClickEvent = self.pick_twotime_index
        self.mp_2t.ui.graphicsView.setBackground("w")
        self.mp_2t_hdls["tt"] = self.mp_2t
        self.mp_2t_hdls["tt"].view.invertY(False)
        self.mp_2t.view.setLabel("left", "t2", units="s")
        self.mp_2t.view.setLabel("bottom", "t1", units="s")

    def pick_twotime_index(self, event) -> None:
        """Re-plot twotime data when the user clicks on the Q-map display."""
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()
            x, y = int(pos.x()), int(pos.y())
            self.plot_twotime(highlight_xy=(x, y))
        event.accept()  # Mark the event as handled

    def plot_qmap(self, dryrun: bool = False) -> dict | None:
        """Display a Q-map image (scattering, dynamic ROI, or static ROI)."""
        kwargs = {
            "rows": self.get_selected_rows(),
            "target": self.comboBox_qmap_target.currentText(),
            "cmap": self.cb_qmap_cmap.currentText(),
        }
        if dryrun:
            return kwargs
        self.plots.plot_qmap(self.pg_qmap, **kwargs)

    def plot_twotime(self, dryrun: bool = False, highlight_xy=None):
        """Display two-time correlation (C2) maps alongside SAXS-2D background.

        Returns keyword arguments in dry-run mode; otherwise renders the twotime view.
        """
        kwargs = {
            "rows": self.get_selected_rows(),
            "auto_crop": self.twotime_autocrop.isChecked(),
            "highlight_xy": highlight_xy,
            "cmap": self.cb_twotime_cmap.currentText(),
            "vmin": self.c2_min.value(),
            "vmax": self.c2_max.value(),
            "correct_diag": self.twotime_correct_diag.isChecked(),
            "autolevel": self.checkBox_twotime_autolevel.isChecked(),
            "selection": max(0, self.comboBox_twotime_selection.currentIndex()),
        }
        if dryrun:
            return kwargs

        if self.mp_2t_hdls is None:
            self.init_twotime_plot_handler()
        new_labels = self.plots.plot_twotime(self.mp_2t_hdls, **kwargs)
        if new_labels is not None:
            self.comboBox_twotime_selection.clear()
            self.comboBox_twotime_selection.addItems(new_labels)
            self.horizontalSlider_twotime_selection.setMaximum(len(new_labels) - 1)

    def show_dataset(self) -> None:
        """Open a pop-up :class:`~pyqtgraph.DataTreeWidget` showing the first target file's data tree."""
        rows = self.get_selected_rows()
        self.tree = self.plots.get_pg_tree(rows)
        if self.tree:
            self.tree.show()

    def plot_stability(self, dryrun: bool = False):
        """Plot SAXS-1D segment (stability) data with optional log-log display."""
        kwargs = {
            "plot_type": self.cb_stab_type.currentIndex(),
            "plot_norm": self.cb_stab_norm.currentIndex(),
            "rows": self.get_selected_rows(),
            "loc": self.stab_legend_loc.currentText(),
        }
        if dryrun:
            return kwargs
        else:
            self.plots.plot_stability(self.mp_stab, **kwargs)

    def plot_intensity_t(self, dryrun: bool = False):
        """Plot intensity-vs-time curves with optional Fourier spectrum and zoom view."""
        kwargs = {
            "sampling": max(1, self.sb_intt_sampling.value()),
            "window": self.sb_window.value(),
            "rows": self.get_selected_rows(),
            "xlabel": self.intt_xlabel.currentText(),
        }
        if dryrun:
            return kwargs
        else:
            self.plots.plot_intt(self.pg_intt, **kwargs)

    def init_diffusion(self) -> None:
        """Initialize the tau-q pre-view subplot with current target data."""
        self.plots.plot_tauq_pre(hdl=self.mp_tauq_pre)

    def plot_diffusion(self, dryrun: bool = False):
        """Plot tau(q) diffusion fitting with optional parameter range configuration.

        Returns keyword arguments in dry-run mode; otherwise runs the tau-q fit and displays results.
        """
        keys = [self.tauq_amin, self.tauq_bmin, self.tauq_amax, self.tauq_bmax]
        bounds = np.array([float(x.text()) for x in keys]).reshape(2, 2)

        fit_flag = [self.tauq_afit.isChecked(), self.tauq_bfit.isChecked()]

        if sum(fit_flag) == 0:
            self.statusbar.showMessage("nothing to fit, really?", 1000)
            return

        tauq = [self.tauq_qmin, self.tauq_qmax]
        q_range = [float(x.text()) for x in tauq]

        kwargs = {
            "bounds": bounds.tolist(),
            "fit_flag": fit_flag,
            "offset": self.sb_tauq_offset.value(),
            "rows": self.get_selected_rows(),
            "q_range": q_range,
            "plot_type": self.cb_tauq_type.currentIndex(),
        }
        if dryrun:
            return kwargs
        else:
            msg = self.plots.plot_tauq(hdl=self.mp_tauq, **kwargs)
            self.tauq_msg.clear()
            self.tauq_msg.setData(msg)
            self.tauq_msg.parent().repaint()

    def select_bkgfile(self) -> None:
        """Open a file dialog to select a background SAXS-1D file for subtraction."""
        path = self.work_dir.text()
        f = QtWidgets.QFileDialog.getOpenFileName(self, caption="select the file for background subtraction", dir=path)[
            0
        ]
        if os.path.isfile(f):
            self.le_bkg_fname.setText(f)
            self.plots.select_bkgfile(f)
        else:
            return

    def set_average_save_path(self) -> None:
        """Open a directory dialog to set the save location for average results."""
        save_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open directory")
        self.avg_save_path.clear()
        self.avg_save_path.setText(save_path)
        return

    def set_average_save_name(self) -> None:
        """Open a file-save dialog to set the output name for average results."""
        save_name = QtWidgets.QFileDialog.getSaveFileName(self, "Save as")
        self.avg_save_name.clear()
        self.avg_save_name.setText(os.path.basename(save_name[0]))
        return

    def init_average(self) -> None:
        """Initialize the average tab settings based on available G2 fields and target files."""
        if len(self.model.target) > 0:
            save_path = self.avg_save_path.text()
            if save_path == "":
                self.avg_save_path.setText(self.work_dir.text())
            else:
                logger.info("use the previous save path")

            has_G2 = all(has_G2_field(x) for x in self.model.target)
            if has_G2:
                logger.info("G2 field is available for averaging")
                self.bx_avg_G2IPIF.setEnabled(True)
            else:
                logger.info("G2 field is not available for averaging")
                self.bx_avg_G2IPIF.setEnabled(False)
                self.bx_avg_G2IPIF.setChecked(False)

            save_name = self.avg_save_name.text()
            save_name = "Average_" + os.path.basename(self.model.target[0])
            self.avg_save_name.setText(save_name)

    def submit_job(self) -> None:
        """Submit an average job to the thread pool with user-configured options."""
        if len(self.model.target) < 2:
            self.statusbar.showMessage("select at least 2 files for averaging", 1000)
            return

        max_workers = min(self.num_workers.value(), psutil.cpu_count(logical=False))
        self.num_workers.setValue(max_workers)
        self.thread_pool.setMaxThreadCount(max_workers)

        save_path = self.avg_save_path.text()
        save_name = self.avg_save_name.text()

        if not os.path.isdir(save_path):
            logger.info("the average save_path doesn't exist; creating one")
            try:
                os.mkdir(save_path)
            except Exception:
                logger.info("cannot create the folder: %s", save_path)
                return

        avg_fields = []
        if self.bx_avg_G2IPIF.isChecked():
            avg_fields.extend(["G2"])
        if self.bx_avg_g2g2err.isChecked():
            avg_fields.extend(["g2", "g2_err", "g2_partial", "g2_partial_err"])
        if self.bx_avg_saxs.isChecked():
            avg_fields.extend(["saxs_1d", "saxs_2d"])

        if len(avg_fields) == 0:
            self.statusbar.showMessage("No average field is selected. quit", 1000)
            return

        save_path = os.path.join(save_path, save_name)

        if not save_path.endswith(".hdf"):
            save_path += ".hdf"

        kwargs = {
            "save_path": save_path,
            # "chunk_size": int(self.cb_avg_chunk_size.currentText()),
            "avg_blmin": self.avg_blmin.value(),
            "avg_blmax": self.avg_blmax.value(),
            "avg_qindex": self.avg_qindex.value(),
            "avg_window": self.avg_window.value(),
            "fields": avg_fields,
            "status_bar": self.statusbar,
            "progress_bar": self.progressbar_average,
            "num_workers": self.num_workers.value(),
        }

        try:
            if os.path.isfile(kwargs["save_path"]):
                reply = QMessageBox.question(
                    self,
                    "File exists",
                    f"The file {kwargs['save_path']} already exists. Do you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return
                else:
                    os.remove(kwargs["save_path"])
            # make sure the write permission
            # "a" = open for append or create; won't truncate existing file
            with open(kwargs["save_path"], "a"):
                pass
        except OSError as e:
            QMessageBox.critical(self, "Save Error", f"Cannot write to:\n{save_path}\n\n{e}")
            return

        if kwargs["avg_blmax"] <= kwargs["avg_blmin"]:
            self.statusbar.showMessage("check avg min/max values.", 1000)
            QMessageBox.critical(self, "Baseline bounds error", "Check avg min/max values for baseline.")
            return

        self.btn_submit_job.setEnabled(False)
        self.btn_submit_job.setText("Running...")

        worker = self.jobs.submit_average(on_finished=self.avg_job_finished, **kwargs)
        if worker is None:
            self.btn_submit_job.setEnabled(True)
            self.btn_submit_job.setText("Submit")
            return
        # the target list has been reset by submit_average
        self.update_box(self.model.target, mode="target")
        self.update_avg_info()

    def avg_job_finished(self, success: bool) -> None:
        """Update the UI and status bar when an average job completes."""
        if success:
            self.statusbar.showMessage("average job finished", 5000)
        else:
            self.statusbar.showMessage("average job failed", 5000)
        self.jobs.avg_worker_active = {}
        self.btn_submit_job.setEnabled(True)
        self.btn_submit_job.setText("Submit")

    def update_avg_info(self) -> None:
        """Set up a timer to periodically poll the averaging worker's progress."""
        self.timer.stop()
        self.timer.setInterval(1000)

        try:
            self.timer.timeout.disconnect()
            logger.info("disconnect previous slot")
        except Exception:
            pass

        worker = self.jobs.avg_worker
        worker.initialize_plot(self.mp_avg_g2)
        self.timer.timeout.connect(self.jobs.update_avg_info)
        self.timer.start()

    # def avg_kill_job(self):
    #     index = self.avg_job_table.currentIndex().row()
    #     if index < 0 or index >= len(self.jobs.avg_worker):
    #         self.statusbar.showMessage("select a job to kill", 1000)
    #         return
    #     worker = self.jobs.avg_worker[index]
    #     if worker.status != "running":
    #         self.statusbar.showMessage("the selected job isn's running", 1000)
    #         return
    #     worker.kill()

    def show_g2_fit_summary_func(self) -> None:
        """Open a pop-up data tree widget showing per-file g2 fitting results."""
        rows = self.get_selected_rows()
        self.tree = self.plots.get_fitting_tree(rows)
        self.tree.show()

    # def show_avg_jobinfo(self):
    #     index = self.avg_job_table.currentIndex().row()
    #     if index < 0 or index >= len(self.jobs.avg_worker):
    #         logger.info("select a job to show it's settting")
    #         return
    #     worker = self.jobs.avg_worker[index]
    #     self.tree = worker.get_pg_tree()
    #     self.tree.show()

    def init_g2(self, qd, tel) -> None:
        """Initialize g2 plot range widgets from the latest G2 data ranges."""
        if qd is None or tel is None:
            return None

        q_auto = self.g2_qauto.isChecked()
        t_auto = self.g2_tauto.isChecked()

        # tel is a list of arrays, which may have diffent shape;
        t_min = np.min([t[0] for t in tel])
        t_max = np.max([t[-1] for t in tel])

        def to_e(x):
            """Format a float in scientific notation."""
            return f"{x:.2e}"

        if not self._g2_bounds_initialized:
            self.g2_bmin.setValue(t_min / 20)
            self.g2_bmax.setValue(t_max * 10)
            self._g2_bounds_initialized = True

        if t_auto:
            self.g2_tmin.setText(to_e(t_min / 1.1))
            self.g2_tmax.setText(to_e(t_max * 1.1))

        if q_auto:
            self.g2_qmin.setValue(np.min(qd) / 1.1)
            self.g2_qmax.setValue(np.max(qd) * 1.1)

    def plot_g2(self, dryrun: bool = False):
        """Plot multitau G2 correlation curves with optional fitting overlay."""
        p = self.check_g2_number(tab="g2")
        bounds, fit_flag, fit_func = self.check_g2_fitting_number()

        kwargs = {
            "num_col": self.sb_g2_column.value(),
            "offset": self.sb_g2_offset.value(),
            "show_fit": self.g2_show_fit.isChecked(),
            "show_label": self.g2_show_label.isChecked(),
            "plot_type": self.g2_plot_type.currentText(),
            "q_range": (p[0], p[1]),
            "t_range": (p[2], p[3]),
            "y_range": (p[4], p[5]),
            "y_auto": self.g2_yauto.isChecked(),
            "q_auto": self.g2_qauto.isChecked(),
            "t_auto": self.g2_tauto.isChecked(),
            "rows": self.get_selected_rows(),
            "bounds": bounds,
            "fit_flag": fit_flag,
            "marker_size": self.g2_marker_size.value(),
            "subtract_baseline": self.g2_sub_baseline.isChecked(),
            "fit_func": fit_func,
            # 'label_size': self.sb_g2_label_size.value(),
        }
        if dryrun:
            return kwargs

        self.pushButton_4.setDisabled(True)
        self.pushButton_4.setText("plotting")

        if not kwargs["show_fit"]:
            self._draw_g2(kwargs)
            return

        # fitting must run (and finish) before pg_plot can draw the overlay;
        # run it in the background so the GUI doesn't freeze on curve_fit
        q_range = None if kwargs["q_auto"] else kwargs["q_range"]
        t_range = None if kwargs["t_auto"] else kwargs["t_range"]
        worker = self.jobs.submit_g2_fit(
            q_range=q_range,
            t_range=t_range,
            bounds=kwargs["bounds"],
            fit_flag=kwargs["fit_flag"],
            fit_func=kwargs["fit_func"],
            on_finished=lambda: self._on_g2_fit_finished(kwargs),
            rows=kwargs["rows"],
        )
        if worker is None:
            self.pushButton_4.setEnabled(True)
            self.pushButton_4.setText("plot")
            return

    def _draw_g2(self, kwargs: dict) -> None:
        """Draw the G2 plot (and diffusion tab, if fitting) using already-fit data."""
        try:
            qd, tel = self.plots.plot_g2(handler=self.mp_g2, **kwargs)
            self.init_g2(qd, tel)
            if kwargs["show_fit"]:
                self.init_diffusion()
        except Exception as e:
            logger.error(f"plot g2 failed, {e}")
            traceback.print_exc()
        finally:
            self.pushButton_4.setEnabled(True)
            self.pushButton_4.setText("plot")

    def _on_g2_fit_finished(self, kwargs: dict) -> None:
        """Slot: background g2 fitting finished — draw the plot now."""
        self._draw_g2(kwargs)

    def plot_g2_stability(self, dryrun: bool = False):
        """Plot G2 stability (partial G2 vs time) curves for a single file."""
        p = self.check_g2_number(tab="g2_stability")

        kwargs = {
            "num_col": self.sb_g2_column_2.value(),
            "offset": self.sb_g2_offset_2.value(),
            "show_label": self.g2_show_label_2.isChecked(),
            "plot_type": self.g2_plot_type_2.currentText(),
            "q_range": (p[0], p[1]),
            "t_range": (p[2], p[3]),
            "y_range": (p[4], p[5]),
            "y_auto": self.g2_yauto_2.isChecked(),
            "q_auto": self.g2_qauto_2.isChecked(),
            "t_auto": self.g2_tauto_2.isChecked(),
            "rows": self.get_selected_rows(),
            "marker_size": self.g2_marker_size_2.value(),
            "subtract_baseline": self.g2_sub_baseline_2.isChecked(),
        }
        if dryrun:
            return kwargs
        else:
            self.pushButton_5.setDisabled(True)
            self.pushButton_5.setText("plotting")
            try:
                qd, tel = self.plots.plot_g2_stability(handler=self.mp_g2_stability, **kwargs)
                self.init_g2(qd, tel)
                # if kwargs["show_fit"]:
                #     self.init_diffusion()
            except Exception:
                traceback.print_exc()
            finally:
                self.pushButton_5.setEnabled(True)
                self.pushButton_5.setText("plot")

    def export_g2(self) -> None:
        """Placeholder — currently a no-op."""
        self.plots.export_g2()

    def reload_source(self) -> None:
        """Re-scan the current directory and refresh the source file list."""
        self.pushButton_11.setText("loading")
        self.pushButton_11.setDisabled(True)
        self.pushButton_11.parent().repaint()
        path = self.work_dir.text()
        self.model.build(path=path, sort_method=self.sort_method.currentText())
        self.pushButton_11.setText("reload")
        self.pushButton_11.setEnabled(True)
        self.pushButton_11.parent().repaint()

        self.update_box(self.model.source, mode="source")
        self.apply_filter_to_source()

    def load_path(self, path=None, debug: bool = False) -> None:
        """Load a directory path, initialize the model/controllers, and reload the source list.

        Args:
            path: Directory path to load; opens a file dialog if ``None``/``False``.
            debug: Not used (reserved).
        """
        if path in [None, False]:
            # DontUseNativeDialog is used so files are shown along with dirs;
            folder = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Open directory",
                self.start_wd,
                QtWidgets.QFileDialog.DontUseNativeDialog,
            )
        else:
            folder = path

        if not os.path.isdir(folder):
            self.statusbar.showMessage(f"{folder} is not a folder.")
            folder = self.start_wd

        self.work_dir.setText(folder)

        if self.model is None:
            self.model = FileLocator(folder)
            self.plots = PlotController(self.model)
            self.jobs = JobManager(self.model, self.thread_pool)
        else:
            self.model.set_path(folder)
            self.model.clear()

        self.reload_source()
        # self.avg_job_table.setModel(self.jobs.avg_worker)
        self.source_model = self.model.source
        self.update_box(self.model.source, mode="source")

    def update_box(self, file_list, mode: str = "source") -> None:
        """Update a source or target list widget with the given :class:`ListDataModel`.

        Args:
            file_list: A ``ListDataModel`` instance to display.
            mode: Either ``"source"`` or ``"target"`` to select which list widget to update.
        """
        if file_list is None:
            return
        if mode == "source":
            self.list_view_source.setModel(file_list)
            self.box_source.setTitle(f"Source: {len(file_list):5d}")
            self.box_source.parent().repaint()
            self.list_view_source.parent().repaint()
        elif mode == "target":
            self.list_view_target.setModel(file_list)
            self.box_target.setTitle(f"Target: {len(file_list):5d}")
            # on macos, the target box doesn't seem to update; force it
            file_list.layoutChanged.emit()
            self.box_target.repaint()
            self.list_view_target.repaint()
            max_size = len(file_list) - 1
            self.horizontalSlider_saxs2d_selection.setMaximum(max_size)
            self.horizontalSlider_saxs2d_selection.setValue(0)
            self.spinBox_saxs2d_selection.setMaximum(max_size)
            self.spinBox_saxs2d_selection.setValue(0)
        self.statusbar.showMessage("Target file list updated.", 1000)
        return

    def add_target(self) -> None:
        """Add selected files from the source list to the target list."""
        target = []
        for x in self.list_view_source.selectedIndexes():
            # in some cases, it will return None
            val = x.data()
            if val is not None:
                target.append(val)
        if target == []:
            return

        if len(self.model.target) == 0:
            self._g2_bounds_initialized = False

        tab_id = self.tabWidget.currentIndex()
        tab_name = tab_mapping[tab_id]
        preload = tab_name != "average"
        self.model.add_target(target, preload=preload)
        self.list_view_source.clearSelection()
        self.update_box(self.model.target, mode="target")

        if tab_name == "average":
            self.init_average()
        else:
            self.update_plot()

    def reorder_target(self, direction: str = "up") -> None:
        """Reorder a single target entry up or down in the target list."""
        rows = self.get_selected_rows()
        if len(rows) != 1 or len(self.model.target) <= 1:
            return
        idx = self.model.reorder_target(rows[0], direction)
        self.list_view_target.setCurrentIndex(idx)
        self.list_view_target.repaint()
        self.update_plot()
        return

    def remove_target(self) -> None:
        """Remove selected files from the target list and update the UI."""
        rmv_list = []
        for index in self.list_view_target.selectedIndexes():
            rmv_list.append(self.model.target[index.row()])

        self.model.remove_target(rmv_list)
        # clear selection to avoid the bug: when the last one is selected, then
        # the list will out of bounds
        self.clear_target_selection()

        # if all files are removed; then go to state 1
        if self.model.target in [[], None] or len(self.model.target) == 0:
            self.reset_gui()
        self.update_box(self.model.target, mode="target")

    def reset_gui(self) -> None:
        """Reset the kernel and clear all plot widgets and input fields."""
        self.model.clear_target()
        self.plots.reset()
        for x in [
            # self.pg_saxs,
            self.pg_intt,
            self.mp_tauq,
            self.mp_g2,
            self.mp_saxs,
            self.mp_stab,
        ]:
            x.clear()
        self.le_bkg_fname.clear()

    def apply_filter_to_source(self) -> None:
        """Filter the source file list by prefix or substring based on the filter widget."""
        min_length = 1
        val = self.filter_str.text()
        if len(val) == 0:
            self.source_model = self.model.source
            self.update_box(self.model.source, mode="source")
            return
        # avoid searching when the filter lister is too short
        if len(val) < min_length:
            self.statusbar.showMessage(f"Please enter at least {min_length} characters", 1000)
            return

        filter_type = ["prefix", "substr"][self.filter_type.currentIndex()]
        self.model.search(val, filter_type)
        self.source_model = self.model.source_search
        self.update_box(self.source_model, mode="source")
        self.list_view_source.selectAll()

    def check_g2_number(self, default_val=(0, 0.0092, 1e-8, 1, 0.95, 1.35), tab: str = "g2"):
        """Read and validate G2 plot range values (q, t, y min/max) from widget state."""
        if tab == "g2":
            keys = (
                self.g2_qmin,
                self.g2_qmax,
                self.g2_tmin,
                self.g2_tmax,
                self.g2_ymin,
                self.g2_ymax,
            )
        else:  # for g2 stability
            keys = (
                self.g2_qmin_2,
                self.g2_qmax_2,
                self.g2_tmin_2,
                self.g2_tmax_2,
                self.g2_ymin_2,
                self.g2_ymax_2,
            )

        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            if isinstance(key, QtWidgets.QDoubleSpinBox):
                val = key.value()
            elif isinstance(key, QtWidgets.QLineEdit):
                try:
                    val = float(key.text())
                except Exception:
                    key.setText(str(default_val[n]))
                    self.statusbar.showMessage("g2 number is invalid", 1000)
            vals[n] = val

        def swap_min_max(id1: int, id2: int) -> None:
            """Swap values when min > max."""
            if vals[id1] > vals[id2]:
                keys[id1].setValue(vals[id2])
                keys[id2].setValue(vals[id1])
                vals[id1], vals[id2] = vals[id2], vals[id1]

        swap_min_max(0, 1)
        # swap_min_max(2, 3, lambda x: '%.2e' % x)
        swap_min_max(4, 5)

        return vals

    def check_g2_fitting_number(self) -> tuple[list, list, str]:
        """Read and validate g2 fitting parameter bounds from widget state.

        Returns:
            Tuple of ``(bounds, fit_flag, fit_func)`` where *bounds* is a list of [min, max] pairs.
        """
        fit_func = ["single", "double"][self.g2_fitting_function.currentIndex()]
        keys = (
            self.g2_amin,
            self.g2_amax,
            self.g2_bmin,
            self.g2_bmax,
            self.g2_cmin,
            self.g2_cmax,
            self.g2_dmin,
            self.g2_dmax,
            self.g2_b2min,
            self.g2_b2max,
            self.g2_c2min,
            self.g2_c2max,
            self.g2_fmin,
            self.g2_fmax,
        )

        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            vals[n] = key.value()

        def swap_min_max(id1: int, id2: int) -> None:
            """Swap values when min > max (for fitting parameter pairs)."""
            if vals[id1] > vals[id2]:
                keys[id1].setValue(vals[id2])
                keys[id2].setValue(vals[id1])
                vals[id1], vals[id2] = vals[id2], vals[id1]

        for n in range(0, 7):
            swap_min_max(2 * n, 2 * n + 1)

        vals = np.array(vals).reshape(len(keys) // 2, 2)
        bounds = vals.T

        fit_keys = (
            self.g2_afit,
            self.g2_bfit,
            self.g2_cfit,
            self.g2_dfit,
            self.g2_b2fit,
            self.g2_c2fit,
            self.g2_ffit,
        )
        fit_flag = [x.isChecked() for x in fit_keys]

        if fit_func == "single":
            fit_flag = fit_flag[0:4]
            bounds = bounds[:, 0:4]
        bounds = bounds.tolist()
        return bounds, fit_flag, fit_func

    def update_saxs2d_level(self, flag: bool = True) -> None:
        """Sync the SAXS-2D level spinboxes with the current image display levels."""
        if not flag:
            vmin = self.pg_saxs.levelMin
            vmax = self.pg_saxs.levelMax
            if vmin is not None:
                self.saxs2d_min.setValue(vmin)
            if vmax is not None:
                self.saxs2d_max.setValue(vmax)
            self.saxs2d_min.setEnabled(True)
            self.saxs2d_max.setEnabled(True)
        else:
            self.saxs2d_min.setDisabled(True)
            self.saxs2d_max.setDisabled(True)

        self.saxs2d_min.parent().repaint()

    def clear_target_selection(self) -> None:
        """Clear the selection in the target list widget."""
        self.list_view_target.clearSelection()

    def update_g2_fitting_function(self) -> None:
        """Update the g2 fitting function title and parameter widget visibility."""
        idx = self.g2_fitting_function.currentIndex()
        title = [
            "g2 fitting with Single Exp:  y = a·exp[-2(x/b)^c]+d",
            "g2 fitting with Double Exp:  y = a·[f·exp[-(x/b)^c +" + "(1-f)·exp[-(x/b2)^c2]^2+d",
        ]
        self.groupBox_2.setTitle(title[idx])

        pvs = [
            [self.g2_b2min, self.g2_b2max, self.g2_b2fit],
            [self.g2_c2min, self.g2_c2max, self.g2_c2fit],
            [self.g2_fmin, self.g2_fmax, self.g2_ffit],
        ]

        # change from double to single
        if idx == 0:
            for n in range(3):
                pvs[n][0].setDisabled(True)
                pvs[n][1].setDisabled(True)
                pvs[n][2].setDisabled(True)
        # change from single to double
        else:
            for n in range(3):
                pvs[n][2].setEnabled(True)
                pvs[n][1].setEnabled(True)
                if pvs[n][2].isChecked():
                    pvs[n][0].setEnabled(True)


def setup_windows_icon() -> None:
    """Set the Windows AppUserModelID for taskbar pinning (Windows only)."""
    # reference: https://stackoverflow.com/questions/1551605
    import ctypes
    from ctypes import wintypes

    lpBuffer = wintypes.LPWSTR()
    AppUserModelID = ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID
    AppUserModelID(ctypes.cast(ctypes.byref(lpBuffer), wintypes.LPWSTR))
    appid = lpBuffer.value
    ctypes.windll.kernel32.LocalFree(lpBuffer)
    if appid is None:
        appid = "aps.xpcs_viewer.viewer.0.20"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)


def qt_message_handler(mode, context, message):
    """
    A custom message handler that intercepts Qt messages and prints a traceback
    for specific warnings.
    """
    # Check if the message contains the text of the warnings we're interested in
    if "QGraphicsItem::itemTransform: null pointer passed" in message:
        print("--- Caught 'null pointer' warning. Traceback: ---")
        traceback.print_stack()
        print("-------------------------------------------------")

    if "unique connections require a pointer" in message:
        print("--- Caught 'unique connections' warning. Traceback: ---")
        traceback.print_stack()
        print("-----------------------------------------------------")

    # Use the default handler to still print the original message
    # You might need to find the original handler if you want to be perfectly clean,
    # but for debugging, printing the message here is fine.
    print(f"Qt Message: {message} (type: {mode}, context: {context.file}:{context.line})")


def main_gui(path=None, label_style=None) -> int:
    """Launch the pyXPCSViewer GUI application.

    Args:
        path: Starting directory for file browsing; opens user's home if ``None``.
        label_style: Comma-separated index string for deriving short file labels.

    Returns:
        The Qt application exit code.
    """
    qInstallMessageHandler(qt_message_handler)

    if os.name == "nt":
        setup_windows_icon()
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    app = QtWidgets.QApplication([])
    window = XpcsViewer(path=path, label_style=label_style)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main_gui()
