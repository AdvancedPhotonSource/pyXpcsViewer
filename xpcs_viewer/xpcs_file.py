import os
import numpy as np
from .fileIO.hdf_reader import get, put, get_type, create_id
from .plothandler.pyqtgraph_handler import ImageViewDev
from .plothandler.matplot_qt import MplCanvasBarV
from .module import saxs2d, g2mod, saxs1d, intt, stability
import pyqtgraph as pg
from .fileIO.hdf_to_str import get_hdf_info
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui, QtCore

# colors and symbols for plots
colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
symbols = ['o', 's', 't', 'd', '+']


class XpcsFile(object):
    def __init__(self, fname, cwd='.', fields=None):
        self.fname = fname
        self.full_path = os.path.join(cwd, fname)
        self.cwd = cwd

        self.type = get_type(self.full_path)
        self.keys, attr = self.load(fields)
        self.__dict__.update(attr)
        self.label = create_id(fname)
        self.hdf_info = None

    def __str__(self):
        ans = ['File:' + str(self.full_path)]
        for key, val in self.__dict__.items():
            if key == 'hdf_key':
                continue
            elif isinstance(val, np.ndarray) and val.size > 1:
                val = str(val.shape)
            else:
                val = str(val)
            ans.append(f"   {key.ljust(12)}: {val.ljust(30)}")

        return '\n'.join(ans)

    def __add__(self, other):
        pass

    def get_hdf_info(self):
        if self.hdf_info is None:
            self.hdf_info = get_hdf_info(self.cwd, self.fname)
        return self.hdf_info

    def load(self, extra_fields=None):
        # default fields;
        fields = ['saxs_2d', "saxs_1d", 'Iqp', 'ql_sta', 'Int_t',
                  't0', 't1', 'ql_dyn', 'type', 'dqmap']

        if self.type == 'Twotime':
            fields = fields + ['g2_full', 'g2_partials']
        # multitau
        else:
            fields = fields + ['tau', 'g2', 'g2_err']

        # append extra fields, eg 'G2', 'IP', 'IF'
        if isinstance(extra_fields, list):
            fields += extra_fields

        ret = get(self.full_path, fields, 'alias')
        ret['dqmap'] = ret['dqmap'].astype(np.uint16)

        if 't0' in ret and 'tau' in ret:
            ret['t_el'] = ret['t0'] * ret['tau']
        if self.type == 'Twotime':
            ret['g2'] = ret['g2_full']
            ret['t_el'] = np.arange(ret['g2'].shape[0]) * ret['t0']

        return fields, ret

    def at(self, key):
        return self.__dict__[key]

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]

    def get_time_scale(self, group='xpcs'):
        # acquire time scale for twotime analysis
        key_frames = [
            '/'.join([group, 'stride_frames']),
            '/'.join([group, 'avg_frames'])
        ]
        stride, avg = get(self.full_path,
                          key_frames,
                          mode='raw',
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

        if self.type == 'Twotime':
            key_c2t = '/'.join([rpath, 'C2T_all'])
            idlist = get(self.full_path, [key_c2t], mode='raw')[key_c2t]
            idlist = [int(x[3:]) for x in idlist]
        else:
            idlist = [None]
        return dqmap, saxs, rpath, idlist

    def get_twotime_c2(self, twotime_key, plot_index):
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
        fields = [
            'ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim', 'X_energy', 'xdim',
            'ydim'
        ]
        res = get(self.full_path, fields, mode='alias', ret_type='dict')

        wlength = 12.398 / res['X_energy']
        pix2q = res['pix_dim'] / res['det_dist'] * (2 * np.pi / wlength)

        qy_min = (0 - res['ccd_x0']) * pix2q
        qy_max = (res['xdim'] - res['ccd_x0']) * pix2q

        qx_min = (0 - res['ccd_y0']) * pix2q
        qx_max = (res['ydim'] - res['ccd_y0']) * pix2q
        extent = (qy_min, qy_max, qx_min, qx_max)

        return extent

    def plot_saxs2d(self, *args, **kwargs):
        app = QtGui.QApplication([])
        win = QtGui.QMainWindow()
        win.resize(1024, 600)
        hdl = ImageViewDev()
        win.setCentralWidget(hdl)
        win.show()
        win.setWindowTitle(self.label + ': ' + self.fname)
        saxs2d.plot([self.saxs_2d], hdl, *args, **kwargs)
        app.exec_()

    def plot_saxs1d(self, *args, **kwargs):
        app = QtGui.QApplication([])
        win = QtGui.QMainWindow()
        win.resize(1024, 600)
        canvas = MplCanvasBarV()
        win.setCentralWidget(canvas)
        win.show()
        win.setWindowTitle(self.label + ': ' + self.fname)
        saxs1d.plot([self], canvas.hdl, *args, **kwargs)
        app.exec_()

    def plot_intt(self, window=1, sampling=1, **kwargs):
        app = QtGui.QApplication([])
        win = pg.GraphicsLayoutWidget(show=True, title=self.label + '_intt')
        win.resize(1024, 600)
        intt.plot([self], win, [self.label], enable_zoom=True,
                  xlabel='Frame Index', rows=None, window=window,
                  sampling=sampling, **kwargs)
        app.exec_()

    def plot_stability(self, **kwargs):
        app = QtGui.QApplication([])
        win = QtGui.QMainWindow()
        win.resize(1024, 600)
        canvas = MplCanvasBarV()
        win.setCentralWidget(canvas)
        win.show()
        stability.plot(self, canvas.hdl,
                       title='stability plot for %s' % self.label, **kwargs)
        app.exec_()

    def get_pg_tree(self):
        data = self.load()
        n = 0
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


def test1():
    cwd = '../../../xpcs_data'
    af = XpcsFile(fname='N077_D100_att02_0128_0001-100000.hdf', cwd=cwd)
    af.plot_saxs2d()


if __name__ == '__main__':
    test1()
