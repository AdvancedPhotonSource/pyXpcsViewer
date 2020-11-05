import numpy as np
from matplotlib.ticker import FormatStrFormatter
import logging


logger = logging.getLogger(__name__)

fn_tuple = None


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
               labels=None):
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

