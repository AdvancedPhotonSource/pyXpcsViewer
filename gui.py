from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QFileSystemModel
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import QObject, pyqtSlot, QDir
import sys
import os
from pyqtgraph import PlotWidget, ImageWindow
import matplotlib.pyplot as plt
import matplotlib
import pyqtgraph as pg
from matplot_qt import MplCanvas
from data_loader import DataLoader
from file_locator import FileLocator
import numpy as np
import time
# from xpcs_ui import


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        self.show()
        self.dl = None
        self.cache = None
        self.load_path()
        self.g2_cache = {}

    def load_data(self):
        if (len(self.dl.target_list)) == 0:
            return

        self.prepare_g2()
        self.btn_load_data.setEnabled(False)
        # self.update_hdf_list()
        self.dl.plot_stability(self.mp_stab, self.mp_stab_it)

    def update_hdf_list(self):
        self.hdf_list.clear()
        self.hdf_list.addItems(self.dl.target_list)

    def show_hdf_info(self):
        fname = self.hdf_list.currentText()
        msg = self.dl.get_hdf_info(fname)

        filter_str = self.hdf_key_filter.text()
        fstr = filter_str.split()
        if len(fstr) > 0:
            msg2 = []
            for x in fstr:
                for n, y in enumerate(msg):
                    if n == len(msg) - 1:
                        break
                    if x in y:
                        msg2 += [msg[n], msg[n + 1]]
            msg = msg2
        self.hdf_info.clear()
        self.hdf_info.setText('\n'.join(msg))

    def plot_saxs_2D(self):
        kwargs = {
            'plot_type': self.cb_saxs2D_type.currentText(),
            'cmap': self.cb_saxs2D_cmap.currentText()}
        self.dl.plot_saxs_2D(pg_hdl=self.pg_saxs, **kwargs)

    def plot_saxs_1D(self):
        kwargs = {
            'plot_type': ('log', 'linear')[self.cb_saxs_type.currentIndex()],
            'plot_offset': self.sb_saxs_offset.value(),
            'plot_norm': self.cb_saxs_norm.currentIndex()}
        self.dl.plot_saxs_1D(self.mp_saxs, **kwargs)

    def prepare_g2(self, max_q=0.0092, max_tel=0.31, num_col=4):
        res, _, _ = self.dl.get_g2_data()
        ql_dyn_list = res['ql_dyn'].ravel()
        ql_dyn_list = list(set(ql_dyn_list))
        ql_dyn_list.sort()

        self.g2_cache['ql_dyn'] = ql_dyn_list
        # get the index for the default max q value
        ql_idx = np.argmin(np.abs(max_q - np.array(ql_dyn_list)))

        ql_dyn_list = ['%.4f' % (x + 1E-4) for x in ql_dyn_list]
        prev_ql_idx = self.cb_q_max.currentIndex()
        self.cb_q_max.clear()
        self.cb_q_max.addItems(ql_dyn_list)
        if prev_ql_idx != -1:
            self.cb_q_max.setCurrentIndex(prev_ql_idx)
        else:
            self.cb_q_max.setCurrentIndex(ql_idx)

        t_el_list = res['t_el'].ravel()
        t_el_list = list(set(t_el_list))
        t_el_list.sort()
        self.g2_cache['t_el'] = t_el_list
        # get the index for the default max t_el value
        t_el_idx = np.argmin(np.abs(np.log(np.array(t_el_list) / max_tel)))

        t_el_list = ['%.2e' % (x * 1.01) for x in t_el_list]
        # only list 20 points because the list can be very long
        self.cb_tel_max.setCurrentIndex(t_el_idx - (len(t_el_list) - 20))
        # t_el_idx = t_el_idx - (len(t_el_list) - 20)

        prev_tel_idx = self.cb_tel_max.currentIndex()
        self.cb_tel_max.clear()
        self.cb_tel_max.addItems(t_el_list[-20:])

        self.mf2.clear()

        return res

    def plot_g2(self, max_points=3):
        if max_points in [False, None]:
            max_points = 3
        num_points = min(len(self.dl.target_list), max_points)
        if num_points == 0:
            return

        # read user defined values
        max_q = float(self.cb_q_max.currentText())
        max_tel = float(self.cb_tel_max.currentText())
        offset = self.sb_offset.value()
        num_col = 4

        # add 1 to convert index to count
        # num_fig = int(self.cb_q_max.currentIndex()) + 1
        num_fig = np.sum(np.array(self.g2_cache['ql_dyn']) <= max_q)

        # adjust canvas size according to number of images
        num_row = (num_fig + num_col - 1) // num_col
        if self.mf2.axes is None or \
                self.mf2.axes.shape != (num_row, num_col) or \
                self.dl.hash(max_points) != self.dl.g2_cache['hash_val']:
            print('create new fig')
            canvas_size = max(600, 200 * num_row)
            self.mf2.setMinimumSize(QtCore.QSize(0, canvas_size))
            self.mf2.fig.clear()
            self.mf2.subplots(num_row, num_col)
            self.mf2.obj = None
            self.dl.create_template_g2(self.mf2, self.g2_cache['ql_dyn'],
                                       num_points, num_fig=num_fig)

            self.mf2.draw()
        bounds = self.check_number()
        err_msg = self.dl.plot_g2(handler=self.mf2, max_q=max_q, max_tel=max_tel,
                                  offset=offset, bounds=bounds)
        self.err_msg.clear()
        self.err_msg.insertPlainText('\n'.join(err_msg))


    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # self.centralWidget.file_panel.work_dir.setValue(f)
        f = './data/files2.txt'
        self.work_dir.setText(f)
        self.dl = DataLoader(f)
        self.update_box(self.dl.source_list, mode='source')

        # for debug
        self.list_view_source.selectAll()
        self.add_target()
        self.list_view_source.clearSelection()

    def update_box(self, file_list, mode='source'):
        if mode == 'source':
            self.list_view_source.clear()
            self.list_view_source.addItems(file_list)
            self.box_source.setTitle('Source: %5d' % len(file_list))
        elif mode == 'target':
            self.list_view_target.clear()
            self.list_view_target.addItems(file_list)
            self.box_target.setTitle('Target: %5d' % len(file_list))
        return

    def add_target(self):
        target = []
        prev_hash = self.dl.hash(-1)
        for x in self.list_view_source.selectedIndexes():
            target.append(x.data())

        self.dl.add_target(target)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        if prev_hash != curr_hash:
            self.btn_load_data.setEnabled(True)

    def remove_target(self):
        prev_hash = self.dl.hash(-1)
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())

        self.dl.remove_target(rmv_list)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        if prev_hash != curr_hash:
            if len(self.dl.target_list) >= 1:
                self.btn_load_data.setEnabled(True)

    def trie_search(self):
        val = self.filter_str.text()
        if len(val) == 0:
            self.update_box(self.dl.source_list, mode='source')
            return
        num, self.cache = self.dl.search(val)
        self.update_box(self.cache, mode='source')
        self.list_view_source.selectAll()

    def check_number(self, default_val=(1e-6, 1e-2, 0.01, 0.20, 0.95, 1.05)):
        keys = (self.tau_min, self.tau_max,
                self.bkg_min, self.bkg_max,
                self.cts_min, self.cts_max)
        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            try:
                val = float(key.text())
            except:
                key.setText(str(default_val[n]))
                return
            else:
                vals[n] = val

        def swap_min_max(id1, id2, fun=str):
            if vals[id1] > vals[id2]:
                keys[id1].setText(fun(vals[id2]))
                keys[id2].setText(fun(vals[id1]))
                vals[id1], vals[id2] = vals[id2], vals[id1]

        swap_min_max(0, 1, lambda x: '%.2e' % x)
        swap_min_max(2, 3)
        swap_min_max(4, 5)
        vals = np.array(vals).reshape(len(keys) // 2, 2)
        return (tuple(vals[:, 0]), tuple(vals[:, 1]))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()