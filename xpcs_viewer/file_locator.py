import marisa_trie
import os
from os.path import commonprefix
from .fileIO.hdf_to_str import get_hdf_info
from .fileIO.hdf_reader import get, put, get_type, XpcsFile as xf
import logging
import h5py
import json
import numpy as np


logger = logging.getLogger(__name__)
pjoin = os.path.join


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


def get_suffix(file_name):
    _, suffix = os.path.splitext(file_name)
    return suffix


def create_id(in_list, repeat=1, keep_slice=None):
    out_list = [x[::-1] for x in in_list]
    prefix = commonprefix(out_list)
    out_list = [x.replace(prefix, '') for x in out_list]
    out_list = [x[::-1] for x in out_list]
    return out_list


def create_id2(in_list, repeat=1, keep_slice=None):
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


class FileLocator(object):
    def __init__(self, path, key_fname='./configure/aps_8idi.json',
                 max_cache_size=None):
        self.path = path
        self.cwd = None
        self.trie = None
        self.source_list = None
        self.target = []
        self.id_list = None
        self.build(path)
        self.type = None
        self.cache = {}
        if max_cache_size is None:
            # 2G
            self.max_cache_size = 1024 ** 3 * 2

        # if key_fname is not None:
        #     with open(key_fname) as f:
        #         self.hdf_key = json.load(f)
        # else:
        #     self.hdf_key = None

    def get_cached(self, fname, fields, ret_type='list'):
        ret = {}
        for key in fields:
            ret[key] = self.cache[fname].at(key)
        if ret_type == 'dict':
            return ret
        elif ret_type == 'list':
            return [ret[key] for key in fields]
        else:
            raise TypeError('ret_type not support')

    def get_type(self, fname):
        return get_type(pjoin(self.cwd, fname))
    
    def get(self, fname, fields_raw, **kwargs):
        return get(pjoin(self.cwd, fname), fields_raw, **kwargs)
    
    def get_xf_list(self, max_points=128):
        ret = []
        if max_points <= 0:
            max_points = len(self.target)

        for fn in self.target[slice(0, max_points)]:
            ret.append(self.cache[fn])
        return ret

    def fetch(self, labels, file_list, mask=None):
        """
        fetch the keys in labels for each file in filelist; either from cache
        or from the files if not cached.
        :param labels: [key1, key2, ...]
        :param file_list:
        :param mask:
        :return:
        """
        if mask is None:
            mask = np.ones(shape=len(file_list), dtype=np.bool)

        cache_list = []
        for n, fn in enumerate(file_list):
            if not mask[n]:
                continue
            if fn in self.cache.keys():
                cache_list.append(self.cache[fn])
            else:
                cache_list.append(xf(fn, self.cwd, labels))

        np_data = {}
        for key in labels:
            temp = []
            for n in range(len(cache_list)):
                temp.append(cache_list[n].at(key))
            np_data[key] = np.array(temp)
        return np_data

    def load(self, file_list=None, max_number=1024,
             progress_bar=None, flag_del=True):
     
        if file_list in [None, []]:
            file_list = self.target
        file_list = file_list[slice(0, max_number)]

        total_num = len(file_list)
        existing_keys = list(self.cache.keys())

        for n, fn in enumerate(file_list):
            if progress_bar is not None:
                progress_bar.setValue((n + 1) / total_num * 100)

            if fn in existing_keys:
                # already exist
                existing_keys.remove(fn)
            else:
                # read from file and output as a dictionary
                self.cache[fn] = xf(fn, self.cwd)

        if flag_del:
            for key in existing_keys:
                self.cache.pop(key, None)

        return

    def get_hdf_info(self, fname):
        if not os.path.isfile(os.path.join(self.cwd, fname)):
            return ['None']
        return get_hdf_info(self.cwd, fname)

    def add_target(self, alist, threshold=64):
        if alist in [[], None]:
            return
        if self.type is None:
            self.type = self.get_type(alist[0])

        single_flag = True

        if len(alist) <= threshold:
            for x in alist:
                if x not in self.target:
                    if self.get_type(x) == self.type:
                        self.target.append(x)
                    else:
                        single_flag = False
            self.id_list = create_id(self.target, 1)
        else:
        # if many files are added; then ignore the type check;
            logger.info('type check is disabled. too many files added')
            self.target = alist.copy()
            self.id_list = alist.copy()
        

        logger.info('length of target = %d' % len(self.target))
        return single_flag

    def clear_target(self):
        self.target = []
        self.id_list = None
        self.type = None

    def remove_target(self, rlist):
        if rlist is None or self.target is None:
            return
        for x in rlist:
            if x in self.target:
                self.target.remove(x)
        if self.target in [None, []]:
            self.clear_target()

    def search(self, val):
        ans = self.trie.keys(val)
        ans.sort()
        return len(ans), ans

    def build(self, path=None, filter_list=['.hdf', '.h5']):
        if path is None:
            path = self.path

        if os.path.isfile(path):
            with open(path, 'r') as f:
                flist = [x[:-1] for x in f]
            self.cwd = os.path.dirname(path)
        elif os.path.isdir(path):
            flist = os.listdir(path)
            self.cwd = path

        flist = [x for x in flist if get_suffix(x) in filter_list]

        # filter configure files
        flist = [x for x in flist if not x.startswith('.')]
        flist.sort()

        self.trie = marisa_trie.Trie(flist)
        self.source_list = flist

        return True


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
