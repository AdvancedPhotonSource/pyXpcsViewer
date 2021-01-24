import h5py
import numpy as np
from scipy.stats import describe
import os
np.set_printoptions(precision=3, suppress=True)


def c2r(x):
    # def convert_to_readable_number(x):
    if not isinstance(x, np.ndarray):
        x = np.array(x)

    val = np.max(np.abs(x))
    if val > 1E4 or val < 1E-4:
        if x.size == 1:
            res = '%.3e' % x
        else:
            res_list = ['%.3e' % t for t in x]
            res = '[' + ', '.join(res_list) + ']'
    else:
        res = str(np.round(x, 3))
    return res


def describe_numpy(arr):
    repr = str(arr.shape) + ', ' + str(arr.dtype) + ':'
    if arr.size > 1:
        res = describe(arr.ravel())
        repr += 'minmax = %s, mean = %s' % (c2r(res.minmax),
                                            c2r(res.mean))
    else:
        repr += 'val = %s' % str(arr[0])
    return repr


def read_h5py(hdl, path, level, guide_str0):
    if path not in hdl:
        return None
    if 'C2T_all' in path:
        return ['C2T_all']
    result = []

    guide_mid = guide_str0 + '├──'
    guide_lst = guide_str0 + '└──'
    guide_nxt_mid = guide_str0 + '│  '
    guide_nxt_lst = guide_str0 + '   '

    if isinstance(hdl[path], h5py._hl.dataset.Dataset):

        if isinstance(hdl[path][()], np.bytes_):
            info = hdl[path][()].decode() 
            return [guide_lst + info]

        if hdl[path].shape == ():
            return [guide_lst + 'empty']

        info = describe_numpy(np.array(hdl[path]))
        result.append(guide_lst + info)
        return result

    for n, key in enumerate(hdl[path].keys()):
        if n == len(hdl[path].keys()) - 1:
            guide = guide_lst
            guide_nxt = guide_nxt_lst
        else:
            guide = guide_mid
            guide_nxt = guide_nxt_mid

        # os.path.join won't work on windows systems
        # new_path = os.path.join(path, key)
        new_path = '/'.join([path, key])
        if isinstance(key, str):
            result.append(guide + key)
            info = read_h5py(hdl, new_path, level + 1, guide_nxt)
            if info is not None:
                result = result + info
        elif isinstance(key, np.ndarray):
            info = describe_numpy(hdl[new_path])
            result.append(guide + info)
        else:
            pass

    return result


def get_hdf_info(path, fname):
    with h5py.File(os.path.join(path, fname), 'r') as hdl:
        res = read_h5py(hdl, '.', 0, '')
    return res


if __name__ == '__main__':
    pass

