import numpy as np
from .file_locator import FileLocator
from .module import saxs2d, saxs1d, intt, stability, g2mod, tauq, twotime
from .module.average_toolbox import AverageToolbox
from shutil import copyfile
from sklearn.cluster import KMeans as sk_kmeans
import h5py
from .helper.listmodel import ListDataModel, TableDataModel

import os
import logging

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
            # twotime
            'twotime_fname': None,
            'twotime_dqmap': None,
            'twotime_ready': False,
            'twotime_ims': [],
            'twotime_text': None,
            # avg
            'avg_file_list': None,
            'avg_intt_minmax': None,
            'avg_g2_avg': None,
            # g2
            'g2_num_points': None,
            'g2_data': None,
            'g2_plot_condition': tuple([None, None, None]),
            'g2_fit_val': {}
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

    def hash(self, max_points=10):
        if self.target is None:
            return hash(None)
        elif max_points <= 0:  # use all items
            val = hash(tuple(self.target))
        else:
            val = hash(tuple(self.target[0:max_points]))
        return val

    def get_g2_data(self, max_points, rows, **kwargs):
        xf_list = self.get_xf_list(max_points, rows=rows)
        flag, tel, qd, g2, g2_err = g2mod.get_data(xf_list, **kwargs)
        return flag, tel, qd, g2, g2_err

    def get_pg_tree(self, rows):
        if rows in [None, []]:
            rows = [0]
        xfile = self.cache[self.target[rows[0]]]
        return xfile.get_pg_tree()

    def plot_g2(self,
                handler,
                q_range=None,
                t_range=None,
                y_range=None,
                offset=None,
                show_fit=False,
                max_points=50,
                bounds=None,
                show_label=False,
                num_col=4,
                rows=None,
                plot_type='multiple'):

        num_points = min(len(self.target), max_points)
        fn_tuple = self.get_fn_tuple(max_points, rows=rows)
        new_condition = (fn_tuple, (q_range, t_range, y_range, offset), bounds)

        plot_level = 0
        if self.meta['g2_plot_condition'] == new_condition:
            logger.info('g2 plot parameters unchanged; skip')
        else:
            cmp = tuple(
                i != j
                for i, j in zip(new_condition, self.meta['g2_plot_condition']))
            self.meta['g2_plot_condition'] = new_condition
            plot_level = 4 * cmp[0] + 2 * cmp[1] + cmp[2]

        if plot_level >= 2:
            # either filename or range changed; re-generate the data
            flag, tel, qd, g2, g2_err = self.get_g2_data(q_range=q_range,
                                                         t_range=t_range,
                                                         max_points=max_points,
                                                         rows=rows)
            self.meta['g2_data'] = (flag, tel, qd, g2, g2_err)
        else:
            # if only the fitting parameters changed; load data from cache
            flag, tel, qd, g2, g2_err = self.meta['g2_data']

        if not flag:
            return

        if show_label:
            if rows is None or len(rows) == 0:
                labels = self.id_list 
            else:
                labels = [self.cache[self.target[n]].label for n in rows]
        else:
            labels = None

        # labels = self.id_list

        res = g2mod.pg_plot(handler,
                            tel,
                            qd,
                            g2,
                            g2_err,
                            num_col,
                            t_range,
                            y_range,
                            offset=offset,
                            labels=labels,
                            show_fit=show_fit,
                            bounds=bounds,
                            plot_type=plot_type)
        self.meta['g2_fit_val'] = res
        return

    def plot_tauq(self, max_q=0.016, hdl=None, offset=None):
        msg = tauq.plot(self.meta['g2_fit_val'],
                        labels=self.id_list,
                        hdl=hdl,
                        max_q=max_q,
                        offset=offset)
        hdl.draw()
        self.show_message(msg)
        return msg

    def plot_saxs_2d(self, *args, **kwargs):
        ans = [self.cache[fn].saxs_2d for fn in self.target]
        # extents = extent = (qy_min, qy_max, qx_min, qx_max)
        extent = self.cache[self.target[0]].get_detector_extent()
        saxs2d.plot(ans, extent=extent, *args, **kwargs)

    def plot_saxs_1d(self, mp_hdl, max_points=8, **kwargs):
        xf_list = self.get_xf_list(max_points)
        saxs1d.plot(xf_list, mp_hdl, legend=self.id_list, **kwargs)

    def setup_twotime(self, file_index=0, group='xpcs'):
        fname = self.target[file_index]
        res = []
        with h5py.File(os.path.join(self.cwd, fname), 'r') as f:
            for key in f.keys():
                if 'xpcs' in key:
                    res.append(key)
        return res

    def get_twotime_qindex(self, ix, iy, hdl):
        res = twotime.get_twotime_qindex(self.meta, ix, iy, hdl)
        return res

    def plot_twotime_map(
        self,
        hdl,
        fname=None,
        **kwargs,
    ):
        if fname is None:
            fname = self.target[0]

        xfile = self.cache[fname]
        twotime.plot_twotime_map(xfile, hdl, meta=self.meta, **kwargs)
        return

    def plot_twotime(self, hdl, current_file_index=0, plot_index=1, **kwargs):

        if self.type != 'Twotime':
            self.show_message('Analysis type must be twotime.')
            return None

        fname = self.target[current_file_index]
        xfile = self.cache[fname]
        ret = twotime.plot_twotime(xfile,
                                   hdl,
                                   plot_index=plot_index,
                                   meta=self.meta,
                                   **kwargs)
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

    # def register_avg_worker(self, worker):
    #     g2_hist = np.zeros(worker.size, dtype=np.float32)
    #     self.avg_wo

    def update_avg_info(self, jid):
        self.avg_worker.layoutChanged.emit()
        if 0 <= jid < len(self.avg_worker):
            self.avg_worker[jid].update_plot()

    def update_avg_values(self, data):
        key, val = data[0], data[1]
        # print(len(data))
        # print(type(key), type(val))
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


if __name__ == "__main__":
    flist = os.listdir('./data')
    dv = ViewerKernel('./data', flist)
