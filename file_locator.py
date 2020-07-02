import marisa_trie
import os


class FileLocator(object):
    def __init__(self, path):
        self.path = path
        self.trie = None
        self.file_list = None
        self.selected_list = None
        self.build(path)

    def add_target(self, alist):
        if self.selected_list is None:
            self.selected_list = [x for x in alist]
        else:
            self.selected_list += alist

    def remove_target(self, rlist):
        for x in rlist:
            if x in self.selected_list:
                self.selected_list.remove(x)

    def search(self, val):
        ans = self.trie.keys(val)
        return len(ans), ans

    def build(self, path):
        if os.path.isfile(path):
            flist = []
            with open(path, 'r') as f:
                flist = [x[:-1] for x in f]
        elif os.path.isdir(path):
            flist = os.listdir(path)

        # only keep hdf files
        flist = [x for x in flist if '.hdf' in x]
        trie = marisa_trie.Trie(flist)
        self.trie = trie
        self.file_list = flist

        return


def test1():
    fl = FileLocator(path='./data/files.txt')


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path='./data/files.txt')
