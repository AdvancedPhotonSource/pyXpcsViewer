from PyQt5 import uic, QtWidgets
from helper.utlis import norm_saxs_data
import numpy as np


class PlotWidget(object):
    def __init__(self, ui_fname, tab_widget, name='saxs1d', plot_args=None,
                 data_labels=None):
        super(PlotWidget, self).__init__()
        self.tab = QtWidgets.QWidget()
        tab_widget.addTab(self.tab, name)
        uic.loadUi(ui_fname, self.tab)
        self.plot_args = plot_args
        self.data = None
        self.data_labels = data_labels

    def get_kwargs(self):
        kwargs = {}
        for k in self.plot_args:
            key = self.tab.__dict__[k]
            if isinstance(key, QtWidgets.QDoubleSpinBox):
                val = key.value()
            elif isinstance(key, QtWidgets.QComboBox):
                val = key.currentText()
            kwargs[k] = val
        return kwargs

    def prepare_data(self, target, dloader, labels=None, max_points=1024):
        file_list = target[slice(0, max_points)]
        if labels is None:
            labels = self.data_labels
        self.data = dloader.read_data(labels, file_list)
        return

    def init_plot(self):
        pass

    def redo_plot(self):
        pass

    def save_plot(self):
        pass


class SAXS1D(PlotWidget):
    def __init__(self, tab_widget):
        ui_fname = './ui/saxs1d.ui'
        name = 'saxs1d'
        plot_args = ['pa_offset', 'pa_type', 'pa_norm']
        data_labels = ['Int_2D', 'Iq', 'ql_sta']

        super(SAXS1D, self).__init__(ui_fname, tab_widget, name, plot_args,
                                     data_labels)
        self.setup_ui()

    def setup_ui(self):
        self.tab.pushButton_10.clicked.connect(self.plot)

    def plot(self):
        pass

    def prepare_data(self, target, dloader, max_points=1024):
        super(SAXS1D, self).prepare_data(target, dloader, max_points)
        q = self.data['q'][0]
        Iq = self.data['Iq']
        legend = target[slice(0, max_points)]

        self.data = [q, Iq, legend]

    def init_plot(self, pa_type='log', pa_norm=0, pa_offset=0, max_points=8,
                  legend=None, title=None):

        mp_hdl = self.tab.mp_saxs
        q, Iq, legend = self.data

        Iq, xlabel, ylabel = norm_saxs_data(Iq, q, pa_norm, pa_type)

        xscale = ['linear', 'log'][pa_type % 2]
        yscale = ['linear', 'log'][pa_type // 2]

        num_points = Iq.shape[0]
        for n in range(1, num_points):
            if yscale == 'linear':
                offset = -pa_offset * n * np.max(Iq[n])
                Iq[n] = offset + Iq[n]

            elif yscale == 'log':
                offset = 10 ** (pa_offset * n)
                Iq[n] = Iq[n] / offset

        mp_hdl.show_lines(Iq, xval=q, xlabel=xlabel, ylabel=ylabel,
                          legend=legend)

        mp_hdl.axes.legend()
        mp_hdl.axes.set_xlabel(xlabel)
        mp_hdl.axes.set_ylabel(ylabel)
        mp_hdl.axes.set_title(title)
        mp_hdl.auto_scale(xscale=xscale, yscale=yscale)
        mp_hdl.draw()
        return


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    tabWidget = QtWidgets.QTabWidget(Form)
    a = SAXS1D(tabWidget)
    print(a.get_kwargs())
    # a = SAXS1D_base()
    print(dir(a.tab))
    Form.show()
    sys.exit(app.exec_())
