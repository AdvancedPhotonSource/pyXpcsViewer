import numpy as np


def smooth_data(fc, window, sampling):
    x, y = fc.Int_t[0], fc.Int_t[1]
    if window > 1:
        y = np.cumsum(y, dtype=float, axis=0)
        y = (y[window:] - y[:-window]) / window
        x = x[window:]
    if sampling >= 2:
        y = y[::sampling]
        x = x[::sampling]

    return x, y


def plot(xf_list, pg_hdl, legend, **kwargs):
    data = []
    for fc in xf_list:
        x, y = smooth_data(fc, **kwargs)
        data.append([x, y])

    pg_hdl.clear()
    pg_hdl.show_lines(data,
                      xlabel="Frame Index",
                      ylabel="Intensity (ph/pixel)",
                      loc='lower right',
                      alpha=0.5,
                      legend=legend)
    pg_hdl.draw()

