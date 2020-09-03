from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
import sys
import os
from data_loader import DataLoader
import numpy as np

# import time
import logging

logging_format = '%(asctime)s %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


class Ui(QtWidgets.QMainWindow):
    def __init__(self, path=None):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        # self.list_view_target.dragMoveEvent().connect
        self.show()
        self.dl = None
        self.cache = None
        self.load_path(path)
        self.g2_cache = {}

    def load_data(self):
        if self.dl.target_list is None or (len(self.dl.target_list)) == 0:
            return
        self.dl.cache_data(progress_bar=self.progress_bar)

        self.reorder_target()
        # self.plot_g2()
        # self.plot_saxs_2D()
        # self.plot_saxs_1D()
        self.update_hdf_list()
        self.update_stab_list()
        # self.plot_g2()
        # self.plot_stability_iq()
        # self.btn_load_data.setEnabled(False)

    def update_hdf_list(self):
        self.hdf_list.clear()
        self.hdf_list.addItems(self.dl.target_list)

    def update_stab_list(self):
        self.cb_stab.clear()
        self.cb_stab.addItems(self.dl.target_list)

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
            'cmap': self.cb_saxs2D_cmap.currentText(),
            'autorotate': self.saxs2d_autorotate.isChecked()}
        self.dl.plot_saxs_2d(pg_hdl=self.pg_saxs, **kwargs)

    def plot_saxs_1D(self):
        kwargs = {
            'plot_type': self.cb_saxs_type.currentIndex(),
            'plot_offset': self.sb_saxs_offset.value(),
            'plot_norm': self.cb_saxs_norm.currentIndex()}
        self.dl.plot_saxs_1d(self.mp_saxs, **kwargs)

    def plot_stability_iq(self):
        kwargs = {
            'plot_type': self.cb_stab_type.currentIndex(),
            'plot_offset': self.sb_stab_offset.value(),
            'plot_norm': self.cb_stab_norm.currentIndex()}
        plot_id = self.cb_stab.currentIndex()
        if plot_id < 0:
            return
        self.dl.plot_stability(self.mp_stab, plot_id, **kwargs)

    def plot_intt(self):
        kwargs = {
            'max_points': self.sb_intt_max.value(),
            'sampling': self.sb_intt_sampling.value()
        }
        self.dl.plot_intt(self.pg_intt, **kwargs)

    def plot_tauq(self):
        kwargs = {
            'max_q': self.sb_tauq_qmax.value(),
            'offset': self.sb_tauq_offset.value()}
        msg = self.dl.plot_tauq(hdl=self.mp_tauq, **kwargs)
        self.tauq_msg.clear()
        self.tauq_msg.setText('\n'.join(msg))

    def update_average_box(self):
        if self.avg_use_source_path.isChecked():
            self.avg_save_path.clear()
            save_path = self.work_dir.text()
            self.avg_save_path.setText(self.work_dir.text())
        else:
            save_path = self.avg_save_path.text()
            while not os.path.isdir(save_path):
                save_path = QFileDialog.getExistingDirectory(self,
                                'Open directory', '../cluster_results',
                                 QFileDialog.ShowDirsOnly | QFileDialog.DontUseCustomDirectoryIcons)
            self.avg_save_path.setText(save_path)

        if len(self.dl.id_list) > 0:
            save_name = self.avg_save_name.text()
            if save_name == '':
                save_name = 'AVG_' + self.dl.target_list[0]
                # save_name = self.dl.target_list[0]
            self.avg_save_name.setText(save_name)
            full_path = os.path.join(save_path, save_name)
            if os.path.isfile(full_path):
                self.show_error('file exist. change save name')

    def plot_outlier_intt(self):
        kwargs = {
            'num_clusters': self.avg_intt_num_clusters.value(),
            'target': 'intt'
        }
        self.dl.average_plot_outlier(self.mp_avg_intt, self.mp_avg_g2,
                                     **kwargs)

    def plot_outlier_g2(self):
        kwargs = {
            'g2_cutoff': self.avg_g2_cutoff.value(),
            'target': 'g2'
        }
        self.dl.average_plot_outlier(self.mp_avg_intt, self.mp_avg_g2,
                                     **kwargs)

    def do_average(self):
        save_path = self.avg_save_path.text()
        save_name = self.avg_save_name.text()

        kwargs = {
            'save_path': os.path.join(save_path, save_name),
            'chunk_size': int(self.cb_avg_chunk_size.currentText())
        }
        # print(kwargs)
        self.dl.average(self.mp_avg_intt, self.mp_avg_g2, **kwargs)

    def plot_g2(self, max_points=3):
        p = self.check_g2_number()
        kwargs = {
            'num_col': self.sb_g2_column.value(),
            'offset': self.sb_g2_offset.value(),
            'show_fit': self.g2_show_fit.isChecked(),
            'show_label': self.g2_show_label.isChecked(),
            'q_range': (p[0], p[1]),
            't_range': (p[2], p[3]),
            'y_range': (p[4], p[5]),
        }

        bounds = self.check_number()
        err_msg = self.dl.plot_g2(handler=self.mp_g2, bounds=bounds, **kwargs)
        self.g2_err_msg.clear()
        if err_msg is None:
            self.g2_err_msg.insertPlainText('None')
        else:
            self.g2_err_msg.insertPlainText('\n'.join(err_msg))

    def reload_source(self):
        self.dl.build()
        self.update_box(self.dl.source_list, mode='source')

    def load_path(self, path=None, debug=False):
        if path in [None, False]:
            f = QFileDialog.getExistingDirectory(self, 'Open directory',
                                                 '../cluster_results',
                                                 QFileDialog.ShowDirsOnly | QFileDialog.DontUseCustomDirectoryIcons)
        else:
            f = path

        if not os.path.isdir(f):
            return

        self.work_dir.setText(f)
        self.dl = DataLoader(f)
        self.update_box(self.dl.source_list, mode='source')

        # for debug
        # self.list_view_source.selectAll()
        # self.add_target()

    def show_error(self, msg):
        print('call show erro')
        error_dialog = QtWidgets.QErrorMessage()
        error_dialog.showMessage('\n'.join(msg))

    def update_box(self, file_list, mode='source'):
        if file_list is None:
            return

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
        self.progress_bar.setValue(0)

        self.dl.add_target(target)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        # if prev_hash != curr_hash:
        #     self.btn_load_data.setEnabled(True)

        self.list_view_source.clearSelection()
        self.update_average_box()

    def reorder_target(self):
        target = []
        prev_hash = self.dl.hash(-1)
        self.list_view_target.selectAll()
        for x in self.list_view_target.selectedIndexes():
            target.append(x.data())
        self.list_view_target.clearSelection()

        self.dl.clear_target()
        self.dl.add_target(target)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        # if prev_hash != curr_hash:
        #     self.btn_load_data.setEnabled(True)

    def remove_target(self):
        prev_hash = self.dl.hash(-1)
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())

        self.progress_bar.setValue(0)
        self.dl.remove_target(rmv_list)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        # if prev_hash != curr_hash:
        #     if len(self.dl.target_list) >= 1:
        #         self.btn_load_data.setEnabled(True)

    def trie_search(self):
        val = self.filter_str.text()
        if len(val) == 0:
            self.update_box(self.dl.source_list, mode='source')
            return
        num, self.cache = self.dl.search(val)
        self.update_box(self.cache, mode='source')
        self.list_view_source.selectAll()

    def check_g2_number(self, default_val=(0, 0.0092, 1E-8, 1, 0.95, 1.35)):
        keys = (self.g2_qmin, self.g2_qmax,
                self.g2_tmin, self.g2_tmax,
                self.g2_ymin, self.g2_ymax)
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

        swap_min_max(0, 1)
        swap_min_max(2, 3, lambda x: '%.2e' % x)
        swap_min_max(4, 5)

        return vals

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
    if len(sys.argv) == 2:
        window = Ui(sys.argv[1])
    else:
        window = Ui()
    app.exec_()
