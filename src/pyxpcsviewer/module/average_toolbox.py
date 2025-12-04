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
from concurrent.futures import ProcessPoolExecutor, as_completed
from sklearn.cluster import (
    KMeans as sk_kmeans,
)  # Added this import based on the original code's usage

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


# Helper function for multiprocessing to process a single file
def _process_single_file(fname, fields, avg_window, avg_qindex, avg_blmin, avg_blmax):
    """
    Processes a single file to extract data and validate G2 baseline.
    This function is designed to be run in a separate process.

    Parameters
    ----------
    fname : str
        Path to the file to process.
    fields : list
        List of fields to fetch from the file.
    avg_window : int
        Window size for G2 baseline calculation.
    avg_qindex : int
        Q-index for G2 baseline calculation.
    avg_blmin : float
        Minimum allowed G2 baseline value.
    avg_blmax : float
        Maximum allowed G2 baseline value.

    Returns
    -------
    tuple
        A tuple containing:
        - dict: Processed data for the specified fields (or None if error/invalid).
        - float: G2 baseline value.
        - bool: True if the file is valid, False otherwise.
        - str: Original filename.
    """
    try:
        xf = get(fname, fields=fields, mode="alias", ret_type="dict")
        flag, val = validate_g2_baseline(
            xf["g2"], avg_window, avg_qindex, avg_blmin, avg_blmax
        )
        if flag:
            # If valid, return the data for averaging
            return {key: xf[key] for key in fields}, val, True, fname
        else:
            # If not valid, return None for data but still return baseline and validity
            return None, val, False, fname
    except Exception:
        traceback.print_exc()
        logger.error(f"unable to process file {fname}, skip")
        # Return None for data, baseline as 0.0, and False for validity on error
        return None, 0.0, False, fname


class WorkerSignal(QObject):
    """Custom signal class for background average worker."""

    progress = QtCore.Signal(tuple)
    values = QtCore.Signal(tuple)
    status = QtCore.Signal(tuple)
    finished = QtCore.Signal(bool)


class AverageToolbox(QtCore.QRunnable):
    """
    Background QRunnable for averaging datasets with G2 filtering and progress tracking.
    Emits signals for progress, status, and individual value feedback.
    """

    def __init__(self, flist=None, jid=None) -> None:
        super().__init__()
        self.model = ListDataModel(flist.copy() if flist else [])
        self.signals = WorkerSignal()
        self.kwargs = {}
        self.jid = jid or uuid.uuid4()
        self.submit_time = time.strftime("%H:%M:%S")
        self.stime = self.submit_time
        self.etime = "--:--:--"
        self.status = "wait"
        self.baseline = np.zeros(max(len(self.model), 1), dtype=np.float32)
        self.ptr = 0
        self.short_name = self.generate_avg_fname()
        self.eta = "..."
        self.size = len(self.model)
        self._progress = "0%"
        self.ax = None
        # Ensure model is not empty before accessing index 0
        self.origin_path = self.model[0] if self.model else None
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
        self.do_average_multiprocess(*self.args, **self.kwargs)

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
        This is the single-process version.
        """
        self.stime = time.strftime("%H:%M:%S")
        self.status = "running"
        tot_num = len(self.model)
        logger.info(
            f"Averaging worker [{self.jid}] starts on {tot_num} datasets with fields {fields}."
        )

        mask = np.zeros(tot_num, dtype=np.int64)
        result = {key: None for key in fields}  # Initialize with None, will be summed

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
            self.signals.progress.emit((self.jid, curr_percentage))  # Emit progress

            fname = self.model[m]
            try:
                xf = get(fname, fields=fields, mode="alias", ret_type="dict")
                flag, val = validate_g2_baseline(
                    xf["g2"], avg_window, avg_qindex, avg_blmin, avg_blmax
                )
                self.baseline[self.ptr] = val
                self.ptr += 1
                if flag:
                    for key in fields:
                        if result[key] is None:
                            result[key] = xf[
                                key
                            ].copy()  # Initialize with first valid data
                        else:
                            result[key] += xf[key]
                    mask[m] = 1
            except Exception:
                traceback.print_exc()
                logger.error(f"unable to process file {fname}, skip")

            self.signals.values.emit((self.jid, val))
            self.update_plot()  # Update plot after each file

        num_valid_dsets = np.sum(mask)
        if num_valid_dsets == 0:
            logger.info("no dataset is valid; check the baseline criteria.")
        else:
            logger.info(f"the valid dataset number is {num_valid_dsets} / {tot_num}")
            for key in fields:
                if result[key] is not None:
                    result[key] /= num_valid_dsets
                    if key == "g2_err":
                        result[key] /= np.sqrt(num_valid_dsets)
                    if key == "saxs_2d" and result[key].ndim == 2:
                        result[key] = np.expand_dims(result[key], axis=0)

            if save_path and self.origin_path:
                logger.info("create file: {}".format(save_path))
                try:
                    copyfile(self.origin_path, save_path)
                    put(save_path, result, ftype="nexus", mode="alias")
                except Exception as e:
                    logger.error(f"Error saving averaged file: {e}")
                    traceback.print_exc()
            else:
                logger.warning("save_path or origin_path is None, skipping file save.")

        self.status = "finished"
        self.signals.status.emit((self.jid, self.status))
        self.etime = time.strftime("%H:%M:%S")
        self.model.layoutChanged.emit()
        self.signals.progress.emit((self.jid, 100))
        self.signals.finished.emit(True)
        logger.info("average job %d finished", self.jid)
        return result

    def do_average_multiprocess(
        self,
        save_path=None,
        avg_window=3,
        avg_qindex=0,
        avg_blmin=0.95,
        avg_blmax=1.05,
        fields=["saxs_2d"],
        max_workers=None,
    ):
        """
        Run the averaging operation on the dataset list using multiprocessing with
        ProcessPoolExecutor for parallel processing and G2 filtering and signal emission.
        """
        self.stime = time.strftime("%H:%M:%S")
        self.status = "running (multiprocess)"
        tot_num = len(self.model)
        logger.info(
            f"Averaging worker [{self.jid}] starts multiprocess on {tot_num} datasets with fields {fields}."
        )

        # Initialize result accumulators. Using None for initial check if data is available.
        # This allows us to handle the first valid dataset correctly for initialization.
        final_averaged_data = {key: None for key in fields}
        num_valid_dsets = 0
        processed_files_count = 0

        t0 = time.perf_counter()

        # Using ProcessPoolExecutor for parallel processing
        # max_workers=None means it will default to the number of CPUs
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks for each file
            futures = {
                executor.submit(
                    _process_single_file,
                    fname,
                    fields,
                    avg_window,
                    avg_qindex,
                    avg_blmin,
                    avg_blmax,
                ): i
                for i, fname in enumerate(self.model)
            }

            # Process results as they complete
            for future in as_completed(futures):
                if self.is_killed:
                    logger.info(
                        "the averaging instance has been killed during multiprocessing."
                    )
                    self._progress = "killed"
                    self.status = "killed"
                    # Shut down the executor immediately to stop ongoing tasks
                    executor.shutdown(wait=False, cancel_futures=True)
                    return

                processed_files_count += 1
                curr_percentage = int((processed_files_count) * 100 / tot_num)
                dt = (time.perf_counter() - t0) / (processed_files_count)
                self.eta = dt * (tot_num - processed_files_count)
                self._progress = f"{curr_percentage}%"
                self.signals.progress.emit((self.jid, curr_percentage))

                try:
                    data_from_file, baseline_val, is_valid, original_fname = (
                        future.result()
                    )
                    self.baseline[self.ptr] = (
                        baseline_val  # Store baseline for plotting
                    )
                    self.ptr += 1
                    self.signals.values.emit((self.jid, baseline_val))
                    self.update_plot()  # Update plot after each result

                    if is_valid and data_from_file is not None:
                        num_valid_dsets += 1
                        for key in fields:
                            if final_averaged_data[key] is None:
                                final_averaged_data[key] = data_from_file[key].copy()
                            else:
                                final_averaged_data[key] += data_from_file[key]
                    else:
                        logger.warning(
                            f"File {original_fname} was invalid or failed processing."
                        )

                except Exception as e:
                    logger.error(f"Error processing a file in multiprocessing: {e}")
                    traceback.print_exc()
                    self.signals.values.emit((self.jid, 0.0))
                    self.update_plot()

        if num_valid_dsets == 0:
            logger.info("no dataset is valid; check the baseline criteria.")
            self.status = "finished"
            self.signals.status.emit((self.jid, self.status))
            self.etime = time.strftime("%H:%M:%S")
            self.model.layoutChanged.emit()
            self.signals.progress.emit((self.jid, 100))
            logger.info("average job %d finished (no valid datasets)", self.jid)
            return {}  # Return an empty dict if no valid datasets
        else:
            logger.info(f"the valid dataset number is {num_valid_dsets} / {tot_num}")
            # Final averaging step
            for key in fields:
                if final_averaged_data[key] is not None:
                    final_averaged_data[key] /= num_valid_dsets
                    if key == "g2_err":
                        final_averaged_data[key] /= np.sqrt(num_valid_dsets)
                    if key == "saxs_2d" and final_averaged_data[key].ndim == 2:
                        final_averaged_data[key] = np.expand_dims(
                            final_averaged_data[key], axis=0
                        )

            # Save the averaged data
            if save_path and self.origin_path:
                logger.info("create file: {}".format(save_path))
                try:
                    copyfile(self.origin_path, save_path)
                    put(save_path, final_averaged_data, ftype="nexus", mode="alias")
                except Exception as e:
                    logger.error(f"Error saving averaged file: {e}")
                    traceback.print_exc()
            else:
                logger.warning("save_path or origin_path is None, skipping file save.")

        self.status = "finished"
        self.signals.status.emit((self.jid, self.status))
        self.etime = time.strftime("%H:%M:%S")
        self.model.layoutChanged.emit()
        self.signals.progress.emit((self.jid, 100))
        logger.info("average job %d finished", self.jid)
        self.signals.finished.emit(True)
        return final_averaged_data

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
            # Only update with the actual collected data points
            self.ax.setData(self.baseline[: self.ptr])

    def get_pg_tree(self):
        """Return a data tree widget with job metadata and parameters."""
        data = {}
        for key, val in self.kwargs.items():
            if isinstance(val, np.ndarray):
                data[key] = (
                    "data size is too large"
                    if val.size > 4096
                    else float(val)
                    if val.size == 1
                    else val
                )
            else:
                data[key] = val

        add_keys = ["submit_time", "etime", "status", "baseline", "ptr", "eta", "size"]
        for key in add_keys:
            # For baseline, only show the relevant part
            if key == "baseline":
                data[key] = self.__dict__[key][
                    : self.ptr
                ].tolist()  # Convert to list for display
            else:
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
    save_path="avg_test.hdf",
    avg_window=3,
    avg_qindex=0,
    avg_blmin=0.95,
    avg_blmax=1.05,
    fields=["saxs_2d", "saxs_1d", "g2", "g2_err"],
):
    tot_num = len(flist)
    logger.info(f"Averaging starts on {tot_num} datasets with fields {fields}.")

    mask = np.zeros(tot_num, dtype=np.int64)
    result = {key: None for key in fields}  # Initialize with None, will be summed

    t0 = time.perf_counter()
    for m in trange(tot_num):
        fname = flist[m]
        try:
            xf = get(fname, fields=fields, mode="alias", ret_type="dict")
            flag, val = validate_g2_baseline(
                xf["g2"], avg_window, avg_qindex, avg_blmin, avg_blmax
            )
            if flag:
                for key in fields:
                    if result[key] is None:
                        result[key] = xf[key].copy()  # Initialize with first valid data
                    else:
                        result[key] += xf[key]
                mask[m] = 1
        except Exception:
            traceback.print_exc()
            logger.error(f"unable to process file {fname}, skip")

    num_valid_dsets = np.sum(mask)
    if num_valid_dsets == 0:
        logger.info("no dataset is valid; check the baseline criteria.")
    else:
        logger.info(f"the valid dataset number is {num_valid_dsets} / {tot_num}")
        for key in fields:
            if result[key] is not None:
                result[key] /= num_valid_dsets
                if key == "g2_err":
                    result[key] /= np.sqrt(num_valid_dsets)
                if key == "saxs_2d" and result[key].ndim == 2:
                    result[key] = np.expand_dims(result[key], axis=0)

        if save_path and self.origin_path:
            logger.info("create file: {}".format(save_path))
            try:
                copyfile(self.origin_path, save_path)
                put(save_path, result, ftype="nexus", mode="alias")
            except Exception as e:
                logger.error(f"Error saving averaged file: {e}")
                traceback.print_exc()
        else:
            logger.warning("save_path or origin_path is None, skipping file save.")

    logger.info("average job finished")
    return result
