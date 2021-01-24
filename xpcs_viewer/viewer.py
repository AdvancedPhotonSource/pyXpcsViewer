from PyQt5 import QtCore
from .viewer_ui import Ui_mainWindow as Ui
from .viewer_kernel import ViewerKernel
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QThread, QObject, Qt

# from pyqtgraph.Qt import QtWidgets
# from pyqtgraph import QtCore, QtGui

import os
import numpy as np
import sys
import json

# log file
import logging

format = logging.Formatter('%(asctime)s %(message)s')
home_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
if not os.path.isdir(home_dir):
    os.mkdir(home_dir)
log_filename = os.path.join(home_dir, 'viewer.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-24s: %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename, mode='a'),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger(__name__)


def exception_hook(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception",
                 exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = exception_hook

# sys.stdout = LoggerWriter(logger.debug)
# sys.stderr = LoggerWriter(logger.warning)


class ViewerKernel2(ViewerKernel, QObject):
    def __init__(self, path, statusbar=None):
        ViewerKernel.__init__(self, path, statusbar)
        QThread.__init__(self)


class XpcsViewer(QtWidgets.QMainWindow, Ui):
    def __init__(self, path=None):
        super(XpcsViewer, self).__init__()
        self.setupUi(self)
        self.tab_id = 0

        self.tabWidget.setCurrentIndex(self.tab_id)
        self.tab_dict = {
            0: "saxs_2d",
            1: "saxs_1d",
            2: "stability",
            3: "intensity_t",
            4: "average",
            5: "g2",
            6: "diffusion",
            7: "twotime",
            8: "exp_setup",
            9: "log",
            10: "None"
        }

        # finite states
        self.data_state = 0
        self.plot_state = np.zeros(len(self.tab_dict), dtype=np.int)
        self.thread_pool = QtCore.QThreadPool()
        logger.info('Maximal threads: %d', self.thread_pool.maxThreadCount())

        self.vk = None
        # list widget models
        self.source_model = None
        self.target_model = None
        self.timer = QtCore.QTimer()

        if path is not None:
            self.start_wd = path
            self.load_path(path)
        else:
            # use home directory
            self.start_wd = os.path.expanduser('~')
        self.start_wd = os.path.abspath(self.start_wd)
        logger.info('Start up directory is [{}]'.format(self.start_wd))

        # additional signal-slot settings
        self.mp_2t_map.hdl.mpl_connect('button_press_event',
                                       self.update_twotime_qindex)

        self.tabWidget.currentChanged.connect(self.init_tab)
        # self.list_view_target.indexesMoved.connect(self.reorder_target)
        self.list_view_target.clicked.connect(self.update_selection)

        self.cb_twotime_type.currentIndexChanged.connect(self.init_twotime)
        self.cb_twotime_saxs_cmap.currentIndexChanged.connect(
            self.init_twotime)
        self.cb_twotime_qmap_cmap.currentIndexChanged.connect(
            self.init_twotime)
        self.twotime_autorotate.stateChanged.connect(self.init_twotime)
        self.twotime_autocrop.stateChanged.connect(self.init_twotime)
        self.avg_job_pop.clicked.connect(self.remove_avg_job)
        self.btn_submit_job.clicked.connect(self.submit_job)
        self.btn_start_avg_job.clicked.connect(self.start_avg_job)
        self.btn_set_average_save_path.clicked.connect(
            self.set_average_save_path)
        self.btn_set_average_save_name.clicked.connect(
            self.set_average_save_name)
        self.btn_avg_kill.clicked.connect(self.avg_kill_job)
        self.btn_avg_jobinfo.clicked.connect(self.show_avg_jobinfo)
        # self.avg_job_table.selectionModel().selectionChanged.connect(
        #     self.update_avg_info)
        self.avg_job_table.clicked.connect(self.update_avg_info)
        self.hdf_key_filter.textChanged.connect(self.show_hdf_info)
        self.load_default_setting()
        self.show()
    
    def load_default_setting(self):
        home_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
        if not os.path.isdir(home_dir):
            os.mkdir(home_dir)

        key_fname = os.path.join(home_dir, 'default_setting.json')
        # copy the default values
        if not os.path.isfile(key_fname):
            from .default_setting import setting
            with open(key_fname, 'w') as f:
                json.dump(setting, f, indent=4)

        # the display size might too big for some laptops
        with open(key_fname, 'r') as f:
            config = json.load(f)
            if "window_size_h" in config:
                new_size = (config["window_size_w"], config["window_size_h"])
                logger.info('set mainwindow to size %s', new_size)
                self.resize(*new_size)
        return

    def get_selected_rows(self):
        selected_index = self.list_view_target.selectedIndexes()
        selected_row = [x.row() for x in selected_index]
        # the selected index is ordered;
        selected_row.sort()
        return selected_row

    def update_selection(self):
        if self.data_state < 3:
            self.init_tab()

        rows = self.get_selected_rows()
        idx = self.tabWidget.currentIndex()
        tab_name = self.tab_dict[idx]

        if tab_name == 'saxs_2d':
            if rows == [] or len(self.vk.target) <= 1:
                return
            self.pg_saxs.setCurrentIndex(rows[0])
        elif tab_name == 'saxs_1d':
            self.plot_saxs_1D()
        elif tab_name == 'intensity_t':
            self.plot_intt()

    def init_tab(self):
        if self.data_state < 2:
            return
        new_tab_id = self.tabWidget.currentIndex()
        tab_name = self.tab_dict[new_tab_id]
        self.statusbar.clearMessage()

        # the plots on this tab is already done;
        if self.plot_state[new_tab_id] > 0:
            return

        logger.info('switch to tab %d: %s', new_tab_id, tab_name)
        self.statusbar.showMessage('visualize {}'.format(tab_name), 500)

        if tab_name == 'saxs_2d':
            self.plot_saxs_2D()
        elif tab_name == 'saxs_1d':
            self.plot_saxs_1D()
        elif tab_name == 'stability':
            self.update_stab_list()
            self.plot_stability_iq()
        elif tab_name == 'intensity_t':
            self.plot_intt()
        elif tab_name == 'twotime':
            self.init_twotime()
        elif tab_name == 'exp_setup':
            self.update_hdf_list()
        elif tab_name == 'stability':
            self.update_stab_list()
        elif tab_name == 'average':
            self.update_average_box()
        elif tab_name == 'g2':
            self.set_g2_range()
            # self.plot_g2(10)

        self.plot_state[new_tab_id] = 1

    def load_data(self):
        tab_id = self.tabWidget.currentIndex()
        tab_name = self.tab_dict[tab_id]
        if tab_name == 'average':
            self.statusbar.showMessage(
                'The average tool reads data from disk directly. skip')
            return
        if self.data_state <= 1:
            self.statusbar.showMessage('Work directory or target not ready.',
                                       1000)
            return
        elif self.data_state == 3:
            self.statusbar.showMessage('Files are preloaded already. skip',
                                       1000)
            return

        self.statusbar.showMessage('Loading hdf files into RAM ...')
        logger.info('loading hdf files into RAM')

        # the state must be 2
        self.vk.load(progress_bar=self.progress_bar)

        self.data_state = 3
        self.plot_state[:] = 0
        self.statusbar.showMessage('Files loaded.', 1000)

        self.init_tab()

    def update_hdf_list(self):
        self.hdf_list.clear()
        self.hdf_list.addItems(self.vk.target)

    def update_stab_list(self):
        self.cb_stab.clear()
        self.cb_stab.addItems(self.vk.target)

    def show_hdf_info(self):
        fname = self.hdf_list.currentText()
        msg = self.vk.get_hdf_info(fname)

        filter_str = self.hdf_key_filter.text()
        fstr = filter_str.split()
        if len(fstr) > 0:
            msg2 = []
            for x in fstr:
                n = 0
                while True:
                    if x in msg[n]:
                        msg2 += [msg[n], msg[n + 1]]
                        n += 2
                    else:
                        n += 1
                    # subtract 1 so don't need to worry access n + 1
                    if n >= len(msg) - 1:
                        break

            msg = msg2
        self.hdf_info.clear()
        self.hdf_info.setText('\n'.join(msg))

    def plot_saxs_2D(self):
        if not self.check_status(show_msg=False):
            return

        kwargs = {
            'plot_type': self.cb_saxs2D_type.currentText(),
            'cmap': self.cb_saxs2D_cmap.currentText(),
            'autorotate': self.saxs2d_autorotate.isChecked(),
            'display': self.saxs2d_display,
        }
        self.vk.plot_saxs_2d(pg_hdl=self.pg_saxs, **kwargs)

    def plot_saxs_1D(self):
        if not self.check_status():
            return

        kwargs = {
            'plot_type': self.cb_saxs_type.currentIndex(),
            'plot_offset': self.sb_saxs_offset.value(),
            'plot_norm': self.cb_saxs_norm.currentIndex(),
            'rows': self.get_selected_rows()
        }
        self.vk.plot_saxs_1d(self.mp_saxs.hdl, **kwargs)

    def init_twotime(self):
        if not self.check_status():
            return
        rows = self.get_selected_rows()
        file_index = 0
        if len(rows) > 0:
            file_index = rows[0]

        # Multitau tau analysis also has dqmap
        if self.vk.type != "Twotime":
            self.statusbar.showMessage("The target files must be twotime " +
                                       "analysis.")
        res = self.vk.setup_twotime(file_index=file_index)
        self.cb_twotime_group.clear()
        self.cb_twotime_group.addItems(res)

        kwargs = {
            # if nothing is selected, currentRow = -1; then plot 0th row;
            'scale': self.cb_twotime_type.currentText(),
            'saxs_cmap': self.cb_twotime_saxs_cmap.currentText(),
            'qmap_cmap': self.cb_twotime_qmap_cmap.currentText(),
            'auto_rotate': self.twotime_autorotate.isChecked(),
            'auto_crop': self.twotime_autocrop.isChecked(),
        }

        self.vk.plot_twotime_map(self.mp_2t_map.hdl, **kwargs)
        self.plot_twotime()

    def update_twotime_qindex(self, event):
        """
        connected to mp_2t.hdl which fetches the mouse click event and plot
        the selected qphi index on the qmap, also plot the twotime for the
        qphi index.
        :param event: mouse click event
        :return: None
        """
        if self.data_state < 3:
            self.statusbar.showMessage('Twotime data not ready', 1000)
            return

        if event.button == Qt.LeftButton:
            self.statusbar.showMessage('Use right click to select points',
                                       1000)
            return

        ix, iy = event.xdata, event.ydata
        # filter events that's outside the boundaries
        if ix is None or iy is None:
            logger.warn('the click event is outside the canvas')
            return
        qindex = self.vk.get_twotime_qindex(ix, iy, self.mp_2t_map.hdl)

        # qindex is linked to plot_twotime(); avoid double shot
        if qindex != self.twotime_q_index.value():
            self.twotime_q_index.setValue(qindex)
            self.plot_twotime()

    def plot_twotime(self):
        """
        plot_twotime reads the parameters from the gui and plot the
        corresponding twotime;
        :return:  None
        """
        if not self.check_status():
            return
        if self.vk.type != "Twotime":
            self.statusbar.showMessage("The target files must be twotime " +
                                       "analysis.")
            return

        rows = self.get_selected_rows()
        file_index = 0
        if len(rows) > 0:
            file_index = rows[0]

        kwargs = {
            # if nothing is selected, currentRow = -1; then plot 0th row;
            # the model base listwidget doesn't have currentRow method
            # 'current_file_index': max(0, self.list_view_target.currentRow()),
            'current_file_index': file_index,
            'plot_index': self.twotime_q_index.value(),
            'cmap': self.cb_twotime_cmap.currentText()
        }
        if kwargs['plot_index'] == 0:
            self.statusbar.showMessage("No twotime data for plot_indx = 0.")
            return
        ret = self.vk.plot_twotime(self.mp_2t.hdl, **kwargs)
        # if ret is not None:
        #     self.vk.get_twotime_qindex(ret[1], ret[0], self.mp_2t_map.hdl)

    def edit_label(self):
        if not self.check_status():
            return
        rows = self.get_selected_rows()
        self.tree = self.vk.get_pg_tree(rows)
        self.tree.show()

    def plot_stability_iq(self):
        if not self.check_status():
            return
        kwargs = {
            'plot_type': self.cb_stab_type.currentIndex(),
            'plot_offset': self.sb_stab_offset.value(),
            'plot_norm': self.cb_stab_norm.currentIndex()
        }
        plot_id = self.cb_stab.currentIndex()
        if plot_id < 0:
            return
        self.vk.plot_stability(self.mp_stab.hdl, plot_id, **kwargs)

    def plot_intt(self):
        if not self.check_status():
            return
        kwargs = {
            'max_points': self.sb_intt_max.value(),
            'sampling': max(1, self.sb_intt_sampling.value()),
            'window': self.sb_window.value(),
            'rows': self.get_selected_rows(),
            'xlabel': self.intt_xlabel.currentText()
        }
        self.vk.plot_intt(self.pg_intt, **kwargs)

    def plot_tauq(self):
        if not self.check_status() or self.vk.type != 'Multitau':
            return

        kwargs = {
            'max_q': self.sb_tauq_qmax.value(),
            'offset': self.sb_tauq_offset.value()
        }
        msg = self.vk.plot_tauq(hdl=self.mp_tauq, **kwargs)
        self.tauq_msg.clear()
        self.tauq_msg.setText('\n'.join(msg))

    def remove_avg_job(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0:
            return
        self.vk.remove_job(index)

    def set_average_save_path(self):
        save_path = QFileDialog.getExistingDirectory(self, 'Open directory')
        self.avg_save_path.clear()
        self.avg_save_path.setText(save_path)
        return

    def set_average_save_name(self):
        save_name = QFileDialog.getSaveFileName(self, 'Save as')
        self.avg_save_name.clear()
        self.avg_save_name.setText(os.path.basename(save_name[0]))
        return

    def update_average_box(self):

        if len(self.vk.target) > 0:
            save_path = self.avg_save_path.text()
            if save_path == '':
                self.avg_save_path.setText(self.work_dir.text())
            else:
                logger.info('use the previous save path')

            save_name = self.avg_save_name.text()
            save_name = 'Avg' + self.vk.target[0]
            self.avg_save_name.setText(save_name)

    def submit_job(self):
        # if not self.check_status(): #  or self.vk.type != 'Multitau':
        #     self.statusbar.showMessage('average files not ready')
        #     return
        if len(self.vk.target) < 2:
            self.statusbar.showMessage(
                'select at least 2 files for averaging')
            return

        self.thread_pool.setMaxThreadCount(self.max_thread_count.value())

        save_path = self.avg_save_path.text()
        save_name = self.avg_save_name.text()

        if not os.path.isdir(save_path):
            logger.info('the average save_path doesn\'t exist; creating one')
            try:
                os.mkdir(save_path)
            except:
                logger.info('cannot create the folder: %s', save_path)
                return

        avg_fields = []
        if self.bx_avg_G2IPIF.isChecked():
            avg_fields.extend(['G2', 'IP', 'IF'])
        if self.bx_avg_g2g2err.isChecked():
            avg_fields.extend(['g2', 'g2_err'])
        if self.bx_avg_saxs.isChecked():
            avg_fields.extend(['saxs_1d', 'saxs_2d'])

        if len(avg_fields) == 0:
            self.statusbar.showMessage('No average field is selected. quit')
            return

        kwargs = {
            'save_path': os.path.join(save_path, save_name),
            'chunk_size': int(self.cb_avg_chunk_size.currentText()),
            'avg_blmin': self.avg_blmin.value(),
            'avg_blmax': self.avg_blmax.value(),
            'avg_qindex': self.avg_qindex.value(),
            'avg_window': self.avg_window.value(),
            'fields': avg_fields
        }

        if kwargs['avg_blmax'] <= kwargs['avg_blmin']:
            self.statusbar.showMessage('check avg min/max values.')
            return

        self.vk.submit_job(**kwargs)
        # the target_average has been reset
        self.update_box(self.vk.target, mode='target')
        self.data_state = 1
        return

    def update_avg_info(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            self.statusbar.showMessage('select a job to start')
            return

        self.timer.stop()
        self.timer.setInterval(1000)

        try:
            self.timer.timeout.disconnect()
            logger.info('disconnect previous slot')
        except:
            pass

        worker = self.vk.avg_worker[index]
        worker.initialize_plot(self.mp_avg_g2)

        self.timer.timeout.connect(lambda x=index: self.vk.update_avg_info(x))
        self.timer.start()

    def start_avg_job(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            self.statusbar.showMessage('select a job to start')
            return
        worker = self.vk.avg_worker[index]
        if worker.status == 'finished':
            self.statusbar.showMessage('this job has finished', 1000)
            return
        elif worker.status == 'running':
            self.statusbar.showMessage('this job is running.', 1000)
            return

        # worker.signals.progress.connect(worker.update_plot)
        # worker.signals.progress.connect(self.vk.update_avg_worker)
        worker.signals.values.connect(self.vk.update_avg_values)
        self.thread_pool.start(worker)
        self.vk.avg_worker_active[worker.jid] = None

    def avg_kill_job(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            self.statusbar.showMessage('select a job to kill')
            return
        worker = self.vk.avg_worker[index]
        if worker.status != 'running':
            self.statusbar.showMessage('the selected job isn\'s running')
            return
        worker.kill()

    def show_avg_jobinfo(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            logger.info('select a job to show it\'s settting')
            return
        worker = self.vk.avg_worker[index]
        self.tree = worker.get_pg_tree()
        self.tree.show()

    def set_g2_range(self, max_points=3):
        if not self.check_status() or self.vk.type != 'Multitau':
            return

        flag, tel, _, _, _ = self.vk.get_g2_data(max_points)
        if not flag:
            self.statusbar.showMessage('g2 data is not consistent. abort')
        t_min = np.min(tel)
        t_max = np.max(tel)

        def to_e(x):
            return '%.2e' % x

        self.tau_min.setText(to_e(t_min / 5))
        self.tau_max.setText(to_e(t_max * 5))
        self.g2_tmin.setText(to_e(t_min / 1.1))
        self.g2_tmax.setText(to_e(t_max * 1.1))

    def plot_g2(self, max_points=3):
        if not self.check_status() or self.vk.type != 'Multitau':
            return

        p = self.check_g2_number()
        kwargs = {
            'num_col': self.sb_g2_column.value(),
            'offset': self.sb_g2_offset.value(),
            'show_fit': self.g2_show_fit.isChecked(),
            'show_label': self.g2_show_label.isChecked(),
            'plot_type': self.g2_plot_type.currentText(),
            'q_range': (p[0], p[1]),
            't_range': (p[2], p[3]),
            'y_range': (p[4], p[5]),
        }

        bounds = self.check_number()
        self.pushButton_4.setDisabled(True)
        self.pushButton_4.setText('plotting')
        try:
            self.vk.plot_g2(handler=self.mp_g2, bounds=bounds, **kwargs)
        except Exception:
            pass
        self.pushButton_4.setEnabled(True)
        self.pushButton_4.setText('plot')
        # self.g2_err_msg.clear()
        # if err_msg is None:
        #     self.g2_err_msg.insertPlainText('None')
        # else:
        #     self.g2_err_msg.insertPlainText('\n'.join(err_msg))

    def reload_source(self):
        self.vk.build()
        self.update_box(self.vk.source, mode='source')

    def load_path(self, path=None, debug=False):
        if path in [None, False]:
            # DontUseNativeDialog is used so files are shown along with dirs;
            f = QFileDialog.getExistingDirectory(
                self, 'Open directory', self.start_wd,
                QFileDialog.DontUseNativeDialog)
        else:
            f = path

        if not os.path.isdir(f):
            self.statusbar.showMessage('{} is not a folder.'.format(f))
            f = self.start_wd

        curr_work_dir = self.work_dir.text()

        # either choose a new work_dir or initialize from state=0
        # if f == curr_work_dir; then the state is kept the same;
        if f != curr_work_dir or self.data_state == 0:
            self.data_state = 1
            self.plot_state[:] = 0

        self.work_dir.setText(f)
        self.vk = ViewerKernel(f, self.statusbar)
        self.avg_job_table.setModel(self.vk.avg_worker)
        # self.thread = QThread()
        # self.vk.moveToThread(self.thread)
        self.source_model = self.vk.source
        self.update_box(self.vk.source, mode='source')

    def update_box(self, file_list, mode='source'):
        if file_list is None:
            return
        if mode == 'source':
            self.list_view_source.setModel(file_list)
            self.box_source.setTitle('Source: %5d' % len(file_list))
        elif mode == 'target':
            self.list_view_target.setModel(file_list)
            self.box_target.setTitle('Target: %5d \t [Type: %s] ' %
                                     (len(file_list), self.vk.type))
            # on macos, the target box doesn't seem to update; force it
            file_list.layoutChanged.emit()
            self.box_target.repaint()
            self.list_view_target.repaint()
        self.statusbar.showMessage('Target file list updated.', 1000)
        return

    def add_target(self):
        if self.data_state == 0:
            msg = 'path has not been specified.'
            self.statusbar.showMessage(msg)
            return

        target = []
        for x in self.list_view_source.selectedIndexes():
            target.append(x.data())

        # only max_display items are displayed; if all are selected; then the
        # ones not displayed are also used
        if len(target) == self.source_model.max_display:
            logger.info('all items are selected in target')
            target = self.source_model

        if target == []:
            return

        self.progress_bar.setValue(0)

        curr_target = tuple(self.vk.target)
        flag_single = self.vk.add_target(target)
        self.list_view_source.clearSelection()

        # no change in self.data_state
        if curr_target == tuple(self.vk.target):
            self.progress_bar.setValue(100)
            return

        # the target list has changed;
        self.update_box(self.vk.target, mode='target')

        if self.data_state in [1, 2, 3]:
            self.data_state = 2
            self.plot_state[:] = 0

        if not flag_single:
            msg = 'more than one xpcs analysis type detected'
            self.statusbar.showMessage(msg)

        tab_id = self.tabWidget.currentIndex()
        if self.tab_dict[tab_id] == 'average':
            self.update_average_box()
        elif self.box_auto_update.isChecked():
            # avoid pressing enter when auto-load is enabled and lots of
            # files are added; it'll take long time to process;
            if len(self.vk.target) > 128:
                self.statusbar.showMessage(
                    'More than 128 files selected. Abort auto loading.', 1000)
            else:
                self.load_data()

    def reorder_target(self):
        target = []
        self.list_view_target.selectAll()
        for x in self.list_view_target.selectedIndexes():
            target.append(x.data())
        self.list_view_target.clearSelection()

        if tuple(target) != tuple(self.vk.target):
            self.vk.clear_target()
            self.vk.add_target(target)
            self.update_box(self.vk.target, mode='target')
        else:
            print('no reorder')

    def remove_target(self):
        if self.data_state in [0, 1]:
            self.statusbar.showMessage('Target is not ready.', 1000)
            return

        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())

        self.progress_bar.setValue(0)
        self.vk.remove_target(rmv_list)

        # if all files are removed; then go to state 1
        if self.vk.target in [[], None] or len(self.vk.target) == 0:
            self.reset_gui()
        else:
            self.data_state = 2
        self.plot_state[:] = 0

        self.update_box(self.vk.target, mode='target')
        if self.box_auto_update.isChecked():
            self.load_data()

    def reset_gui(self):
        self.data_state = 1
        self.plot_state[:] = 0
        self.vk.reset_kernel()
        for x in [self.pg_saxs, self.pg_intt, self.mp_tauq, self.mp_2t,
                  self.mp_2t_map, self.mp_g2, self.mp_saxs, self.mp_stab]:
            x.clear()

    def trie_search(self):
        min_length = 2
        val = self.filter_str.text()
        if len(val) == 0:
            self.source_model = self.vk.source
            self.update_box(self.vk.source, mode='source')
            return
        # avoid searching when the filter lister is too short
        if len(val) < min_length:
            self.statusbar.showMessage(
                'Please enter at least %d characters' % min_length
            )
            return

        filter_type = ['prefix', 'substr'][self.filter_type.currentIndex()]
        self.vk.search(val, filter_type)
        self.source_model = self.vk.source_search
        self.update_box(self.source_model, mode='source')
        self.list_view_source.selectAll()

    def check_g2_number(self, default_val=(0, 0.0092, 1E-8, 1, 0.95, 1.35)):
        keys = (self.g2_qmin, self.g2_qmax, self.g2_tmin, self.g2_tmax,
                self.g2_ymin, self.g2_ymax)
        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            try:
                val = float(key.text())
            except Exception:
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
        keys = (self.tau_min, self.tau_max, self.bkg_min, self.bkg_max,
                self.cts_min, self.cts_max)
        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            try:
                val = float(key.text())
            except Exception:
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

    def check_status(self, show_msg=True, min_state=2):
        flag = False
        if self.data_state == 0:
            msg = "The working directory hasn't be specified."
        elif self.data_state == 1:
            msg = "No target files have been selected."
        elif self.data_state == 2:
            msg = "Target files haven't been loaded."
        else:
            msg = "%d file(s) is selected" % len(self.vk.target)
            flag = True

        if show_msg and not flag:
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage(msg)
            logger.error(msg)

        self.statusbar.showMessage(msg, 1000)

        return flag


def setup_windows_icon():
    # reference: https://stackoverflow.com/questions/1551605
    import ctypes
    from ctypes import wintypes

    lpBuffer = wintypes.LPWSTR()
    AppUserModelID = ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID
    AppUserModelID(ctypes.cast(ctypes.byref(lpBuffer), wintypes.LPWSTR))
    appid = lpBuffer.value
    ctypes.windll.kernel32.LocalFree(lpBuffer)
    if appid is None:
        appid = 'aps.xpcs_viewer.viewer.0.20'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)


def run():
    if os.name == 'nt':
        setup_windows_icon()
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
        # use arg[1] as the starting directory
        window = XpcsViewer(sys.argv[1])
    elif len(sys.argv) > 2:
        # deal with white space cases
        path = '_'.join(sys.argv[1:])
        window = XpcsViewer(path)
    else:
        window = XpcsViewer()
    app.exec_()


if __name__ == '__main__':
    run()
