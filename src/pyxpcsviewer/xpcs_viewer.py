from PySide6 import QtCore, QtWidgets
from .viewer_ui import Ui_mainWindow as Ui
from .viewer_kernel import ViewerKernel
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter
import os
import numpy as np
import sys
import json
import shutil
import logging
from pyqtgraph.Qt import QtCore
import argparse
import traceback


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
}


def create_param_tree(data_dict):
         """Convert a dictionary into PyQtGraph's ParameterTree format."""
         params = []
         for key, value in data_dict.items():
             if isinstance(value, dict):  # If value is a nested dictionary
                 params.append({'name': key, 'type': 'group', 'children': create_param_tree(value)})
             elif isinstance(value, (int, float, np.number)):  # Numeric types
                 params.append({'name': key, 'type': 'float', 'value': float(value)})
             elif isinstance(value, str):  # String types
                 params.append({'name': key, 'type': 'str', 'value': value})
             elif isinstance(value, np.ndarray):  # Numpy arrays
                 params.append({'name': key, 'type': 'text', 'value': str(value.tolist())})
             else:  # Default fallback
                 params.append({'name': key, 'type': 'text', 'value': str(value)})
         return params


class XpcsViewer(QtWidgets.QMainWindow, Ui):
    def __init__(self, path=None, label_style=None):
        super(XpcsViewer, self).__init__()
        self.setupUi(self)
        self.tab_id = 0
        self.home_dir = home_dir
        self.label_style = label_style

        self.tabWidget.setCurrentIndex(self.tab_id)

        self.plot_kwargs_record = {}
        for _, v in tab_mapping.items():
            self.plot_kwargs_record[v] = {}

        self.thread_pool = QtCore.QThreadPool()
        logger.info('Maximal threads: %d', self.thread_pool.maxThreadCount())

        self.vk = None
        self.hdf_params = None
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

        self.pushButton_plot_saxs2d.clicked.connect(self.plot_saxs_2d)
        self.pushButton_plot_saxs1d.clicked.connect(self.plot_saxs_1d)
        self.pushButton_plot_stability.clicked.connect(self.plot_stability)
        self.pushButton_plot_intt.clicked.connect(self.plot_intensity_t)
        # self.saxs1d_lb_type.currentIndexChanged.connect(self.switch_saxs1d_line)

        self.tabWidget.currentChanged.connect(self.update_plot)
        self.list_view_target.clicked.connect(self.update_plot)

        self.mp_2t_hdls = None
        self.init_twotime_plot_handler()
        self.twotime_kwargs = None

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
        self.show_g2_fit_summary.clicked.connect(self.show_g2_fit_summary_func)
        self.btn_g2_refit.clicked.connect(self.plot_g2)
        self.saxs2d_autorange.stateChanged.connect(self.update_saxs2d_range)
        self.btn_deselect.clicked.connect(self.clear_target_selection)
        self.list_view_target.doubleClicked.connect(self.edit_label)

        self.btn_select_bkgfile.clicked.connect(self.select_bkgfile)

        self.g2_fitting_function.currentIndexChanged.connect(
            self.update_g2_fitting_function
        )
        self.btn_up.clicked.connect(lambda: self.reorder_target('up'))
        self.btn_down.clicked.connect(lambda: self.reorder_target('down'))

        # saxs1d export profiles
        self.btn_export_saxs1d.clicked.connect(self.saxs1d_export)

        # saxs2d roi
        # self.btn_saxs2d_roi_add.clicked.connect(self.saxs2d_roi_add)
        self.comboBox_qmap_target.currentIndexChanged.connect(self.update_plot)
        self.update_g2_fitting_function()

        self.load_default_setting()
        self.show()

    def load_default_setting(self):
        # home_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
        if not os.path.isdir(self.home_dir):
            os.mkdir(self.home_dir)

        key_fname = os.path.join(self.home_dir, 'default_setting.json')
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

        # remove joblib cache
        cache_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer',
                                 'joblib/xpcs_viewer')
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir)

        return

    def get_selected_rows(self):
        selected_index = self.list_view_target.selectedIndexes()
        selected_row = [x.row() for x in selected_index]
        # the selected index is ordered;
        selected_row.sort()
        return selected_row

    def update_plot(self):
        idx = self.tabWidget.currentIndex()
        tab_name = tab_mapping[idx]
        if tab_name == 'average':
            return
        func = getattr(self, 'plot_' + tab_name)
        try:
            kwargs = func(dryrun=True)
            kwargs['target_timestamp'] = self.vk.timestamp
            if self.plot_kwargs_record[tab_name] != kwargs:
                func(dryrun=False)
                self.plot_kwargs_record[tab_name] = kwargs
        except Exception as e:
            logger.error(f'update selection in [{tab_name}] failed')
            logger.error(e)
            traceback.print_exc()

    def init_tab(self):
        new_tab_id = self.tabWidget.currentIndex()
        tab_name = tab_mapping[new_tab_id]
        if tab_name in ['twotime', 'average']:
            function = getattr(self, 'init_' + tab_name)
            try:
                function()
            except Exception as e:
                logger.error('init %s failed', tab_name)
                logger.error(e)

    def plot_metadata(self, dryrun=False):
        kwargs = {
            'rows': self.get_selected_rows()
        }
        if dryrun:
            return kwargs

        msg = self.vk.get_xf_list(**kwargs)[0].get_hdf_info()
        hdf_info_data = create_param_tree(msg)
        self.hdf_params = Parameter.create(name="Settings", type="group",
                                       children=hdf_info_data)
        self.hdf_info.setParameters(self.hdf_params, showTop=True)

    def plot_saxs_2d(self, dryrun=False):
        kwargs = {
            'rows': self.get_selected_rows(),
            'plot_type': self.cb_saxs2D_type.currentText(),
            'cmap': self.cb_saxs2D_cmap.currentText(),
            'rotate': self.saxs2d_rotate.isChecked(),
            'display': self.saxs2d_display,
            'autorange': self.saxs2d_autorange.isChecked(),
            'vmin': self.saxs2d_min.value(),
            'vmax': self.saxs2d_max.value(),
        }
        if dryrun:
            return kwargs
        else:
            self.vk.plot_saxs_2d(pg_hdl=self.pg_saxs, **kwargs)
    
    def saxs2d_roi_add(self):
        if not self.check_status(show_msg=False):
            return
        #         sl_type='Pie', width=3, sl_mode='exclusive',
        #         second_point=None, label=Non
        sl_type_idx = self.cb_saxs2D_roi_type.currentIndex()
        color = ('g', 'y', 'b', 'r', 'c', 'm', 'k', 'w')[
            self.cb_saxs2D_roi_color.currentIndex()]
        kwargs = {
            'sl_type': ('Pie', 'Circle')[sl_type_idx],
            'width': self.sb_saxs2D_roi_width.value(),
            'color': color,
        }
        self.vk.add_roi(self.pg_saxs, **kwargs)

    def plot_saxs_1d(self, dryrun=False):
        kwargs = {
            'plot_type': self.cb_saxs_type.currentIndex(),
            'plot_offset': self.sb_saxs_offset.value(),
            'plot_norm': self.cb_saxs_norm.currentIndex(),
            'rows': self.get_selected_rows(),
            'qmin': self.saxs1d_qmin.value(),
            'qmax': self.saxs1d_qmax.value(),
            'loc': self.saxs1d_legend_loc.currentText(),
            'marker_size': self.sb_saxs_marker_size.value(),
            'sampling': self.saxs1d_sampling.value(),
            'all_phi': self.box_all_phi.isChecked(),
            'absolute_crosssection': self.cbox_use_abs.isChecked(),
            'subtract_background': self.cb_sub_bkg.isChecked(),
            'weight': self.bkg_weight.value(),
            'show_roi': self.box_show_roi.isChecked(),
            'show_phi_roi': self.box_show_phi_roi.isChecked(),
        }
        if kwargs['qmin'] >= kwargs['qmax']:
            self.statusbar.showMessage('check qmin and qmax')
            return

        if dryrun:
            return kwargs
        else:
            self.vk.plot_saxs_1d(self.pg_saxs, self.mp_saxs.hdl, **kwargs)
            self.mp_saxs.repaint()
            # adjust the line behavior
            self.switch_saxs1d_line()

    def switch_saxs1d_line(self):
        lb_type = self.saxs1d_lb_type.currentIndex()
        lb_type = [None, 'slope', 'hline'][lb_type]
        self.vk.switch_saxs1d_line(self.mp_saxs.hdl, lb_type)
    
    def saxs1d_export(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 
            caption='select a folder to export SAXS profiles')

        if folder in [None, '']:
            return

        self.vk.export_saxs_1d(self.pg_saxs, folder)
    
    def init_twotime_plot_handler(self):
        # self.mp_2t.setBackground('w')
        self.mp_2t_hdls = {}
        labels = ['saxs', 'dqmap']
        titles = ['scattering', 'dynamic_qmap']
        cmaps = ['viridis', 'tab20']
        self.mp_2t_map.setBackground('w')
        for n in range(2):
            plot_item = self.mp_2t_map.addPlot(row=0, col=n)
            # Remove axes
            plot_item.hideAxis('left')
            plot_item.hideAxis('bottom')
            plot_item.getViewBox().setDefaultPadding(0)

            plot_item.setMouseEnabled(x=False, y=False)
            image_item = pg.ImageItem(np.ones((128, 128)))
            image_item.setOpts(axisOrder='row-major')  # Set to row-major order

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
            self.mp_2t_hdls[labels[n] + '_colorbar'] = colorbar

        c2g2_plot = self.mp_2t_map.addPlot(row=0, col=2)
        self.mp_2t_hdls['c2g2'] = c2g2_plot

        self.mp_2t_hdls['dqmap'].mouseClickEvent = self.pick_twotime_index
        self.mp_2t_hdls['saxs'].mouseClickEvent = self.pick_twotime_index
        # self.mp_2t.getView().setBackgroundColor('w')
        self.mp_2t.ui.graphicsView.setBackground('w')
        self.mp_2t_hdls['tt'] = self.mp_2t
        self.mp_2t_hdls['tt'].view.invertY(False)
        self.mp_2t.view.setLabel('left', 't2', units='s')
        self.mp_2t.view.setLabel('bottom', 't1', units='s')

        self.mp_2t.sigTimeChanged.connect(
            lambda x: self.plot_twotime_map(highlight_dqbin=x+1))
    
    def pick_twotime_index(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()
            x, y = int(pos.x()), int(pos.y())
            dq_bin = self.plot_twotime_map(highlight_xy=(x, y))
            if dq_bin is not None and dq_bin != np.nan:
                if self.mp_2t_hdls['tt'].image is not None:
                    self.mp_2t_hdls['tt'].setCurrentIndex(int(dq_bin) - 1)
        event.accept()  # Mark the event as handled

    def plot_qmap(self, dryrun=False):
        kwargs = {
            'rows': self.get_selected_rows(),
            'target': self.comboBox_qmap_target.currentText()
        }
        if dryrun:
            return kwargs
        self.vk.plot_qmap(self.pg_qmap, **kwargs)
    
    def plot_twotime(self, dryrun=False):
        kwargs = {'rows': self.get_selected_rows()}
        if dryrun:
            return kwargs
        self.plot_twotime_map()
        self.plot_twotime_correlation()

    def plot_twotime_map(self, dryrun=False, highlight_xy=None, 
                         highlight_dqbin=None):
        if self.mp_2t_hdls is None:
            self.init_twotime_plot_handler()
        kwargs = {
            'auto_crop': self.twotime_autocrop.isChecked(),
            'highlight_xy': highlight_xy,
            'highlight_dqbin': highlight_dqbin,
            'rows': self.get_selected_rows(),
        }
        if dryrun:
            return kwargs
        return self.vk.plot_twotime_map(self.mp_2t_hdls, **kwargs)

    def plot_twotime_correlation(self, dryrun=False):
        kwargs = {
            'rows': self.get_selected_rows(),
            'cmap': self.cb_twotime_cmap.currentText(),
            'vmin': self.c2_min.value(),
            'vmax': self.c2_max.value(),
            'correct_diag': self.twotime_correct_diag.isChecked(),
        }
        if dryrun: return kwargs
        self.vk.plot_twotime_correlation(self.mp_2t_hdls, **kwargs)

    def edit_label(self):
        if not self.check_status():
            return
        rows = self.get_selected_rows()
        self.tree = self.vk.get_pg_tree(rows)
        self.tree.show()

    def plot_stability(self, dryrun=False):
        kwargs = {
            'plot_type': self.cb_stab_type.currentIndex(),
            'plot_offset': self.sb_stab_offset.value(),
            'plot_norm': self.cb_stab_norm.currentIndex(),
            'rows': self.get_selected_rows()
        }
        if dryrun:
            return kwargs
        else:
            self.vk.plot_stability(self.mp_stab.hdl, **kwargs)

    def plot_intensity_t(self, dryrun=False):
        kwargs = {
            # 'max_points': self.sb_intt_max.value(),
            'sampling': max(1, self.sb_intt_sampling.value()),
            'window': self.sb_window.value(),
            'rows': self.get_selected_rows(),
            'xlabel': self.intt_xlabel.currentText()
        }
        if dryrun:
            return kwargs
        else:
            self.vk.plot_intt(self.pg_intt, **kwargs)

    def init_diffusion(self):
        self.vk.plot_tauq_pre(hdl=self.mp_tauq_pre.hdl)

    def plot_diffusion(self, dryrun=False):
        keys = [self.tauq_amin, self.tauq_bmin,
                self.tauq_amax, self.tauq_bmax]
        bounds = np.array([float(x.text()) for x in keys]).reshape(2, 2)

        fit_flag = [self.tauq_afit.isChecked(), self.tauq_bfit.isChecked()]

        if sum(fit_flag) == 0:
            self.statusbar.showMessage('nothing to fit, really?', 1000)
            return

        tauq = [self.tauq_qmin, self.tauq_qmax]
        q_range = [float(x.text()) for x in tauq]

        kwargs = {
            'bounds': bounds.tolist(),
            'fit_flag': fit_flag,
            'offset': self.sb_tauq_offset.value(),
            'rows': self.get_selected_rows(),
            'q_range': q_range,
            'plot_type': self.cb_tauq_type.currentIndex()
        }
        if dryrun:
            return kwargs
        else:
            msg = self.vk.plot_tauq(hdl=self.mp_tauq.hdl, **kwargs)
            self.mp_tauq.parent().repaint()
            self.tauq_msg.clear()
            self.tauq_msg.setData(msg)
            self.tauq_msg.parent().repaint()
    
    def select_bkgfile(self):
        path = self.work_dir.text()
        f = QtWidgets.QFileDialog.getOpenFileName(self, 
            caption='select the file for background subtraction',
            directory=path)[0]
        if os.path.isfile(f):
            self.le_bkg_fname.setText(f)
            self.vk.select_bkgfile(f)
        else:
            return

    def remove_avg_job(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0:
            return
        self.vk.remove_job(index)

    def set_average_save_path(self):
        save_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Open directory')
        self.avg_save_path.clear()
        self.avg_save_path.setText(save_path)
        return

    def set_average_save_name(self):
        save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as')
        self.avg_save_name.clear()
        self.avg_save_name.setText(os.path.basename(save_name[0]))
        return

    def init_average(self):
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
                'select at least 2 files for averaging', 1000)
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
            self.statusbar.showMessage(
                'No average field is selected. quit', 1000)
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
            self.statusbar.showMessage('check avg min/max values.', 1000)
            return

        self.vk.submit_job(**kwargs)
        # the target_average has been reset
        self.update_box(self.vk.target, mode='target')

    def update_avg_info(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            self.statusbar.showMessage('select a job to start', 1000)
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
            self.statusbar.showMessage('select a job to start', 1000)
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
            self.statusbar.showMessage('select a job to kill', 1000)
            return
        worker = self.vk.avg_worker[index]
        if worker.status != 'running':
            self.statusbar.showMessage('the selected job isn\'s running', 1000)
            return
        worker.kill()

    def show_g2_fit_summary_func(self):
        if not self.check_status(): return
        
        rows = self.get_selected_rows()
        self.tree = self.vk.get_fitting_tree(rows)
        self.tree.show()

    def show_avg_jobinfo(self):
        index = self.avg_job_table.currentIndex().row()
        if index < 0 or index >= len(self.vk.avg_worker):
            logger.info('select a job to show it\'s settting')
            return
        worker = self.vk.avg_worker[index]
        self.tree = worker.get_pg_tree()
        self.tree.show()

    def init_g2(self, flag, tel, qd):
        if not flag:
            logger.error('g2 data is not consistent or not multitau analysis. abort')
            return

        # tel is a list of arrays, which may have diffent shape;
        t_min = np.min([t[0] for t in tel])
        t_max = np.max([t[-1] for t in tel])

        def to_e(x):
            return '%.2e' % x

        self.g2_bmin.setValue(t_min / 20)
        # self.g2_bmax.setText(to_e(t_max * 10))
        self.g2_bmax.setValue(t_max * 10)

        self.g2_tmin.setText(to_e(t_min / 1.1))
        self.g2_tmax.setText(to_e(t_max * 1.1))

        if self.g2_qmin.value() > np.max(qd):
            self.g2_qmin.setValue(np.min(qd) * 0.9)

        qmax = self.g2_qmax.value()
        if qmax < np.min(qd) or qmax < self.g2_qmin.value():
            self.g2_qmin.setValue(np.max(qd) * 1.1)

    def plot_g2(self, dryrun=False):
        p = self.check_g2_number()
        bounds, fit_flag, fit_func = self.check_g2_fitting_number()

        kwargs = {
            'num_col': self.sb_g2_column.value(),
            'offset': self.sb_g2_offset.value(),
            'show_fit': self.g2_show_fit.isChecked(),
            'show_label': self.g2_show_label.isChecked(),
            'plot_type': self.g2_plot_type.currentText(),
            'q_range': (p[0], p[1]),
            't_range': (p[2], p[3]),
            'y_range': (p[4], p[5]),
            'y_auto': self.g2_yauto.isChecked(),
            'rows': self.get_selected_rows(),
            'bounds': bounds,
            'fit_flag': fit_flag,
            'marker_size': self.g2_marker_size.value(),
            'subtract_baseline': self.g2_sub_baseline.isChecked(),
            'fit_func': fit_func
            # 'label_size': self.sb_g2_label_size.value(),
        }
        if kwargs['show_fit'] and sum(kwargs['fit_flag']) == 0:
            self.statusbar.showMessage('nothing to fit, really?', 1000)
            return

        if dryrun:
            return kwargs
        else:
            self.pushButton_4.setDisabled(True)
            self.pushButton_4.setText('plotting')
            try:
                flag, tel, qd = self.vk.plot_g2(handler=self.mp_g2, **kwargs)
                self.init_g2(flag, tel, qd)
            except ZeroDivisionError:
                self.statusbar.showMessage('check range', 1000)
            self.pushButton_4.setEnabled(True)
            self.pushButton_4.setText('plot')
            if kwargs['show_fit']:
                self.init_diffusion()

    def export_g2(self):
        self.vk.export_g2()

    def reload_source(self):
        self.pushButton_11.setText('loading')
        self.pushButton_11.setDisabled(True)
        self.pushButton_11.parent().repaint()
        path = self.work_dir.text()
        self.vk.build(path=path, sort_method=self.sort_method.currentText())
        self.pushButton_11.setText('reload')
        self.pushButton_11.setEnabled(True)
        self.pushButton_11.parent().repaint()

        self.update_box(self.vk.source, mode='source')
        self.apply_filter_to_source()

    def load_path(self, path=None, debug=False):
        if path in [None, False]:
            # DontUseNativeDialog is used so files are shown along with dirs;
            f = QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Open directory', self.start_wd,
                QtWidgets.QFileDialog.DontUseNativeDialog)
        else:
            f = path

        if not os.path.isdir(f):
            self.statusbar.showMessage('{} is not a folder.'.format(f), 1000)
            f = self.start_wd

        # either choose a new work_dir or initialize from state=0
        # if f == curr_work_dir; then the state is kept the same;
        self.work_dir.setText(f)

        if self.vk is None:
            self.vk = ViewerKernel(f, self.statusbar)
        else:
            self.vk.set_path(f)
            self.vk.clear()

        self.reload_source()
        self.avg_job_table.setModel(self.vk.avg_worker)
        self.source_model = self.vk.source
        self.update_box(self.vk.source, mode='source')

    def update_box(self, file_list, mode='source'):
        if file_list is None:
            return
        if mode == 'source':
            self.list_view_source.setModel(file_list)
            self.box_source.setTitle('Source: %5d' % len(file_list))
            self.box_source.parent().repaint()
            self.list_view_source.parent().repaint()
        elif mode == 'target':
            self.list_view_target.setModel(file_list)
            self.box_target.setTitle('Target: %5d' % (len(file_list)))
            # on macos, the target box doesn't seem to update; force it
            file_list.layoutChanged.emit()
            self.box_target.repaint()
            self.list_view_target.repaint()
        self.statusbar.showMessage('Target file list updated.', 1000)
        return

    def add_target(self):
        target = []
        for x in self.list_view_source.selectedIndexes():
            # in some cases, it will return None
            val = x.data()
            if val is not None:
                target.append(val)
        if target == []:
            return
        self.vk.add_target(target)
        self.list_view_source.clearSelection()
        self.update_box(self.vk.target, mode='target')
        tab_id = self.tabWidget.currentIndex()
        if tab_mapping[tab_id] == 'average':
            self.init_average()
        else:
            self.update_plot()

    def reorder_target(self, direction='up'):
        rows = self.get_selected_rows()
        if len(rows) != 1 or len(self.vk.target) <= 1:
            return
        idx = self.vk.reorder_target(rows[0], direction)
        self.list_view_target.setCurrentIndex(idx)
        self.list_view_target.repaint()
        self.update_plot()
        return

    def remove_target(self):
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())

        self.vk.remove_target(rmv_list)
        # clear selection to avoid the bug: when the last one is selected, then
        # the list will out of bounds
        self.clear_target_selection()

        # if all files are removed; then go to state 1
        if self.vk.target in [[], None] or len(self.vk.target) == 0:
            self.reset_gui()
        self.update_box(self.vk.target, mode='target')

    def reset_gui(self):
        self.vk.reset_kernel()
        for x in [self.pg_saxs, self.pg_intt, self.mp_tauq, 
                  self.mp_g2, self.mp_saxs, self.mp_stab]:
            x.clear()
        self.le_bkg_fname.clear()

    def apply_filter_to_source(self):
        min_length = 1
        val = self.filter_str.text()
        if len(val) == 0:
            self.source_model = self.vk.source
            self.update_box(self.vk.source, mode='source')
            return
        # avoid searching when the filter lister is too short
        if len(val) < min_length:
            self.statusbar.showMessage(
                'Please enter at least %d characters' % min_length, 1000)
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
            if isinstance(key, QtWidgets.QDoubleSpinBox):
                val = key.value()
            elif isinstance(key, QtWidgets.QLineEdit):
                try:
                    val = float(key.text())
                except Exception:
                    key.setText(str(default_val[n]))
                    self.statusbar.showMessage('g2 number is invalid', 1000)
            vals[n] = val

        def swap_min_max(id1, id2):
            if vals[id1] > vals[id2]:
                keys[id1].setValue(vals[id2])
                keys[id2].setValue(vals[id1])
                vals[id1], vals[id2] = vals[id2], vals[id1]

        swap_min_max(0, 1)
        # swap_min_max(2, 3, lambda x: '%.2e' % x)
        swap_min_max(4, 5)

        return vals

    def check_g2_fitting_number(self):
        fit_func = ['single', 'double'][self.g2_fitting_function.currentIndex()]
        keys = (self.g2_amin, self.g2_amax, self.g2_bmin, self.g2_bmax,
                self.g2_cmin, self.g2_cmax, self.g2_dmin, self.g2_dmax,
                self.g2_b2min, self.g2_b2max, self.g2_c2min, self.g2_c2max,
                self.g2_fmin, self.g2_fmax)

        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            vals[n] = key.value()

        def swap_min_max(id1, id2):
            if vals[id1] > vals[id2]:
                keys[id1].setValue(vals[id2])
                keys[id2].setValue(vals[id1])
                vals[id1], vals[id2] = vals[id2], vals[id1]

        for n in range(0, 7):
            swap_min_max(2 * n, 2 * n + 1)

        vals = np.array(vals).reshape(len(keys) // 2, 2)
        bounds = vals.T

        fit_keys = (self.g2_afit, self.g2_bfit, self.g2_cfit, self.g2_dfit,
                    self.g2_b2fit, self.g2_c2fit, self.g2_ffit)
        fit_flag = [x.isChecked() for x in fit_keys]

        if fit_func == 'single':
            fit_flag = fit_flag[0:4]
            bounds = bounds[:, 0:4]
        bounds = bounds.tolist()
        return bounds, fit_flag, fit_func

    def check_status(self, show_msg=True, min_state=2):
        pass

    def update_saxs2d_range(self, flag=True):
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

    def clear_target_selection(self):
        self.list_view_target.clearSelection()
        # self.list_view_target.repaint()

    def update_g2_fitting_function(self):
        idx = self.g2_fitting_function.currentIndex()
        title = [
            "g2 fitting with Single Exp:  y = a·exp[-2(x/b)^c]+d",
            "g2 fitting with Double Exp:  y = a·[f·exp[-(x/b)^c +" +
            "(1-f)·exp[-(x/b2)^c2]^2+d"
        ]
        self.groupBox_2.setTitle(title[idx])

        pvs = [[self.g2_b2min, self.g2_b2max, self.g2_b2fit],
               [self.g2_c2min, self.g2_c2max, self.g2_c2fit],
               [self.g2_fmin, self.g2_fmax, self.g2_ffit]]

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


def main_gui():
    if os.name == 'nt':
        setup_windows_icon()
    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_EnableHighDpiScaling, True)
    
    argparser = argparse.ArgumentParser(
        description='pyXpcsViewer: a GUI tool for XPCS data analysis')
    argparser.add_argument('--path', type=str, help='path to the result folder',
                          default='./')
    # Positional argument
    argparser.add_argument("positional_path", nargs="?", default=None,
                        help="positional path to the result folder")
    # Determine the directory to monitor
    argparser.add_argument('--label_style', type=str, help='label style',
                          default=None)

    args = argparser.parse_args()
    if args.positional_path is not None:
        args.path = args.positional_path
    
    app = QtWidgets.QApplication([])
    window = XpcsViewer(path=args.path, label_style=args.label_style)
    app.exec_()


if __name__ == '__main__':
    main_gui()