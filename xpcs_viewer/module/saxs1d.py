import numpy as np
from .g2mod import create_slice
from ..plothandler.matplot_qt import get_color_marker


def offset_intensity(Iq, n, plot_offset=None, yscale=None):
    """
    offset the intensity accordingly in both linear and log scale
    """
    if yscale == 'linear':
        offset = -1 * plot_offset * n * np.max(Iq)
        Iq = offset + Iq

    elif yscale == 'log':
        offset = 10**(plot_offset * n)
        Iq = Iq / offset
    return Iq


def norm_saxs_data(Iq, q, plot_norm=0):
    """
    normalize small angle scattering data to enhance the visual difference;
    log / linear plot is handled by matplotlib ax objects;
    Args:
        Iq: SAXS Intensity, numpy.ndarray
        q: wave transfer;
        plot_norm: [0, 1, 2, 3]
            0: no normalization
            1: q^2
            2: q^4
            3: I / I0
    Return:
        Iq: normalized SAXS data
        xlabel: 
        ylabel:
    Raise:
        ValueError: if plot_norm not in [0, 1, 2, 3]
    """
    if plot_norm not in range(4):
        raise ValueError('plot_norm must be in [0, 1, 2, 3]')

    ylabel = 'Intensity'
    if plot_norm == 1:
        Iq = Iq * np.square(q)
        ylabel = ylabel + ' * q^2'
    elif plot_norm == 2:
        Iq = Iq * np.square(np.square(q))
        ylabel = ylabel + ' * q^4'
    elif plot_norm == 3:
        baseline = Iq[0]
        Iq = Iq / baseline
        ylabel = ylabel + ' / I_0'

    xlabel = '$q (\\AA^{-1})$'
    return Iq, q, xlabel, ylabel


def switch_line_builder(hdl, lb_type=None):
    hdl.link_line_builder(lb_type)
    # if lb_type is not None:
    #     hdl.link_line_builder(lb_type)
    # elif lb_type is None and hdl.line_builder is not None:
    #     hdl.unlink_line_builder()


def plot(xf_list, mp_hdl, plot_type=2, plot_norm=0, plot_offset=0,
         max_points=8, title=None, rows=None, qmax=10.0, qmin=0,
         loc='best', marker_size=3, sampling=1, all_phi=False, 
         absolute_crosssection=False, subtract_background=False, 
         bkg_file=None, weight=1.0):

    xscale = ['linear', 'log'][plot_type % 2]
    yscale = ['linear', 'log'][plot_type // 2]

    mp_hdl.clear()
    ax = mp_hdl.subplots(1, 1)

    if rows in [None, []]:
        alpha = np.ones(len(xf_list)) * 0.75
    else:
        alpha = np.ones(len(xf_list)) * 0.15
        for t in rows:
            if t < len(xf_list):
                alpha[t] = 1.0

    if subtract_background and bkg_file is not None:
        Iq_bkg, q_bkg = bkg_file.saxs_1d['Iq'], bkg_file.saxs_1d['q']
        # apply sampling
        Iq_bkg, q_bkg = Iq_bkg[:, ::sampling], q_bkg[::sampling]
        sl = create_slice(q_bkg, (qmin, qmax))
        Iq_bkg = Iq_bkg[:, sl]
        q_bkg = q_bkg[sl]

    plot_id = 0
    for n, fi in enumerate(xf_list[slice(0, max_points)]):
        Iq, q = fi.saxs_1d['Iq'], fi.saxs_1d['q']
        # apply sampling
        Iq, q = Iq[:, ::sampling], q[::sampling]

        # apply qrange
        sl = create_slice(q, (qmin, qmax))
        Iq = Iq[:, sl]
        q = q[sl]

        if subtract_background and bkg_file is not None:
            if np.allclose(q, q_bkg):
                Iq = Iq - weight * Iq_bkg
                bad_index = Iq <= 0
                Iq[bad_index] = float('nan')
            else:
                print('bkg not applied because bkg q has different values.')

        if all_phi:
            num_lines = Iq.shape[0]
        else:
            num_lines = 1

        for m in range(num_lines):
            cl, mk = get_color_marker(plot_id)
            Iqm = offset_intensity(Iq[m], plot_id, plot_offset, yscale)
            Iqm, _, xlabel, ylabel = norm_saxs_data(Iqm, q, plot_norm)
            ax.plot(q, Iqm, mk + '-', label=fi.saxs_1d['labels'][m],
                    ms=marker_size, alpha=alpha[n], color=cl, mfc='none')
            plot_id += 1
        
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    mp_hdl.auto_scale(xscale=xscale, yscale=yscale)
    if loc != 'outside':
        ax.legend(loc=loc)
    elif loc == 'outside':
        ax.legend(bbox_to_anchor=(1.03, 1.0), loc='upper left')
    mp_hdl.fig.tight_layout(rect=(0.07, 0.07, 0.93, 0.93))

    mp_hdl.draw()
    return