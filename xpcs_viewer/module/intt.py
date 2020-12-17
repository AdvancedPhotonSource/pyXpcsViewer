import numpy as np
import pyqtgraph as pg

colors = [
    (192, 0, 0),
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


def matplot_plot(xf_list, pg_hdl, legend, rows=None, **kwargs):
    data = []
    for fc in xf_list:
        x, y = smooth_data(fc, **kwargs)
        data.append([x, y])

    pg_hdl.clear()
    pg_hdl.show_lines(data,
                      xlabel="Frame Index",
                      ylabel="Intensity (ph/pixel)",
                      loc='lower right',
                      legend=legend,
                      rows=rows)
    pg_hdl.draw()


def plot(xf_list, pg_hdl, legend, rows=None, enable_zoom=True, **kwargs):
    data = []
    for fc in xf_list:
        x, y = smooth_data(fc, **kwargs)
        data.append([x, y])
    t0 = xf_list[0].t0

    pg_hdl.clear()
    t = pg_hdl.addPlot(colspan=2)
    t.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)
    for n in range(len(data)):
        t.plot(data[n][0], data[n][1], pen=pg.mkPen(colors[n], width=1),
               name=legend[n])
    t.setTitle('Intensity vs Frame Index')
    if enable_zoom:
        vmin = np.min(data[0][0])
        vmax = np.max(data[0][0])
        cen = vmin * 0.382 + vmax * 0.618
        width = (vmax - vmin) * 0.05
        lr = pg.LinearRegionItem([cen - width, cen + width])
        # lr.setZValue(-10)
        t.addItem(lr)

    tf = pg_hdl.addPlot(row=1, col=0, title='Fourier Spectrum')
    tf.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)
    for n in range(len(data)):
        y = np.abs(np.fft.fft(data[n][1]))
        y[0] = 0
        sl = slice(0, y.size // 2)
        x = data[n][0][sl] / (y.size * t0 * kwargs['sampling'])
        y = y[sl]
        tf.plot(data[n][0][sl], y, pen=pg.mkPen(colors[n], width=1),
                name=legend[n])

    tz = pg_hdl.addPlot(row=1, col=1, title='Zoom In')
    tz.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)
    for n in range(len(data)):
        tz.plot(data[n][0], data[n][1], pen=pg.mkPen(colors[n], width=1),
                name=legend[n])

    def updatePlot():
        tz.setXRange(*lr.getRegion(), padding=0)

    def updateRegion():
        lr.setRegion(tz.getViewBox().viewRange()[0])

    lr.sigRegionChanged.connect(updatePlot)
    tz.sigXRangeChanged.connect(updateRegion)
    updatePlot()

    return
