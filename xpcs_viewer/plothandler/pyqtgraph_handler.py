import pyqtgraph as pg
from pyqtgraph import ImageView, PlotWidget, GraphicsLayoutWidget
from .mpl_cmaps_in_ImageItem import pg_get_cmap
import matplotlib.pyplot as plt
from PyQt5 import QtCore


pg.setConfigOptions(imageAxisOrder='row-major')


class ImageViewDev(ImageView):
    def __init__(self, *args, **kwargs) -> None:
        super(ImageViewDev, self).__init__(*args, **kwargs)

    def adjust_viewbox(self):
        vb = self.getView()
        xMin, xMax = vb.viewRange()[0]
        yMin, yMax = vb.viewRange()[1]

        vb.setLimits(xMin=xMin,
                     xMax=xMax,
                     yMin=yMin,
                     yMax=yMax,
                     minXRange=(xMax - xMin) / 50,
                     minYRange=(yMax - yMin) / 50)
        vb.setMouseMode(vb.RectMode)
        vb.setAspectLocked(1.0)

    def reset_limits(self):
        """
        reset the viewbox's limits so updating image won't break the layout;
        """
        self.view.state['limits'] = {'xLimits': [None, None],
                                     'yLimits': [None, None],
                                     'xRange': [None, None],
                                     'yRange': [None, None]
                                     }

    def set_colormap(self, cmap):
        pg_cmap = pg_get_cmap(plt.get_cmap(cmap))
        self.setColorMap(pg_cmap)

    def add_readback(self, display=None, extent=None, type='log'):
        # vLine = pg.InfiniteLine(angle=90, movable=False)
        # hLine = pg.InfiniteLine(angle=0, movable=False)
        # self.view.addItem(vLine, ignoreBounds=True)
        # self.view.addItem(hLine, ignoreBounds=True)

        # def print_roi_shape(evt):
        #     print(self.roi.boundingRect())

        # self.roi.sigRegionChanged.connect(print_roi_shape)

        def compute_qxy(col, row):
            s = self.image.shape[-2:]
            # qx
            a1, a2 = col, s[1] - col
            qx = (extent[0] * a2 + extent[1] * a1) / s[1]

            # qy
            b1, b2 = row, s[0] - row
            qy = (extent[2] * b2 + extent[3] * b1) / s[0]

            return qx, qy

        def mouse_moved(pos):
            shape = self.image.shape
            if self.scene.itemsBoundingRect().contains(pos):
                mouse_point = self.getView().mapSceneToView(pos)
                # vLine.setPos(mouse_point.x())
                # hLine.setPos(mouse_point.y())
                col = int(mouse_point.x())
                row = int(mouse_point.y())

                if col < 0 or col >= shape[-1]:
                    return
                if row < 0 or row >= shape[-2]:
                    return

                if len(shape) == 3:
                    pixel_val = self.image[self.currentIndex, row, col]
                elif len(shape) == 2:
                    pixel_val = self.image[row, col]
                else:
                    raise ValueError('Check array dimension')

                if type == 'log':
                    pixel_val = 10 ** pixel_val
                qx, qy = compute_qxy(col, row)

                if display is None:
                    print(pixel_val)
                else:
                    display.clear()
                    display.setText(
                        '%d: [x=%4d, y=%4d, qx=%fÅ⁻¹, qy=%fÅ⁻¹, c:%.3f]' % (
                            self.currentIndex, col, row, qx, qy, pixel_val))
        self.scene.sigMouseMoved.connect(mouse_moved)

    def clear(self):
        super(ImageViewDev, self).clear()
        self.reset_limits()
        # incase the signal isn't connected to anything.
        try:
            self.scene.sigMouseMoved.disconnect()
        except:
            pass


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
