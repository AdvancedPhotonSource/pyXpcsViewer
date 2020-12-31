import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSlot
import logging
import os
import numpy as np
from numpy.lib.npyio import save
from sklearn.cluster import k_means as sk_kmeans
from ..fileIO.hdf_reader import get, put
from ..xpcs_file import XpcsFile as XF
from collections import deque
from shutil import copyfile
import time


logger = logging.getLogger(__name__)


def average_plot_cluster(self, hdl1, num_clusters=2):
    if self.meta['avg_file_list'] != tuple(self.target) or \
            'avg_intt_minmax' not in self.meta:
        logger.info('avg cache not exist')
        labels = ['Int_t']
        res = self.fetch(labels, file_list=self.target)
        Int_t = res['Int_t'][:, 1, :].astype(np.float32)
        Int_t = Int_t / np.max(Int_t)
        intt_minmax = []
        for n in range(len(self.target)):
            intt_minmax.append([np.min(Int_t[n]), np.max(Int_t[n])])
        intt_minmax = np.array(intt_minmax).T.astype(np.float32)

        self.meta['avg_file_list'] = tuple(self.target)
        self.meta['avg_intt_minmax'] = intt_minmax
        self.meta['avg_intt_mask'] = np.ones(len(self.target))

    else:
        logger.info('using avg cache')
        intt_minmax = self.meta['avg_intt_minmax']

    y_pred = sk_kmeans(n_clusters=num_clusters).fit_predict(intt_minmax.T)
    freq = np.bincount(y_pred)
    self.meta['avg_intt_mask'] = y_pred == y_pred[freq.argmax()]
    valid_num = np.sum(y_pred == y_pred[freq.argmax()])
    title = '%d / %d' % (valid_num, y_pred.size)
    hdl1.show_scatter(intt_minmax,
                      color=y_pred,
                      xlabel='Int-t min',
                      ylabel='Int-t max',
                      title=title)


class DataModel(QtCore.QAbstractListModel):
    def __init__(self, input_list=None) -> None:
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.input_list[index.row()]
            return text

    def rowCount(self, index):
        return len(self.input_list)

    def update_data(self, new_input_list):
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def at(self, index):
        return self.input_list[index]

    def __len__(self):
        return len(self.input_list)


class WorkerSignal(QObject):
    progress = QtCore.pyqtSignal(int)
    values = QtCore.pyqtSignal(tuple)


class AverageToolbox(QtCore.QRunnable):

    def __init__(self, work_dir) -> None:
        super().__init__()
        self.file_list = []
        self.model = DataModel(self.file_list)
        self.work_dir = work_dir
        self.signals = WorkerSignal()
        self.kwargs = {}

    def update_data(self, new_list):
        self.model.update_data(new_list)

    def generate_avg_fname(self):
        if len(self.file_list) == 0:
            return
        fname = self.file_list[0]
        end = fname.rfind('_')
        if end == -1:
            end = len(fname)
        new_fname = 'Avg' + fname[slice(0, end)]
        if new_fname[-3:] not in ['.h5', 'hdf']:
            new_fname += '.hdf'
        return new_fname

    @pyqtSlot()
    def run(self):
        self.do_average(*self.args, **self.kwargs)

    def setup(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def do_average(self, chunk_size=256, save_path=None, origin_path=None,
                   avg_window=3, avg_qindex=0, avg_blmin=0.95, avg_blmax=1.05):
        tot_num = len(self.file_list)
        steps = (tot_num + chunk_size - 1) // chunk_size
        mask = np.ones(tot_num, dtype=np.int)
        valid_list = deque()
        discard_list = deque()

        fields = ["saxs_1d", 'g2', 'g2_err', 'saxs_2d']

        def validate_g2_baseline(g2_data):
            g2_baseline = np.mean(g2_data[-avg_window:, avg_qindex])
            if avg_blmax >= g2_baseline >= avg_blmin:
                return True, g2_baseline
            else:
                return False, g2_baseline

        result = {}
        for key in fields:
            result[key] = 0

        for n in range(steps):

            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(tot_num, end)
            for m in range(beg, end):
                if ((m + 1) * 100) % tot_num == 0:
                    self.signals.progress.emit(((m + 1) * 100) // tot_num)
                fname = self.file_list[m]
                xf = XF(fname, cwd=self.work_dir, fields=fields)
                flag, val = validate_g2_baseline(xf.g2)
                if flag:
                    valid_list.append(fname)
                    for key in fields:
                        result[key] += xf.at(key)
                else:
                    discard_list.append(fname)
                    mask[m] = 0
                self.signals.values.emit((m, val))

        for key in fields:
            result[key] /= np.sum(mask)

        save_path = os.path.join(self.work_dir, self.generate_avg_fname())
        if save_path is None:
            save_path = os.path.join(self.work_dir, self.generate_avg_fname())
        if origin_path is None:
            origin_path = os.path.join(self.work_dir, self.file_list[0])

        logger.info('create file: {}'.format(save_path))
        copyfile(origin_path, save_path)
        put(save_path, result, mode='alias')

        return result

    def initialize_plot(self, hdl):
        hdl.clear()
        t = hdl.addPlot()
        t.setLabel('bottom', 'Dataset Index')
        t.setLabel('left', 'g2 baseline')
        self.g2_data = np.zeros(shape=(100, 2))
        self.ptr = 0
        self.ax = t.plot(symbol='o')
        return

    def update_plot(self, new_data):
        size = len(self.g2_data)
        if self.ptr == size:
            g2_data = np.zeros(shape=(2 * size, 2))
            g2_data[:size] = self.g2_data
            self.g2_data = g2_data

        self.g2_data[self.ptr] = new_data
        self.ax.setData(x=self.g2_data[:self.ptr, 0],
                        y=self.g2_data[:self.ptr, 1])
        self.ptr += 1
        return
    
    def print(self):
        print('still alive')

