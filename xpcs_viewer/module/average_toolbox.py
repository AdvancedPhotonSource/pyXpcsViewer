import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class DataModel(QtCore.QAbstractListModel):
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
        self.input_list.append(new_input_list)


class AverageToolbox(object):
    def __init__(self) -> None:
        super().__init__()
        self.model = DataModel()
    
    def update_data(self, new_list):
        self.model.update_data(new_list)


