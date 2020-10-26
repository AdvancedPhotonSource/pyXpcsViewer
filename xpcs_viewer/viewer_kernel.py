import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.patches import Circle
from .helper.fitting import fit_xpcs, fit_tau
from .file_locator import FileLocator
from .module import saxs2d, saxs1d, intt, stability, g2mod

from PyQt5 import QtCore
from shutil import copyfile
from sklearn.cluster import KMeans as sk_kmeans
import h5py

import os
import logging

logging_format = '%(asctime)s %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


class ViewerKernel(FileLocator):
    def __init__(self, path, statusbar=None):
        super().__init__(path)
        self.statusbar = statusbar

        self.meta = {
            # twotime
            'twotime_fname': None,
            'twotime_dqmap': None,
            'twotime_ready': False,
            # avg
            'avg_file_list': None,
            'avg_intt_minmax': None,
            'avg_g2_avg': None,
            # g2
            'g2_num_points': None,
            'g2_hash_val': None,
            'g2_res': None,
            'g2_plot_condition': tuple([None, None, None]),
            'g2_fit_val': {}
        }

    def show_message(self, msg):
        if self.statusbar is not None:
            self.statusbar.showMessage(msg)
        logger.info(msg)

    def hash(self, max_points=10):
        if self.target is None:
            return hash(None)
        elif max_points <= 0:  # use all items
            val = hash(tuple(self.target))
        else:
            val = hash(tuple(self.target[0:max_points]))
        return val

    def get_g2_data(self, max_points=10, q_range=None, t_range=None):
        xf_list = self.get_xf_list(max_points)
        tel, qd, g2, g2_err = g2mod.get_data(xf_list, q_range, t_range)

        return tel, qd, g2, g2_err

    def plot_g2_initialize(self,
                           mp_hdl,
                           num_fig,
                           num_points,
                           num_col=4,
                           show_label=False):
        # adjust canvas size according to number of images
        if num_fig < num_col:
            num_col = num_fig
        num_row = (num_fig + num_col - 1) // num_col

        mp_hdl.adjust_canvas_size(num_col, num_row)
        mp_hdl.fig.clear()

        # mp_hdl.subplots(num_row, num_col, sharex=True, sharey=True)
        mp_hdl.subplots(num_row, num_col)
        mp_hdl.obj = None

        # dummy x y fit line
        x = np.logspace(-5, 0, 32)
        y = np.exp(-x / 1E-3) * 0.25 + 1.0
        err = y / 40

        err_obj = []
        lin_obj = []

        for idx in range(num_points):
            for i in range(num_fig):
                offset = 0.03 * idx
                ax = np.array(mp_hdl.axes).ravel()[i]
                obj1 = ax.errorbar(x,
                                   y + offset,
                                   yerr=err,
                                   fmt='o',
                                   markersize=3,
                                   markerfacecolor='none',
                                   label='{}'.format(self.id_list[idx]))
                err_obj.append(obj1)

                obj2 = ax.plot(x, y + offset)
                obj2[0].set_visible(False)
                lin_obj.append(obj2)

                # last image
                if idx == num_points - 1:
                    # ax.set_title('Q = %5.4f $\AA^{-1}$' % ql_dyn[i])
                    ax.set_xscale('log')
                    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                    # if there's only one point, do not add title; the title
                    # will be too long.
                    if show_label and i == num_fig - 1:
                        # if idx >= 1 and num_points < 10:
                        ax.legend(fontsize=8)

        # mp_hdl.fig.tight_layout()
        mp_hdl.obj = {
            'err': err_obj,
            'lin': lin_obj,
        }

    def plot_g2(
        self,
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
        prepare=False,
    ):

        num_points = min(len(self.target), max_points)
        new_condition = (tuple(self.target[:num_points]),
                         (q_range, t_range, y_range, offset), bounds)
        # if self.meta['g2_plot_condition'] == new_condition:
        #     return ['No target files selected or change in setting.']
        # else:
        #     cmp = tuple(i != j for i, j in
        #                 zip(new_condition, self.meta['g2_plot_condition']))
        #     self.meta['g2_plot_condition'] = new_condition
        #     plot_target = 4 * cmp[0] + 2 * cmp[1] + cmp[2]

        tel, qd, g2, g2_err = self.get_g2_data(q_range=q_range,
                                               t_range=t_range,
                                               max_points=max_points)
        if prepare:
            return np.min(tel), np.max(tel)

        num_fig = g2[0].shape[1]

        plot_target = 4
        if plot_target >= 2 or handler.axes is None:
            self.plot_g2_initialize(handler,
                                    num_fig,
                                    num_points,
                                    show_label=show_label,
                                    num_col=num_col)

        # if plot_target >= 2:
        if True:
            for ipt in range(num_points):
                for ifg in range(num_fig):
                    # add the title
                    if ipt == 0:
                        ax = np.array(handler.axes).ravel()[ifg]
                        ax.set_title('Q=%.4f $\\AA^{-1}$' % qd[ipt][ifg])
                    # update info
                    loc = ipt * num_fig + ifg
                    offset_i = -1 * offset * (ipt + 1)
                    handler.update_err(loc, tel[ipt], g2[ipt][:, ifg] + offset_i,
                                       g2_err[ipt][:, ifg])

        err_msg = []
        if show_fit:
            for ipt in range(num_points):
                fit_res, fit_val = fit_xpcs(tel[ipt],
                                            qd[ipt],
                                            g2[ipt],
                                            g2_err[ipt],
                                            b=bounds)
                self.meta['g2_fit_val'][self.target[ipt]] = fit_val
                offset_i = -1 * offset * (ipt + 1)
                err_msg.append(self.target[ipt])
                prev_len = len(err_msg)
                for ifg in range(num_fig):
                    loc = ipt * num_fig + ifg
                    handler.update_lin(loc,
                                       fit_res[ifg]['fit_x'],
                                       fit_res[ifg]['fit_y'] + offset_i,
                                       visible=show_fit)
                    msg = fit_res[ifg]['err_msg']
                    if msg is not None:
                        err_msg.append('----' + msg)

                if len(err_msg) == prev_len:
                    err_msg.append('---- fit finished without errors')

        # x_range = (np.min(tel) / 2.5, np.max(tel) * 2.5)
        x_range = t_range
        handler.auto_scale(ylim=y_range, xlim=x_range)
        handler.fig.tight_layout()
        handler.draw()
        handler.draw()
        return err_msg

    def plot_tauq(self, max_q=0.016, hdl=None, offset=None):
        num_points = len(self.meta['g2_fit_val'])
        if num_points == 0:
            msg = 'g2 fitting not ready'
            self.show_message(msg)
            return [msg]
        labels = list(self.meta['g2_fit_val'].keys())

        # prepare fit values
        fit_val = []
        for _, val in self.meta['g2_fit_val'].items():
            fit_val.append(val)
        fit_val = np.hstack(fit_val).swapaxes(0, 1)
        q = fit_val[::7]
        sl = q[0] <= max_q

        tau = fit_val[1::7]
        cts = fit_val[3::7]

        tau_err = fit_val[4::7]
        cts_err = fit_val[6::7]

        fit_val = []

        if True:
            # if hdl.axes is None:
            hdl.clear()
            ax = hdl.subplots(1, 1)
            line_obj = []
            for n in range(tau.shape[0]):
                s = 10**(offset * n)
                line = ax.errorbar(q[n][sl],
                                   tau[n][sl] / s,
                                   yerr=tau_err[n][sl] / s,
                                   fmt='o-',
                                   markersize=3,
                                   label=self.id_list[n])
                line_obj.append(line)
                slope, intercept, xf, yf = fit_tau(q[n][sl], tau[n][sl],
                                                   tau_err[n][sl])
                line2 = ax.plot(xf, yf / s)
                fit_val.append('fn: %s, slope = %.4f, intercept = %.4f' %
                               (self.target[n], slope, intercept))

            ax.set_xlabel('$q (\\AA^{-1})$')
            ax.set_ylabel('$\\tau \\times 10^4$')
            ax.legend()
            ax.set_xscale('log')
            ax.set_yscale('log')
            hdl.obj = line_obj
            hdl.draw()

            return fit_val

    def plot_saxs_2d(self, *args, **kwargs):
        ans = [self.cache[fn].saxs_2d for fn in self.target]
        saxs2d.plot(ans, *args, **kwargs)

    def plot_saxs_1d(self, mp_hdl, max_points=8, **kwargs):
        xf_list = [self.cache[fn] for fn in self.target[slice(0, max_points)]]
        saxs1d.plot(xf_list, mp_hdl, **kwargs)

    def setup_twotime(self, file_index=0, group='xpcs'):
        fname = self.target[file_index]
        res = []
        with h5py.File(os.path.join(self.cwd, fname), 'r') as f:
            for key in f.keys():
                if 'xpcs' in key:
                    res.append(key)
        return res

    def get_twotime_qindex(self, ix, iy, hdl):
        shape = self.meta['twotime_dqmap'].shape
        if len(hdl.axes[0].patches) >= 1:
            hdl.axes[0].patches.pop()
        if len(hdl.axes[1].patches) >= 1:
            hdl.axes[1].patches.pop()

        h = np.argmin(np.abs(np.arange(shape[1]) - ix))
        v = np.argmin(np.abs(np.arange(shape[0]) - iy))
        mark0 = Circle((ix, iy), radius=5, color='white')
        hdl.axes[0].add_patch(mark0)
        mark1 = Circle((ix, iy), radius=5, color='white')
        hdl.axes[1].add_patch(mark1)
        hdl.draw()
        self.meta['twotime_pos'] = (v, h)

        return self.meta['twotime_dqmap'][v, h]

    def plot_twotime_map(self,
                         hdl,
                         fname=None,
                         group='xpcs',
                         cmap='jet',
                         scale='log',
                         auto_crop=True):
        if fname is None:
            fname = self.target[0]

        if fname == self.meta['twotime_fname'] and \
                group == self.meta['twotime_group']:
            return

        rpath = os.path.join(group, 'output_data')
        rpath = self.get(fname, [rpath], mode='raw')[rpath]

        key_dqmap = os.path.join(group, 'dqmap')
        key_saxs = os.path.join(rpath, 'pixelSum')

        dqmap, saxs = self.get(fname, [key_dqmap, key_saxs], mode='raw',
                               ret_type='list')

        # acquire time scale
        key_frames = [
            os.path.join(group, 'stride_frames'),
            os.path.join(group, 'avg_frames')
        ]
        stride, avg = self.get(fname, key_frames, mode='raw', ret_type='list')
        t0, t1 = self.get_cached(fname, ['t0', 't1'], ret_type='list')
        time_scale = max(t0, t1) * stride * avg

        self.meta['twotime_key'] = rpath
        self.meta['twotime_group'] = group
        self.meta['twotime_scale'] = time_scale

        if self.type == 'Twotime':
            key_c2t = os.path.join(rpath, 'C2T_all')
            id_all = self.get(fname, [key_c2t], mode='raw')[key_c2t]
            self.meta['twotime_idlist'] = [int(x[3:]) for x in id_all]

        if auto_crop:
            idx = np.nonzero(dqmap >= 1)
            sl_v = slice(np.min(idx[0]), np.max(idx[0]))
            sl_h = slice(np.min(idx[1]), np.max(idx[1]))
            dqmap = dqmap[sl_v, sl_h]
            saxs = saxs[sl_v, sl_h]

        if dqmap.shape[0] > dqmap.shape[1]:
            dqmap = np.swapaxes(dqmap, 0, 1)
            saxs = np.swapaxes(saxs, 0, 1)

        self.meta['twotime_dqmap'] = dqmap
        self.meta['twotime_fname'] = fname
        self.meta['twotime_saxs'] = saxs
        self.meta['twotime_ready'] = True

        if scale == 'log':
            saxs = np.log10(saxs + 1)

        hdl.clear()
        ax = hdl.subplots(1, 2, sharex=True, sharey=True)
        im0 = ax[0].imshow(saxs, cmap=plt.get_cmap(cmap))
        im1 = ax[1].imshow(dqmap, cmap=plt.get_cmap(cmap))
        plt.colorbar(im0, ax=ax[0])
        plt.colorbar(im1, ax=ax[1])
        hdl.draw()

    def plot_twotime(self,
                     hdl,
                     current_file_index=0,
                     plot_index=1,
                     cmap='jet'):

        if self.type != 'Twotime':
            self.show_message('Analysis type must be twotime.')
            return None

        if plot_index not in self.meta['twotime_idlist']:
            self.show_message('plot_index is not found.')
            return None

        # check if a twotime selected point is already there; if so
        if 'twotime_pos' not in self.meta or self.meta['twotime_dqmap'][
                self.meta['twotime_pos']] != plot_index:
            v, h = np.where(self.meta['twotime_dqmap'] == plot_index)
            ret = (np.mean(v), np.mean(h))
        else:
            ret = None

        c2_key = os.path.join(self.meta['twotime_key'],
                              'C2T_all/g2_%05d' % plot_index)

        labels = ['g2_full', 'g2_partials']

        res = self.fetch(labels, [self.target[current_file_index]])
        c2 = self.get(self.target[current_file_index], [c2_key], mode='raw')

        c2_half = c2[c2_key]

        if c2_half is None:
            return None

        c2 = c2_half + np.transpose(c2_half)
        c2_translate = np.zeros(c2.shape)
        c2_translate[:, 0] = c2[:, -1]
        c2_translate[:, 1:] = c2[:, :-1]

        c2 = np.where(c2 > 1.3, c2_translate, c2)

        t = self.meta['twotime_scale'] * np.arange(len(c2))
        t_min = np.min(t)
        t_max = np.max(t)

        hdl.clear()
        ax = hdl.subplots(1, 2)
        im = ax[0].imshow(c2,
                          interpolation='none',
                          origin='lower',
                          extent=([t_min, t_max, t_min, t_max]),
                          cmap=plt.get_cmap(cmap))
        plt.colorbar(im, ax=ax[0])
        ax[0].set_ylabel('t1 (s)')
        ax[0].set_xlabel('t2 (s)')

        # the first element in the list seems to deviate from the rest a lot
        g2f = res['g2_full'][0][:, plot_index - 1][1:]
        g2p = res['g2_partials'][0][:, :, plot_index - 1].T
        g2p = g2p[:, 1:]

        t = self.meta['twotime_scale'] * np.arange(g2f.size)
        ax[1].plot(t, g2f, lw=3, color='blue', alpha=0.5)
        for n in range(g2p.shape[0]):
            t = self.meta['twotime_scale'] * np.arange(g2p[n].size)
            ax[1].plot(t, g2p[n], label='partial%d' % n, alpha=0.5)
        ax[1].set_xscale('log')
        ax[1].set_ylabel('g2')
        ax[1].set_xlabel('t (s)')
        hdl.fig.tight_layout()

        hdl.draw()

        return ret

    def plot_intt(self, pg_hdl, max_points=128, **kwargs):
        xf_list = self.get_xf_list(max_points)
        intt.plot(xf_list, pg_hdl, self.target, **kwargs)

    def plot_stability(self, mp_hdl, plot_id, **kwargs):
        fc = self.cache[self.target[plot_id]]
        stability.plot(fc, mp_hdl, **kwargs)

    def average_plot_outlier(self,
                             hdl1,
                             hdl2,
                             target='g2',
                             avg_blmin=0.95,
                             avg_blmax=1.05,
                             avg_qindex=5,
                             avg_window=10):

        if self.meta['avg_file_list'] != tuple(self.target) or \
                'avg_g2' not in self.meta:
            logger.info('avg cache not exist')
            labels = ['g2']

            g2 = self.fetch(labels, file_list=self.target)['g2']

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

        hdl2.show_lines(g2_avg,
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
