# import marisa_trie
import os
from .xpcs_file import XpcsFile as xf
import logging
from .helper.listmodel import ListDataModel
import traceback


logger = logging.getLogger(__name__)


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


class FileLocator(object):
    def __init__(self, path):
        self.path = path
        self.cwd = None
        self.trie = None
        self.source = ListDataModel()
        self.source_search = ListDataModel()
        self.target = ListDataModel()
        self.id_list = None
        self.cache = {}
    
    def set_path(self, path):
        self.path = path
    
    def clear(self):
        self.source.clear()
        self.source_search.clear()

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
             flag_del=True, label_style=None):

        if file_list in [None, []]:
            file_list = self.target

        total_num = min(max_number, len(file_list))
        existing_keys = list(self.cache.keys())

        for n in range(total_num):
            fn = self.target[n]
            if progress_bar is not None:
                progress_bar.setValue(int((n + 1) / total_num * 100))

            if fn in existing_keys:
                # already exist
                existing_keys.remove(fn)
            else:
                # read from file and output as a dictionary
                try:
                    temp = xf(fn, self.cwd, label_style=label_style)
                    self.cache[fn] = temp
                except Exception as e:
                    logger.error("failed to load file: %s", fn)
                    logger.error(traceback.format_exc())

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

        single_flag = True
        if len(alist) <= threshold:
            for x in alist:
                if x not in self.target:
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
            # split by white space
            filter_str = val.split()
            def func(x):
                for t in filter_str:
                    if t not in x:
                        return False
                return True
            ans = [x for x in self.source if func(x)]
        self.source_search.replace(ans)

        return

    def build(self, path=None, filter_list=('.hdf', '.h5'),
              sort_method='Filename'):
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

        if sort_method.startswith('Filename'):
            flist.sort()
        elif sort_method.startswith('Time'):
            flist.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
        elif sort_method.startswith('Index'):
            def func(fname):
                try:
                    # may fail when fname doesn't contain any number
                    # get the start of a number
                    start = [x.isdigit() for x in fname].index(True)
                    # get the end of the number
                    end = [x.isdigit() for x in fname[start:]].index(False)
                    # end = fname.find('_')
                    end = end + start
                    ans = int(fname[start:end])
                except Exception as e:
                    ans = fname
                finally:
                    return ans
            flist.sort(key=func)

        if sort_method.endswith('-reverse'):
            flist.reverse()

        self.source.replace(flist)

        return True


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
