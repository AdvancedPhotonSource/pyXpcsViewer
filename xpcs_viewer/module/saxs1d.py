import numpy as np


def offset_intensity(Iq, n, plot_offset=None, yscale=None):
    """
    offset the intensity accordingly in both linear and log scale
    """
    if yscale == 'linear':
        offset = -plot_offset * n * np.max(Iq)
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

    # make sure the dimesions match and orders are right
    if Iq.size != q.size:
        size = min(Iq.size, q.size)
        Iq = Iq[-size:]
        q = q[-size:]

    sort_idx = np.argsort(q)
    q = q[sort_idx]
    Iq = Iq[sort_idx]

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


def plot(xf_list, mp_hdl, plot_type='log', plot_norm=0, plot_offset=0,
         max_points=8, legend=None, title=None, rows=None):

    xscale = ['linear', 'log'][plot_type % 2]
    yscale = ['linear', 'log'][plot_type // 2]

    data = []
    for n, fi in enumerate(xf_list[slice(0, max_points)]):
        Iq, q = fi.saxs_1d, fi.ql_sta

        Iq, q, xlabel, ylabel = norm_saxs_data(Iq, q, plot_norm)
        Iq = offset_intensity(Iq, n, plot_offset, yscale)
        data.append([q, Iq])

    mp_hdl.clear()
    mp_hdl.show_lines(data, xlabel=xlabel, ylabel=ylabel, legend=legend,
                      rows=rows)

    mp_hdl.axes.set_title(title)
    mp_hdl.auto_scale(xscale=xscale, yscale=yscale)
    mp_hdl.draw()
    return
