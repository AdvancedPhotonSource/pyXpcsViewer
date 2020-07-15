import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from xpcs_fitting import fit_xpcs, fit_tau
from file_locator import FileLocator
from mpl_cmaps_in_ImageItem import pg_get_cmap
from hdf_to_str import get_hdf_info
from hdf_reader import read_file
from PyQt5 import QtCore

import os
import h5py
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
    ylabel = 'I'
    if plot_norm == 1:
        Iq = Iq * np.square(q)
        ylabel = ylabel + 'q^2'
    elif plot_norm == 2:
        Iq = Iq * np.square(np.square(q))
        ylabel = ylabel + 'q^4'
    elif plot_norm == 3:
        baseline = Iq[0]
        Iq = Iq / baseline
        ylabel = ylabel + '/I_0'

    # if plot_type == 'log':
    #     Iq = np.log10(Iq)
    #     ylabel = '$log(%s)$' % ylabel
    # else:
    #     ylabel = '$%s$' % ylabel

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


class DataLoader(FileLocator):
    def __init__(self, path):
        super().__init__(path)
        # self.target_list
        self.g2_cache = {
            'num_points': None,
            'hash_val': None,
            'res': None,
            'plot_condition': tuple([None, None, None]),
            'fit_val': {}
        }
        self.stab_cache = {
            'num_points': None
        }


    def hash(self, max_points=10):
        if self.target_list is None:
            return hash(None)
        elif max_points <= 0:   # use all items
            val = hash(tuple(self.target_list))
        else:
            val = hash(tuple(self.target_list[0: max_points]))
        return val

    def get_hdf_info(self, fname):
        if not os.path.isfile(os.path.join(self.cwd, fname)):
            return ['None']
        return get_hdf_info(self.cwd, fname)

    def get_g2_data(self, max_points=10, q_range=None, t_range=None):
        labels = ['Iq', 'g2', 'g2_err', 't_el', 'ql_sta', 'ql_dyn']
        file_list = self.target_list

        hash_val = self.hash(max_points)
        if self.g2_cache['hash_val'] == hash_val:
            res = self.g2_cache['res']
        else:
            res = self.read_data(labels, file_list[0: max_points])
            self.g2_cache['hash_val'] = hash_val
            self.g2_cache['res'] = res

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
        if num_fig == 1:
            num_col = 1
        num_row = (num_fig + num_col - 1) // num_col


        width = mp_hdl.width()
        # height = mp_hdl.height()
        canvas_size = max(750, int(width / num_col / 1.618 * num_row))
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
                show_label=False, num_col=4):

        msg = self.check_target()
        if msg != True:
            return msg

        num_points = min(len(self.target_list), max_points)
        new_condition = (tuple(self.target_list[:num_points]),
                         (q_range, t_range, y_range, offset),
                         bounds)
        # if self.g2_cache['plot_condition'] == new_condition:
        #     return ['No target files selected or change in setting.']
        # else:
        #     cmp = tuple(i != j for i, j in
        #                 zip(new_condition, self.g2_cache['plot_condition']))
        #     self.g2_cache['plot_condition'] = new_condition
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
                self.g2_cache['fit_val'][self.target_list[ipt]] = fit_val
                offset_i = -1 * offset * (ipt + 1)
                err_msg.append(self.target_list[ipt])
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

        x_range = (np.min(tel) / 2.5, np.max(tel) * 2.5)
        handler.auto_scale(ylim=y_range, xlim=x_range)
        handler.fig.tight_layout()
        handler.draw()
        handler.draw()
        return err_msg

    def plot_tauq(self, max_q=0.016, hdl=None, offset=None):
        num_points = len(self.g2_cache['fit_val'])
        if num_points == 0:
            return ['g2 fitting not ready']
        labels = list(self.g2_cache['fit_val'].keys())

        # prepare fit values
        fit_val = []
        for _, val in self.g2_cache['fit_val'].items():
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
                               self.target_list[n], slope, intercept))

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
        res = self.read_data(labels, file_list)
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
        extents = self.get_detector_extent(self.target_list)
        res = self.get_saxs_data()
        ans = res['Int_2D']
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
        msg = self.check_target()
        if msg != True:
            return msg
        ans = self.get_saxs_data()['Int_2D']
        if plot_type == 'log':
            ans = np.log10(ans + 1E-8)

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
        vb.setLimits(xMin= -1 * margin_h,
                     yMin= -1 * margin_v,
                     xMax= 1 * sp[0] + margin_h,
                     yMax= 1 * sp[1] + margin_v,
                     minXRange=sp[0] // 10,
                     minYRange=int(sp[0] / 10 / w0 * h0))
        vb.setAspectLocked(1.0)
        vb.setMouseMode(vb.RectMode)
        # minYRange=sp[1] // 10)
        # maxXRange=sp[0] * 4,
                     # maxYRange=sp[1] * 4)

    def plot_saxs_1d(self, mp_hdl, plot_type='log', plot_norm=0,
                     plot_offset=0, max_points=8):
        msg = self.check_target()
        if msg != True:
            return msg

        num_points = min(len(self.target_list), max_points)
        res = self.get_saxs_data()
        q = res['ql_sta']
        Iq = res['Iq']

        Iq, xlabel, ylabel = norm_saxs_data(Iq, q, plot_norm, plot_type)
        xscale = ['linear', 'log'][plot_type % 2]
        yscale = ['linear', 'log'][plot_type // 2]

        if mp_hdl.shape == (1, 1) and len(mp_hdl.obj) == num_points:
            for n in range(num_points):
                line = mp_hdl.obj[n]
                if yscale == 'linear':
                    offset = -plot_offset * (n + 1) * np.max(Iq[n])
                    line.set_data(q[n], Iq[n] + offset)
                else:
                    offset = 10 ** (plot_offset * (n + 1))
                    line.set_data(q[n], Iq[n] * offset)

                line.set_label(self.target_list[n])
        else:
            mp_hdl.clear()
            ax = mp_hdl.subplots(1, 1)
            lin_obj = []
            for n in range(num_points):
                if yscale == 'linear':
                    offset = -plot_offset * (n + 1) * np.max(Iq[n])
                    line, = ax.plot(q[n], Iq[n] + offset, 'o--', lw=0.5,
                                    alpha=0.8, markersize=2,
                                    label=self.target_list[n])
                else:
                    offset = 10 ** (plot_offset * (n + 1))
                    line, = ax.plot(q[n], Iq[n] * offset, 'o--', lw=0.5,
                                    alpha=0.8, markersize=2,
                                    label=self.target_list[n])

                lin_obj.append(line)
            mp_hdl.obj = lin_obj

        mp_hdl.axes.legend()
        mp_hdl.axes.set_xlabel(xlabel)
        mp_hdl.axes.set_ylabel(ylabel)
        mp_hdl.auto_scale(xscale=xscale, yscale=yscale)

        # do not use tight layout because the ylabel may not display fully.
        # mp_hdl.fig.tight_layout()
        mp_hdl.draw()
        return

    def get_saxs_data(self, max_points=128):
        labels = ['Int_2D', 'Iq', 'ql_sta']
        file_list = self.target_list[0: max_points]
        res = self.read_data(labels, file_list)
        # ans = np.swapaxes(ans, 1, 2)
        # the detector figure is not oriented to image convention;
        return res

    def get_stability_data(self, max_point=128, plot_id=0, **kwargs):
        # labels = ['Int_t', 'Iq', 'ql_sta']
        labels = ['Iqp', 'ql_sta']
        res = self.read_data(labels, [self.target_list[plot_id]])
        # avg_size = (res['Int_t'].shape[2] + max_point - 1) // max_point
        # int_t = res['Int_t'][:, 1, :]
        # int_t = int_t / np.mean(int_t)
        # cum_int = np.cumsum(int_t, axis=1)
        # mean_int = np.diff(cum_int[:, ::avg_size]) / avg_size
        # res['Int_t'] = mean_int

        q = res["ql_sta"][0]
        seg_len = res["Iqp"].shape[1]
        # Iqp = res["Iqp"][0: max_point].reshape(-1, len(q))
        Iqp = res["Iqp"][0].reshape(-1, len(q))
        Iqp, xlabel, ylabel = norm_saxs_data(Iqp, q, **kwargs)

        # switch axes and flip ud so the image has high q on the top
        Iqp = Iqp.swapaxes(0, 1)
        res["Iqp"] = np.flipud(Iqp).astype(np.float32)

        return res, xlabel, ylabel, seg_len

    def check_target(self):
        if self.target_list is None or len(self.target_list) < 1:
            return ['No target files selected.']
        else:
            return True

    def plot_stability(self, mp_hdl, plot_id, **kwargs):
        msg = self.check_target()
        if msg != True:
            return msg

        res, qlabel, ylabel, seg_len = self.get_stability_data(plot_id,
                                                               **kwargs)

        if self.stab_cache['num_points'] != res['ql_sta'].shape[0]:
            self.stab_cache['num_points'] = res['ql_sta'].shape[0]
            mp_hdl.clear()

        q = res['ql_sta'][0]
        Iqp = res['Iqp']

        Iqp_vmin, Iqp_vmax = get_min_max(Iqp, 1, 99, **kwargs)

        if seg_len >= Iqp.shape[1]:
            title = 'Single-Scan SAXS:'
            xlabel = 'Segment'
            extent = (-0.5, Iqp.shape[1] - 0.5, np.min(q), np.max(q))
        else:
            title = 'Multi-Scan SAXS:'
            xlabel = 'Scan number (each has %d segments)' % seg_len
            extent = (-0.5, Iqp.shape[1] // seg_len - 0.5,
                      np.min(q), np.max(q))

        # mp_hdl.show_image(Iqp, vmin=Iqp_vmin, vmax=Iqp_vmax,
        #                   vline_freq=1,
        #                   extent=extent,
        #                   title=title + ylabel,
        #                   ylabel=qlabel,
        #                   xlabel=xlabel)
        mp_hdl.show_lines(np.fliplr(Iqp.T), xval=q, xlabel=qlabel,
                          ylabel=ylabel, legend=True)

        mp_hdl.axes.set_yscale(kwargs['plot_type'])
        mp_hdl.axes.set_title(self.target_list[plot_id])
        mp_hdl.draw()


    def read_data(self, labels, file_list=None, mask=None):
        if file_list is None:
            file_list = self.target_list

        if mask is None:
            mask = np.ones(shape=len(file_list), dtype=np.bool)

        data = []
        for n, fn in enumerate(file_list):
            if mask[n]:
                data.append(read_file(labels, fn, self.cwd))

        np_data = {}
        for n, label in enumerate(labels):
            temp = [x[n] for x in data]
            np_data[label] = np.array(temp)

        return np_data

    def average(self, baseline=1.03, chunk_size=256):
        labels = ['Iq', 'g2', 'g2_err', 'Int_2D']
        g2 = self.read_data(['g2'], self.target_list)['g2']
        mask = np.mean(g2[:, -10:, 1], axis=1) < baseline

        steps = (len(mask) + chunk_size - 1) // chunk_size
        result = {}
        for n in range(steps):
            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(len(mask), end)
            slice0 = slice(beg, end)
            values = self.read_data(labels, file_list=self.target_list[slice0],
                                    mask=mask[slice0])
            if n == 0:
                for label in labels:
                    result[label] = np.sum(values[label], axis=0)
            else:
                for label in labels:
                    result[label] += np.sum(values[label], axis=0)

        num_points = np.sum(mask)
        for label in labels:
            result[label] = result[label] / num_points

        return result


if __name__ == "__main__":
    flist = os.listdir('./data')
    dv = DataLoader('./data', flist)
    dv.average()
    # dv.plot_g2()
