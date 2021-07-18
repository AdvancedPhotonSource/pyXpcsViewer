import os
import numpy as np
from .fileIO.hdf_reader import get, get_type, create_id
from .plothandler.pyqtgraph_handler import ImageViewDev
from .plothandler.matplot_qt import MplCanvasBarV
from .module import saxs2d, saxs1d, intt, stability, g2mod
from .module.g2mod import create_slice
from .helper.fitting import fit_with_fixed
import pyqtgraph as pg
from .fileIO.hdf_to_str import get_hdf_info
from pyqtgraph.Qt import QtGui


def single_exp_all(x, a, b, c, d):
    """
    single exponential fitting for xpcs-multitau analysis
    :param x: delay in seconds
    :param a: contrast
    :param b: tau
    :param c: restriction factor
    :param d: baseline
    :return:
    """
    return a * np.exp(-2 * (x / b) ** c) + d


def double_exp_all(x, a, b1, c1, d, b2, c2, f):
    """
    double exponential fitting for xpcs-multitau analysis
    Args:
        x: delay in seconds, float or 1d-numpy.ndarray
        a: contrast
        f: fraction for the 1st exp function; the 2nd has (1-f) weight
        b1: tau for 1st exp function
        c1: restriction factor for the 1st exp function
        b2: tau for 2nd exp function
        c2: restriction factor for the 2nd exp function
        d: baseline
    Return:
        function value
    """
    t1 = np.exp(-1 * (x / b1) ** c1) * f
    t2 = np.exp(-1 * (x / b2) ** c2) * (1 - f)
    return a * (t1 + t2) ** 2 + d


def power_law(x, a, b):
    """
    power law for fitting the diffusion factor
    :param x: tau
    :param a:
    :param b:
    :return:
    """
    return a * x ** b


class XpcsFile(object):
    """
    XpcsFile is a class that wraps an Xpcs analysis hdf file;
    """
    def __init__(self, fname, cwd='.', fields=None):
        self.fname = fname
        self.full_path = os.path.join(cwd, fname)
        self.cwd = cwd

        self.type = get_type(self.full_path)
        self.keys, attr = self.load(fields)
        self.__dict__.update(attr)

        # label is a short string to describe the file/filename
        self.label = create_id(fname)
        self.hdf_info = None
        self.fit_summary = None

    def __str__(self):
        ans = ['File:' + str(self.full_path)]
        for key, val in self.__dict__.items():
            # omit those to avoid lengthy output
            if key in ['hdf_key', "hdf_info"]:
                continue
            elif isinstance(val, np.ndarray) and val.size > 1:
                val = str(val.shape)
            else:
                val = str(val)
            ans.append(f"   {key.ljust(12)}: {val.ljust(30)}")

        return '\n'.join(ans)
    
    def __repr__(self):
        ans = str(type(self))
        ans = '\n'.join([ans, self.__str__()])
        return ans

    def __add__(self, other):
        pass

    def get_hdf_info(self, fstr=None):
        """
        get a text representation of the xpcs file; the entries are organized
        in a tree structure;
        :param fstr: list of filter strings, ['string_1', 'string_2', ...]
        :return: a list strings
        """
        # only call it once because it may take long time to generate the str
        if self.hdf_info is None:
            self.hdf_info = get_hdf_info(self.cwd, self.fname)

        if fstr is None or len(fstr) == 0:
            return self.hdf_info

        def filter_str(aline):
            for x in fstr:
                if x in aline:
                    return True
            return False

        msg = []
        n = 0
        while n < len(self.hdf_info):
            if filter_str(self.hdf_info[n]):
                msg.append(self.hdf_info[n])
                if n < len(self.hdf_info) - 1:
                    msg.append(self.hdf_info[n + 1])
                n += 2
            else:
                n += 1

        return msg

    def load(self, extra_fields=None):
        # default common fields for both twotime and multitau analysis;
        fields = ['saxs_2d', "saxs_1d", 'Iqp', 'ql_sta', 'Int_t', 't0', 't1',
                  'ql_dyn', 'type', 'dqmap', 'ccd_x0', 'ccd_y0', 'det_dist', 
                  'pix_dim_x', 'pix_dim_y', 'X_energy', 'xdim', 'ydim']

        # extra fields for twotime analysis
        if self.type == 'Twotime':
            fields = fields + ['g2_full', 'g2_partials']
        # extra fields for multitau analysis
        else:
            fields = fields + ['tau', 'g2', 'g2_err']

        # append other extra fields, eg 'G2', 'IP', 'IF'
        if isinstance(extra_fields, list):
            fields += extra_fields

        # avoid multiple keys
        fields = list(set(fields))

        ret = get(self.full_path, fields, 'alias')
        ret['dqmap'] = ret['dqmap'].astype(np.uint16)

        # get t_el which is in the unit of seconds;
        if 't0' in ret and 'tau' in ret:
            ret['t_el'] = ret['t0'] * ret['tau']

        if self.type == 'Twotime':
            ret['g2'] = ret['g2_full']
            ret['t_el'] = np.arange(ret['g2'].shape[0]) * ret['t0']
        else:
            # correct g2_err to avoid fitting divergence
            ret['g2_err_mod'] = self.correct_g2_err(ret['g2_err'])

        return ret.keys(), ret

    def at(self, key):
        return self.__dict__[key]

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            raise KeyError

    def get_time_scale(self, group='xpcs'):
        # acquire time scale for twotime analysis
        key_frames = [
            '/'.join([group, 'stride_frames']),
            '/'.join([group, 'avg_frames'])
        ]
        stride, avg = get(self.full_path, key_frames, mode='raw',
                          ret_type='list')
        time_scale = max(self.t0, self.t1) * stride * avg
        return time_scale

    def get_twotime_maps(self, group='xpcs'):
        rpath = '/'.join([group, 'output_data'])
        rpath = get(self.full_path, [rpath], mode='raw')[rpath]

        key_dqmap = '/'.join([group, 'dqmap'])
        key_saxs = '/'.join([rpath, 'pixelSum'])

        dqmap, saxs = get(self.full_path, [key_dqmap, key_saxs],
                          mode='raw',
                          ret_type='list')

        # some dataset may swap the axis
        if saxs.shape != dqmap.shape:
            saxs = saxs.T

        if self.type == 'Twotime':
            key_c2t = '/'.join([rpath, 'C2T_all'])
            idlist = get(self.full_path, [key_c2t], mode='raw')[key_c2t]
            idlist = [int(x[3:]) for x in idlist]
        else:
            idlist = [None]
        return dqmap, saxs, rpath, idlist

    def get_twotime_c2(self, twotime_key, plot_index):
        """
        get the twotime data for a particular key and index
        :param twotime_key: the twotime analysis key
        :param plot_index: the targeted q index;
        :return: a 2d numpy.ndarray representation of twotime correlation.
        """
        c2_key = '/'.join([twotime_key, 'C2T_all/g2_%05d' % plot_index])
        c2_half = get(self.full_path, [c2_key], mode='raw')[c2_key]

        if c2_half is None:
            return None

        c2 = c2_half + np.transpose(c2_half)
        c2_translate = np.zeros(c2.shape)
        c2_translate[:, 0] = c2[:, -1]
        c2_translate[:, 1:] = c2[:, :-1]
        c2 = np.where(c2 > 1.3, c2_translate, c2)
        return c2

    def get_detector_extent(self):
        """
        get the angular extent on the detector, for saxs2d, qmap/display;
        :return:
        """
        fields = [
            'ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim_x', 'pix_dim_y', 
            'X_energy', 'xdim', 'ydim'
        ]
        res = get(self.full_path, fields, mode='alias', ret_type='dict')

        wlength = 12.398 / res['X_energy']
        pix2q = res['pix_dim_x'] / res['det_dist'] * (2 * np.pi / wlength)

        qy_min = (0 - res['ccd_x0']) * pix2q
        qy_max = (res['xdim'] - res['ccd_x0']) * pix2q

        qx_min = (0 - res['ccd_y0']) * pix2q
        qx_max = (res['ydim'] - res['ccd_y0']) * pix2q
        extent = (qy_min, qy_max, qx_min, qx_max)

        return extent

    def show(self, mode, **kwargs):
        app = QtGui.QApplication([])

        if mode == 'saxs2d':
            try:
                win = ImageViewDev()
                saxs2d.plot([self.saxs_2d], win, **kwargs)
            except Exception:
                pass
        elif mode == 'saxs1d':
            win = MplCanvasBarV()
            saxs1d.plot([self], win.hdl, **kwargs)
        elif mode == 'intt':
            win = pg.GraphicsLayoutWidget()
            intt.plot([self], win, **kwargs)
        elif mode == 'stability':
            win = MplCanvasBarV()
            stability.plot(self, win.hdl, **kwargs)
        elif mode == 'g2':
            win = MplCanvasBarV()
            g2mod.matplot_plot([self], win.hdl, **kwargs)

        win.show()
        win.setWindowTitle(': '.join([mode, self.label, self.fname]))
        app.exec_()

    def plot_saxs2d(self, **kwargs):
        self.show('saxs2d', **kwargs)

    def plot_saxs1d(self, **kwargs):
        self.show('saxs1d', **kwargs)

    def plot_intt(self, window=1, sampling=1, **kwargs):
        self.show('intt', window=window, sampling=sampling)

    def plot_stability(self, **kwargs):
        self.show('stability', **kwargs)

    def get_pg_tree(self):
        _, data = self.load()
        for key, val in data.items():
            if isinstance(val, np.ndarray):
                if val.size > 4096:
                    data[key] = 'data size is too large'
                # suqeeze one-element array
                if val.size == 1:
                    data[key] = float(val)

        data['type'] = self.type
        data['label'] = self.label

        tree = pg.DataTreeWidget(data=data)
        tree.setWindowTitle(self.fname)
        tree.resize(600, 800)
        return tree
    
    def get_g2_fitting_line(self, q, tor=1E-6):
        """
        get the fitting line for q, within tor
        """
        if self.fit_summary is None:
            return None, None
        flag = np.abs(self.fit_summary['q_val'] - q) < tor
        idx = np.argmin(flag)
        fit_x = self.fit_summary['fit_line'][idx]['fit_x']
        fit_y = self.fit_summary['fit_line'][idx]['fit_y']
        return fit_x, fit_y

    def get_fitting_info(self, mode='g2_fitting'):
        if self.fit_summary is None:
            return "fitting is not ready for %s" % self.label

        if mode == 'g2_fitting':
            result = self.fit_summary.copy()
            # fit_line is not useful to display
            result.pop('fit_line', None)
            val = result.pop('fit_val', None)
            if result['fit_func'] == 'single':
                prefix = ['a', 'b', 'c', 'd']
            else:
                prefix = ['a', 'b', 'c', 'd', 'b2', 'c2', 'f']

            msg = []
            for n in range(val.shape[0]):
                temp = []
                for m in range(len(prefix)):
                    temp.append('%s = %f ± %f' % (
                        prefix[m], val[n, 0, m], val[n, 1, m]))
                msg.append(', '.join(temp))
            result['fit_val'] = np.array(msg)

        elif mode == 'tauq_fitting':
            if 'tauq_fit_val' not in self.fit_summary:
                result = 'tauq fitting is not available'
            else:
                v = self.fit_summary['tauq_fit_val']
                result = "a = %e ± %e; b = %f ± %f" % (v[0, 0], v[1, 0],
                                                       v[0, 1], v[1, 1])
        else:
            raise ValueError('mode not supported.')

        return result

    def fit_g2(self, q_range=None, t_range=None, bounds=None,
               fit_flag=None, fit_func='single'):
        """
        fit the g2 values using single exponential decay function
        :param q_range: a tuple of q lower bound and upper bound
        :param t_range: a tuple of t lower bound and upper bound
        :param bounds: bounds for fitting;
        :param fit_flag: tuple of bools; True to fit and False to float
        :param fit_func: ['single' | 'double']: to fit with single exponential
            or double exponential function
        :return: dictionary with the fitting result;
        """
        assert len(bounds) == 2
        if fit_func == 'single':
            assert len(bounds[0]) == 4, \
                "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(4)]
            func = single_exp_all 
        else:
            assert len(bounds[0]) == 7, \
                "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(7)]
            func = double_exp_all

        if q_range is None:
            q_range = [np.min(self.ql_dyn) * 0.95, np.max(self.ql_dyn) * 1.05]
        
        if t_range is None:
            q_range = [np.min(self.t_el) * 0.95, np.max(self.t_el) * 1.05]
        
        
        # create a data slice for the given range;    
        t_slice = create_slice(self.t_el, t_range)
        q_slice = create_slice(self.ql_dyn, q_range)

        t_el = self.t_el[t_slice]
        q = self.ql_dyn[q_slice]
        g2 = self.g2[t_slice, q_slice]
        sigma = self.g2_err_mod[t_slice, q_slice]

        # set the initial guess
        p0 = np.array(bounds).mean(axis=0)
        # tau's bounds are in log scale, set as the geometric average
        p0[1] = np.sqrt(bounds[0][1] * bounds[1][1])
        if fit_func == 'double':
            p0[4] = np.sqrt(bounds[0][4] * bounds[1][4])

        fit_x = np.logspace(np.log10(np.min(t_el)) - 0.5,
                            np.log10(np.max(t_el)) + 0.5, 128)

        fit_line, fit_val = fit_with_fixed(func, t_el, g2, sigma,
                                           bounds, fit_flag, fit_x, p0=p0)

        self.fit_summary = {
            'fit_func': fit_func,
            'fit_val': fit_val,
            't_el': t_el,
            'q_val': q,
            # 'g2': g2,
            # 'sigma': sigma,
            'q_range': str(q_range),
            't_range': str(t_range),
            'bounds': bounds,
            'fit_flag': str(fit_flag),
            'fit_line': fit_line
        }

        return self.fit_summary

    @staticmethod
    def correct_g2_err(g2_err=None, threshold=1E-6):
        # correct the err for some data points with really small error, which
        # may cause the fitting to blowup

        g2_err_mod = np.copy(g2_err)
        for n in range(g2_err.shape[1]):
            data = g2_err[:, n]
            idx = data > threshold
            avg = np.mean(data[idx])
            g2_err_mod[np.logical_not(idx), n] = avg 

        return g2_err_mod
    
    def fit_tauq(self, q_range, bounds, fit_flag):
        if self.fit_summary is None:
            return
        
        x = self.fit_summary['q_val']
        q_slice = create_slice(x, q_range)
        x = x[q_slice]

        y = self.fit_summary['fit_val'][q_slice, 0, 1]
        sigma = self.fit_summary['fit_val'][q_slice, 1, 1]
        
        # filter out those invalid fittings; failed g2 fitting has -1 err
        valid_idx = (sigma > 0)

        if np.sum(valid_idx) == 0:
            self.fit_summary['tauq_success'] = False
            return

        x = x[valid_idx]
        y = y[valid_idx]
        sigma = sigma[valid_idx]

        # reshape to two-dimension so the fit_with_fixed function works
        y = y.reshape(-1, 1)
        sigma = sigma.reshape(-1, 1)

        # the initial value for typical gel systems
        p0 = [1.0e-7, -2.0]
        fit_x = np.logspace(np.log10(np.min(x) / 1.1),
                            np.log10(np.max(x) * 1.1), 128)

        fit_line, fit_val = fit_with_fixed(power_law, x, y, sigma, bounds, 
                                           fit_flag, fit_x, p0=p0) 

        # fit_line and fit_val are lists with just one element;
        self.fit_summary['tauq_success'] = fit_line[0]['success']
        self.fit_summary['tauq_q'] = x
        self.fit_summary['tauq_tau'] = np.squeeze(y)
        self.fit_summary['tauq_tau_err'] = np.squeeze(sigma)
        self.fit_summary['tauq_fit_line'] = fit_line[0]
        self.fit_summary['tauq_fit_val'] = fit_val[0]

        return self.fit_summary


def test1():
    cwd = '../../../xpcs_data'
    af = XpcsFile(fname='N077_D100_att02_0128_0001-100000.hdf', cwd=cwd)
    af.plot_saxs2d()


if __name__ == '__main__':
    test1()
