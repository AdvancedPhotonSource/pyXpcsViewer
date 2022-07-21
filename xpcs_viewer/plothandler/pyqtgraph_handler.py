import pyqtgraph as pg
from pyqtgraph import ImageView, GraphicsLayoutWidget
from .mpl_cmaps_in_ImageItem import pg_get_cmap
import matplotlib.pyplot as plt
# from PyQt5 import QtCore, QtGui
from pyqtgraph import QtGui, QtCore
import numpy as np


pg.setConfigOptions(imageAxisOrder='row-major')


class ImageViewDev(ImageView):
    def __init__(self, *args, **kwargs) -> None:
        super(ImageViewDev, self).__init__(*args, **kwargs)
        self.roi_record = {}
        self.roi_idx = 0

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

        self.remove_rois()
        self.reset_limits()
        # incase the signal isn't connected to anything.
        try:
            self.scene.sigMouseMoved.disconnect()
        except:
            pass
    
    def add_roi(self, cen=None, num_edges=None, radius=60, color='r',
                sl_type='Pie', width=3, sl_mode='exclusive',
                second_point=None, label=None, center=None):
        # label: label of roi; default is None, which is for roi-draw

        if label is not None and label in self.roi_record:
            self.remove_roi(label)

        if sl_mode == 'inclusive':
            pen = pg.mkPen(color=color, width=width, style=QtCore.Qt.DotLine)
        else:
            pen = pg.mkPen(color=color, width=width)

        kwargs = {
            'pen': pen,
            'removable': True,
            'hoverPen': pen,
            'handlePen': pen
        }

        if sl_type == 'Circle':
            if second_point is not None:
                radius = np.sqrt((second_point[1] - cen[1]) ** 2 + 
                                 (second_point[0] - cen[0]) ** 2)
            new_roi = pg.CircleROI(pos=[cen[0] - radius, cen[1] - radius],
                                   radius=radius, movable=False,
                                   **kwargs)

        elif sl_type == 'Line':
            if second_point is None:
                return
            width = kwargs.pop('width', 1)
            new_roi = pg.LineROI(cen, second_point, width,
                              **kwargs)
        elif sl_type == 'Pie':
            width = kwargs.pop('width', 1)
            new_roi = PieROI(cen, radius, movable=False, **kwargs)
        elif sl_type == 'Center':
            if center is None:
                return
            new_roi = pg.ScatterPlotItem()
            new_roi.addPoints(x=[center[0]], y=[center[1]], symbol='+', 
                              size=15)
        else:
            raise TypeError('type not implemented. %s' % sl_type)

        new_roi.sl_mode = sl_mode

        if label is None:
            label = f"roi_{self.roi_idx:06d}"
            self.roi_idx += 1
        self.roi_record[label] = new_roi
        self.addItem(new_roi)
        if sl_type is not 'Center':
            new_roi.sigRemoveRequested.connect(lambda: self.remove_roi(label))
        return label 
    
    def remove_rois(self, filter_str=None):
        # if filter_str is None; then remove all rois
        keys = list(self.roi_record.keys()).copy()
        if filter_str is not None:
            keys = list(filter(lambda x: x.startswith(filter_str), keys))
        for key in keys:
            self.remove_roi(key)
    
    def remove_roi(self, roi_key):
        t = self.roi_record.pop(roi_key, None)
        if t is not None:
            self.removeItem(t)

    def get_roi_list(self):
        parameter = []
        for key, roi in self.roi_record.items():
            if key == 'Center':
                continue
            elif key.startswith('RingB'):
                temp = {
                    'sl_type': 'Ring',
                    'radius': (roi.getState()['size'][1] / 2.0,
                        self.roi_record['RingA'].getState()['size'][1] / 2.0)}
                parameter.append(temp)
            elif key.startswith('roi'):
                temp = roi.get_parameter()
                parameter.append(temp)
        return parameter


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


class PieROI(pg.ROI):
    r"""
    Equilateral triangle ROI subclass with one scale handle and one rotation handle.
    Arguments
    pos            (length-2 sequence) The position of the ROI's origin.
    size           (float) The length of an edge of the triangle.
    \**args        All extra keyword arguments are passed to ROI()
    ============== =============================================================
    """

    def __init__(self, pos, size, **args):
        cen = (pos[0], pos[1] - size / 2.0)
        pg.ROI.__init__(self, cen, [size, size], aspectLocked=False, **args)
        # _updateView is a rendering method inherited; used here to force
        # update the view
        self.sigRegionChanged.connect(self._updateView)
        self.poly = None
        self.half_angle = None
        self.create_poly()
        self.addScaleRotateHandle([1.0, 0], [0, 0.5])
        self.addScaleHandle([1.0, 1.0], [0, 0.5])

    def create_poly(self, width=1.0, height=1.0):
        radius = np.hypot(width, height / 2.0)
        max_angle = np.arcsin(height / 2.0 / radius)
        angle = np.linspace(-max_angle, max_angle, 16)
        self.half_angle = np.rad2deg(max_angle)

        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        # make the x[0] and x[-1] two vertices at x = width after scaling
        x = x / np.abs(x[0])
        # make the y range to be height after scaling
        y = y / (np.max(y) - np.min(y)) + 0.5
        poly = QtGui.QPolygonF()
        poly.append(QtCore.QPointF(0.0, 0.5))
        for pt in zip(x, y):
            poly.append(QtCore.QPointF(*pt))
        self.poly = None
        self.poly = poly
    
    def get_parameter(self):
        state = self.getState()
        angle_range = np.array([-1, 1]) * self.half_angle + state['angle'] 
        # shift angle_range's origin to 6 clock
        angle_range = angle_range - 90
        angle_range = angle_range - np.floor(angle_range / 360.0) * 360.0
        size = state['size']
        dist = np.hypot(size[0], size[1] / 2.0)
        ret = {
            'sl_type': 'Pie',
            'dist': dist,
            'angle_range': angle_range,
            'pos': tuple(self.pos())
        }
        return ret

    def paint(self, p, *args):
        r = self.boundingRect()
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.scale(r.width(), r.height())
        p.setPen(self.currentPen)
        p.drawPolygon(self.poly)

    def shape(self):
        self.path = QtGui.QPainterPath()
        r = self.boundingRect()
        # scale the path to match whats on the screen
        t = QtGui.QTransform()
        t.scale(r.width(), r.height())

        width = r.width()
        height = r.height()
        self.create_poly(width, height)
        self.path.addPolygon(self.poly)
        return t.map(self.path)

    def getArrayRegion(self, *args, **kwds):
        return self._getArrayRegionForArbitraryShape(*args, **kwds)
