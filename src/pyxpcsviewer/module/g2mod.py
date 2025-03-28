import numpy as np
from matplotlib.ticker import FormatStrFormatter
import pyqtgraph as pg
import logging
import matplotlib.pyplot as plt


pg.setConfigOption("foreground", pg.mkColor(80, 80, 80))
# pg.setConfigOption("background", 'w')
logger = logging.getLogger(__name__)

fn_tuple = None

# colors converted from
# https://matplotlib.org/stable/tutorials/colors/colors.html
# colors = ('#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
#           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf')

colors = (
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
)


# https://www.geeksforgeeks.org/pyqtgraph-symbols/
symbols = ['o', 't', 't1', 't2', 't3', 's', 'p', 'h', 'star', '+', 'd', 'x']


def create_slice(arr, x_range):
    start, end = 0, arr.size - 1

    # switch order if lower > upper
    if x_range is not None and x_range[0] > x_range[1]:
        temp = list(x_range)
        x_range = [temp[1], temp[0]]

    # return all range for None and invalid inputs
    if x_range is None or x_range[0] > np.max(arr) or x_range[1] < np.min(arr):
        return slice(start, end + 1)

    while arr[start] < x_range[0]:
        start += 1
        if start == arr.size:
            break

    while arr[end] >= x_range[1]:
        end -= 1
        if end <= 0:
            break

    return slice(start, end + 1)


def get_data(xf_list, q_range=None, t_range=None):
    for xf in xf_list:
        if 'Multitau' not in xf.atype:
            return False, None, None, None, None

    flag = True
    tel, g2, dq, g2_err, labels = [], [], [], [], []
    for fc in xf_list:
        _tel, _dq, _g2, _g2_err, _labels = fc.get_g2_data(qrange=q_range, trange=t_range)
        tel.append(_tel)
        dq.append(_dq)
        g2.append(_g2)
        g2_err.append(_g2_err)
        labels.append(_labels)

    return flag, tel, dq, g2, g2_err, labels


def compute_geometry(g2, plot_type):
    """
    compute the number of figures and number of plot lines for a given type
    and dataset;
    :param g2: input g2 data; 2D array; dim0: t_el; dim1: q_vals
    :param plot_type: string in ['multiple', 'single', 'single-combined']
    :return: tuple of (number_of_figures, number_of_lines)
    """
    if plot_type == 'multiple':
        num_figs = g2[0].shape[1]
        num_lines = len(g2)
    elif plot_type == 'single':
        num_figs = len(g2)
        num_lines = g2[0].shape[1]
    elif plot_type == 'single-combined':
        num_figs = 1
        num_lines = g2[0].shape[1] * len(g2)
    else:
        raise ValueError('plot_type not support.')
    return num_figs, num_lines


def pg_plot(hdl, xf_list, q_range, t_range, y_range,
            y_auto=False, num_col=4, rows=None,
            offset=0, show_fit=False, show_label=False, bounds=None,
            fit_flag=None, plot_type='multiple', subtract_baseline=True,
            marker_size=5, label_size=4, fit_func='single'):

    flag, tel, dq, g2, g2_err, labels = get_data(xf_list, q_range=q_range,
                                         t_range=t_range)
    num_figs, num_lines = compute_geometry(g2, plot_type)

    num_data, num_qval = len(g2), g2[0].shape[1]
    # col and rows for the 2d layout
    col = min(num_figs, num_col)
    row = (num_figs + col - 1) // col

    if len(rows) == 0:
        rows = list(range(len(xf_list)))

    hdl.adjust_canvas_size(num_col=col, num_row=row)
    hdl.clear()
    # a bug in pyqtgraph; the log scale in x-axis doesn't apply
    t0_range = np.log10(t_range)

    axes = []
    for n in range(num_figs):
        i_col = n % col
        i_row = n // col
        t = hdl.addPlot(row=i_row, col=i_col)
        axes.append(t)
        if show_label:
            t.addLegend(offset=(-1, 1), labelTextSize='9pt',
                        verSpacing=-10)

        t.setMouseEnabled(x=False, y=y_auto)

    for m in range(num_data):
        # default base line to be 1.0; used for non-fitting or fit error cases
        baseline_offset = np.ones(num_qval)
        if show_fit:
            fit_summary = xf_list[m].fit_g2(q_range, t_range, bounds, fit_flag,
                                            fit_func)
            if fit_summary is not None and subtract_baseline:
                # make sure the fitting is successful
                if fit_summary['fit_line'][n].get('success', False):
                    baseline_offset = fit_summary['fit_val'][:, 0, 3]

        for n in range(num_qval):
            color = colors[rows[m] % len(colors)]
            label = None
            if plot_type == 'multiple':
                ax = axes[n]
                title = labels[m][n] 
                label = xf_list[m].label
                if m == 0:
                    ax.setTitle(title)
            elif plot_type == 'single':
                ax = axes[m]
                # overwrite color; use the same color for the same set;
                color = colors[n % len(colors)]
                title = xf_list[m].label
                # label = labels[m][n] 
                ax.setTitle(title)
            elif plot_type == 'single-combined':
                ax = axes[0]
                label = xf_list[m].label + labels[m][n]

            ax.setLabel('bottom', 'tau (s)')
            ax.setLabel('left', 'g2')

            symbol = symbols[rows[m] % len(symbols)]

            x = tel[m]
            # normalize baseline
            y = g2[m][:, n] - baseline_offset[n] + 1.0 + m * offset
            y_err = g2_err[m][:, n]

            pg_plot_one_g2(ax, x, y, y_err, color, label=label, symbol=symbol,
                           symbol_size=marker_size)

            ax.setRange(xRange=t0_range)

            if not y_auto:
                ax.setRange(yRange=y_range)

            if show_fit and fit_summary is not None:
                if fit_summary['fit_line'][n].get('success', False):
                    y_fit = fit_summary['fit_line'][n]['fit_y'] + m * offset
                    # normalize baseline
                    y_fit = y_fit - baseline_offset[n] + 1.0
                    ax.plot(fit_summary['fit_line'][n]['fit_x'], y_fit,
                            pen=pg.mkPen(color, width=2.5))
    return


def pg_plot_one_g2(ax, x, y, dy, color, label, symbol, symbol_size=5):
    pen = pg.mkPen(color=color, width=2)

    line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy,
                           pen=pen)
    pen = pg.mkPen(color=color, width=1)
    ax.plot(x, y, pen=None, symbol=symbol, name=label, symbolSize=symbol_size,
            symbolPen=pen, symbolBrush=pg.mkBrush(color=(*color, 0)))

    ax.setLogMode(x=True, y=None)
    ax.addItem(line)
    return
