import numpy as np
from matplotlib.ticker import FormatStrFormatter
import pyqtgraph as pg
import logging
from ..helper.fitting import fit_xpcs


pg.setConfigOption("foreground", pg.mkColor(80, 80, 80))
# pg.setConfigOption("background", 'w')
logger = logging.getLogger(__name__)

fn_tuple = None
# colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
colors = [
    (220, 0, 0),
    (0, 220, 0),
    (0, 0, 220),
    (0, 176, 80),
    (0, 32, 96),
    (255, 0, 0),
    (0, 176, 240),
    (0, 32, 96),
    (255, 164, 0),
    (146, 208, 80),
    (0, 112, 192),
    (112, 48, 160),
    (54, 96, 146),
    (150, 54, 52),
    (118, 147, 60),
    (96, 73, 122),
    (49, 134, 155),
    (226, 107, 10),
]

symbols = ['o', 's', 't', 'd', '+']


def create_slice(arr, x_range):
    start, end = 0, arr.size - 1
    if x_range is None:
        return slice(start, end + 1)

    while arr[start] < x_range[0]:
        start += 1
        if start == arr.size:
            break

    while arr[end] >= x_range[1]:
        end -= 1
        if end == 0:
            break

    return slice(start, end + 1)


def get_data(xf_list, q_range=None, t_range=None):
    logger.info('qrange is %s', str(q_range))
    tslice = create_slice(xf_list[0].t_el, t_range)
    qslice = create_slice(xf_list[0].ql_dyn, q_range)

    flag = True
    tel, qd, g2, g2_err = [], [], [], []
    for fc in xf_list:
        tel.append(fc.t_el[tslice])
        qd.append(fc.ql_dyn[qslice])
        g2.append(fc.g2[tslice, qslice])
        g2_err.append(fc.g2_err[tslice, qslice])

    t_shape = set([t.shape for t in tel])
    q_shape = set([q.shape for q in qd])
    if len(t_shape) != 1 or len(q_shape) != 1:
        logger.info('the data files are not consistent in tau or q')
        flag = False

    return flag, tel, qd, g2, g2_err


def plot_empty(mp_hdl, num_fig, num_points, num_col=4, show_label=False,
               labels=None, show_fit=False):
    # adjust canvas size according to the number of images
    if num_fig < num_col:
        num_col = num_fig
    num_row = (num_fig + num_col - 1) // num_col

    mp_hdl.adjust_canvas_size(num_col, num_row)
    mp_hdl.fig.clear()

    mp_hdl.subplots(num_row, num_col)
    mp_hdl.obj = None

    # dummy x y fit line
    x = np.logspace(-5, 0, 32)
    y = np.exp(-x / 1E-3) * 0.25 + 1.0
    err = y / 40

    err_obj = []
    lin_obj = []

    for idx in range(num_points):
        for i in range(num_fig):
            offset = 0.03 * idx
            ax = np.array(mp_hdl.axes).ravel()[i]
            obj1 = ax.errorbar(x, y + offset, yerr=err, fmt='o', markersize=3,
                               markerfacecolor='none',
                               label='{}'.format(labels[idx]))
            err_obj.append(obj1)

            # plot fit line
            obj2 = ax.plot(x, y + offset)
            obj2[0].set_visible(False)
            lin_obj.append(obj2)

            # last image
            if idx == num_points - 1:
                # ax.set_title('Q = %5.4f $\AA^{-1}$' % ql_dyn[i])
                ax.set_xscale('log')
                ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                # if there's only one point, do not add title; the title
                # will be too long.
                if show_label and i == num_fig - 1:
                    # if idx >= 1 and num_points < 10:
                    ax.legend(fontsize=8)

    # mp_hdl.fig.tight_layout()
    mp_hdl.obj = {
        'err': err_obj,
        'lin': lin_obj,
    }


def pg_plot(hdl, tel, qd, g2, g2_err, num_col, xrange, yrange, offset=None,
            labels=None, show_fit=False, bounds=None, plot_type='multiple'):

    if offset is None:
        offset = 0

    num_fig = 1
    num_lines = 1

    if plot_type == 'multiple':
        num_fig = g2[0].shape[1]
        num_lines = len(g2)
    elif plot_type == 'single':
        num_fig = len(g2)
        num_lines = g2[0].shape[1]

    elif plot_type == 'single-combined':
        num_fig = 1
        num_lines = g2[0].shape[1] * len(g2)
        
    col = min(num_fig, num_col)
    row = (num_fig + col - 1) // col

    hdl.adjust_canvas_size(num_col=col, num_row=row)
    hdl.clear()
    # a bug in pyqtgraph; the log scale in x-axis doesn't apply
    xrange = np.log10(xrange)
    if labels is None:
        labels = [None] * num_lines

    axes = []
    for n in range(num_fig):
        i_col = n % col
        i_row = n // col
        t = hdl.addPlot(row=i_row, col=i_col)
        axes.append(t)
        if labels[0] is not None:
            t.addLegend(offset=(-1, 1), labelTextSize='4pt', verSpacing=-10)
        t.setMouseEnabled(x=False, y=False)

    err_msg = []
    fit_val_dict = {}
    for m in range(len(g2)):
        if show_fit:
            fit_res, fit_val = fit_xpcs(tel[m], qd[m], g2[m], g2_err[m],
                                        b=bounds)
            fit_val_dict[m] = fit_val
            err_msg.append(labels[m])

        for n in range(g2[0].shape[1]):
            color = colors[m % len(colors)]
            label = None
            if plot_type == 'multiple':
                ax = axes[n]
                title = 'q=%.5f Å⁻¹' % qd[0][n]
                label = labels[m]
                if m == 0:
                    ax.setTitle(title)
            elif plot_type == 'single':
                ax = axes[m]
                # overwrite color; use the same color for the same set;
                color = colors[n % len(colors)]
                title = labels[m]
                label = 'q=%.5f Å⁻¹' % qd[0][n]
                ax.setTitle(title)
            elif plot_type == 'single-combined':
                ax = axes[0]
                label = labels[m] + ' q=%.5f Å⁻¹' % qd[0][n]

            ax.setLabel('bottom', 'tau (s)')
            ax.setLabel('left', 'g2')

            symbol = symbols[m % len(symbols)]

            x = tel[m]
            y = g2[m][:, n] + m * offset
            y_err = g2_err[m][:, n]

            pg_plot_one_g2(ax, x, y, y_err, color, label=label, symbol=symbol)
            ax.setRange(xRange=xrange, yRange=yrange)
            if show_fit:
                y_fit = fit_res[n]['fit_y'] + m * offset
                ax.plot(fit_res[n]['fit_x'], y_fit,
                        pen=pg.mkPen(color, width=1.2))

            # msg = fit_res[m]['err_msg']
            # if msg is not None:
            #     err_msg.append('----' + msg)

        # if len(err_msg) == prev_len:
        #     err_msg.append('---- fit finished without errors')
    return fit_val_dict


def pg_plot_one_g2(ax, x, y, dy, color, label, symbol):
    pen = pg.mkPen(color=color, width=2)

    line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy,
                           pen=pen)
    pen = pg.mkPen(color=color, width=1)
    ax.plot(x, y, pen=None, symbol=symbol, name=label, symbolSize=5,
            symbolPen=pen, symbolBrush=pg.mkBrush(color=(*color, 0)))

    ax.setLogMode(x=True, y=None)
    ax.addItem(line)
    return
