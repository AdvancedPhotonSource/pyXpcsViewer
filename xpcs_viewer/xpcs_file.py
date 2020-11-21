import os
import numpy as np
from .fileIO.hdf_reader import get, put, get_type, create_id
from .plothandler.pyqtgraph_handler import ImageViewDev
from .module import saxs2d

# colors and symbols for plots
colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
symbols = ['o', 's', 't', 'd', '+']


class XpcsFile(object):
    def __init__(self, fname, cwd='../../data', labels=None):

        self.full_path = os.path.join(cwd, fname)
        self.cwd = cwd

        self.type = get_type(self.full_path)
        attr = self.load()
        self.__dict__.update(attr)
        self.label = create_id(fname)

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

    def load(self, labels=None):
        if labels is None:
            if self.type == 'Twotime':
                labels = [
                    'saxs_2d', "saxs_1d", 'Iqp', 'ql_sta', 'Int_t', 't0', 't1',
                    'ql_dyn', 'g2_full', 'g2_partials', 'type'
                ]
            else:
                labels = [
                    'saxs_2d', "saxs_1d", 'Iqp', 'ql_sta', 'Int_t', 't0', 't1',
                    't_el', 'ql_dyn', 'g2', 'g2_err', 'type'
                ]

        ret = get(self.full_path, labels, 'alias')
        return ret

    def at(self, key):
        return self.__dict__[key]

    def get_detector_extent(self):
        labels = [
            'ccd_x0', 'ccd_y0', 'det_dist', 'pix_dim', 'X_energy', 'xdim',
            'ydim'
        ]
        res = get(self.full_path, labels, mode='alias', ret_type='dict')

        wlength = 12.398 / res['X_energy']
        pix2q = res['pix_dim'] / res['det_dist'] * (2 * np.pi / wlength)

        qy_min = (0 - res['ccd_x0']) * pix2q
        qy_max = (res['xdim'] - res['ccd_x0']) * pix2q

        qx_min = (0 - res['ccd_y0']) * pix2q
        qx_max = (res['ydim'] - res['ccd_y0']) * pix2q
        extent = (qy_min, qy_max, qx_min, qx_max)

        return extent
    
    def plot_saxs2d(self, *args, **kwargs):
        from pyqtgraph.Qt import QtGui
        app = QtGui.QApplication([])
        hdl = ImageViewDev()
        saxs2d.plot([self.saxs_2d], hdl, *args, **kwargs)
        app.exec_()

    def pg_plot_g2(self, qrange, ax, idx):
        color = colors[idx // len(colors)]
        symbol = symbols[idx // len(symbols)]

        pen = pg.mkPen(color=color, width=3)
        line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy,
                               pen=pen)
        ax.plot(x, y, pen=None, symbol=symbol, name=self.label, symbolSize=3,
                symbolBrush=pg.mkBrush(color=color))

        ax.setLogMode(x=True, y=None)
        ax.addItem(line)
        return


def test1():
    cwd = '../../../xpcs_data'
    af = XpcsFile(fname='N077_D100_att02_0128_0001-100000.hdf', cwd=cwd)
    af.plot_saxs2d()
    # af = XpcsFile(path='A178_SMB_C_BR_Hetero_SI35_att0_Lq0_001_0001-0768_Twotime.hdf')
    # print(af)
    # print(af.getattr('saxs_2d'))
