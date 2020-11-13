import h5py
import os
import numpy as np
import json
import logging
import pyqtgraph as pg


logger = logging.getLogger(__name__)

# read the default.json in the home_directory
home_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
key_fname = os.path.join(home_dir, 'default.json')

# if no such file; then use 8idi configure
if not os.path.isfile(key_fname):
    from .aps_8idi import key
    with open(key_fname, 'w') as f:
        json.dump(key, f, indent=4)
    logger.info('no key configuration files found; using APS-8IDI')

with open(key_fname) as f:
    try:
        hdf_key = json.load(f)
    except json.JSONDecodeError as e:
        logger.info('default.json in .xpcs_viewer is damaged.')
        from .aps_8idi import key
        hdf_key = key
    

# colors and symbols for plots
colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
symbols = ['o', 's', 't', 'd', '+']


def put(save_path, fields, result, mode='raw'):
    with h5py.File(save_path, 'a') as f:
        for key in fields:
            if mode == 'alias':
                key2 = hdf_key[key]
            else:
                key2 = key
            if key2 in f:
                del f[key2]
            f[key2] = result[key]
        return


def get(fname, fields_raw, mode='raw', ret_type='dict'):
    """
    get the values for the various keys listed in fields for a single
    file;
    :param fname:
    :param fields_raw: list of keys [key1, key2, ..., ]
    :param mode: ['raw' | 'alias']; alias is defined in .hdf_key
                 otherwise the raw hdf key will be used
    :param ret_type: return dictonary if 'dict', list if it is 'list'
    :return: dictionary or dictionary;
    """
    ret = {}

    # python will modify mutable lists;
    fields = fields_raw.copy()
    fields_org = fields.copy()
    flag = False
    # t_el is not defined in the HDF keys; t_el = t0 * tau
    if 't_el' in fields:
        flag = True
        fields.remove('t_el')
        fields += ['t0', 'tau']

    with h5py.File(fname, 'r') as HDF_Result:
        for key in fields:
            if mode == 'alias':
                key2 = hdf_key[key]
            elif mode == 'raw':
                key2 = key
            else:
                raise ValueError("mode not supported.")

            if key2 not in HDF_Result:
                val = None
            elif 'C2T_all' in key2:
                # C2T_allxxx has to be converted by numpy.array
                val = np.array(HDF_Result.get(key2))
            else:
                val = HDF_Result.get(key2)[()]

            if type(val) == np.ndarray:
                # get rid of length=1 axies;
                val = np.squeeze(val)
            elif type(val) in [np.bytes_, bytes]:
                # converts bytes to unicode;
                val = val.decode()
            ret[key] = val

    if flag:
        ret['t_el'] = ret['t0'] * ret['tau']

    if ret_type == 'dict':
        return ret
    elif ret_type == 'list':
        return [ret[key] for key in fields_org]
    else:
        raise TypeError('ret_type not support')


def get_type(fname):
    try:
        ret = get(fname, ['type'], mode='alias')['type']
        ret.capitalize()
    except Exception:
        return None
    else:
        return ret


def create_id(fname):
    x = os.path.basename(fname)
    idx_1 = x.find('_')
    idx_2 = x.rfind('_', 0, len(x))
    idx_3 = x.rfind('_', 0, idx_2)
    ret = x[0: idx_1] + '_' + x[idx_3: idx_2]
    return ret


class XpcsFile(object):
    def __init__(self, fname, cwd='../../data', labels=None):

        self.full_path = os.path.join(cwd, fname)
        self.cwd = cwd

        self.type = get_type(self.full_path)
        attr = self.load()
        self.__dict__.update(attr)
        self.label = create_id(fname)

    def __str2__(self):
        ans = ['File:' + str(self.full_path)]
        for key, val in self.__dict__.items():
            if isinstance(val, np.ndarray) and val.size > 1:
                val = str(val.shape)
            else:
                val = str(val)
            ans.append(f"   {key.ljust(12)}: {val.ljust(30)}")

        return '\n'.join(ans)

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
    # XpcsFile._cwd = '../../data'
    af = XpcsFile(fname='N077_D100_att02_0128_0001-100000.hdf')
    # af = XpcsFile(path='A178_SMB_C_BR_Hetero_SI35_att0_Lq0_001_0001-0768_Twotime.hdf')
    print(af)
    print(af.getattr('saxs_2d'))


if __name__ == '__main__':
    test1()
