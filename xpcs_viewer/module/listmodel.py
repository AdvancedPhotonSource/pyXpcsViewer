import sys
from PyQt5 import QtCore, QtGui, QtWidget
from PyQt5.QtCore import QObject, Qt, pyqtSlot


class ListDataModel(QtCore.QAbstractListModel):
    def __init__(self, input_list=None) -> None:
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.input_list[index.row()]
            return text

    def rowCount(self, index):
        return len(self.input_list)

    def update_data(self, new_input_list):
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def at(self, index):
        return self.input_list[index]

    def __len__(self):
        return len(self.input_list)
