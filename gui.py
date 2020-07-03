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
import numpy as np
# from xpcs_ui import

# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure
#
#
# class MplCanvas(FigureCanvasQTAgg):
#
#     def __init__(self, parent=None, width=5.1, height=3.2, dpi=100):
#         fig = Figure(figsize=(width, height), dpi=dpi)
#         self.axes = fig.add_subplot(111)
#         super(MplCanvas, self).__init__(fig)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        # self.f1 = MplCanvas()
        self.show()

        self.dl = None
        self.fl = None
        self.cache = None
        self.load_path()


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

    def load_data(self):
        self.dl = DataLoader(prefix=self.fl.cwd,
                             file_list=self.fl.target_list)
        res = self.dl.get_stability_data()

        # data = res['Int_t']
        data = res['Iq']
        # self.graphWidget.setImage(data)
        self.mf1.subplots(2, 1)
        for n in range(data.shape[0]):
        #     self.f0.plot(np.log10(data[n]), pen=pg.mkPen('b', width=1))
        #     # self.mf1.axes[0].plot(np.log10(res['Iq']))
            self.mf1.axes[1].plot(res['Int_t_statistics'][n, :, 0], '-o', lw=1, alpha=0.5)
        # self.mf1.axes[1].imshow((res['Int_t'][:, :, 0]).T, aspect='auto')

        self.mf1.draw()
        #     self.graphWidget.setImage()
        # saxs = self.dl.get_saxs()
        # xvals = np.arange(saxs.shape[0])
        # self.graphWidget.setImage(saxs, xvals=xvals)
        # self.f1.plot(x, y, pen=None, symbol='o')


    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # self.centralWidget.file_panel.work_dir.setValue(f)
        f = './data/files2.txt'
        self.work_dir.setText(f)
        self.fl = FileLocator(f)
        self.update_box(self.fl.source_list, mode='source')

        # for debug
        self.list_view_source.selectAll()
        self.add_target()

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
        target = []
        for x in self.list_view_source.selectedIndexes():
            target.append(x.data())

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
        self.list_view_source.selectAll()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()