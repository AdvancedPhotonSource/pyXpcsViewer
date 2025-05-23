import os
from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot

import logging
import uuid
import time
import numpy as np
from ..fileIO.hdf_reader import put
from ..xpcs_file import XpcsFile as XF
from shutil import copyfile
from ..helper.listmodel import ListDataModel
import pyqtgraph as pg
from tqdm import trange
import traceback


logger = logging.getLogger(__name__)


def average_plot_cluster(self, hdl1, num_clusters=2):
    if (
        self.meta["avg_file_list"] != tuple(self.target)
        or "avg_intt_minmax" not in self.meta
    ):
        logger.info("avg cache not exist")
        labels = ["Int_t"]
        res = self.fetch(labels, file_list=self.target)
        Int_t = res["Int_t"][:, 1, :].astype(np.float32)
        Int_t = Int_t / np.max(Int_t)
        intt_minmax = []
        for n in range(len(self.target)):
            intt_minmax.append([np.min(Int_t[n]), np.max(Int_t[n])])
        intt_minmax = np.array(intt_minmax).T.astype(np.float32)

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
    title = "%d / %d" % (valid_num, y_pred.size)
    hdl1.show_scatter(
        intt_minmax, color=y_pred, xlabel="Int-t min", ylabel="Int-t max", title=title
    )


class WorkerSignal(QObject):
    progress = QtCore.Signal(tuple)
    values = QtCore.Signal(tuple)
    status = QtCore.Signal(tuple)


class AverageToolbox(QtCore.QRunnable):
    def __init__(self, work_dir=None, flist=["hello"], jid=None) -> None:
        super().__init__()
        self.file_list = flist.copy()
        self.model = ListDataModel(self.file_list)

        self.work_dir = work_dir
        self.signals = WorkerSignal()
        self.kwargs = {}
        if jid is None:
            self.jid = uuid.uuid4()
        else:
            self.jid = jid
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
        # axis to show the baseline;
        self.ax = None
        # use one file as templelate
        self.origin_path = os.path.join(self.work_dir, self.model[0])

        self.is_killed = False

    def kill(self):
        self.is_killed = True

    def __str__(self) -> str:
        return str(self.jid)

    def generate_avg_fname(self):
        if len(self.model) == 0:
            return
        fname = self.model[0]
        end = fname.rfind("_")
        if end == -1:
            end = len(fname)
        new_fname = "Avg" + fname[slice(0, end)]
        # if new_fname[-3:] not in ['.h5', 'hdf']:
        #     new_fname += '.hdf'
        return new_fname

    @Slot()
    def run(self):
        self.do_average(*self.args, **self.kwargs)

    def setup(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def do_average(
        self,
        chunk_size=256,
        save_path=None,
        avg_window=3,
        avg_qindex=0,
        avg_blmin=0.95,
        avg_blmax=1.05,
        fields=["saxs_2d"],
    ):
        self.stime = time.strftime("%H:%M:%S")
        self.status = "running"
        logger.info("average job %d starts", self.jid)
        tot_num = len(self.model)
        steps = (tot_num + chunk_size - 1) // chunk_size
        mask = np.zeros(tot_num, dtype=np.int64)
        prev_percentage = 0

        def validate_g2_baseline(g2_data, q_idx):
            if q_idx >= g2_data.shape[1]:
                idx = 0
                logger.info("q_index is out of range; using 0 instead")
            else:
                idx = q_idx

            g2_baseline = np.mean(g2_data[-avg_window:, idx])
            if avg_blmax >= g2_baseline >= avg_blmin:
                return True, g2_baseline
            else:
                return False, g2_baseline

        result = {}
        for key in fields:
            result[key] = None

        t0 = time.perf_counter()
        for n in range(steps):
            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(tot_num, end)
            for m in range(beg, end):
                # time.sleep(0.5)
                if self.is_killed:
                    logger.info("the averaging instance has been killed.")
                    self._progress = "killed"
                    self.status = "killed"
                    return

                curr_percentage = int((m + 1) * 100 / tot_num)
                if curr_percentage >= prev_percentage:
                    prev_percentage = curr_percentage
                    dt = (time.perf_counter() - t0) / (m + 1)
                    eta = dt * (tot_num - m - 1)
                    self.eta = eta
                    self._progress = "%d%%" % (curr_percentage)
                    # self.signals.progress.emit((self.jid, curr_percentage))

                fname = self.model[m]
                try:
                    xf = XF(os.path.join(self.work_dir, fname), fields=fields)
                    flag, val = validate_g2_baseline(xf.g2, avg_qindex)
                    self.baseline[self.ptr] = val
                    self.ptr += 1
                # except Exceptionn as ec:
                except:
                    traceback.print_exc()
                    flag, val = False, 0
                    logger.error("file %s is damaged, skip", fname)

                if flag:
                    for key in fields:
                        if key != "saxs_1d":
                            data = xf.__getattr__(key)
                        else:
                            data = xf.__getattr__("saxs_1d")["data_raw"]
                        if result[key] is None:
                            result[key] = data
                            mask[m] = 1
                        elif result[key].shape == data.shape:
                            result[key] += data
                            mask[m] = 1
                        else:
                            logger.info(
                                f"data shape does not match for key {key}, {fname}"
                            )

                self.signals.values.emit((self.jid, val))

        if np.sum(mask) == 0:
            logger.info("no dataset is valid; check the baseline criteria.")
            return
        else:
            for key in fields:
                if key == "saxs_1d":
                    # only keep the Iq component, put method doesn't accept dict
                    result["saxs_1d"] = result["saxs_1d"] / np.sum(mask)
                else:
                    result[key] /= np.sum(mask)
                if key == "g2_err":
                    result[key] /= np.sqrt(np.sum(mask))
                if key == "saxs_2d":
                    # saxs_2d needs to be (1, height, width)
                    saxs_2d = result[key]
                    if saxs_2d.ndim == 2:
                        saxs_2d = np.expand_dims(saxs_2d, axis=0)
                    result[key] = saxs_2d

            logger.info("the valid dataset number is %d / %d" % (np.sum(mask), tot_num))

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
        hdl.clear()
        t = hdl.addPlot()
        t.setLabel("bottom", "Dataset Index")
        t.setLabel("left", "g2 baseline")
        self.ax = t.plot(symbol="o")
        if "avg_blmin" in self.kwargs:
            dn = pg.InfiniteLine(
                pos=self.kwargs["avg_blmin"], angle=0, pen=pg.mkPen("r")
            )
            t.addItem(dn)
        if "avg_blmax" in self.kwargs:
            up = pg.InfiniteLine(
                pos=self.kwargs["avg_blmax"], angle=0, pen=pg.mkPen("r")
            )
            # t.addItem(pg.FillBetweenItem(dn, up))
            t.addItem(up)
        t.setMouseEnabled(x=False, y=False)

        return

    def update_plot(self):
        if self.ax is not None:
            self.ax.setData(self.baseline[: self.ptr])
            return

    def get_pg_tree(self):
        data = {}
        for key, val in self.kwargs.items():
            if isinstance(val, np.ndarray):
                if val.size > 4096:
                    data[key] = "data size is too large"
                # suqeeze one-element array
                if val.size == 1:
                    data[key] = float(val)
            else:
                data[key] = val

        # additional keys to describe the worker
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
    work_dir=None,
    save_path=None,
    avg_window=3,
    avg_qindex=0,
    avg_blmin=0.95,
    avg_blmax=1.05,
    fields=["saxs_2d", "saxs_1d", "g2", "g2_err"],
):

    if work_dir is None:
        work_dir = "./"

    tot_num = len(flist)
    abs_cs_scale_tot = 0.0
    baseline = np.zeros(tot_num, dtype=np.float32)
    mask = np.zeros(tot_num, dtype=np.int64)

    def validate_g2_baseline(g2_data, q_idx):
        if q_idx >= g2_data.shape[1]:
            idx = 0
            logger.info("q_index is out of range; using 0 instead")
        else:
            idx = q_idx

        g2_baseline = np.mean(g2_data[-avg_window:, idx])
        if avg_blmax >= g2_baseline >= avg_blmin:
            return True, g2_baseline
        else:
            return False, g2_baseline

    result = {}
    for key in fields:
        result[key] = None

    for m in trange(tot_num):
        fname = flist[m]
        try:
            xf = XF(os.path.join(work_dir, fname), fields=fields)
            flag, val = validate_g2_baseline(xf.g2, avg_qindex)
            baseline[m] = val
        except Exception as ec:
            flag, val = False, 0
            traceback.print_exc()
            logger.error("file %s is damaged, skip", fname)

        if flag:
            for key in fields:
                if key != "saxs_1d":
                    data = xf.at(key)
                else:
                    data = xf.at("saxs_1d")["data_raw"]
                    scale = xf.abs_cross_section_scale
                    if scale is None:
                        scale = 1.0
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
    else:
        for key in fields:
            if key == "saxs_1d":
                result["saxs_1d"] /= abs_cs_scale_tot
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
