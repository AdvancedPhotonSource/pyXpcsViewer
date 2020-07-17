from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5 import QtWidgets
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.pyplot.style.use(['science', 'no-latex'])


markers = [
    "o", "v", "^", "<", ">", "s", "p", "P", "*", "h", "H"
]





class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5.1, height=3.2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.shape = None
        self.axes = None
        self.obj = None

    def subplots(self, n, m, **kwargs):
        self.axes = self.fig.subplots(n, m, **kwargs)
        self.shape = (n, m)
        return self.axes

    def clear(self):
        self.clear_axes()
        self.fig.clear()
        self.axes = None
        self.obj = None

    def clear_axes(self):
        if self.axes is None:
            return
        else:
            if self.shape == (1, 1):
                self.axes.clear()
            else:
                for ax in self.axes.ravel():
                    ax.clear()

    def auto_scale(self, ylim=None, xlim=None, xscale=None, yscale=None):
        if self.axes is None:
            return
        else:
            for ax in np.array(self.axes).ravel():
                if xscale is not None:
                    ax.set_xscale(xscale)
                if yscale is not None:
                    ax.set_yscale(yscale)
                ax.relim()
                ax.autoscale_view(True, True, True)
                if ylim is not None:
                    ax.set_ylim(ylim)
                if xlim is not None:
                    ax.set_xlim(xlim)

    def update_lin(self, loc, x, y, visible=True):
        if self.obj is None:
            return
        lin_obj, = self.obj['lin'][loc]
        lin_obj.set_data(x, y)
        lin_obj.set_visible(visible)
        return

    def update_err(self, loc, x, y, y_error):
        if self.obj is None:
            return
        err_obj = self.obj['err'][loc]
        adjust_yerr(err_obj, x, y, y_error)
        return

    def show_image(self, data, vmin=None, vmax=None, extent=None,
                   cmap='seismic', xlabel=None, ylabel=None, title=None,
                   id_list=None, vline_freq=-1):

        def add_vline(ax, stop, vline_freq):
            if vline_freq < 0:
                return
            for x in np.arange(vline_freq, stop - 1, vline_freq):
            # for x in np.arange(1, stop // vline_freq - 1):
                ax.axvline(x - 0.5, ls='--', lw=0.5, color='black', alpha=0.5)

        if self.axes is None:
            ax = self.subplots(1, 1)
            add_vline(ax, data.shape[1], vline_freq)
            im0 = ax.imshow(data, aspect='auto',
                            cmap=plt.get_cmap(cmap),
                            vmin=vmin, vmax=vmax, extent=extent,
                            interpolation=None)
            self.fig.colorbar(im0, ax=ax)

            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)

            # when there are too many points, avoid labeling.
            # if data.shape < 20:
            #     ax.set_xticks(np.arange(data.shape[1]))
            #     ax.set_xticklabels(id_list[0: data.shape[1]])

            self.obj = [im0]
            self.fig.tight_layout()
        else:
            self.obj[0].set_data(data)
            self.obj[0].set_clim(vmin, vmax)
            self.axes.set_title(title)
            self.axes.set_xlabel(xlabel)
            self.axes.set_ylabel(ylabel)

        self.draw()
        return

    def show_lines(self, data, xval=None, xlabel=None, ylabel=None,
                   title=None, legend=None, loc='best', alpha=0.85):
        if xval is None:
            xval = np.arange(data.shape[1])

        if legend in [None, False]:
           legend = np.arange(data.shape[0])

        if self.axes is None or data.shape[0] != len(self.obj):
            ax = self.subplots(1, 1)
            line_obj = []
            for n in range(data.shape[0]):
                mk = markers[n % len(markers)]
                line = ax.plot(xval, data[n], mk + '--', ms=3,
                               alpha=alpha, label=legend[n])
                line_obj.append(line)
            self.obj = line_obj

            if legend is not None:
                ax.legend(loc=loc)

        else:
            for n in range(data.shape[0]):
                line, = self.obj[n]
                line.set_data(xval, data[n])
                if legend is not None:
                    line.set_label(legend[n])
            self.auto_scale()

        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.draw()
        return

    def show_scatter(self, data, xlabel=None, ylabel=None,
                   title=None, legend=None, loc='best', alpha=0.85):
        if data.ndim != 2 or data.shape[0] != 2:
            raise ValueError('input data shape not supported')
        x, y = data[0], data[1]
        c = np.arange(x.size)

        # if legend in [None, False]:
        #     legend = np.arange(len(x))

        if self.axes is None:
            ax = self.subplots(1, 1)
            line_obj = []
            line = ax.scatter(x, y, c=c)
            self.fig.colorbar(line, ax=ax)
            line_obj.append(line)
            self.obj = line_obj
            if legend is not None:
                ax.legend(loc=loc)

        else:
            line, = self.obj[0]
            line.set_data(x, y)
            if legend is not None:
                line.set_label(legend[0])
            self.auto_scale()

        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.draw()
        return


# https://github.com/matplotlib/matplotlib/issues/4556
def adjust_yerr(err_obj, x, y, y_error):
    # not using error top / bot bar;
    # ln, (err_top, err_bot), (bars, ) = err_obj
    ln, _, (bars, ) = err_obj
    ln.set_data(x, y)

    yerr_top = y + y_error
    yerr_bot = y - y_error

    # err_top.set_ydata(yerr_top)
    # err_bot.set_ydata(yerr_bot)

    new_segments = [np.array([[x, yt], [x, yb]]) for
                    x, yt, yb in zip(x, yerr_top, yerr_bot)]

    bars.set_segments(new_segments)


MplToolbar = NavigationToolbar2QT
# class MplToolbar(MplCanvas):
#     def __init__(self, **kwargs):
#         super(MplCanvas, self).__init__(**kwargs)
#         toolbar = NavigationToolbar2QT(self.fig, self)
#         layout = QtWidgets.QVBoxLayout()
#         layout.addWidget(toolbar)
#         layout.addWidget(self)
#
#         widget = QtWidgets.QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)