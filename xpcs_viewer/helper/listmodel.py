from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class ListDataModel(QtCore.QAbstractListModel):
    def __init__(self, input_list=None, max_display=16384) -> None:
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list
        self.max_display = max_display

    # overwrite parent method
    def data(self, index, role):
        if role == Qt.DisplayRole:
            content = self.input_list[index.row()]
            return str(content)

    # overwrite parent method
    def rowCount(self, index):
        return min(self.max_display, len(self.input_list))

    def extend(self, new_input_list):
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def append(self, new_item):
        self.input_list.append(new_item)
        self.layoutChanged.emit()

    def replace(self, new_input_list):
        self.input_list.clear()
        self.extend(new_input_list)

    def __len__(self):
        return len(self.input_list)

    def __getitem__(self, i):
        return self.input_list[i]

    def copy(self):
        return self.input_list.copy()
        self.layoutChanged.emit()

    def remove(self, x):
        self.input_list.remove(x)
        self.layoutChanged.emit()

    def clear(self):
        self.input_list.clear()
        self.layoutChanged.emit()


class TableDataModel(QtCore.QAbstractTableModel):
    def __init__(self, input_list=None, max_display=16384) -> None:
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list
        self.max_display = max_display
        self.xlabels = ['id', 'size', 'progress', 'time', 'ETA (s)',
                        'finish', 'name']

    # overwrite parent method
    def data(self, index, role):
        if role == Qt.DisplayRole:
            x = self.input_list[index.row()]
            ret = [x.jid, x.size, x._progress, x.stime, x.eta, x.etime,
                   x.short_name]
            return ret[index.column()]

    # overwrite parent method
    def rowCount(self, index):
        return min(self.max_display, len(self.input_list))

    # overwrite parent method
    def columnCount(self, index):
        return len(self.xlabels)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.xlabels[section]

    def extend(self, new_input_list):
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def append(self, new_item):
        self.input_list.append(new_item)
        self.layoutChanged.emit()

    def replace(self, new_input_list):
        self.input_list.clear()
        self.extend(new_input_list)

    def pop(self, index):
        if 0 <= index < self.__len__():
            self.input_list.pop(index)
            self.layoutChanged.emit()

    def __len__(self):
        return len(self.input_list)

    def __getitem__(self, i):
        return self.input_list[i]

    def copy(self):
        return self.input_list.copy()

    def remove(self, x):
        self.input_list.remove(x)

    def clear(self):
        self.input_list.clear()


def test():
    a = ['a', 'b', 'c']
    model = ListDataModel(a)
    for n in range(len(model)):
        print(model[n])


if __name__ == "__main__":
    test()
