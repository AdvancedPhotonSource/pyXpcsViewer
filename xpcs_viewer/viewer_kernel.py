import numpy as np
from .file_locator import FileLocator
from .module import saxs2d, saxs1d, intt, stability, g2mod, tauq, twotime

from shutil import copyfile
from sklearn.cluster import KMeans as sk_kmeans
import h5py

import os
import logging


logger = logging.getLogger(__name__)


class ViewerKernel(FileLocator):
    def __init__(self, path, statusbar=None):
        super().__init__(path)
        self.statusbar = statusbar
        self.meta = None
        self.reset_meta()

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

    def get_g2_data(self, max_points, **kwargs):
        xf_list = self.get_xf_list(max_points)
        flag, tel, qd, g2, g2_err = g2mod.get_data(xf_list, **kwargs)
        return flag, tel, qd, g2, g2_err
    
    def get_pg_tree(self, rows):
        if rows in [None, []]:
            rows = [0]
        xfile = self.cache[self.target[rows[0]]]
        return xfile.get_pg_tree()

    def plot_g2(self, handler, q_range=None, t_range=None, y_range=None,
                offset=None, show_fit=False, max_points=50, bounds=None,
                show_label=False, num_col=4, plot_type='multiple'):

        num_points = min(len(self.target), max_points)
        fn_tuple = self.get_fn_tuple(max_points)
        new_condition = (fn_tuple, (q_range, t_range, y_range, offset), bounds)

        plot_level = 0
        if self.meta['g2_plot_condition'] == new_condition:
            logger.info('g2 plot parameters unchanged; skip')
        else:
            cmp = tuple(i != j for i, j in
                        zip(new_condition, self.meta['g2_plot_condition']))
            self.meta['g2_plot_condition'] = new_condition
            plot_level = 4 * cmp[0] + 2 * cmp[1] + cmp[2]

        if plot_level >= 2:
            # either filename or range changed; re-generate the data
            flag, tel, qd, g2, g2_err = self.get_g2_data(q_range=q_range,
                                                         t_range=t_range,
                                                         max_points=max_points)
            self.meta['g2_data'] = (flag, tel, qd, g2, g2_err)
        else:
            # if only the fitting parameters changed; load data from cache
            flag, tel, qd, g2, g2_err = self.meta['g2_data']

        if not flag:
            return
        
        if show_label:
            labels = self.id_list
        else:
            labels = None

        # labels = self.id_list

        res = g2mod.pg_plot(handler, tel, qd, g2, g2_err, num_col, t_range,
                            y_range, offset=offset, labels=labels,
                            show_fit=show_fit, bounds=bounds,
                            plot_type=plot_type)
        self.meta['g2_fit_val'] = res
        return

    def plot_tauq(self, max_q=0.016, hdl=None, offset=None):
        msg = tauq.plot(self.meta['g2_fit_val'], labels=self.id_list, hdl=hdl,
                        max_q=max_q, offset=offset)
        hdl.draw()
        self.show_message(msg)
        return msg

    def plot_saxs_2d(self, *args, **kwargs):
        ans = [self.cache[fn].saxs_2d for fn in self.target]
        saxs2d.plot(ans, *args, **kwargs)

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

    def plot_twotime_map(self, hdl, fname=None, **kwargs,):
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
        ret = twotime.plot_twotime(xfile, hdl, plot_index=plot_index,
                                   meta=self.meta, **kwargs)
        return ret

    def plot_intt(self, pg_hdl, max_points=128, **kwargs):
        xf_list = self.get_xf_list(max_points)
        intt.plot(xf_list, pg_hdl, self.id_list, **kwargs)

    def plot_stability(self, mp_hdl, plot_id, **kwargs):
        fc = self.cache[self.target[plot_id]]
        stability.plot(fc, mp_hdl, **kwargs)

    def average_plot_outlier(self, hdl, avg_blmin=0.95, avg_blmax=1.05,
                             avg_qindex=5, avg_window=10):

        if self.meta['avg_file_list'] != tuple(self.target) or \
                'avg_g2' not in self.meta:
            logger.info('avg cache not exist')
            xf_list = self.get_xf_list()
            flag, _, _, g2, _ = self.get_g2_data(max_points=-1)
            if not flag:
                return
            g2 = np.array(g2)

            self.meta['avg_file_list'] = tuple(self.target)
            self.meta['avg_g2'] = g2
            self.meta['avg_g2_mask'] = np.ones(len(self.target))

        else:
            logger.info('using avg cache')
            g2 = self.meta['avg_g2']

        g2_avg = np.mean(g2[:, -avg_window:, avg_qindex], axis=1)
        cut_min = np.ones_like(g2_avg) * avg_blmin
        cut_max = np.ones_like(g2_avg) * avg_blmax
        g2_avg = np.vstack([g2_avg, cut_min, cut_max])

        mask_min = g2_avg[0] >= avg_blmin
        mask_max = g2_avg[0] <= avg_blmax
        mask = np.logical_and(mask_min, mask_max)
        self.meta['avg_g2_mask'] = mask
        valid_num = np.sum(mask)

        legend = ['data', 'cutoff_min', 'cutoff_max']

        title = '%d / %d' % (valid_num, g2_avg.shape[1])

        hdl.show_lines(g2_avg,
                       xlabel='index',
                       ylabel='g2 average',
                       legend=legend,
                       title=title)

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

    def average(self,
                chunk_size=256,
                save_path=None,
                origin_path=None,
                p_bar=None):
        # TODO: need to comfirm the format to use.
        return

        labels = ["saxs_1d", 'g2', 'g2_err', 'saxs_2d']

        # mask = np.logical_and(self.meta['avg_g2_mask'],
        #                       self.meta['avg_intt_mask'])
        mask = self.meta['avg_g2_mask']

        steps = (len(mask) + chunk_size - 1) // chunk_size
        result = {}
        for n in range(steps):
            logger.info('n = {}'.format(n))
            if p_bar is not None:
                p_bar.setValue((n + 1) / steps * 100)
            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(len(mask), end)
            sl = slice(beg, end)
            values = self.fetch(labels,
                                file_list=self.target[sl],
                                mask=mask[sl])
            if n == 0:
                for label in labels:
                    result[label] = np.sum(values[label], axis=0)
            else:
                for label in labels:
                    result[label] += np.sum(values[label], axis=0)

        num_points = np.sum(mask)
        for label in labels:
            result[label] = result[label] / num_points

        if save_path is None:
            return result
        if origin_path is None:
            origin_path = os.path.join(self.cwd, self.target[0])

        logger.info('create file: {}'.format(save_path))
        copyfile(origin_path, save_path)
        self.put(save_path, labels, result, mode='raw')

        return result


if __name__ == "__main__":
    flist = os.listdir('./data')
    dv = ViewerKernel('./data', flist)
