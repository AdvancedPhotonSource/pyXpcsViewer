# import marisa_trie
import os
from os.path import commonprefix
from .fileIO.hdf_reader import get_type
from .xpcs_file import XpcsFile as xf
import logging
from .helper.listmodel import ListDataModel

logger = logging.getLogger(__name__)
pjoin = os.path.join


# the following functions are copied from:
# https://stackoverflow.com/questions/2892931
def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0]) - i + 1):
                if j > len(substr) and is_substr(data[0][i:i + j], data):
                    substr = data[0][i:i + j]
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


def create_id(in_list):
    ret = []
    for x in in_list:
        idx_1 = x.find('_')
        idx_2 = x.rfind('_', 0, len(x))
        idx_3 = x.rfind('_', 0, idx_2)
        ret.append(x[0:idx_1] + x[idx_3:idx_2])

    return ret


def create_id3(in_list, repeat=1, keep_slice=None):
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
    def __init__(self,
                 path,
                 max_cache_size=None):
        self.path = path
        self.cwd = None
        self.trie = None
        self.source = ListDataModel()
        self.source_search = ListDataModel()
        self.target = ListDataModel()
        self.id_list = None
        self.build(path)
        self.type = None
        self.cache = {}
        if max_cache_size is None:
            # 2G
            self.max_cache_size = 1024 ** 3 * 2

    def get_type(self, fname):
        return get_type(pjoin(self.cwd, fname))

    # def get(self, fname, fields_raw, **kwargs):
    #     return get(pjoin(self.cwd, fname), fields_raw, **kwargs)

    def get_fn_tuple(self, max_points=128, rows=None):
        # compile the filenames upto max_points to a tuple
        if max_points <= 0:
            max_points = len(self.target)

        ret = []
        if rows is None or len(rows) == 0:
            for n in range(min(max_points, len(self.target))):
                ret.append(self.target[n])
        else:
            for n in rows[0:max_points]:
                ret.append(self.target[n])
        return tuple(ret)

    def get_xf_list(self, max_points=8, rows=None):
        """
        get the cached xpcs_file list;
        :param max_points: maxiaml number of xpcs_files to get
        :param rows: a list of index to select; if None is given, then use
            max_points;
        :return: list of xpcs_file objects;
        """
        if max_points <= 0:
            max_points = len(self.target)

        if rows is None or len(rows) == 0:
            selected = list(range(min(max_points, len(self.target))))
        else:
            # make sure no more than max_points are loaded.
            selected = rows[0:max_points]

        ret = []
        for n in selected:
            fn = self.target[n]
            ret.append(self.cache[fn])

        return ret

    def load(self, file_list=None, max_number=1024, progress_bar=None,
             flag_del=True):

        if file_list in [None, []]:
            file_list = self.target

        total_num = min(max_number, len(file_list))
        existing_keys = list(self.cache.keys())

        for n in range(total_num):
            fn = self.target[n]
            if progress_bar is not None:
                progress_bar.setValue((n + 1) / total_num * 100)

            if fn in existing_keys:
                # already exist
                existing_keys.remove(fn)
            else:
                # read from file and output as a dictionary
                try:
                    self.cache[fn] = xf(fn, self.cwd)
                except Exception as e:
                    logger.info("failed to load file: %s", fn)
                    logger.info("%s", str(e))

        if flag_del:
            for key in existing_keys:
                self.cache.pop(key, None)

        return

    def get_hdf_info(self, fname, fstr=None):
        """
        get the hdf information / hdf structure for fname
        :param fname: input filename
        :param fstr: list of filter string;
        :return: list of strings that contains the hdf information;
        """
        if fname in self.cache:
            return self.cache[fname].get_hdf_info(fstr)
        else:
            return ['None']

    def add_target(self, alist, threshold=64):
        if alist in [[], None]:
            return
        if self.type is None:
            self.type = self.get_type(alist[0])

        single_flag = True

        if len(alist) <= threshold:
            for x in alist:
                if x not in self.target:
                    t = self.get_type(x)
                    if t not in ['Multitau', 'Twotime']:
                        logger.info('Failed to get type for %s', x)
                        continue
                    if self.type is None:
                        self.type = t
                    elif t != self.type:
                        logger.info('Mixed analysis type for %s. Discard', x)
                        single_flag = False
                        continue
                    self.target.append(x)

            self.id_list = create_id(self.target)
        else:
            # if many files are added; then ignore the type check;
            logger.info('type check is disabled. too many files added')
            self.target.extend(alist)
            self.id_list = alist.copy()

        logger.info('length of target = %d' % len(self.target))
        return single_flag

    def clear_target(self):
        self.target.clear()
        self.id_list = None
        self.type = None

    def remove_target(self, rlist):
        if rlist is None or len(self.target) == 0:
            return

        for x in rlist:
            if x in self.target:
                self.target.remove(x)
                self.cache.pop(x, 'None')

        if self.target is None or len(self.target) == 0:
            self.clear_target()
        else:
            self.id_list = create_id(self.target)

    def search(self, val, filter_type='prefix'):
        ans = None
        if filter_type == 'prefix':
            ans = [x for x in self.source if x.startswith(val)]
        elif filter_type == 'substr':
            ans = [x for x in self.source if val in x]
        self.source_search.replace(ans)

        return

    def build(self, path=None, filter_list=('.hdf', '.h5')):
        if path is None:
            path = self.path

        if os.path.isfile(path):
            with open(path, 'r') as f:
                flist = [x[:-1] for x in f]
            self.cwd = os.path.dirname(path)
        elif os.path.isdir(path):
            flist = os.listdir(path)
            self.cwd = path
        else:
            return

        flist = [x for x in flist if get_suffix(x) in filter_list]

        # filter configure files
        flist = [x for x in flist if not x.startswith('.')]
        flist.sort()

        self.source.replace(flist)

        return True


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
