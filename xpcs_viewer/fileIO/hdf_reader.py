import h5py
import os
import numpy as np
import logging


logger = logging.getLogger(__name__)

# read the default.json in the home_directory
home_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
if not os.path.isdir(home_dir):
    os.mkdir(home_dir)
key_fname = os.path.join(home_dir, 'default.json')

from .aps_8idi import key as hdf_key

# colors and symbols for plots
colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
symbols = ['o', 's', 't', 'd', '+']


def put(save_path, result, ftype='nexus', mode='raw'):
    with h5py.File(save_path, 'a') as f:
        for key, val in result.items():
            if mode == 'alias':
                key = hdf_key[ftype][key]
            if key in f:
                del f[key]
            if isinstance(val, np.ndarray) and val.ndim == 1:
                val = np.reshape(val, (1, -1))
            f[key] = val
        return


def get_abs_cs_scale(fname, ftype='nexus'):
    key = hdf_key[ftype]['abs_cross_section_scale']
    with h5py.File(fname, 'r') as f:
        if key not in f:
            return None
        else:
            return float(f[key][()])


def read_metadat_to_dict(file_path):
    """
    Reads an HDF5 file and loads its contents into a nested dictionary.

    Parameters
    ----------
    file_path : str
        Path to the HDF5 file.

    Returns
    -------
    dict
        A nested dictionary containing datasets as NumPy arrays.
    """

    def recursive_read(h5_group, target_dict):
        """ Recursively reads groups and datasets into the dictionary. """
        for key in h5_group:
            obj = h5_group[key]
            if isinstance(obj, h5py.Dataset):
                val = obj[()]
                if type(val) in [np.bytes_, bytes]:
                    val = val.decode()
                target_dict[key] = val
            elif isinstance(obj, h5py.Group):
                target_dict[key] = {}
                recursive_read(obj, target_dict[key])

    data_dict = {}
    groups = ['/entry/instrument/', 
              '/xpcs/multitau/config', '/xpcs/twotime/config']
    with h5py.File(file_path, 'r') as hdf_file:
        for group in groups:
            if group in hdf_file:
                data_dict[group] = {}
                recursive_read(hdf_file[group], data_dict[group])
    return data_dict


def get(fname, fields, mode='raw', ret_type='dict', ftype='nexus'):
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
    assert mode in ['raw', 'alias'], 'mode not supported'
    assert ret_type in ['dict', 'list'], 'ret_type not supported'

    ret = {}
    with h5py.File(fname, 'r') as HDF_Result:
        for key in fields:
            path = hdf_key[ftype][key] if mode == 'alias' else key
            if path not in HDF_Result:
                logger.error('path to field not found: %s', path)
                raise ValueError('key not found: %s:%s', key, path)
            else:
                val = HDF_Result.get(path)[()]
            if key in ['saxs_2d']:  # saxs_2d is in [1xNxM] format
                val = val[0]
            # converts bytes to unicode;
            if type(val) in [np.bytes_, bytes]:
                val = val.decode()
            ret[key] = val

    if ret_type == 'dict':
        return ret
    elif ret_type == 'list':
        return [ret[key] for key in fields]


def get_analysis_type(fname, ftype='nexus'):
    """
    determine the analysis type of the file
    Parameters
    ----------
    fname: str
        file name
    ftype: str
        file type, 'nexus' or 'legacy'
    Returns
    -------
    tuple
        analysis type, 'Twotime' or 'Multitau', or both
    """
    c2_prefix = hdf_key[ftype]['c2_prefix']
    g2_prefix = hdf_key[ftype]['g2']
    analysis_type = []
    with h5py.File(fname, 'r') as HDF_Result:
        if c2_prefix in HDF_Result:
            analysis_type.append('Twotime')
        if g2_prefix in HDF_Result:
            analysis_type.append('Multitau')

    if len(analysis_type) == 0:
        raise ValueError(f'No analysis type found in {fname}')
    return tuple(analysis_type)


def create_id(fname, label_style=None):
    if len(fname) < 10:
        return fname

    if label_style is None:
        selection = [0, 1, -1]
    else:
        selection = [int(x) for x in label_style.split(',')]

    segments = os.path.splitext(fname)[0].split('_')
    if segments[-1].startswith('r'):
        try:
            simplified_repeat = f'{int(segments[-1][1:]):02d}'
            segments[-1] = simplified_repeat
        except Exception:
            pass

    id_str = '_'.join([segments[i] for i in selection])

    return id_str


if __name__ == '__main__':
    pass
