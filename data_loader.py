import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplot_qt import MplCanvas
from matplotlib.ticker import FormatStrFormatter
from xpcs_fitting import fit_xpcs

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

# the following functions are copied from:
# https://stackoverflow.com/questions/2892931
def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and is_substr(data[0][i:i+j], data):
                    substr = data[0][i:i+j]
    return substr

def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True


def create_id(in_list, repeat=2, keep_slice=None):
    """
    :param in_list: input file name list
    :param repeat: number of repeats to remove common string
    :param keep_slice: the slice in the original string to keep, if not given,
        then use the segment before the first underscore.
    :return: label list with minimal information redundancy
    """
    if len(in_list) < 1:
        return []

    if keep_slice is None:
        idx = in_list[0].find('_')
        keep_slice = slice(0, idx + 1)

    keep_str = in_list[0][keep_slice]
    if keep_str[-1] != '_':
        keep_str = keep_str + '_'

    for n in range(repeat):
        substr = long_substr(in_list)
        in_list = [x.replace(substr, '') for x in in_list]

    in_list = [keep_str + x for x in in_list]
    return in_list


class DataLoader(object):
    def __init__(self, prefix, file_list):
        self.size = len(file_list)
        self.prefix = prefix
        self.file_list = file_list
        self.id_list = create_id(self.file_list)

    def get_g2_data(self, file_list=None):
        labels = ['Iq', 'g2', 'g2_err', 't_el', 'ql_sta', 'ql_dyn']
        # labels = ['ql_dyn']
        if file_list is None:
            file_list = self.file_list
        res = self.read_data(labels, file_list)
        return res

    def fit_g2(self, g2_data, idx, max_q, contrast=None):
        return fit_xpcs(g2_data, idx, max_q=max_q, contrast=contrast)

    def plot_g2(self, max_q=0.016, handler=None, contrast=None):
        res = self.get_g2_data()
        t_el, g2, g2_err = res['t_el'][0], res['g2'], res['g2_err']
        ql_dyn = res['ql_dyn'][0]

        num_row = 7
        num_col = 4

        def plot_one_sample(ax, idx):
            fit_res = self.fit_g2(res, idx, max_q, contrast=0.16)
            for i in range(num_row * num_col):
                if i >= g2.shape[-1] or ql_dyn[i] > max_q:
                   return
                ax = ax_all.ravel()[i]
                ax.errorbar(t_el, g2[idx][:, i], yerr=g2_err[idx][:, i],
                            fmt='o', markersize=3, markerfacecolor='none')
                if idx == 0:
                    ax.text(0.6, 0.8, ('Q = %5.4f $\AA^{-1}$' % ql_dyn[i]),
                            horizontalalignment='center',
                            verticalalignment='center', transform=ax.transAxes)
                    ax.set_xscale('log')
                    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

                ax.plot(fit_res[i]['fit_x'], fit_res[i]['fit_y'])

        if isinstance(handler, MplCanvas):
            ax_all = handler.axes
            # for idx in range(res['g2'].shape[0]):
            for idx in range(2):
                plot_one_sample(ax_all, idx)

            handler.fig.tight_layout()
            handler.draw()


    def get_detector_extend(self, file_list):
        labels = ['ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim', 'X_energy',
                  'xdim', 'ydim']
        res = self.read_data(labels, file_list)
        extents = []
        for n in range(len(file_list)):
            pix2q = res['pix_dim'][n] / res['det_dist'][n] * \
                    (2 * np.pi /(12.398 / res['X_energy'][n]))

            qy_min = (0 - res['ccd_x0'][n]) * pix2q
            qy_max = (res['ydim'][n] - res['ccd_x0'][n]) * pix2q

            qx_min = (0 - res['ccd_y0'][n]) * pix2q
            qx_max = (res['xdim'][n] - res['ccd_y0'][n]) * pix2q
            temp = (qy_min, qy_max, qx_min, qx_max)

            extents.append(temp)

        return extents

    def plot_saxs(self, method='None', scale='log'):
        extents = self.get_detector_extend(self.file_list)

        ans = self.get_saxs()
        if scale == 'log':
            ans = np.log10(ans + 1E-8)

        num_fig = min(8, len(extents))

        if isinstance(method, MplCanvas):
            if len(extents) <= 3:
                ax = method.subplots(1, num_fig)
            else:
                ax = method.subplots(2, (num_fig + 1) // 2)

            for n in range(num_fig):
                if num_fig == 1:
                    ax_0 = ax
                else:
                    ax_0 = ax.flatten()[n]
                im = ax_0.imshow(ans[n], cmap=plt.get_cmap('jet'),
                               # norm=LogNorm(vmin=1e-7, vmax=1e-4),
                               interpolation='none')
                               # extent=extents[n])
                ax_0.set_title(self.id_list[n])
            method.draw()
        else:
            xvals = np.arange(ans.shape[0])
            method(ans.swapaxes(1, 2), xvals=xvals)

    def get_saxs(self):
        ans = self.read_data(['Int_2D'])['Int_2D']
        # ans = np.swapaxes(ans, 1, 2)
        # the detector figure is not oriented to image convention;
        return ans

    def get_stability_data(self, max_point=128):
        labels = ['Int_t', 'Iq']
        res = self.read_data(labels)
        avg_int_t = []

        int_t = res['Int_t'][:, 1, :]
        int_t = int_t / np.mean(int_t)
        avg_size = (int_t.shape[1] + max_point - 1) // max_point
        for n in range(max_point):
            sl = slice(n * avg_size, (n + 1) * avg_size)
            temp = int_t[:, sl]
            avg, mean = np.mean(temp, axis=1), np.std(temp, axis=1)
            avg_int_t.append(np.vstack([avg, mean]).T)

        res['Int_t_statistics'] = np.array(avg_int_t).swapaxes(0, 1)
        res['Int_t'] = None
        res['avg_size'] = avg_size

        return res

    def read_data(self, labels, file_list=None, mask=None):
        if file_list is None:
            file_list = self.file_list

        if mask is None:
            mask = np.ones(shape=len(file_list), dtype=np.bool)

        data = []
        for n, fn in enumerate(file_list):
            if mask[n]:
                data.append(read_file(labels, fn, self.prefix))

        np_data = {}
        for n, label in enumerate(labels):
            temp = [x[n] for x in data]
            np_data[label] = np.array(temp)

        return np_data

    def average(self, baseline=1.03, chunk_size=256):
        labels = ['Iq', 'g2', 'g2_err', 'Int_2D']
        g2 = self.read_data(['g2'], self.file_list)['g2']
        mask = np.mean(g2[:, -10:, 1], axis=1) < baseline

        steps = (len(mask) + chunk_size - 1) // chunk_size
        result = {}
        for n in range(steps):
            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(len(mask), end)
            slice0 = slice(beg, end)
            values = self.read_data(labels, file_list=self.file_list[slice0],
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
