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
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('xpcs.ui', self) # Load the .ui file
        self.show() # Show the GUI
        self.selected_record = set()

        flist = os.listdir('./data')
        self.dv = DataLoader('./data', flist)
        self.avg = self.dv.average()

        import numpy as np
        x = np.random.normal(size=1000)
        y = np.random.normal(size=1000)
        # self.graphWidget.plot(x, y, pen=None, symbol='o')
        avg = self.dv.read_data(['Int_2D'])['Int_2D']
        avg = np.log10(avg + 1E-8)
        xvals = np.arange(avg.shape[0])
        self.graphWidget.setImage(avg, xvals=xvals)

        # model = QFileSystemModel()
        # model.setRootPath(QDir.currentPath())
        # self.treeView.setModel(model)
        # self.treeView.setRootIndex(model.index(QDir.currentPath()))

    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # self.centralWidget.file_panel.work_dir.setValue(f)
        f = './'
        self.work_dir.setText(f)
        all_files = os.listdir(f)

        self.file_list.clear()

        for x in all_files:
            # filter configure files
            if x.startswith('.'):
                continue

            self.file_list.addItem(x)
            row_position = self.file_table.rowCount()
            self.file_table.insertRow(row_position)
            self.file_table.setItem(row_position, 0, QTableWidgetItem(x))


    def add_target(self):
        for x in self.file_list.selectedIndexes():
            f = x.data()
            if f not in self.selected_record:
                self.selected_record.add(f)
                self.selected_list.addItem(f)

    def remove_target(self):
        for x in self.selected_list.selectedIndexes():
            f = x.data()
            self.selected_record.remove(f)
            self.selected_list.takeItem(x.row())



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()