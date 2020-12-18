import pyqtgraph as pg
from pyqtgraph import ImageView, PlotWidget, GraphicsLayoutWidget
from .mpl_cmaps_in_ImageItem import pg_get_cmap
import matplotlib.pyplot as plt
from PyQt5 import QtCore


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
        # xMin, xMax = vb.viewRange()[0]
        # yMin, yMax = vb.viewRange()[1]
        xMin = -margin_h
        xMax = target_shape[1] + margin_h
        yMin = -margin_v
        yMax = target_shape[0] + margin_v

        vb.setLimits(xMin=xMin,
                     xMax=xMax,
                     yMin=yMin,
                     yMax=yMax,
                     minXRange=(xMax - xMin) / 50,
                     minYRange=(yMax - yMin) / 50)
        vb.setMouseMode(vb.RectMode)
        # vb.setAspectLocked(1.0)

        # print('weight', -margin_h, target_shape[1] + margin_h)
        # print('height', -margin_v, target_shape[0] + margin_v)

        # print('vb.range', vb.viewRange())
        # print('vb.rect', vb.viewRect())
    
    def set_colormap(self, cmap):
        pg_cmap = pg_get_cmap(plt.get_cmap(cmap))
        self.setColorMap(pg_cmap)


class PlotWidgetDev(GraphicsLayoutWidget):
    def __init__(self, *args, **kwargs) -> None:
        super(PlotWidgetDev, self).__init__(*args, **kwargs)
        self.setBackground('w')

    def adjust_canvas_size(self, num_col, num_row):
        t = self.parent().parent().parent()
        if t is None:
            aspect = 1 / 1.618
        else:
            aspect = t.height() / self.width()

        min_size = t.height() - 20
        width = self.width()
        canvas_size = max(min_size, int(width / num_col * aspect * num_row))
        self.setMinimumSize(QtCore.QSize(0, canvas_size))

