import numpy as np
from .file_locator import FileLocator
from .module import saxs2d, saxs1d, intt, stability, g2mod, tauq, twotime
from .module.average_toolbox import AverageToolbox
from .helper.listmodel import TableDataModel
import pyqtgraph as pg
import os
import logging
from .xpcs_file import XpcsFile


logger = logging.getLogger(__name__)


class ViewerKernel(FileLocator):
    def __init__(self, path, statusbar=None):
        super().__init__(path)
        self.statusbar = statusbar
        self.meta = None
        self.reset_meta()
        self.avg_tb = AverageToolbox(path)
        self.avg_worker = TableDataModel()
        self.avg_jid = 0
        self.avg_worker_active = {}

    def reset_meta(self):
        self.meta = {
            # saxs 1d:
            'saxs1d_bkg_fname': None,
            'saxs1d_bkg_xf': None,

            # twotime
            'twotime_fname': None,
            'twotime_dqmap': None,
            'twotime_ready': False,
            'twotime_map_kwargs': None,
            'twotime_kwargs': None,
            # avg
            'avg_file_list': None,
            'avg_intt_minmax': None,
            'avg_g2_avg': None,
            # g2
            'g2_num_points': None,
            'g2_data': None,
            'g2_plot_condition': tuple([None, None, None]),
            'g2_fit_val': {},
        }
        return

    def reset_kernel(self):
        self.clear_target()
        self.reset_meta()

    def show_message(self, msg):
        if msg in [None, [None]]:
            return

        if isinstance(msg, list):
            for t in msg:
                logger.info(t)
            msg = '\n'.join(msg)
        else:
            logger.info(msg)

        if self.statusbar is not None:
            self.statusbar.showMessage(msg, 1500)
    
    def select_bkgfile(self, f):
        fname = os.path.basename(f)
        path = os.path.dirname(f)
        self.meta['saxs1d_bkg_fname'] = f
        self.meta['saxs1d_bkg_xf'] = XpcsFile(fname, path)

    def get_g2_data(self, max_points, rows, **kwargs):
        xf_list = self.get_xf_list(max_points, rows=rows)
        flag, tel, qd, g2, g2_err = g2mod.get_data(xf_list, **kwargs)
        return flag, tel, qd, g2, g2_err

    def get_pg_tree(self, rows):
        if rows in [None, []]:
            rows = [0]
        xfile = self.cache[self.target[rows[0]]]
        return xfile.get_pg_tree()
    
    def get_fitting_tree(self, rows, max_points=12):
        xf_list = self.get_xf_list(max_points, rows)
        result = {}
        for x in xf_list:
            result[x.label] = x.get_fitting_info(mode='g2_fitting')
        tree = pg.DataTreeWidget(data=result)
        tree.setWindowTitle('fitting summary')
        tree.resize(1024, 800)
        return tree

    def plot_g2(self, handler, q_range, t_range, y_range, max_points=128,
                rows=None, **kwargs):
        xf_list = self.get_xf_list(max_points, rows=rows) 
        g2mod.pg_plot(handler, xf_list, q_range, t_range, y_range, rows=rows,
                      **kwargs)
        return

    def plot_tauq_pre(self, hdl=None, max_points=128, rows=None):
        xf_list = self.get_xf_list(max_points, rows=rows)
        short_list = [xf for xf in xf_list if xf.fit_summary is not None]
        tauq.plot_pre(short_list, hdl)

    def plot_tauq(self, hdl=None, bounds=None, rows=[], plot_type=3,
                  fit_flag=None, offset=None, max_points=128, q_range=None):
        
        xf_list = self.get_xf_list(max_points, rows=rows) 
        result = {}
        for x in xf_list:
            if x.fit_summary is None:
                logger.info('g2 fitting is not available for %s', x.fname)
            else:
                x.fit_tauq(q_range, bounds, fit_flag)
                result[x.label] = x.get_fitting_info(mode='tauq_fitting')
        
        tauq.plot(xf_list, hdl=hdl, q_range=q_range, offset=offset,
                  plot_type=plot_type)

        return result

    def plot_saxs_2d(self, *args, **kwargs):
        ans = [self.cache[fn].saxs_2d for fn in self.target]
        # extents = extent = (qy_min, qy_max, qx_min, qx_max)
        extent = self.cache[self.target[0]].get_detector_extent()
        center = (self.cache[self.target[0]].bcy,
                  self.cache[self.target[0]].bcx)
        saxs2d.plot(ans, extent=extent, center=center, *args, **kwargs)
    
    def add_roi(self, hdl, max_points=128, **kwargs):
        xf_list = self.get_xf_list(max_points)
        cen = (xf_list[0].bcx, xf_list[0].bcy)
        if kwargs['sl_type'] == 'Pie':
            hdl.add_roi(cen=cen, radius=100, **kwargs)
        elif kwargs['sl_type'] == 'Circle':

            radius_v = min(xf_list[0].mask.shape[0] - cen[1], cen[1])
            radius_h = min(xf_list[0].mask.shape[1] - cen[0], cen[0])
            radius = min(radius_h, radius_v) * 0.8

            hdl.add_roi(cen=cen, radius=radius, label='RingA', **kwargs)
            hdl.add_roi(cen=cen, radius=0.8*radius, label='RingB', **kwargs)

    def plot_saxs_1d(self, pg_hdl, mp_hdl, max_points=128, **kwargs):
        xf_list = self.get_xf_list(max_points)
        roi_list = pg_hdl.get_roi_list()
        saxs1d.plot(xf_list, mp_hdl, bkg_file=self.meta['saxs1d_bkg_xf'],
                    max_points=max_points, roi_list=roi_list, **kwargs)

    def export_saxs_1d(self, pg_hdl, folder, max_points=128):
        xf_list = self.get_xf_list(max_points)
        roi_list = pg_hdl.get_roi_list()
        for xf in xf_list:
            xf.export_saxs1d(roi_list, folder)
        return
    
    def switch_saxs1d_line(self, mp_hdl, lb_type):
        saxs1d.switch_line_builder(mp_hdl, lb_type)

    def plot_twotime_map(self, hdl, fname=None, **kwargs):
        if fname is None:
            fname = self.target[0]
        config = {'fname': fname, **kwargs} 
        if self.meta['twotime_map_kwargs'] == config:
            return
        else:
            self.meta['twotime_map_kwargs'] = config

        xfile = self.cache[fname]
        return twotime.plot_twotime_map(xfile, hdl, **kwargs)

    def plot_twotime(self, hdl, current_file_index=0, **kwargs):
        fname = self.target[current_file_index]
        xfile = self.cache[fname]
        if "Twotime" not in xfile.atype:
            logger.error(f"The selected file [{fname}] doesn't have Twotime data")
            return
        config = {'fname': fname, **kwargs}
        if self.meta['twotime_kwargs'] == config:
            return
        else:
            self.meta['twotime_kwargs'] = config

        ret = twotime.plot_twotime(xfile, hdl, meta=self.meta, **kwargs)
        return ret

    def plot_intt(self, pg_hdl, max_points=128, rows=None, **kwargs):
        xf_list = self.get_xf_list(max_points, rows=rows)
        intt.plot(xf_list, pg_hdl, self.id_list, **kwargs)

    def plot_stability(self, mp_hdl, plot_id, **kwargs):
        fc = self.cache[self.target[plot_id]]
        stability.plot(fc, mp_hdl, **kwargs)

    def submit_job(self, *args, **kwargs):
        if len(self.target) <= 0:
            logger.error('no average target is selected')
            return
        worker = AverageToolbox(work_dir=self.cwd,
                                flist=self.target,
                                jid=self.avg_jid)
        worker.setup(*args, **kwargs)
        self.avg_worker.append(worker)
        logger.info('create average job, ID = %s', worker.jid)
        self.avg_jid += 1

        self.target.clear()
        return

    def remove_job(self, index):
        self.avg_worker.pop(index)
        return

    def update_avg_info(self, jid):
        self.avg_worker.layoutChanged.emit()
        if 0 <= jid < len(self.avg_worker):
            self.avg_worker[jid].update_plot()

    def update_avg_values(self, data):
        key, val = data[0], data[1]
        if self.avg_worker_active[key] is None:
            self.avg_worker_active[key] = [0, np.zeros(128, dtype=np.float32)]
        record = self.avg_worker_active[key]
        if record[0] == record[1].size:
            new_g2 = np.zeros(record[1].size * 2, dtype=np.float32)
            new_g2[0:record[0]] = record[1]
            record[1] = new_g2
        record[1][record[0]] = val
        record[0] += 1

        return
    
    def export_g2(self):
       pass 


if __name__ == "__main__":
    flist = os.listdir('./data')
    dv = ViewerKernel('./data', flist)
