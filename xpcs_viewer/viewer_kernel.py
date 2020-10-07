import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.patches import Circle
from helper.fitting import fit_xpcs, fit_tau
from fileIO.file_locator import FileLocator
from mpl_cmaps_in_ImageItem import pg_get_cmap

from PyQt5 import QtCore
from shutil import copyfile
from sklearn.cluster import KMeans as sk_kmeans
import h5py

import os
import logging

logging_format = '%(asctime)s %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


def get_min_max(data, min_percent=0, max_percent=100, **kwargs):
    vmin = np.percentile(data.ravel(), min_percent)
    vmax = np.percentile(data.ravel(), max_percent)

    if 'plot_norm' in kwargs and 'plot_type' in kwargs:
        if kwargs['plot_norm'] == 3:
            if kwargs['plot_type'] == 'log':
                t = max(abs(vmin), abs(vmax))
                vmin, vmax = -t, t
            else:
                t = max(abs(1 - vmin), abs(vmax - 1))
                vmin, vmax = 1 - t, 1 + t

    return vmin, vmax


def norm_saxs_data(Iq, q, plot_norm=0, plot_type='log'):
    ylabel = 'Intensity'
    if plot_norm == 1:
        Iq = Iq * np.square(q)
        ylabel = ylabel + ' * q^2'
    elif plot_norm == 2:
        Iq = Iq * np.square(np.square(q))
        ylabel = ylabel + ' * q^4'
    elif plot_norm == 3:
        baseline = Iq[0]
        Iq = Iq / baseline
        ylabel = ylabel + ' / I_0'

    xlabel = '$q (\\AA^{-1})$'
    return Iq, xlabel, ylabel


def create_slice(arr, x_range):
    start, end = 0, arr.size - 1
    while arr[start] < x_range[0]:
        start += 1
        if start == arr.size:
            break

    while arr[end] >= x_range[1]:
        end -= 1
        if end == 0:
            break

    return slice(start, end + 1)


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
        elif max_points <= 0:   # use all items
            val = hash(tuple(self.target))
        else:
            val = hash(tuple(self.target[0: max_points]))
        return val

    def get_g2_data(self, max_points=10, q_range=None, t_range=None):
        labels = ["saxs_1d", 'g2', 'g2_err', 't_el', 'ql_sta', 'ql_dyn']
        file_list = self.target

        hash_val = self.hash(max_points)
        if self.meta['g2_hash_val'] == hash_val:
            res = self.meta['g2_res']
        else:
            res = self.get_list(labels, file_list[0: max_points])
            self.meta['g2_hash_val'] = hash_val
            self.meta['g2_res'] = res

        tslice = create_slice(res['t_el'][0], t_range)
        qslice = create_slice(res['ql_dyn'][0], q_range)

        tel = res['t_el'][0][tslice]
        qd = res['ql_dyn'][0][qslice]
        g2 = res['g2'][:, tslice, qslice]
        g2_err = res['g2_err'][:, tslice, qslice]

        return tel, qd, g2, g2_err

    def plot_g2_initialize(self, mp_hdl, num_fig, num_points, num_col=4,
                           show_label=False):
        # adjust canvas size according to number of images
        if num_fig < num_col:
            num_col = num_fig
        num_row = (num_fig + num_col - 1) // num_col
        if mp_hdl.parent().parent() is None:
            aspect = 1 / 1.618
            logger.info('using static aspect ratio')
            min_size = 740
        else:
            t = mp_hdl.parent().parent().parent()
            aspect = t.height() / mp_hdl.width()
            logger.info('using dynamic aspect ratio')
            min_size = t.height() - 20

        width = mp_hdl.width()
        # height = mp_hdl.height()
        logger.info('aspect: {}'.format(aspect))
        canvas_size = max(min_size, int(width / num_col * aspect * num_row))
        logger.info('row, col: ({}, {})'.format(num_row, num_col))
        logger.info('canvas size: ({}, {})'.format(width, canvas_size))
        # canvas_size = min(height,  250 * num_row)
        mp_hdl.setMinimumSize(QtCore.QSize(0, canvas_size))
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
                obj1 = ax.errorbar(x, y + offset,
                                   yerr=err, fmt='o', markersize=3,
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
                    if show_label and i == num_fig -1:
                    # if idx >= 1 and num_points < 10:
                         ax.legend(fontsize=8)

        # mp_hdl.fig.tight_layout()
        mp_hdl.obj = {
            'err': err_obj,
            'lin': lin_obj,
        }

    def plot_g2(self, handler, q_range=None, t_range=None, y_range=None,
                offset=None, show_fit=False, max_points=50, bounds=None,
                show_label=False, num_col=4, aspect=(1/1.618)):

        num_points = min(len(self.target), max_points)
        new_condition = (tuple(self.target[:num_points]),
                         (q_range, t_range, y_range, offset),
                         bounds)
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
        num_fig = g2.shape[2]

        plot_target = 4
        if plot_target >= 2 or handler.axes is None:
            self.plot_g2_initialize(handler, num_fig, num_points,
                                    show_label=show_label, num_col=num_col)

        # if plot_target >= 2:
        if True:
            for ipt in range(num_points):
                for ifg in range(num_fig):
                    # add the title
                    if ipt == 0:
                        ax = np.array(handler.axes).ravel()[ifg]
                        ax.set_title('Q=%.4f $\\AA^{-1}$' % qd[ifg])
                    # update info
                    loc = ipt * num_fig + ifg
                    offset_i = -1 * offset * (ipt + 1)
                    handler.update_err(loc, tel, g2[ipt][:, ifg] + offset_i,
                                       g2_err[ipt][:, ifg])

        err_msg = []
        if show_fit:
            for ipt in range(num_points):
                fit_res, fit_val = fit_xpcs(tel, qd, g2[ipt], g2_err[ipt],
                                            b=bounds)
                self.meta['g2_fit_val'][self.target[ipt]] = fit_val
                offset_i = -1 * offset * (ipt + 1)
                err_msg.append(self.target[ipt])
                prev_len = len(err_msg)
                for ifg in range(num_fig):
                    loc = ipt * num_fig + ifg
                    handler.update_lin(loc, fit_res[ifg]['fit_x'],
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
            # for n in range(tau.shape[0]):
            for n in range(tau.shape[0]):
                s = 10 ** (offset * n)
                line = ax.errorbar(q[n][sl], tau[n][sl] / s,
                                   yerr=tau_err[n][sl] / s,
                                   fmt='o-', markersize=3,
                                   label=self.id_list[n]
                                   )
                line_obj.append(line)
                slope, intercept, xf, yf = fit_tau(q[n][sl], tau[n][sl],
                                                   tau_err[n][sl])
                line2 = ax.plot(xf, yf / s)
                fit_val.append('fn: %s, slope = %.4f, intercept = %.4f' % (
                               self.target[n], slope, intercept))

            ax.set_xlabel('$q (\\AA^{-1})$')
            ax.set_ylabel('$\\tau \\times 10^4$')
            ax.legend()
            ax.set_xscale('log')
            ax.set_yscale('log')
            hdl.obj = line_obj
            hdl.draw()

            return fit_val

    def get_detector_extent(self, file_list):
        labels = ['ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim', 'X_energy',
                  'xdim', 'ydim']
        res = self.get_list(labels, file_list)
        extents = []
        for n in range(len(file_list)):
            pix2q = res['pix_dim'][n] / res['det_dist'][n] * \
                    (2 * np.pi / (12.398 / res['X_energy'][n]))

            qy_min = (0 - res['ccd_x0'][n]) * pix2q
            qy_max = (res['xdim'][n] - res['ccd_x0'][n]) * pix2q

            qx_min = (0 - res['ccd_y0'][n]) * pix2q
            qx_max = (res['ydim'][n] - res['ccd_y0'][n]) * pix2q
            temp = (qy_min, qy_max, qx_min, qx_max)

            extents.append(temp)

        return extents

    def plot_saxs_2d_mpl(self, mp_hdl=None, scale='log', max_points=8):
        extents = self.get_detector_extent(self.target)
        res = self.get_saxs_data()
        ans = res['saxs_2d']
        if scale == 'log':
            ans = np.log10(ans + 1E-8)
        num_fig = min(max_points, len(extents))
        num_col = (num_fig + 1) // 2
        ax_shape = (2, num_col)

        if mp_hdl.axes is not None and mp_hdl.axes.shape == ax_shape:
            axes = mp_hdl.axes
            for n in range(num_fig):
                img = mp_hdl.obj[n]
                img.set_data(ans[n])
                ax = axes.flatten()[n]
                ax.set_title(self.id_list[n])
        else:
            mp_hdl.clear()
            axes = mp_hdl.subplots(2, num_col, sharex=True, sharey=True)
            img_obj = []
            for n in range(num_fig):
                ax = axes.flatten()[n]
                img = ax.imshow(ans[n], cmap=plt.get_cmap('jet'),
                                # norm=LogNorm(vmin=1e-7, vmax=1e-4),
                                interpolation=None,
                                extent=extents[n])
                img_obj.append(img)
                ax.set_title(self.id_list[n])
                # ax.axis('off')
            mp_hdl.obj = img_obj
            mp_hdl.fig.tight_layout()
        mp_hdl.draw()

    def plot_saxs_2d(self, pg_hdl, plot_type='log', cmap='jet',
                     autorotate=False):

        ans = self.get_saxs_data()['saxs_2d']
        if plot_type == 'log':
            ans = np.log10(ans + 0.001)

        ans = ans.astype(np.float32)

        if autorotate is True:
            if ans.shape[1] > ans.shape[2]:
                ans = ans.swapaxes(1, 2)

        sp = ans.T.shape

        pg_cmap = pg_get_cmap(plt.get_cmap(cmap))
        pg_hdl.setColorMap(pg_cmap)

        if ans.shape[0] > 1:
            xvals = np.arange(ans.shape[0])
            pg_hdl.setImage(ans.swapaxes(1, 2), xvals=xvals)
        else:
            pg_hdl.setImage(ans[0].swapaxes(0, 1))

        # pg_hdl.getFrame
        fs = pg_hdl.frameSize()
        w0, h0 = fs.width(), fs.height()
        w1, h1 = sp[0], sp[1]

        if w1 / w0 > h1 / h0:
            # the fig is wider than the canvas
            margin_v = int((w1 / w0 * h0 - h1) / 2)
            margin_h = 0
        else:
            # the canvas is wider than the figure
            margin_v = 0
            margin_h = int((h1 / h0 * w0 - w1) / 2)

        vb = pg_hdl.getView()
        vb.setLimits(xMin=-1 * margin_h,
                     yMin=-1 * margin_v,
                     xMax=1 * sp[0] + margin_h,
                     yMax=1 * sp[1] + margin_v,
                     minXRange=sp[0] // 10,
                     minYRange=int(sp[0] / 10 / w0 * h0))
        vb.setAspectLocked(1.0)
        vb.setMouseMode(vb.RectMode)


    def plot_saxs_1d(self, mp_hdl, **kwargs):
        res = self.get_saxs_data(max_points=8)
        q = res['ql_sta'][0]
        Iq = res["saxs_1d"]
        sl = slice(0, min(q.size, Iq.shape[1]))
        self.plot_saxs_line(mp_hdl, q[sl], Iq[:, sl],
                            legend=self.target, **kwargs)

    def plot_saxs_line(self, mp_hdl, q, Iq, plot_type='log', plot_norm=0,
                       plot_offset=0, max_points=8, legend=None, title=None):

        Iq, xlabel, ylabel = norm_saxs_data(Iq, q, plot_norm, plot_type)
        xscale = ['linear', 'log'][plot_type % 2]
        yscale = ['linear', 'log'][plot_type // 2]

        num_points = min(len(self.target), max_points)
        for n in range(1, num_points):
            if yscale == 'linear':
                offset = -plot_offset * n * np.max(Iq[n])
                Iq[n] = offset + Iq[n]

            elif yscale == 'log':
                offset = 10 ** (plot_offset * n)
                Iq[n] = Iq[n] / offset

        mp_hdl.show_lines(Iq, xval=q, xlabel=xlabel,
                              ylabel=ylabel, legend=legend)

        mp_hdl.axes.legend()
        mp_hdl.axes.set_xlabel(xlabel)
        mp_hdl.axes.set_ylabel(ylabel)
        mp_hdl.axes.set_title(title)
        mp_hdl.auto_scale(xscale=xscale, yscale=yscale)
        mp_hdl.draw()
        return

    def get_saxs_data(self, max_points=1024):
        labels = ['saxs_2d', "saxs_1d", 'ql_sta']
        file_list = self.target[0: max_points]
        res = self.get_list(labels, file_list)
        # ans = np.swapaxes(ans, 1, 2)
        # the detector figure is not oriented to image convention;
        return res

    def get_stability_data(self, max_point=128, plot_id=0):
        # labels = ['Int_t', "saxs_1d", 'ql_sta']
        labels = ['Iqp', 'ql_sta']
        res = self.get_list(labels, [self.target[plot_id]])
        q = res["ql_sta"][0]
        Iqp = res["Iqp"][0]
        # res["Iqp"] = np.flipud(Iqp).astype(np.float32)
        return q, Iqp

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

        return self.meta['twotime_dqmap'][v, h]

    def plot_twotime_map(self, hdl, fname=None, group='xpcs', cmap='jet',
                         scale='log', auto_crop=True):
        if fname is None:
            fname = self.target[0]

        if fname == self.meta['twotime_fname'] and \
                group == self.meta['twotime_group']:
            return

        rpath = os.path.join(group, 'output_data')
        rpath = self.get(fname, [rpath], 'raw')[rpath]

        key_dqmap = os.path.join(group, 'dqmap')
        key_saxs = os.path.join(rpath, 'pixelSum')

        dqmap, saxs = self.get(fname, [key_dqmap, key_saxs], 'raw',
                               ret_type='list')

        # acquire time scale
        key_frames = [os.path.join(group, 'stride_frames'),
                      os.path.join(group, 'avg_frames')]
        stride, avg = self.get(fname, key_frames, 'raw', ret_type='list')
        t0, t1 = self.get_cached(fname, ['t0', 't1'], ret_type='list')
        time_scale = max(t0, t1) * stride * avg

        self.meta['twotime_key'] = rpath
        self.meta['twotime_group'] = group
        self.meta['twotime_scale'] = time_scale

        if self.type == 'Twotime':
            key_c2t = os.path.join(rpath, 'C2T_all')
            print(key_c2t)
            id_all = self.get(fname, [key_c2t], 'raw')[key_c2t]
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
        im1 = ax[1].imshow(dqmap,  cmap=plt.get_cmap(cmap))
        plt.colorbar(im0, ax=ax[0])
        plt.colorbar(im1, ax=ax[1])
        hdl.draw()

    def plot_twotime(self, hdl, current_file_index=0, plot_index=1,
                     cmap='jet'):

        if self.type != 'Twotime':
            self.show_message('Analysis type must be twotime.')
            return

        if plot_index not in self.meta['twotime_idlist']:
            self.show_message('plot_index is not found.')
            return

        c2_key = os.path.join(self.meta['twotime_key'],
                              'C2T_all/g2_%05d' % plot_index)

        labels = ['g2_full', 'g2_partials']

        res = self.get_list(labels, [self.target[current_file_index]])
        c2 = self.get(self.target[current_file_index], [c2_key],
                      mode='raw')

        c2_half = c2[c2_key]

        if c2_half is None:
            return

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
        im = ax[0].imshow(c2, interpolation='none', origin='lower',
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

    def plot_intt(self, pg_hdl, max_points=128, window=5, sampling=-1):
        labels = ['Int_t', 't0']
        num_points = min(max_points, len(self.target))

        res = self.get_list(labels, self.target[0: num_points])
        t0 = self.get_cached(self.target[0], ['t0'], ret_type='list')[0]
        y = res["Int_t"][:, 1, :]

        if window > 1:
            y = np.cumsum(y, dtype=float, axis=1)
            y = (y[:, window:] - y[:, :-window]) / window

        if sampling > 0:
            y = y[:, ::sampling]
        else:
            sampling = 1

        x = (np.arange(y.shape[1]) * sampling * t0).astype(np.float32)

        pg_hdl.clear()
        pg_hdl.show_lines(y, xval=x, xlabel="Time (s)",
                          ylabel="Intensity (ph/pixel)",
                          loc='lower right', alpha=0.5,
                          legend=self.target)
        pg_hdl.draw()

    def plot_stability(self, mp_hdl, plot_id, method='1d', **kwargs):

        q, Iqp = self.get_stability_data(plot_id)
        sl = slice(0, min(q.size, Iqp.shape[1]))
        q = q[sl]
        Iqp = Iqp[:, sl]
        if method == '1d':
            self.plot_saxs_line(mp_hdl, q, Iqp, legend=None,
                                title=self.target[plot_id], **kwargs)
        # else:
        #     Iqp_vmin, Iqp_vmax = get_min_max(Iqp, 1, 99, **kwargs)

        #     if seg_len >= Iqp.shape[1]:
        #         title = 'Single-Scan SAXS:'
        #         xlabel = 'Segment'
        #         extent = (-0.5, Iqp.shape[1] - 0.5, np.min(q), np.max(q))
        #     else:
        #         title = 'Multi-Scan SAXS:'
        #         xlabel = 'Scan number (each has %d segments)' % seg_len
        #         extent = (-0.5, Iqp.shape[1] // seg_len - 0.5,
        #                   np.min(q), np.max(q))

        #     mp_hdl.show_image(Iqp, vmin=Iqp_vmin, vmax=Iqp_vmax,
        #                       vline_freq=1,
        #                       extent=extent,
        #                       title=title + ylabel,
        #                       ylabel=qlabel,
        #                       xlabel=xlabel)

    def average_plot_outlier(self, hdl1, hdl2,
                             target='g2', avg_blmin=0.95, avg_blmax=1.05,
                             avg_qindex=5, avg_window=10):

        if self.meta['avg_file_list'] != tuple(self.target):
            logger.info('avg cache not exist')
            labels = ['g2']

            g2 = self.get_list(labels, file_list=self.target)['g2']

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

        hdl2.show_lines(g2_avg, xlabel='index', ylabel='g2 average',
                        legend=legend, title=title)

    def average_plot_v0(self, hdl1, hdl2, num_clusters=2, g2_cutoff=1.03,
                                 target='g2'):
        if self.meta['avg_file_list'] != tuple(self.target):
            logger.info('avg cache not exist')
            labels = ['Int_t', 'g2']
            res = self.get_list(labels, file_list=self.target)
            Int_t = res['Int_t'][:, 1, :].astype(np.float32)
            Int_t = Int_t / np.max(Int_t)
            intt_minmax = []
            for n in range(len(self.target)):
                intt_minmax.append([np.min(Int_t[n]), np.max(Int_t[n])])
            intt_minmax = np.array(intt_minmax).T.astype(np.float32)
            g2_avg = np.mean(res['g2'][:, -10:, 1], axis=1)
            cutoff_line = np.ones_like(g2_avg) * g2_cutoff
            g2_avg = np.vstack([g2_avg, cutoff_line])

            self.meta['avg_file_list'] = tuple(self.target)
            self.meta['avg_intt_minmax'] = intt_minmax
            self.meta['avg_g2_avg'] = g2_avg
            self.meta['avg_intt_mask'] = np.ones(len(self.target))
            self.meta['avg_g2_mask'] = np.ones(len(self.target))
        else:
            logger.info('using avg cache')
            intt_minmax = self.meta['avg_intt_minmax']
            g2_avg = self.meta['avg_g2_avg']

        if target == 'intt':
            y_pred = sk_kmeans(n_clusters=num_clusters).fit_predict(intt_minmax.T)
            freq = np.bincount(y_pred)
            self.meta['avg_intt_mask'] = y_pred == y_pred[freq.argmax()]
            valid_num = np.sum(y_pred == y_pred[freq.argmax()])
            title = '%d / %d' % (valid_num, y_pred.size)
            hdl1.show_scatter(intt_minmax, color=y_pred, xlabel='Int-t min',
                              ylabel='Int-t max', title=title)
        elif target == 'g2':
            self.meta['avg_g2_mask'] = g2_avg[0] >= g2_cutoff
            g2_avg[1, :] = g2_cutoff
            valid_num = np.sum(g2_avg[0] >= g2_cutoff)
            legend = ['data', 'cutoff']
            title = '%d / %d' % (valid_num, g2_avg.shape[1])
            hdl2.show_lines(g2_avg, xlabel='index', ylabel='g2 average',
                            legend=legend, title=title)
        else:
            return

    def average(self, chunk_size=256, save_path=None, origin_path=None,
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
            values = self.get_list(labels, file_list=self.target[sl],
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
    dv.average()
    # dv.plot_g2()