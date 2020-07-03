import marisa_trie
import os


class FileLocator(object):
    def __init__(self, path):
        self.path = path
        self.cwd = None
        self.trie = None
        self.source_list = None
        self.target_list = None
        self.build(path)

    def add_target(self, alist):
        if self.target_list is None:
            self.target_list = [x for x in alist]
        else:
            for x in alist:
                # avoid multiple add
                if x not in self.target_list:
                    self.target_list.append(x)

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

        trie = marisa_trie.Trie(flist)
        self.trie = trie
        self.source_list = flist

        return


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
