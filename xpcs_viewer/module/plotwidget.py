from PyQt5 import uic, QtWidgets
from helper.utlis import norm_saxs_data
import numpy as np
from saxs1d import Ui_Form as Saxs1DUi


class PlotWidget(object):
    def __init__(self, name='saxs1d', plot_args=None, data_labels=None):
        super(PlotWidget, self).__init__()
        self.plot_args = plot_args
        self.data = []
        self.data_labels = data_labels

    def get_kwargs(self, keys=None):
        if keys is None:
            keys = self.plot_args

        kwargs = {}
        for k in keys:
            key = self.__dict__[k]
            if isinstance(key, QtWidgets.QDoubleSpinBox):
                val = key.value()
            elif isinstance(key, QtWidgets.QComboBox):
                val = key.currentText()
            kwargs[k] = val
        return kwargs

    def _prepare_data(self, target, ds, labels=None, max_points=1024):
        file_list = target[slice(0, max_points)]
        if labels is None:
            labels = self.data_labels
        self.data = ds.read_data(labels, file_list)
        return

    def init_plot(self):
        pass

    def redo_plot(self):
        pass

    def save_plot(self):
        pass


class SAXS1D(PlotWidget, Saxs1DUi):
    def __init__(self, parent):
        ui_fname = './ui/saxs1d.ui'
        name = 'saxs1d'
        plot_args = ['pa_offset', 'pa_type', 'pa_norm']
        data_labels = ['Int_2D', 'Iq', 'ql_sta']

        PlotWidget.__init__(self, name, plot_args, data_labels)
        Saxs1DUi.__init__(self)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # reuse setupUi method from Ui
        self.setupUi(self.parent)
        self.pushButton_10.clicked.connect(self.plot)

    def plot(self):
        print(self.get_kwargs())

    def prepare_data(self, target, dloader, max_points=1024):
        self.prepare_data(target, dloader, max_points)
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
    a = SAXS1D(Form)
    Form.show()
    sys.exit(app.exec_())
