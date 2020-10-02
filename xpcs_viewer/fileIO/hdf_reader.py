import h5py
import os
import numpy as np
from multiprocessing import Pool
import time
import logging


logger = logging.getLogger(__name__)


hdf_dict_8idi = {
    'Iq': '/exchange/partition-mean-total',
    'Iqp': '/exchange/partition-mean-partial',
    'ql_sta': '/xpcs/sqlist',
    'ql_dyn': '/xpcs/dqlist',
    'type': '/xpcs/analysis_type',
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
    'ydim': '/measurement/instrument/detector/y_dimension',
    # for twotime datasets
    'c2_half': '/exchange/C2T_all',
    'g2_full': '/exchange/g2full',
    'g2_partials': '/exchange/g2partials',
}


class HDF_Dict(dict):
    def __init__(self, raw_hdf_dict):
        self.__dict__.update(raw_hdf_dict)

    def __getitem__(self, key):
        if key in self.__dict__.keys():
            ans = self.__dict__[key]
        else:
            ans = key
        return ans


hdf_dict = HDF_Dict(hdf_dict_8idi)

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


def get_analysis_type(fn, prefix):
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        val = HDF_Result.get(hdf_dict['type'])[()].decode()
    return val


def get_key(fields, fn, prefix):
    res = []
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        for key in fields:
            if key not in HDF_Result:
                res.append(None)
            else:
                val = np.squeeze(HDF_Result.get(key))
                res.append(val)
    return res


def save_file(fname, fields, res):
    with h5py.File(fname, 'a') as f:
        for field in fields:
            key = hdf_dict[field]
            f[key] = res[field]
    return


def read_file(fields, fn, prefix='./data', dtype='list'):
    if dtype == 'list':
        res = []
    elif dtype == 'dict':
        res = {}
    else:
        raise TypeError('dtype not supported.')

    logger.info('start read')
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        for field in fields:
            if field == 't_el':
                val1 = np.squeeze(HDF_Result.get(hdf_dict['t0']))
                val2 = np.squeeze(HDF_Result.get(hdf_dict['tau']))
                val = val1 * val2
            else:
                link = hdf_dict[field]
                if link in HDF_Result.keys():
                    val = np.squeeze(HDF_Result.get(link))
                else:
                    link = avg_hdf_dict[field]
                    val = np.squeeze(HDF_Result.get(link))
            if dtype == 'list':
                res.append(val)
            elif dtype == 'dict':
                res[field] = val
    logger.info('end read')
    return res


def read_file_wrap(args):
    return read_file(*args)

def read_multiple_files(fields, fn_list, prefix='./data', p_size=4):
    arg_list = []
    for fn in fn_list:
        arg_list.append((fields, fn, prefix))
    with Pool(p_size) as p:
        res = p.map(read_file_wrap, arg_list)
    return res


def test_01():
    fn_list = [
        'N077_D100_att02_0001_0001-100000.hdf',
        'N077_D100_att02_0002_0001-100000.hdf',
        'N077_D100_att02_0003_0001-100000.hdf',
        'N077_D100_att02_0004_0001-100000.hdf',
        'N077_D100_att02_0005_0001-100000.hdf',
        'N077_D100_att02_0006_0001-100000.hdf',
        'N077_D100_att02_0007_0001-100000.hdf',
        'N077_D100_att02_0008_0001-100000.hdf',
        'N077_D100_att02_0009_0001-100000.hdf'] * 50
    fields = ['Iq', 'ql_dyn', 'Int_2D']

    s1 = time.perf_counter()
    x = read_multiple_files(fields, fn_list)
    s2 = time.perf_counter()
    print(s2 - s1)

    s1 = time.perf_counter()
    for i in fn_list:
        read_file(fields, i)
    s2 = time.perf_counter()
    print(s2 - s1)


def test02():
    fields = ['g2', 'Int_2D']
    res={
        'g2': np.random.uniform(0, 1, 100),
        'Int_2D': np.random.uniform(0, 1, 100)
    }
    save_file('test.hdf', fields, res)


if __name__ == '__main__':
    test02()
