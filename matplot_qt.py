from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
import matplotlib
matplotlib.pyplot.style.use(['science', 'no-latex'])


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

    def auto_scale(self):
        if self.axes is None:
            return
        else:
            if self.shape == (1, 1):
                self.axes.relim()
                self.axes.autoscale_view(True, True, True)
            else:
                for ax in self.axes.ravel():
                    ax.relim()
                    ax.autoscale_view(True, True, True)

    def update_lin(self, loc, x, y):
        if self.obj is None:
            return
        lin_obj, = self.obj['lin'][loc]
        lin_obj.set_data(x, y)
        return

    def update_err(self, loc, x, y, y_error):
        if self.obj is None:
            return
        err_obj = self.obj['err'][loc]
        adjust_yerr(err_obj, x, y, y_error)
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
