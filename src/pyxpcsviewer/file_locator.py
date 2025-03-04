import os
from .xpcs_file import XpcsFile as XF 
import logging
from .helper.listmodel import ListDataModel
import traceback
from functools import lru_cache
import datetime


logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def create_xpcs_dataset(fname):
    """
    create a xpcs_file objects from a given path
    """
    try:
        temp = XF(fname)
    except Exception as e:
        logger.error("failed to load file: %s", fname)
        logger.error(traceback.format_exc())
        temp = None
    return temp


class FileLocator(object):
    def __init__(self, path):
        self.path = path
        self.source = ListDataModel()
        self.source_search = ListDataModel()
        self.target = ListDataModel()
        self.cache = {}
        self.timestamp = None

    def set_path(self, path):
        self.path = path

    def clear(self):
        self.source.clear()
        self.source_search.clear()

    def get_xf_list(self, rows=None, filter_atype=None, filter_fitted=False):
        """
        get the cached xpcs_file list;
        :param rows: a list of index to select; if None is given, then use
        :return: list of xpcs_file objects;
        """
        if not rows:
            selected = list(range(len(self.target)))
        else:
            selected = rows

        ret = []
        for n in selected:
            full_fname = os.path.join(self.path, self.target[n])
            if full_fname not in self.cache:
                xf_obj = create_xpcs_dataset(full_fname)
                self.cache[full_fname] = xf_obj
            xf_obj = self.cache[full_fname]
            if xf_obj.fit_summary is None and filter_fitted:
                continue
            if filter_atype is None:
                ret.append(xf_obj)
            elif filter_atype in xf_obj.atype:
                ret.append(xf_obj)
        return ret

    def get_hdf_info(self, fname, filter_str=None):
        """
        get the hdf information / hdf structure for fname
        :param fname: input filename
        :param fstr: list of filter string;
        :return: list of strings that contains the hdf information;
        """
        xf_obj = create_xpcs_dataset(os.path.join(self.path, fname))
        return xf_obj.get_hdf_info(filter_str)

    def add_target(self, alist, threshold=256, preload=True):
        if not alist:
            return
        if preload and len(alist) <= threshold:
            for fn in alist:
                if fn in self.target:
                    continue
                full_fname = os.path.join(self.path, fn)
                xf_obj = create_xpcs_dataset(full_fname)
                if xf_obj is not None:
                    self.target.append(fn)
                    self.cache[full_fname] = xf_obj
        else:
            logger.info('type check is disabled. too many files added')
            self.target.extend(alist)
        logger.info('length of target = %d' % len(self.target))
        self.timestamp = str(datetime.datetime.now())
        return

    def clear_target(self):
        self.target.clear()
        self.cache.clear()

    def remove_target(self, rlist):
        for x in rlist:
            if x in self.target:
                self.target.remove(x)
            self.cache.pop(os.path.join(self.path, x), None)
        if not self.target:
            self.clear_target()
        self.timestamp = str(datetime.datetime.now())

    def reorder_target(self, row, direction='up'):
        size = len(self.target)
        assert 0 <= row < size, 'check row value'
        if (direction == 'up' and row == 0) or \
           (direction == 'down' and row == size - 1):
            return -1

        item = self.target.pop(row)
        pos = row - 1 if direction == 'up' else row + 1
        self.target.insert(pos, item)
        idx = self.target.index(pos)
        self.timestamp = str(datetime.datetime.now())
        return idx

    def search(self, val, filter_type='prefix'):
        assert filter_type in ['prefix', 'substr'], 'filter_type must be prefix or substr'
        if filter_type == 'prefix':
            selected = [x for x in self.source if x.startswith(val)]
        elif filter_type == 'substr':
            filter_words = val.split()  # Split search query by whitespace
            selected = [x for x in self.source if all(t in x for t in filter_words)]
        self.source_search.replace(selected)
        return

    def build(self, path=None, filter_list=('.hdf', '.h5'),
              sort_method='Filename'):
        self.path = path
        flist = [
            entry.name for entry in os.scandir(path) if entry.is_file() 
            and entry.name.lower().endswith(filter_list) 
            and not entry.name.startswith('.')
        ]
        if sort_method.startswith('Filename'):
            flist.sort()
        elif sort_method.startswith('Time'):
            flist.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
        elif sort_method.startswith('Index'):
            pass

        if sort_method.endswith('-reverse'):
            flist.reverse()
        self.source.replace(flist)
        return True


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
