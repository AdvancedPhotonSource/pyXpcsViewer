import marisa_trie
import os


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


def create_id(in_list, repeat=1, keep_slice=None):
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
    def __init__(self, path):
        self.path = path
        self.cwd = None
        self.trie = None
        self.source_list = None
        self.target_list = None
        self.id_list = None
        self.build(path)

    def add_target(self, alist):
        if self.target_list is None:
            self.target_list = [x for x in alist]
        else:
            for x in alist:
                # avoid multiple add
                if x not in self.target_list:
                    self.target_list.append(x)
        self.id_list = create_id(self.target_list, 1)

    def remove_target(self, rlist):
        for x in rlist:
            if x in self.target_list:
                self.target_list.remove(x)

    def search(self, val):
        ans = self.trie.keys(val)
        return len(ans), ans

    def build(self, path):
        if os.path.isfile(path):
            flist = []
            with open(path, 'r') as f:
                flist = [x[:-1] for x in f]
            self.cwd = os.path.dirname(path)
        elif os.path.isdir(path):
            flist = os.listdir(path)
            self.cwd = path

        # only keep hdf files
        flist = [x for x in flist if '.hdf' in x]
        # filter configure files
        flist = [x for x in flist if not x.startswith('.')]

        self.trie = marisa_trie.Trie(flist)
        self.source_list = flist

        return


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
