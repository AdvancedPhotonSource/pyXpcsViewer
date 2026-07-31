# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pyqtgraph as pg

from .palette import get_color_marker


def smooth_data(fc, window: int = 1, sampling: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Apply a moving-average window and optional temporal downsampling to intensity data.

    Args:
        fc: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance with ``Int_t`` data.
        window: Moving-average span in frames. Pass ``1`` to skip smoothing.
        sampling: Temporal subsample factor (≥ 2). Pass ``1`` for no subsampling.

    Returns:
        Tuple of ``(x_array, y_array)`` — frame indices and smoothed intensities.
    """
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


def plot(xf_list, pg_hdl, enable_zoom=True, xlabel="Frame Index", **kwargs):
    """Plot intensity-vs-time for a list of XPCS files.

    Args:
        xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` objects.
        pg_hdl: PyQtGraph handler widget for plotting.
        enable_zoom: If ``True``, enable the zoom view.
        xlabel: Label for the x-axis. Defaults to ``"Frame Index"``.
        **kwargs: Passed to :func:`smooth_data` for averaging / sampling.
    """
    data = []
    for fc in xf_list:
        x, y = smooth_data(fc, **kwargs)
        if xlabel != "Frame Index":
            x = x * fc.t0
        data.append([x, y])

    pg_hdl.clear()

    t = pg_hdl.addPlot(colspan=2)
    t.addLegend(offset=(-1, 1), labelTextSize="8pt", verSpacing=-10)
    tf = pg_hdl.addPlot(row=1, col=0, title="Fourier Spectrum")
    tf.addLegend(offset=(-1, 1), labelTextSize="8pt", verSpacing=-10)
    tf.setLabel("bottom", "Frequency (Hz)")
    tf.setLabel("left", "FFT Intensity")

    tz = pg_hdl.addPlot(row=1, col=1, title="Zoom In")
    tz.addLegend(offset=(-1, 1), labelTextSize="8pt", verSpacing=-10)

    t.setDownsampling(mode="peak")
    tf.setDownsampling(mode="peak")
    tz.setDownsampling(mode="peak")

    for n in range(len(data)):
        color, _ = get_color_marker(n, backend="pyqtgraph")
        t.plot(
            data[n][0],
            data[n][1],
            pen=pg.mkPen(color, width=1),
            name=xf_list[n].label,
        )
    t.setTitle(f"Intensity vs {xlabel}")

    if enable_zoom:
        vmin = np.min(data[0][0])
        vmax = np.max(data[0][0])
        cen = vmin * 0.382 + vmax * 0.618
        width = (vmax - vmin) * 0.05
        lr = pg.LinearRegionItem([cen - width, cen + width])
        # lr.setZValue(-10)
        t.addItem(lr)
    t.setLabel("bottom", f"{xlabel}")
    t.setLabel("left", "Intensity (cts / pixel)")

    for n in range(len(data)):
        x, y = xf_list[n].Int_t_fft
        color, _ = get_color_marker(n, backend="pyqtgraph")
        tf.plot(x, y, pen=pg.mkPen(color, width=1), name=xf_list[n].label)

    for n in range(len(data)):
        color, _ = get_color_marker(n, backend="pyqtgraph")
        tz.plot(
            data[n][0],
            data[n][1],
            pen=pg.mkPen(color, width=1),
            name=xf_list[n].label,
        )

    def update_plot():
        """Update the zoom plot's x-range to match the linear-region selection."""
        tz.setXRange(*lr.getRegion(), padding=0)

    def update_region():
        """Sync the linear-region selection when the zoom plot is panned."""
        lr.setRegion(tz.getViewBox().viewRange()[0])

    lr.sigRegionChanged.connect(update_plot)
    tz.sigXRangeChanged.connect(update_region)

    tz.setLabel("bottom", f"{xlabel}")
    tz.setLabel("left", "Intensity (cts / pixel)")
    update_plot()

    return
