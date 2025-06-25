import os
from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot
import logging
import uuid
import time
import numpy as np
from ..fileIO.hdf_reader import put, get
from ..xpcs_file import XpcsFile as XF
from shutil import copyfile
from ..helper.listmodel import ListDataModel
import pyqtgraph as pg
from tqdm import trange
import traceback

logger = logging.getLogger(__name__)


def average_plot_cluster(self, hdl1, num_clusters=2):
    """
    Cluster datasets based on min/max of normalized Int_t and visualize them.

    Parameters
    ----------
    self : object with fetch and meta
    hdl1 : UI plot handler
    num_clusters : int
        Number of clusters to form
    """
    if (
        self.meta["avg_file_list"] != tuple(self.target)
        or "avg_intt_minmax" not in self.meta
    ):
        logger.info("avg cache not exist")
        labels = ["Int_t"]
        res = self.fetch(labels, file_list=self.target)
        Int_t = res["Int_t"][:, 1, :].astype(np.float32)
        Int_t = Int_t / np.max(Int_t)
        intt_minmax = np.array([[np.min(row), np.max(row)] for row in Int_t]).T.astype(
            np.float32
        )

        self.meta["avg_file_list"] = tuple(self.target)
        self.meta["avg_intt_minmax"] = intt_minmax
        self.meta["avg_intt_mask"] = np.ones(len(self.target))
    else:
        logger.info("using avg cache")
        intt_minmax = self.meta["avg_intt_minmax"]

    y_pred = sk_kmeans(n_clusters=num_clusters).fit_predict(intt_minmax.T)
    freq = np.bincount(y_pred)
    self.meta["avg_intt_mask"] = y_pred == y_pred[freq.argmax()]
    valid_num = np.sum(y_pred == y_pred[freq.argmax()])
    title = f"{valid_num} / {y_pred.size}"
    hdl1.show_scatter(
        intt_minmax, color=y_pred, xlabel="Int-t min", ylabel="Int-t max", title=title
    )


def validate_g2_baseline(
    g2_data, avg_window=3, avg_qindex=0, avg_blmin=0.95, avg_blmax=1.05
):
    """
    Check if the G2 baseline in the given Q index falls within a valid range.

    Returns
    -------
    (bool, float)
        Whether baseline is valid, and the baseline value
    """
    idx = avg_qindex if avg_qindex < g2_data.shape[1] else 0
    g2_baseline = np.mean(g2_data[-avg_window:, idx])
    return avg_blmin <= g2_baseline <= avg_blmax, g2_baseline


class WorkerSignal(QObject):
    """Custom signal class for background average worker."""

    progress = QtCore.Signal(tuple)
    values = QtCore.Signal(tuple)
    status = QtCore.Signal(tuple)


class AverageToolbox(QtCore.QRunnable):
    """
    Background QRunnable for averaging datasets with G2 filtering and progress tracking.
    Emits signals for progress, status, and individual value feedback.
    """

    def __init__(self, work_dir=None, flist=["hello"], jid=None) -> None:
        super().__init__()
        self.file_list = flist.copy()
        self.model = ListDataModel(self.file_list)
        self.work_dir = work_dir
        self.signals = WorkerSignal()
        self.kwargs = {}
        self.jid = jid or uuid.uuid4()
        self.submit_time = time.strftime("%H:%M:%S")
        self.stime = self.submit_time
        self.etime = "--:--:--"
        self.status = "wait"
        self.baseline = np.zeros(max(len(self.model), 10), dtype=np.float32)
        self.ptr = 0
        self.short_name = self.generate_avg_fname()
        self.eta = "..."
        self.size = len(self.model)
        self._progress = "0%"
        self.ax = None
        self.origin_path = os.path.join(self.work_dir, self.model[0])
        self.is_killed = False

    def kill(self):
        """Signal the worker to stop."""
        self.is_killed = True

    def __str__(self) -> str:
        return str(self.jid)

    def generate_avg_fname(self):
        """Generate a default output filename prefix."""
        if len(self.model) == 0:
            return None
        fname = self.model[0]
        end = fname.rfind("_")
        end = end if end != -1 else len(fname)
        return "Avg" + fname[:end]

    @Slot()
    def run(self):
        self.do_average(*self.args, **self.kwargs)

    def setup(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def do_average(
        self,
        save_path=None,
        avg_window=3,
        avg_qindex=0,
        avg_blmin=0.95,
        avg_blmax=1.05,
        fields=["saxs_2d"],
    ):
        """
        Run the averaging operation on the dataset list with filtering and signal emission.
        """
        self.stime = time.strftime("%H:%M:%S")
        self.status = "running"
        tot_num = len(self.model)
        logger.info(
            f"Averaging worker [{self.jid}] starts on {tot_num} datasets with fields {fields}."
        )

        mask = np.zeros(tot_num, dtype=np.int64)
        result = {key: 0.0 for key in fields}

        t0 = time.perf_counter()
        for m in range(tot_num):
            if self.is_killed:
                logger.info("the averaging instance has been killed.")
                self._progress = "killed"
                self.status = "killed"
                return

            # ETA and progress tracking
            curr_percentage = int((m + 1) * 100 / tot_num)
            dt = (time.perf_counter() - t0) / (m + 1)
            self.eta = dt * (tot_num - m - 1)
            self._progress = f"{curr_percentage}%"

            fname = os.path.join(self.work_dir, self.model[m])
            try:
                xf = get(fname, fields=fields, mode="alias", ret_type="dict")
                flag, val = validate_g2_baseline(
                    xf["g2"], avg_window, avg_qindex, avg_blmin, avg_blmax
                )
                self.baseline[self.ptr] = val
                self.ptr += 1
                if flag:
                    for key in fields:
                        result[key] += xf[key]
                        mask[m] = 1
            except Exception:
                traceback.print_exc()
                logger.error(f"unable to process file {fname}, skip")

            self.signals.values.emit((self.jid, val))

        num_valid_dsets = np.sum(mask)
        if num_valid_dsets == 0:
            logger.info("no dataset is valid; check the baseline criteria.")
        else:
            logger.info(f"the valid dataset number is {num_valid_dsets} / {tot_num}")
            for key in fields:
                result[key] /= num_valid_dsets
                if key == "g2_err":
                    result[key] /= np.sqrt(num_valid_dsets)
                if key == "saxs_2d" and result[key].ndim == 2:
                    result[key] = np.expand_dims(result[key], axis=0)

            logger.info("create file: {}".format(save_path))
            copyfile(self.origin_path, save_path)
            put(save_path, result, ftype="nexus", mode="alias")

        self.status = "finished"
        self.signals.status.emit((self.jid, self.status))
        self.etime = time.strftime("%H:%M:%S")
        self.model.layoutChanged.emit()
        self.signals.progress.emit((self.jid, 100))
        logger.info("average job %d finished", self.jid)
        return result

    def initialize_plot(self, hdl):
        """Initialize scatter plot for g2 baseline values."""
        hdl.clear()
        t = hdl.addPlot()
        t.setLabel("bottom", "Dataset Index")
        t.setLabel("left", "g2 baseline")
        self.ax = t.plot(symbol="o")
        if "avg_blmin" in self.kwargs:
            t.addItem(
                pg.InfiniteLine(
                    pos=self.kwargs["avg_blmin"], angle=0, pen=pg.mkPen("r")
                )
            )
        if "avg_blmax" in self.kwargs:
            t.addItem(
                pg.InfiniteLine(
                    pos=self.kwargs["avg_blmax"], angle=0, pen=pg.mkPen("r")
                )
            )
        t.setMouseEnabled(x=False, y=False)

    def update_plot(self):
        """Update the baseline plot with current data."""
        if self.ax is not None:
            self.ax.setData(self.baseline[: self.ptr])

    def get_pg_tree(self):
        """Return a data tree widget with job metadata and parameters."""
        data = {}
        for key, val in self.kwargs.items():
            if isinstance(val, np.ndarray):
                data[key] = (
                    "data size is too large"
                    if val.size > 4096
                    else float(val) if val.size == 1 else val
                )
            else:
                data[key] = val

        add_keys = ["submit_time", "etime", "status", "baseline", "ptr", "eta", "size"]
        for key in add_keys:
            data[key] = self.__dict__[key]

        if self.size > 20:
            data["first_10_datasets"] = self.model[0:10]
            data["last_10_datasets"] = self.model[-10:]
        else:
            data["input_datasets"] = self.model[:]

        tree = pg.DataTreeWidget(data=data)
        tree.setWindowTitle("Job_%d_%s" % (self.jid, self.model[0]))
        tree.resize(600, 800)
        return tree


def do_average(
    flist,
    work_dir="./",
    save_path="avg_test.hdf",
    avg_window=3,
    avg_qindex=0,
    avg_blmin=0.95,
    avg_blmax=1.05,
    fields=["saxs_2d", "saxs_1d", "g2", "g2_err"],
):
    """
    Standalone function for averaging datasets.
    Suitable for batch/script mode without GUI.

    Returns
    -------
    np.ndarray
        The baseline values from each file.
    """
    tot_num = len(flist)
    abs_cs_scale_tot = 0.0
    baseline = np.zeros(tot_num, dtype=np.float32)
    mask = np.zeros(tot_num, dtype=np.int64)
    result = {key: None for key in fields}

    for m in trange(tot_num):
        fname = flist[m]
        try:
            xf = XF(os.path.join(work_dir, fname), fields=fields)
            flag, val = validate_g2_baseline(
                xf.g2, avg_window, avg_qindex, avg_blmin, avg_blmax
            )
            baseline[m] = val
        except Exception:
            flag, val = False, 0
            traceback.print_exc()
            logger.error("file %s is damaged, skip", fname)

        if flag:
            for key in fields:
                data = xf.at(key) if key != "saxs_1d" else xf.at("saxs_1d")["data_raw"]
                if key == "saxs_1d":
                    scale = xf.abs_cross_section_scale or 1.0
                    data *= scale
                    abs_cs_scale_tot += scale

                if result[key] is None:
                    result[key] = data
                    mask[m] = 1
                elif result[key].shape == data.shape:
                    result[key] += data
                    mask[m] = 1
                else:
                    logger.info(f"data shape does not match for key {key}, {fname}")

    if np.sum(mask) == 0:
        logger.info("no dataset is valid; check the baseline criteria.")
        return

    for key in fields:
        if key == "saxs_1d":
            result[key] /= abs_cs_scale_tot
        else:
            result[key] /= np.sum(mask)
        if key == "g2_err":
            result[key] /= np.sqrt(np.sum(mask))

    logger.info("the valid dataset number is %d / %d" % (np.sum(mask), tot_num))
    original_file = os.path.join(work_dir, flist[0])
    if save_path is None:
        save_path = "AVG" + os.path.basename(flist[0])
    logger.info("create file: {}".format(save_path))
    copyfile(original_file, save_path)
    put(save_path, result, ftype="nexus", mode="alias")

    return baseline
