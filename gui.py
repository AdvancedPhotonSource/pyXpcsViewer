from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QFileSystemModel
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import QObject, pyqtSlot, QDir
import sys
import os
from pyqtgraph import PlotWidget, ImageWindow
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from data_loader import DataLoader
from file_locator import FileLocator


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        self.show()

        self.dl = None
        self.fl = None
        self.cache = None

        # flist = os.listdir('./data')
        # self.dv = DataLoader('./data', flist)
        # self.avg = self.dv.average()

        # import numpy as np
        # x = np.random.normal(size=1000)
        # y = np.random.normal(size=1000)
        # # self.graphWidget.plot(x, y, pen=None, symbol='o')
        # avg = self.dv.read_data(['Int_2D'])['Int_2D']
        # avg = np.log10(avg + 1E-8)
        # xvals = np.arange(avg.shape[0])
        # self.graphWidget.setImage(avg, xvals=xvals)

        # model = QFileSystemModel()
        # model.setRootPath(QDir.currentPath())
        # self.treeView.setModel(model)
        # self.treeView.setRootIndex(model.index(QDir.currentPath()))

    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # self.centralWidget.file_panel.work_dir.setValue(f)
        f = './data/files2.txt'
        self.work_dir.setText(f)
        self.fl = FileLocator(f)
        self.update_box(self.fl.source_list, mode='source')

    def update_box(self, file_list, mode='source'):
        if mode == 'source':
            self.list_view_source.clear()
            self.list_view_source.addItems(file_list)
            self.box_source.setTitle('Source: %5d' % len(file_list))
        elif mode == 'target':
            self.list_view_target.clear()
            self.list_view_target.addItems(file_list)
            self.box_target.setTitle('Target: %5d' % len(file_list))
        return

    def add_target(self):
        if self.cache is None:
            target = []
            for x in self.list_view_source.selectedIndexes():
                target.append(x.data())
        else:
            target = self.cache
        self.fl.add_target(target)
        self.update_box(self.fl.target_list, mode='target')

    def remove_target(self):
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())
        self.fl.remove_target(rmv_list)
        self.update_box(self.fl.target_list, mode='target')

    def trie_search(self):
        val = self.filter_str.text()
        if len(val) == 0:
            self.update_box(self.fl.source_list, mode='source')
            return
        num, self.cache = self.fl.search(val)
        self.update_box(self.cache, mode='source')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()