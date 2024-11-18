from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import random
import time

# hide the lines in legend
# https://stackoverflow.com/questions/21285885
# matplotlib.rcParams['legend.handlelength'] = 2
# matplotlib.rcParams['legend.numpoints'] = 1

# matplotlib.pyplot.style.use(['science', 'no-latex'])

# https://matplotlib.org/stable/api/markers_api.html
markers = ['o', 'v', '^', '>', '<', 's', 'p', 'h', '*', '+', 'd', 'x']

colors = ('#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf')


def get_color_marker(n):
    mk = markers[n % len(markers)]
    cl = colors[n % len(colors)]
    return (cl, mk)


class NavigationToolbarSimple(NavigationToolbar2QT):
    def __init__(self, *kw, **kwargs):
        super(NavigationToolbarSimple, self).__init__(*kw, **kwargs)

    def mouse_move(self, event):
        # just disable the mose_move event
        pass


class MplCanvasBarH(QtWidgets.QWidget):
    """
    MplWidget combines a MplCanvas with a vertical toolbar
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.hdl = MplCanvas()
        self.navi_toolbar = NavigationToolbarSimple(self.hdl, self)
        self.navi_toolbar.setOrientation(QtCore.Qt.Vertical)
        self.hbl = QHBoxLayout()
        self.hbl.addWidget(self.hdl)
        self.hbl.addWidget(self.navi_toolbar)
        # self.navi_toolbar.setOrientation(QtCore.Qt.Vertical)
        self.setLayout(self.hbl)

    def clear(self):
        self.hdl.clear()
        self.hdl.draw()


class MplCanvasBarV(QWidget):
    """
    MplWidget combines a MplCanvas with a horizontal toolbar
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.hdl = MplCanvas()
        self.navi_toolbar = NavigationToolbar2QT(self.hdl, self)
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.navi_toolbar)
        self.vbl.addWidget(self.hdl)
        self.setLayout(self.vbl)

    def clear(self):
        self.hdl.clear()
        self.hdl.draw()


class MplCanvasBar(QWidget):
    """
    MplWidget combines a MplCanvas with a Toolbar
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.hdl = MplCanvas()
        self.navi_toolbar = NavigationToolbarSimple(self.hdl, self)
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.hdl)
        self.vbl.addWidget(self.navi_toolbar)
        # self.navi_toolbar.setOrientation(QtCore.Qt.Vertical)
        self.setLayout(self.vbl)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=15, height=12, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.shape = None
        self.axes = None
        self.obj = None
        self.line_builder = None
        self.cids = []

    def link_line_builder(self, lb_type=None):
        if lb_type is None:
            self.unlink_line_builder()
        
        if self.line_builder is not None and \
            self.line_builder.lb_type != lb_type:
            self.unlink_line_builder()

        if self.line_builder is None and self.shape == (1, 1):
            self.line_builder = LineBuilder(self.fig, self.axes, lb_type)
            cid1 = self.fig.canvas.mpl_connect('button_press_event',
                                               self.line_builder.mouse_click)
            cid2 = self.fig.canvas.mpl_connect('motion_notify_event',
                                               self.line_builder.mouse_move)
            self.cids = [cid1, cid2]

    def unlink_line_builder(self):
        if self.line_builder is not None:
            for cid in self.cids:
                self.fig.canvas.mpl_disconnect(cid)
            self.line_builder.clear()
            self.line_builder = None

    def subplots(self, n, m, **kwargs):
        self.axes = self.fig.subplots(n, m, **kwargs)
        self.shape = (n, m)
        return self.axes

    def clear(self):
        self.unlink_line_builder()
        self.clear_axes()
        self.fig.clear()
        self.axes = None
        self.obj = None

    def adjust_canvas_size(self, num_col, num_row):
        t = self.parent().parent().parent()
        if t is None:
            aspect = 1 / 1.618
        else:
            aspect = t.height() / self.width()

        min_size = t.height() - 20
        width = self.width()
        canvas_size = max(min_size, int(width / num_col * aspect * num_row))
        self.setMinimumSize(QtCore.QSize(0, canvas_size))

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

    def show_image(self,
                   data,
                   vmin=None,
                   vmax=None,
                   extent=None,
                   cmap='seismic',
                   xlabel=None,
                   ylabel=None,
                   title=None,
                   id_list=None,
                   vline_freq=-1):
        def add_vline(ax, stop, vline_freq):
            if vline_freq < 0:
                return
            for x in np.arange(vline_freq, stop - 1, vline_freq):
                # for x in np.arange(1, stop // vline_freq - 1):
                ax.axvline(x - 0.5, ls='--', lw=0.5, color='black', alpha=0.5)

        if self.axes is None:
            ax = self.subplots(1, 1)
            add_vline(ax, data.shape[1], vline_freq)
            im0 = ax.imshow(data,
                            aspect='auto',
                            cmap=plt.get_cmap(cmap),
                            vmin=vmin,
                            vmax=vmax,
                            extent=extent,
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

    def show_lines(self,
                   data,
                   xlabel=None,
                   ylabel=None,
                   title=None,
                   legend=None,
                   loc='best',
                   rows=None,
                   marker_size=3,
                   ):

        if legend in [None, False]:
            legend = np.arange(len(data))

        if rows in [None, []]:
            alpha = np.ones(len(data)) * 0.75
        else:
            alpha = np.ones(len(data)) * 0.15
            for t in rows:
                if t < len(data):
                    alpha[t] = 1.0

        if isinstance(data, np.ndarray):
            x = np.arange(data.shape[1])
            data2 = []
            for n in range(data.shape[0]):
                data2.append([x, data[n]])
            data = data2

        if self.axes is None or len(data) != len(self.obj):
            ax = self.subplots(1, 1)
            line_obj = []
            for n in range(len(data)):
                cl, mk = get_color_marker(n)
                line = ax.plot(data[n][0], data[n][1], mk + '-',
                               ms=marker_size, alpha=alpha[n], label=legend[n],
                               color=cl, mfc='none')
                line_obj.append(line)
            self.obj = line_obj

            if legend is not None and loc != 'outside':
                ax.legend(loc=loc)
            elif loc == 'outside':
                ax.legend(bbox_to_anchor=(1.03, 1.0), loc='upper left')

        else:
            for n in range(len(data)):
                line, = self.obj[n]
                line.set_data(data[n][0], data[n][1])
                if legend is not None:
                    line.set_label(legend[n])
            self.auto_scale()

        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.fig.tight_layout(rect=(0.07, 0.07, 0.93, 0.93))
        self.draw()
        return

    def show_scatter(self,
                     data,
                     color=None,
                     xlabel=None,
                     ylabel=None,
                     title=None,
                     legend=None,
                     loc='best',
                     alpha=0.85):
        if data.ndim != 2 or data.shape[0] != 2:
            raise ValueError('input data shape not supported')
        x, y = data[0], data[1]
        if color is None:
            color = np.arange(x.size)
        # if legend in [None, False]:
        #     legend = np.arange(len(x))

        if self.axes is not None:
            self.clear()
        ax = self.subplots(1, 1)
        line = ax.scatter(x, y, c=color)
        self.fig.colorbar(line, ax=ax)
        if legend is not None:
            ax.legend(loc=loc)

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

    new_segments = [
        np.array([[x, yt], [x, yb]])
        for x, yt, yb in zip(x, yerr_top, yerr_bot)
    ]

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


class LineBuilder(object):
    '''
        code copied from
        http://chuanshuoge2.blogspot.com/2019/12/matplotlib-mouse-click-event\
            -draw-line.html

    '''
    def __init__(self, fig, ax, lb_type='hline'):
        self.xs = []
        self.ys = []
        self.ax = ax
        self.fig = fig
        self.color = random.choice(colors)
        self.color_hist = []
        self.num_lines = 0
        self.labels = []
        self.curr_time = -1
        self.lb_type = lb_type
        self.reserve_lines = len(self.ax.lines)

    def clear(self):
        self.xs = []
        self.ys = []
        self.color_hist = []
        for n in range(len(self.ax.lines) - self.reserve_lines):
            self.ax.lines.pop()
        for n in range(len(self.labels)):
            label = self.labels.pop()
            label.remove()
        self.fig.canvas.draw()
    
    def plot_line(self):
        if self.lb_type == 'slope':
            xa, xb = self.xs[-2], self.xs[-1]
            ya, yb = self.ys[-2], self.ys[-1]
            dn_term = np.log(xa / xb)
            if dn_term == 0:
                dn_term = 1E-8
            slope = np.log(ya / yb) / dn_term
            txt = '$q^{%.2f}$' % slope 

            # compute position to add label, notice the plot should be 
            # logx-logy; slightly offset cen_x to make the label more clear
            cen_x = np.sqrt(xa * xb * 1.2)
            cen_y = np.sqrt(ya * yb * 1.2)

        elif self.lb_type == 'hline':
            xa, xb = self.xs[-2], self.xs[-1]
            ya, yb = self.ys[-1], self.ys[-1]
            delta_x = 2 * np.pi / abs(xa - xb)
            txt = '$\\Delta_x={%.1f}\\AA$' % delta_x 

            cen_x = np.sqrt(xa * xa)
            cen_y = np.sqrt(ya * yb * 0.3)
        else:
            return

        line, = self.ax.plot([xa, xb], [ya, yb], self.color)
        label = self.ax.annotate(txt, (cen_x, cen_y), color=self.color)
        self.labels.append(label)

        line.figure.canvas.draw()
        self.num_lines += 1
        self.color_hist.append(self.color)
        self.color = random.choice(colors)
    
    def mouse_click(self, event):
        if not event.inaxes:
            return

        # left click
        if event.button == 1:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)

            if self.lb_type == 'hline':
                line = self.ax.axvline(event.xdata, color=self.color, ls=':')
                line.figure.canvas.draw()

            # add a line to plot if it has 2 points
            if len(self.xs) % 2 == 0 and len(self.xs) > 0:
                self.plot_line()

        # right click
        if event.button == 3:
            if len(self.xs) == 0:
                return
            else:
                self.xs.pop()
                self.ys.pop()
                if self.lb_type == 'hline':
                    self.ax.lines.pop()
            # delete last line drawn if the line is missing a point,
            # never delete the original stock plot
            if len(self.xs) % 2 == 1 and \
                len(self.ax.lines) > self.reserve_lines:
                self.ax.lines.pop()
                self.num_lines -= 1
                self.color = self.color_hist.pop()
                label = self.labels.pop()
                label.remove()
            # refresh plot
            self.fig.canvas.draw()

    def mouse_move(self, event):
        if self.lb_type is None or not event.inaxes:
            return
        # draw temporary line from a single point to the mouse position
        # delete the temporary line when mouse move to another position
        if time.perf_counter() - self.curr_time < 0.1:
            return

        self.curr_time = time.perf_counter()
        if len(self.xs) % 2 == 1:
            if self.lb_type == 'slope':
                line, = self.ax.plot([self.xs[-1], event.xdata],
                                     [self.ys[-1], event.ydata], self.color)
            else:
                line, = self.ax.plot([self.xs[-1], event.xdata],
                                     [event.ydata, event.ydata], self.color)
            line.figure.canvas.draw()
            self.ax.lines.pop()
