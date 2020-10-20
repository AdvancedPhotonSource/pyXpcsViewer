import pyqtgraph as pg
from pyqtgraph import ImageView
from mpl_cmaps_in_ImageItem import pg_get_cmap
import matplotlib.pyplot as plt


pg.setConfigOptions(imageAxisOrder='row-major')


class ImageViewDev(ImageView):
    def __init__(self, *args, **kwargs) -> None:
        super(ImageViewDev, self).__init__(*args, **kwargs)

    def adjust_viewbox(self, target_shape):
        fs = self.frameSize()
        w0, h0 = fs.width(), fs.height()
        h1, w1 = target_shape

        if w1 / w0 > h1 / h0:
            # the fig is wider than the canvas
            margin_v = int((w1 / w0 * h0 - h1) / 2)
            margin_h = 0
        else:
            # the canvas is wider than the figure
            margin_v = 0
            margin_h = int((h1 / h0 * w0 - w1) / 2)

        vb = self.getView()
        vb.setLimits(xMin=-margin_h,
                     yMin=-margin_v,
                     xMax=target_shape[1] + margin_h,
                     yMax=target_shape[0] + margin_v,
                     minXRange=target_shape[1] / 20,
                     minYRange=target_shape[1] / 20 * h0 / w0)
        vb.setMouseMode(vb.RectMode)
        vb.setAspectLocked(1.0)
    
    def set_colormap(self, cmap):
        pg_cmap = pg_get_cmap(plt.get_cmap(cmap))
        self.setColorMap(pg_cmap)
