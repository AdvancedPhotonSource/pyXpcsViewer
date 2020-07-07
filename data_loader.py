import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplot_qt import MplCanvas
from matplotlib.ticker import FormatStrFormatter
from xpcs_fitting import fit_xpcs
from file_locator import FileLocator
import pyqtgraph as pg
from mpl_cmaps_in_ImageItem import pg_get_cmap
from hdf_to_str import get_hdf_info


import os
import h5py

hdf_dict = {
    'Iq': '/exchange/partition-mean-total',
    'ql_sta': '/xpcs/sqlist',
    'ql_dyn': '/xpcs/dqlist',
    't0': '/measurement/instrument/detector/exposure_period',
    'tau': '/exchange/tau',
    'g2': '/exchange/norm-0-g2',
    'g2_err': '/exchange/norm-0-stderr',
    'Int_2D': '/exchange/pixelSum',
    'Int_t': '/exchange/frameSum',
    'ccd_x0': '/measurement/instrument/acquisition/beam_center_x',
    'ccd_y0': '/measurement/instrument/acquisition/beam_center_y',
    'det_dist': '/measurement/instrument/detector/distance',
    'pix_dim': '/measurement/instrument/detector/x_pixel_size',
    'X_energy': '/measurement/instrument/source_begin/energy',
    'xdim': '/measurement/instrument/detector/x_dimension',
    'ydim': '/measurement/instrument/detector/y_dimension'
}

avg_hdf_dict = {
    'Iq': '/Iq_ave',
    'g2': '/g2_ave',
    'g2_nb': '/g2_ave_nb',
    'g2_err': '/g2_ave_err',
    'fn_count': '/fn_count',
    't_el': '/t_el',
    'ql_sta': '/ql_sta',
    'ql_dyn': '/ql_dyn',
    'Int_2D': '/Int_2D_ave',
}


def read_file(fields, fn, prefix='./data'):
    res = []
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        for field in fields:
            if field == 't_el':
                val1 = np.squeeze(HDF_Result.get(hdf_dict['t0']))
                val2 = np.squeeze(HDF_Result.get(hdf_dict['tau']))
                val = val1 * val2
            else:
                if field in hdf_dict.keys():
                    link = hdf_dict[field]
                    if link in HDF_Result.keys():
                        val = np.squeeze(HDF_Result.get(link))
                    else:
                        link = avg_hdf_dict[field]
                        val = np.squeeze(HDF_Result.get(link))
            res.append(val)
    return res


def create_slice(arr, cutoff):
    id = arr <= cutoff
    end = np.argmin(id)
    if end == 0 and arr[-1] < cutoff:
        end = len(arr)
    return slice(0, end)


class DataLoader(FileLocator):
    def __init__(self, path):
        super().__init__(path)
        # self.target_list
        self.g2_cache = {
            'num_points': None,
            'hash_val': None,
            'res': None,
            'plot_condition': (None, None)
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
        return get_hdf_info(self.cwd, fname)


    def get_g2_data(self, max_points=10, max_q=1.0, max_tel=1e8):

        labels = ['Iq', 'g2', 'g2_err', 't_el', 'ql_sta', 'ql_dyn']
        file_list = self.target_list

        hash_val = self.hash(max_points)
        if self.g2_cache['hash_val'] == hash_val:
            res = self.g2_cache['res']
        else:
            res = self.read_data(labels, file_list[0: max_points])
            self.g2_cache['hash_val'] = hash_val
            self.g2_cache['res'] = res

        tslice = create_slice(res['t_el'][0], max_tel)
        qslice = create_slice(res['ql_dyn'][0], max_q)

        return res, tslice, qslice

    def create_template_g2(self, handler, ql_dyn, num_points, num_fig=17):
        # dummy line as the place holder
        x = np.logspace(-5, 0, 32)
        y = np.exp(-x / 1E-3) * 0.25 + 1.0
        err = y / 40

        ax_all = handler.axes
        err_obj = []
        lin_obj = []

        for idx in range(num_points):
            for i in range(num_fig):
                offset = 0.03 * idx
                ax = ax_all.ravel()[i]
                obj1 = ax.errorbar(x, y + offset,
                                  yerr=err, fmt='o', markersize=3,
                                  markerfacecolor='none',
                                  label='{}'.format(self.id_list[idx]))
                err_obj.append(obj1)

                obj2 = ax.plot(x, y + offset)
                lin_obj.append(obj2)

                # last image
                if idx == num_points - 1:
                    ax.set_title('Q = %5.4f $\AA^{-1}$' % ql_dyn[i])
                    ax.set_xscale('log')
                    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                    # if there's only one point, do not add title; the title
                    # will be too long.
                    if idx >= 1:
                        ax.legend(fontsize=8)

        handler.fig.tight_layout()
        # handler.draw()
        handler.obj = {
            'err': err_obj,
            'lin': lin_obj,
        }

    def plot_g2(self, max_q=0.016, max_tel=1E8, handler=None,
                offset=None, max_points=3, bounds=None):
        if len(self.target_list) < 1:
            return
        res, tslice, qslice = self.get_g2_data(max_q=max_q, max_tel=max_tel,
                                               max_points=max_points)
        num_points = min(res['g2'].shape[0], max_points)

        t_el = res['t_el'][0][tslice]
        g2 = res['g2'][:, tslice, qslice]
        g2_err = res['g2_err'][:, tslice, qslice]

        num_fig = qslice.stop

        new_condition = ((max_q, max_tel, offset), bounds)

        if self.g2_cache['plot_condition'] == new_condition:
            return
        else:
            s1 = self.g2_cache['plot_condition'][0] != new_condition[0]
            s2 = self.g2_cache['plot_condition'][1] != new_condition[1]
            self.g2_cache['plot_condition'] = new_condition
            plot_target = 2 * int(s1) + int(s2)

        err_msg = []
        for ipt in range(num_points):
            fit_res = fit_xpcs(res, ipt, tslice, qslice, b=bounds)
            offset_i = -1 * offset * (ipt + 1)
            err_msg.append('\n' + self.target_list[ipt])
            for ifg in range(num_fig):
                loc = ipt * num_fig + ifg
                handler.update_lin(loc, fit_res[ifg]['fit_x'],
                       fit_res[ifg]['fit_y'] + offset_i)
                err_msg.append('----' + fit_res[ifg]['err_msg'])

                if plot_target >= 2:
                    handler.update_err(loc, t_el, g2[ipt][:, ifg] + offset_i,
                                       g2_err[ipt][:, ifg])

        handler.auto_scale()
        handler.draw()
        return err_msg

    def get_detector_extent(self, file_list):
        labels = ['ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim', 'X_energy',
                  'xdim', 'ydim']
        res = self.read_data(labels, file_list)
        extents = []
        for n in range(len(file_list)):
            pix2q = res['pix_dim'][n] / res['det_dist'][n] * \
                    (2 * np.pi /(12.398 / res['X_energy'][n]))

            qy_min = (0 - res['ccd_x0'][n]) * pix2q
            qy_max = (res['xdim'][n] - res['ccd_x0'][n]) * pix2q

            qx_min = (0 - res['ccd_y0'][n]) * pix2q
            qx_max = (res['ydim'][n] - res['ccd_y0'][n]) * pix2q
            temp = (qy_min, qy_max, qx_min, qx_max)

            extents.append(temp)

        return extents

    def plot_saxs_2D_mpl(self, mp_hdl=None,  scale='log', max_points=8):
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

    def plot_saxs_2D(self, pg_hdl, plot_type='log', cmap='jet'):
        ans = self.get_saxs_data()['Int_2D']
        if plot_type == 'log':
            ans = np.log10(ans + 1E-8)
        if True:
            pg_cmap = pg_get_cmap(plt.get_cmap(cmap))
            pg_hdl.setColorMap(pg_cmap)

            if ans.shape[0] > 1:
                xvals = np.arange(ans.shape[0])
                pg_hdl.setImage(ans.swapaxes(1, 2), xvals=xvals)
            else:
                pg_hdl.setImage(ans[0].swapaxes(0, 1))

    def plot_saxs_1D(self, mp_hdl, plot_type='log', plot_norm=0,
                     plot_offset=0, max_points=8):
        num_points = min(len(self.target_list), max_points)
        res = self.get_saxs_data()
        q = res['ql_sta']
        Iq = res['Iq']

        ylabel = 'I'
        if plot_norm == 1:
            Iq = Iq * np.square(q)
            ylabel = ylabel + 'q^2'
        elif plot_norm == 2:
            Iq = Iq * q ** 4
            ylabel = ylabel + 'q^4'
        elif plot_norm == 3:
            baseline = Iq[0]
            Iq = Iq / baseline
            ylabel = ylabel + '/I_0'

        if plot_type == 'log':
            Iq = np.log10(Iq)
            ylabel = '$log(%s)$' % ylabel
        else:
            ylabel = '$%s$' % ylabel

        xlabel = '$q (\\AA^{-1})$'

        if mp_hdl.shape == (1, 1) and len(mp_hdl.obj) == num_points:
            for n in range(num_points):
                offset = -plot_offset * (n + 1)
                line = mp_hdl.obj[n]
                line.set_data(q[n], Iq[n] + offset)
            mp_hdl.axes.set_ylabel(ylabel)
            mp_hdl.auto_scale()
        else:
            mp_hdl.clear()
            ax = mp_hdl.subplots(1, 1)
            lin_obj = []
            for n in range(num_points):
                offset = -plot_offset * (n + 1)
                line, = ax.plot(q[n], Iq[n] + offset, 'o--', lw=0.5, alpha=0.8,
                                markersize=2, label=self.id_list[n])
                lin_obj.append(line)
            mp_hdl.obj = lin_obj
            mp_hdl.axes.set_ylabel(ylabel)
            mp_hdl.axes.set_xlabel(xlabel)
            ax.legend()
            # do not use tight layout because the ylabel may not display fully.
            # mp_hdl.fig.tight_layout()
        mp_hdl.draw()
        return


    def get_saxs_data(self):
        labels = ['Int_2D', 'Iq', 'ql_sta']
        res = self.read_data(labels)
        # ans = np.swapaxes(ans, 1, 2)
        # the detector figure is not oriented to image convention;
        return res

    def get_stability_data(self, max_point=512):
        labels = ['Int_t', 'Iq']
        res = self.read_data(labels)
        avg_int_t = []

        avg_size = (res['Int_t'].shape[2] + max_point - 1) // max_point

        int_t = res['Int_t'][:, 1, ::avg_size]
        int_t = int_t / np.mean(int_t)
        res['Int_t'] = int_t

        for n in range(max_point):
            sl = slice(n * avg_size, min((n + 1) * avg_size, int_t.shape[1]))
            temp = int_t[:, sl]
            avg, mean = np.mean(temp, axis=1), np.std(temp, axis=1)
            avg_int_t.append(np.vstack([avg, mean]).T)

        res['Int_t_statistics'] = np.array(avg_int_t).swapaxes(0, 1)
        # res['Int_t'] = None
        res['avg_size'] = avg_size

        # normalize Iq data
        Iq = res["Iq"]
        Iq_norm = np.log10(Iq / Iq[0])
        res['Iq_norm'] = Iq_norm

        return res

    def plot_stability(self, mp_hdl, mp_hdl_it):
        res = self.get_stability_data()
        if mp_hdl.axes is None:
            ax = mp_hdl.subplots(1, 1)
            ax.imshow((res['Iq_norm'][:, :].T), aspect='auto',
                      cmap=plt.get_cmap('seismic'), vmin=-0.2, vmax=0.2,
                      interpolation=None)
        mp_hdl.fig.tight_layout()
        mp_hdl.draw()

        if mp_hdl_it.axes is None:
            ax = mp_hdl_it.subplots(1, 1)
            # shape = res['Int_t'].shape
            shape = res['Iq_norm'].shape
            # step = res['avg_size']
            x_line = np.arange(shape[1])

            cen = shape[1] // 2
            for n in range(shape[0]):
                ax.plot(x_line + n * shape[1], res['Iq_norm'][n], alpha=0.75)
                # ax.legend(loc="upper left", ncol=len())
            # avg = np.mean(res['Int_t'].ravel())
            # std = np.std(res['Int_t'].ravel())

            # ax.axhline(avg, ls='--', color='b', label='mean')
            # ax.axhline(avg - 3 * std, ls='--', color='g', label='$-3\sigma$')
            # ax.axhline(avg + 3 * std, ls='--', color='r', label='$+3\sigma$')
            # ax.legend()

            ax.set_xticks(cen + shape[1] * np.arange(shape[0]))
            ax.set_xticklabels(self.id_list[0 : shape[0]])
            ax.set_ylabel('Intensity (a.u.)')
            mp_hdl_it.fig.tight_layout()

        mp_hdl_it.draw()

        # for n in range(res['Int_t'].shape[0]):
        #     pg_hdl.plot(res['Int_t'][n, 1, ::100])
        # pg_hdl.plot(res['Int_t'].ravel())
        # mp_hdl.plot(res['Int_t_statistics'][n, :, 0], '-o', lw=1, alpha=0.5)

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
