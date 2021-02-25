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


def smooth_data(fc, window=1, sampling=1):
    # some bad frames have both x and y = 0;
    # x, y = fc.Int_t[0], fc.Int_t[1]
    y = fc.Int_t[1]
    x = np.arange(y.shape[0])

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


def plot(xf_list, pg_hdl, enable_zoom=True, xlabel='Frame Index', **kwargs):
    """
    :param xf_list: list of xf objects
    :param pg_hdl: pyqtgraph handler to plot
    :param enable_zoom: bool, if to plot the zoom view or not
    :param xlabel:
    :param kwargs: used to define how to average/sample the data
    :return:
    """

    t0 = xf_list[0].t0
    data = []
    for fc in xf_list:
        x, y = smooth_data(fc, **kwargs)
        if xlabel != 'Frame Index':
            x = x * t0
        data.append([x, y])

    pg_hdl.clear()

    t = pg_hdl.addPlot(colspan=2)
    t.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)
    tf = pg_hdl.addPlot(row=1, col=0, title='Fourier Spectrum')
    tf.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)
    tf.setLabel('bottom', 'Frequency (Hz)')
    tf.setLabel('left', 'FFT Intensity')

    tz = pg_hdl.addPlot(row=1, col=1, title='Zoom In')
    tz.addLegend(offset=(-1, 1), labelTextSize='8pt', verSpacing=-10)

    t.setDownsampling(mode='peak')
    tf.setDownsampling(mode='peak')
    tz.setDownsampling(mode='peak')

    for n in range(len(data)):
        t.plot(data[n][0], data[n][1], pen=pg.mkPen(colors[n], width=1),
               name=xf_list[n].label)
    t.setTitle('Intensity vs %s' % xlabel)

    if enable_zoom:
        vmin = np.min(data[0][0])
        vmax = np.max(data[0][0])
        cen = vmin * 0.382 + vmax * 0.618
        width = (vmax - vmin) * 0.05
        lr = pg.LinearRegionItem([cen - width, cen + width])
        # lr.setZValue(-10)
        t.addItem(lr)
    t.setLabel('bottom', '%s' % xlabel)
    t.setLabel('left', 'Intensity (cts / pixel)')

    for n in range(len(data)):
        y = np.abs(np.fft.fft(data[n][1]))

        x = np.arange(y.size // 2) / (y.size * t0 * kwargs['sampling'])
        y = y[slice(0, y.size // 2)]
        # get ride of zero frequency;
        y[0] = 0

        tf.plot(x, y, pen=pg.mkPen(colors[n], width=1), name=xf_list[n].label)

    for n in range(len(data)):
        tz.plot(data[n][0], data[n][1], pen=pg.mkPen(colors[n], width=1),
                name=xf_list[n].label)

    def update_plot():
        tz.setXRange(*lr.getRegion(), padding=0)

    def update_region():
        lr.setRegion(tz.getViewBox().viewRange()[0])

    lr.sigRegionChanged.connect(update_plot)
    tz.sigXRangeChanged.connect(update_region)

    tz.setLabel('bottom', '%s' % xlabel)
    tz.setLabel('left', 'Intensity (cts / pixel)')
    update_plot()

    return
