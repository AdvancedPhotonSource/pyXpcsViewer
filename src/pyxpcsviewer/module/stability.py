from .saxs1d import offset_intensity, norm_saxs_data
import os


def plot(fc, mp_hdl, plot_type=2, plot_norm=0, plot_offset=0, legend=None, 
         title=None, **kwargs):

    xscale = ['linear', 'log'][plot_type % 2]
    yscale = ['linear', 'log'][plot_type // 2]

    q = fc.sqlist
    Iqp = fc.Iqp

    if Iqp.ndim == 1:
        Iqp = Iqp.reshape(1, -1) 
    sl = slice(0, min(q.size, Iqp.shape[1]))
    q = q[sl]
    Iqp = Iqp[:, sl]

    data = []
    for n in range(Iqp.shape[0]):
        Iq, q = Iqp[n], q
        Iq, q, xlabel, ylabel = norm_saxs_data(Iq, q, plot_norm)
        Iq = offset_intensity(Iq, n, plot_offset, yscale)
        data.append([q, Iq])

    mp_hdl.clear()
    mp_hdl.show_lines(data, xlabel=xlabel, ylabel=ylabel, legend=legend)
    
    mp_hdl.axes.set_title(fc.label)
    mp_hdl.auto_scale(xscale=xscale, yscale=yscale)
    mp_hdl.draw()
