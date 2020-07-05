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
from data_loader import DataLoader
from file_locator import FileLocator
import numpy as np
import time
# from xpcs_ui import

# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure
#
#
# class MplCanvas(FigureCanvasQTAgg):
#
#     def __init__(self, parent=None, width=5.1, height=3.2, dpi=100):
#         fig = Figure(figsize=(width, height), dpi=dpi)
#         self.axes = fig.add_subplot(111)
#         super(MplCanvas, self).__init__(fig)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        self.show()
        self.dl = None
        self.fl = None
        self.cache = None
        self.load_path()
        self.g2_cache = {}

    def load_data(self):
        if (len(self.fl.target_list)) == 0:
            return
        self.dl = DataLoader(prefix=self.fl.cwd,
                             file_list=self.fl.target_list)

        self.mf1.subplots(2, 1)
        self.mf1.draw()
        self.prepare_g2()
        # self.plot_g2()
        # for n in range(data.shape[0]):
        #     self.mf1.axes[1].plot(res['Int_t_statistics'][n, :, 0], '-o', lw=1, alpha=0.5)
        # self.mf1.axes[1].imshow((res['Int_t'][:, :, 0]).T, aspect='auto')

    def prepare_g2(self, max_q=0.015, max_tel=0.31, num_col=4):
        res, _, _ = self.dl.get_g2_data()
        ql_dyn_list = res['ql_dyn'].ravel()
        ql_dyn_list = list(set(ql_dyn_list))
        ql_dyn_list.sort()

        self.g2_cache['ql_dyn'] = ql_dyn_list
        # get the index for the default max q value
        ql_idx = np.argmin(np.abs(max_q - np.array(ql_dyn_list)))

        ql_dyn_list = ['%.4f' % (x + 1E-4) for x in ql_dyn_list]
        self.cb_q_max.clear()
        self.cb_q_max.addItems(ql_dyn_list)
        self.cb_q_max.setCurrentIndex(ql_idx)

        t_el_list = res['t_el'].ravel()
        t_el_list = list(set(t_el_list))
        t_el_list.sort()
        self.g2_cache['t_el'] = t_el_list
        # get the index for the default max t_el value
        t_el_idx = np.argmin(np.abs(np.log(np.array(t_el_list) / max_tel)))

        t_el_list = ['%.2e' % (x * 1.01) for x in t_el_list]
        # only list 20 points because the list can be very long
        self.cb_tel_max.clear()
        self.cb_tel_max.addItems(t_el_list[-20:])
        self.cb_tel_max.setCurrentIndex(t_el_idx - (len(t_el_list) - 20))

        self.mf2.clear()

        return res

    def plot_g2(self, max_points=3):
        if max_points in [False, None]:
            max_points = 3

        num_col = 4
        # add 1 to convert index to count
        num_fig = int(self.cb_q_max.currentIndex()) + 1
        num_points = min(len(self.fl.target_list), max_points)

        # read user defined values
        max_q = float(self.cb_q_max.currentText())
        max_tel = float(self.cb_tel_max.currentText())
        offset = self.sb_offset.value()

        # read ql_dyn

        # adjust canvas size according to number of images
        num_row = (num_fig + num_col - 1) // num_col
        if self.mf2.axes is None or self.mf2.axes.shape != (num_row, num_col):
            canvas_size = max(600, 200 * num_row)
            self.mf2.setMinimumSize(QtCore.QSize(0, canvas_size))
            self.mf2.fig.clear()
            self.mf2.subplots(num_row, num_col)
            self.mf2.obj = None
            self.dl.create_template_g2(self.mf2, self.g2_cache['ql_dyn'],
                                       num_points, num_fig=num_fig)

        self.mf2.draw()
        bounds = self.check_number()
        self.dl.plot_g2(handler=self.mf2, max_q=max_q, max_tel=max_tel,
                        offset=offset, bounds=bounds)


    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # self.centralWidget.file_panel.work_dir.setValue(f)
        f = './data/files2.txt'
        self.work_dir.setText(f)
        self.fl = FileLocator(f)
        self.update_box(self.fl.source_list, mode='source')

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
        for x in self.list_view_source.selectedIndexes():
            target.append(x.data())

        self.fl.add_target(target)
        self.update_box(self.fl.target_list, mode='target')

    def remove_target(self):
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())
        self.fl.remove_target(rmv_list)
        self.update_box(self.fl.target_list, mode='target')

    def trie_search(self):
        val = self.filter_str.text()
        if len(val) == 0:
            self.update_box(self.fl.source_list, mode='source')
            return
        num, self.cache = self.fl.search(val)
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