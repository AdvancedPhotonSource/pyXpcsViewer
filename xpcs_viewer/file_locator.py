import os
from .xpcs_file import XpcsFile as xf
import logging
from .helper.listmodel import ListDataModel
import traceback


logger = logging.getLogger(__name__)


def get_suffix(file_name):
    _, suffix = os.path.splitext(file_name)
    return suffix


class FileLocator(object):
    def __init__(self, path):
        self.path = path
        self.source = ListDataModel()
        self.source_search = ListDataModel()
        self.target = ListDataModel()
        self.cache = {}

    def set_path(self, path):
        self.path = path

    def clear(self):
        self.source.clear()
        self.source_search.clear()


    def get_xf_list(self, rows=None, filter_atype=None):
        """
        get the cached xpcs_file list;
        :param max_points: maxiaml number of xpcs_files to get
        :param rows: a list of index to select; if None is given, then use
        :return: list of xpcs_file objects;
        """
        if not rows:
            selected = list(range(len(self.target)))
        else:
            selected = rows

        ret = []
        for n in selected:
            fn = self.target[n]
            xf_obj = self.cache[fn]
            if filter_atype is None:
                ret.append(xf_obj)
            elif filter_atype in xf_obj.atype:
                ret.append(xf_obj)
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
                    temp = xf(fn, self.path, label_style=label_style)
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
        else:
            # if many files are added; then ignore the type check;
            logger.info('type check is disabled. too many files added')
            self.target.extend(alist)

        logger.info('length of target = %d' % len(self.target))
        return single_flag

    def clear_target(self):
        self.target.clear()

    def remove_target(self, rlist):
        if rlist is None or len(self.target) == 0:
            return

        for x in rlist:
            if x in self.target:
                self.target.remove(x)
                self.cache.pop(x, 'None')

        if self.target is None or len(self.target) == 0:
            self.clear_target()

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
        flist = os.listdir(path)
        self.path = path
        flist = [x for x in flist if os.path.splitext(x)[1] in filter_list]

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



if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
