# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import os

import numpy as np
import pyqtgraph as pg

from ...core.xpcs_file import XpcsFile
from ..model.file_locator import FileLocator
from .average_toolbox import AverageToolbox
from .plot import g2mod, intt, saxs1d, saxs2d, stability, tauq, twotime

logger = logging.getLogger(__name__)


def _build_pg_tree(xf) -> pg.DataTreeWidget:
    """Build a pyqtgraph DataTreeWidget from an XpcsFile's loaded data.

    Args:
        xf: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance.

    Returns:
        A populated ``DataTreeWidget`` window.
    """
    data = xf.load_data()
    for key, val in data.items():
        if isinstance(val, np.ndarray):
            if val.size > 4096:
                data[key] = "data size is too large"
            if val.size == 1:
                data[key] = float(val)
    data["analysis_type"] = xf.atype
    data["label"] = xf.label
    tree = pg.DataTreeWidget(data=data)
    tree.setWindowTitle(xf.fname)
    tree.resize(600, 800)
    return tree


class ViewerKernel(FileLocator):
    """Controller for the XPCS viewer GUI — mediates between model files and plot widgets."""

    def __init__(self, path: str, statusbar=None):
        """Initialize with a data directory and optional status bar widget.

        Args:
            path: Directory containing XPCS result HDF5 files.
            statusbar: Optional PySide6 ``QStatusBar`` for progress messages.
        """
        super().__init__(path)
        self.statusbar = statusbar
        self.meta = None
        self.reset_meta()
        self.path = path
        self.avg_worker = None
        self.avg_jid = 0
        self.avg_worker_active = {}
        self.current_dset = None

    def reset_meta(self) -> dict:
        """Reset all metadata fields (SAXS-1D background, averaging state)."""
        self.meta = {
            # saxs 1d:
            "saxs1d_bkg_fname": None,
            "saxs1d_bkg_xf": None,
            # avg
            "avg_file_list": None,
            "avg_intt_minmax": None,
            "avg_g2_avg": None,
            # g2
        }
        return

    def reset_kernel(self) -> None:
        """Clear the target file list and reset all metadata."""
        self.clear_target()
        self.reset_meta()

    def select_bkgfile(self, fname: str) -> None:
        """Set a background SAXS-1D reference file in metadata.

        Args:
            fname: Path to the HDF5 background result file.
        """
        base_fname = os.path.basename(fname)
        self.meta["saxs1d_bkg_fname"] = base_fname
        self.meta["saxs1d_bkg_xf"] = XpcsFile(fname, qmap_manager=self.qmap_manager)

    def get_pg_tree(self, rows: list[int] | None = None) -> pg.DataTreeWidget | None:
        """Return a pyqtgraph DataTreeWidget for the first target file.

        Args:
            rows: List of target indices; ``None`` uses all targets.
        """
        xf_list = self.get_xf_list(rows)
        if xf_list:
            return _build_pg_tree(xf_list[0])
        else:
            return None

    def get_fitting_tree(self, rows: list[int] | None = None):
        """Return a pyqtgraph DataTreeWidget with per-file g2 fitting summaries.

        Args:
            rows: List of target indices; ``None`` uses all multitau targets.
        """
        xf_list = self.get_xf_list(rows, filter_atype="Multitau")
        result = {}
        for x in xf_list:
            result[x.label] = x.get_fitting_info(mode="g2_fitting")
        tree = pg.DataTreeWidget(data=result)
        tree.setWindowTitle("fitting summary")
        tree.resize(1024, 800)
        return tree

    def plot_g2(self, handler, q_range, t_range, y_range, rows=None, **kwargs):
        """Delegate to :func:`.plot.g2mod.pg_plot` for multitau G2 data.

        Returns:
            Tuple of ``(q_values, elapsed_time)`` arrays, or ``(None, None)``.
        """
        xf_list = self.get_xf_list(rows=rows, filter_atype="Multitau")
        if xf_list:
            g2mod.pg_plot(handler, xf_list, q_range, t_range, y_range, rows=rows, **kwargs)
            q, tel, *_unused = g2mod.get_g2_data(xf_list)
            return q, tel
        else:
            return None, None

    def plot_g2_stability(self, handler, q_range, t_range, y_range, rows=None, **kwargs):
        """Delegate to :func:`.plot.g2mod.pg_plot_stability` for G2 stability display."""
        xf_obj = self.get_xf_list(rows=rows, filter_atype="Multitau")[0]
        if xf_obj and xf_obj.g2_partial is not None:
            g2mod.pg_plot_stability(handler, xf_obj, q_range, t_range, y_range, rows=rows, **kwargs)
            q, tel, *_unused = g2mod.get_g2_data([xf_obj])
            return q, tel
        else:
            return None, None

    def plot_g2map(self, g2map_hdl, qmap_hdl, g2_hdl, rows=None, qbin: int = 0, normalization: bool = False):
        """Display a G2 correlation image overlayed with its Q-map and a G2-vs-tau trace.

        Args:
            g2map_hdl: ``ImageView`` widget for the G2 correlation image.
            qmap_hdl: ``ImageView`` widget for the Q-map display.
            g2_hdl: ``PlotWidget`` for the G2 vs time-delay trace.
            rows: List of target indices; uses all targets if ``None``.
            qbin: Column index in the G2 array to extract for the trace.
            normalization: Apply baseline normalisation before display.
        """
        xf_obj = self.get_xf_list(rows=rows)[0]
        if xf_obj:
            g2map_hdl.setImage(xf_obj.get_offseted_g2(normalization).T)
            qmap_hdl.setImage(xf_obj.get_cropped_qmap("dqmap"))

            g2_hdl.clear()
            color = (0, 128, 255)
            pen = pg.mkPen(color=color, width=2)

            x = xf_obj.t_el
            y = xf_obj.g2[:, qbin]
            dy = xf_obj.g2_err[:, qbin]

            line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy, pen=pen)
            pen = pg.mkPen(color=color, width=1)
            g2_hdl.plot(
                x,
                y,
                pen=None,
                symbol="o",
                name=f"{qbin=}",
                symbolSize=3,
                symbolPen=pen,
                symbolBrush=None,  # no fill → hollow markers
            )

            g2_hdl.setLogMode(x=True, y=None)
            g2_hdl.addItem(line)
            g2_hdl.setLabel("bottom", "tau", units="s")
            g2_hdl.setLabel("left", "g2")
            return

    def plot_qmap(self, hdl, rows=None, target: str | None = None, cmap: str = "tab20b"):
        """Display a Q-map image (scattering intensity or ROI maps) with a colour map.

        Args:
            hdl: ``ImageView`` widget to draw on.
            rows: List of target indices; uses all targets if ``None``.
            target: One of ``"scattering"``, ``"dynamic_roi_map"``, or ``"static_roi_map"``.
            cmap: Name of the matplotlib colour map.
        """
        xf_list = self.get_xf_list(rows=rows)
        if xf_list:
            if target == "scattering":
                value = np.log10(xf_list[0].saxs_2d + 1)
                vmin, vmax = np.percentile(value, (2, 98))
                hdl.setImage(value, levels=(vmin, vmax))
            elif target == "dynamic_roi_map":
                hdl.setImage(xf_list[0].dqmap)
            elif target == "static_roi_map":
                hdl.setImage(xf_list[0].sqmap)
            hdl.setColorMap(pg.colormap.getFromMatplotlib(cmap))

    def plot_tauq_pre(self, hdl=None, rows=None):
        """Plot g2 fitting parameter pre-view subplots (contrast, tau, stretch, baseline vs q).

        Args:
            hdl: pyqtgraph ``GraphicsLayoutWidget`` to draw on.
            rows: List of target indices.
        """
        xf_list = self.get_xf_list(rows=rows, filter_atype="Multitau")
        short_list = [xf for xf in xf_list if xf.fit_summary is not None]
        tauq.plot_pre(short_list, hdl)

    def plot_tauq(
        self,
        hdl=None,
        bounds=None,
        rows=None,
        plot_type: int = 3,
        fit_flag=None,
        offset=None,
        q_range=None,
    ):
        """Run tau-q fitting and plot the results.

        Args:
            hdl: pyqtgraph ``PlotWidget`` to draw on.
            bounds: Parameter bounds for tau-q fitting.
            rows: List of target indices.
            plot_type: Bitmask controlling axes scales.
            fit_flag: Boolean flags for free/fixed parameters.
            offset: Vertical log-offset per file.
            q_range: Q-range filter for the fit selection.

        Returns:
            Dict mapping file labels to fitting info, or ``{}`` on failure.
        """
        if rows is None:
            rows = []
        xf_list = self.get_xf_list(rows=rows, filter_atype="Multitau", filter_fitted=True)
        result = {}
        for x in xf_list:
            if x.fit_summary is None:
                logger.info("g2 fitting is not available for %s", x.fname)
            else:
                x.fit_tauq(q_range, bounds, fit_flag)
                result[x.label] = x.get_fitting_info(mode="tauq_fitting")

        if len(result) > 0:
            tauq.plot(xf_list, hdl=hdl, q_range=q_range, offset=offset, plot_type=plot_type)

        return result

    def get_info_at_mouse(self, rows: list[int], x: int, y: int) -> str | None:
        """Query intensity and Q-map values at pixel *(x, y)* for the first target file.

        Args:
            rows: List of target indices (uses the first).
            x: Column pixel index.
            y: Row pixel index.
        """
        xf = self.get_xf_list(rows)
        if xf:
            info = xf[0].get_info_at_position(x, y)
            return info

    def plot_saxs_2d(self, *args, rows=None, **kwargs):
        """Delegate SAXS-2D plotting to :func:`.plot.saxs2d.plot`."""
        xf_list = self.get_xf_list(rows)[0:1]
        if xf_list:
            saxs2d.plot(xf_list[0], *args, **kwargs)

    def plot_saxs_1d(self, pg_hdl, mp_hdl, **kwargs):
        """Delegate SAXS 1D plotting to :func:`.plot.saxs1d.pg_plot`.

        Args:
            pg_hdl: pyqtgraph plot handler (unused when only matplotlib is available).
            mp_hdl: Matplotlib plot handler widget.
            **kwargs: Passed to ``saxs1d.pg_plot``.
        """
        xf_list = self.get_xf_list()
        if xf_list:
            saxs1d.pg_plot(xf_list, mp_hdl, bkg_file=self.meta["saxs1d_bkg_xf"], **kwargs)

    def export_saxs_1d(self, pg_hdl, folder: str) -> None:
        """Export SAXS 1D data (ROI-extracted and full) to text files.

        Args:
            pg_hdl: pyqtgraph handler that holds the ROI definitions.
            folder: Destination directory for the output ``.txt`` files.
        """
        xf_list = self.get_xf_list()
        roi_list = pg_hdl.get_roi_list()
        for xf in xf_list:
            xf.export_saxs1d(roi_list, folder)
        return

    def switch_saxs1d_line(self, mp_hdl, lb_type):
        """Toggle the active matplotlib line-builder type (currently a no-op placeholder)."""
        pass
        # saxs1d.switch_line_builder(mp_hdl, lb_type)

    def savefile_G2_regroup(self, rows=None, **kwargs) -> bool | None:
        """Save regrouped G2 data to a new file.

        Args:
            rows: List of target indices; uses the first.
            **kwargs: Passed to :meth:`~pyxpcsviewer.core.xpcs_file.XpcsFile.save_G2`.

        Returns:
            ``True`` on success, ``False`` on failure, or ``None`` if no target file.
        """
        xf_list = self.get_xf_list(rows)
        if len(xf_list) == 0:
            return None
        xfile = xf_list[0]
        flag = xfile.save_G2(**kwargs)
        return flag

    def process_G2_regroup(self, rows=None, method: str = "internal", **kwargs) -> bool | None:
        """Re-group per-pixel G2 correlations into multitau bins for the first target file.

        Args:
            rows: List of target indices; uses the first.
            method: Reserved future parameter.
            **kwargs: Passed to :meth:`~pyxpcsviewer.core.xpcs_file.XpcsFile.regroup_G2`.

        Returns:
            ``True`` on success, ``False`` on failure, or ``None`` if no target file.
        """
        xf_list = self.get_xf_list(rows)
        if len(xf_list) == 0:
            return None
        xfile = xf_list[0]
        flag = xfile.regroup_G2(**kwargs)
        return flag

    def plot_G2_regroup(self, hdl, cmap: str = "jet", rows=None, vmin=None, vmax=None, **kwargs):
        """Display the per-pixel G2 correlation image with optional clipping and a colour map.

        Args:
            hdl: ``ImageView`` widget to draw on.
            cmap: Name of the matplotlib colour map.
            rows: List of target indices; uses all multitau targets.
            vmin / vmax: Optional intensity range for clipping.
            **kwargs: Passed to :meth:`~pyxpcsviewer.core.xpcs_file.XpcsFile.get_G2_data`.
        """
        xf_list = self.get_xf_list(rows, filter_atype="Multitau")
        if len(xf_list) == 0:
            return None
        xfile = xf_list[0]
        G2_data = xfile.get_G2_data(**kwargs)

        if vmin is not None and vmax is not None:
            G2_data = np.clip(G2_data, vmin, vmax)

        hdl.setImage(G2_data, levels=(vmin, vmax))
        hdl.setColorMap(pg.colormap.getFromMatplotlib(cmap))
        return

    def plot_twotime(self, hdl, rows=None, **kwargs):
        """Display two-time correlation (C2) map alongside SAXS-2D background and G2 traces.

        Args:
            hdl: Dict-like handle mapping names to ``ImageView`` / ``PlotWidget`` widgets.
            rows: List of target indices; uses twotime targets.
            **kwargs: Passed to :func:`.plot.twotime.plot_twotime`.

        Returns:
            A new ``qbin_labels`` list if the active file changed, else ``None``.
        """
        xf_list = self.get_xf_list(rows, filter_atype="Twotime")
        if len(xf_list) == 0:
            return None
        xfile = xf_list[0]
        new_qbin_labels = None
        if self.current_dset is None or self.current_dset.fname != xfile.fname:
            self.current_dset = xfile
            new_qbin_labels = xfile.get_twotime_qbin_labels()
        twotime.plot_twotime(xfile, hdl, **kwargs)
        return new_qbin_labels

    def plot_intt(self, pg_hdl, rows=None, **kwargs):
        """Plot intensity-vs-time curves with Fourier spectrum and zoom view.

        Args:
            pg_hdl: pyqtgraph ``GraphicsLayoutWidget`` to draw on.
            rows: List of target indices.
            **kwargs: Passed to :func:`.plot.intt.plot` (e.g. ``window``, ``sampling``).
        """
        xf_list = self.get_xf_list(rows=rows)
        intt.plot(xf_list, pg_hdl, **kwargs)

    def plot_stability(self, mp_hdl, rows=None, **kwargs):
        """Plot SAXS-1D partial intensities vs Q (stability/segment lines).

        Args:
            mp_hdl: matplotlib plot handler widget.
            rows: List of target indices; uses the first multitau target.
            **kwargs: Passed to :func:`.plot.stability.plot`.
        """
        xf_obj = self.get_xf_list(rows)[0]
        stability.plot(xf_obj, mp_hdl, **kwargs)

    def submit_job(self, status_bar=None, progress_bar=None, *args, **kwargs):
        """Create and configure an :class:`AverageToolbox` worker for background averaging.

        Args:
            status_bar: Optional ``QStatusBar`` for message display.
            progress_bar: Optional ``QProgressBar`` for progress tracking.
            *args: Positional arguments forwarded to ``AverageToolbox.setup()``.
            **kwargs: Keyword arguments forwarded to ``AverageToolbox.setup()``.

        Returns:
            The :class:`AverageToolbox` instance, or ``None`` if a job is already running
            or no target files are selected.
        """
        if self.avg_worker is not None:
            logger.error("average job is already running")
            return

        if len(self.target) <= 0:
            logger.error("no average target is selected")
            return

        worker = AverageToolbox(flist=self.target, jid=self.avg_jid)
        worker.setup(*args, **kwargs)
        worker.signals.status.connect(status_bar.showMessage)
        worker.signals.progress.connect(progress_bar.setValue)
        self.avg_worker = worker
        logger.info("create average job, ID = %s", worker.jid)
        self.avg_jid += 1
        self.target.clear()
        return

    def update_avg_info(self) -> None:
        """Trigger an update of the averaging worker's baseline plot."""
        if self.avg_worker is None:
            return
        self.avg_worker.update_plot()

    def update_avg_values(self, data: tuple) -> None:
        """Accumulate a streamed G2 value into the running average record.

        Args:
            data: Tuple of ``(jid, g2_value)`` emitted by an ``AverageToolbox`` worker.
        """
        key, val = data[0], data[1]
        if self.avg_worker_active[key] is None:
            self.avg_worker_active[key] = [0, np.zeros(128, dtype=np.float32)]
        record = self.avg_worker_active[key]
        if record[0] == record[1].size:
            new_g2 = np.zeros(record[1].size * 2, dtype=np.float32)
            new_g2[0 : record[0]] = record[1]
            record[1] = new_g2
        record[1][record[0]] = val
        record[0] += 1
        return

    def export_g2(self) -> None:
        """Placeholder — currently a no-op."""
        pass


if __name__ == "__main__":
    flist = os.listdir("./data")
    dv = ViewerKernel("./data", flist)
