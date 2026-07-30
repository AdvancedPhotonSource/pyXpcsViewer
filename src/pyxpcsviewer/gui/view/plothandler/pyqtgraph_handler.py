# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import builtins
import contextlib

import numpy as np
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget, ImageView, QtCore, QtGui

from .utils import adjust_canvas_size

pg.setConfigOptions(imageAxisOrder="row-major")


class ImageViewPlotItem(ImageView):
    """Custom :class:`ImageView` with a ``PlotItem`` view for x/y tick support."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize with a :class:`~pyqtgraph.PlotItem` as the internal view."""
        plot_item = pg.PlotItem()
        super().__init__(*args, view=plot_item, **kwargs)


class ImageViewDev(ImageView):
    """Extended ``ImageView`` with ROI management (Pie, Circle, Line, Center, Ring types)."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize and set up empty ROI tracking dicts."""
        super().__init__(*args, **kwargs)
        self.roi_record = {}
        self.roi_idx = 0

    def reset_limits(self):
        """
        reset the viewbox's limits so updating image won't break the layout;
        """
        self.view.state["limits"] = {
            "xLimits": [None, None],
            "yLimits": [None, None],
            "xRange": [None, None],
            "yRange": [None, None],
        }

    def set_colormap(self, cmap: str) -> None:
        """Set the colour map for image display from a matplotlib colormap name.

        Args:
            cmap: Matplotlib colormap name (e.g. ``"jet"``, ``"viridis"``).
        """
        pg_cmap = pg.colormap.getFromMatplotlib(cmap)
        self.setColorMap(pg_cmap)

    def clear(self) -> None:
        """Clear all images, remove ROIs, and reset viewbox limits."""
        super().clear()

        self.remove_rois()
        self.reset_limits()
        # incase the signal isn't connected to anything.
        with contextlib.suppress(builtins.BaseException):
            self.scene.sigMouseMoved.disconnect()

    def add_roi(
        self,
        cen=None,
        num_edges=None,
        radius=60,
        color: str = "r",
        sl_type: str = "Pie",
        width=3,
        sl_mode: str = "exclusive",
        second_point=None,
        label=None,
        center=None,
    ):
        """Add a Region of Interest (Circle, Line, Pie, Center) and track it.

        Args:
            cen: Centroid pixel coordinates for the ROI.
            num_edges: Ignored (reserved).
            radius: Radius in pixels.
            color: PySide colour string.
            sl_type: ROI shape — ``"Circle"``, ``"Line"``, ``"Pie"``, or ``"Center"``.
            width: Border width for the ROI outline.
            sl_mode: Either ``"exclusive"`` or ``"inclusive"`` pen style.
            second_point: Second point defining a line (for ``"Line"`` type) or corner (for ``"Circle"``).
            label: Optional identifier; auto-generated if ``None``.
            center: Extra centre offset (used by ``"Center"`` type).

        Returns:
            The string label assigned to this ROI.
        """
        # label: label of roi; default is None, which is for roi-draw

        if label is not None and label in self.roi_record:
            self.remove_roi(label)

        if sl_mode == "inclusive":
            pen = pg.mkPen(color=color, width=width, style=QtCore.Qt.DotLine)
        else:
            pen = pg.mkPen(color=color, width=width)

        kwargs = {"pen": pen, "removable": True, "hoverPen": pen, "handlePen": pen}

        if sl_type == "Circle":
            if second_point is not None:
                radius = np.sqrt((second_point[1] - cen[1]) ** 2 + (second_point[0] - cen[0]) ** 2)
            new_roi = pg.CircleROI(
                pos=[cen[0] - radius, cen[1] - radius],
                radius=radius,
                movable=False,
                **kwargs,
            )

        elif sl_type == "Line":
            if second_point is None:
                return
            width = kwargs.pop("width", 1)
            new_roi = pg.LineROI(cen, second_point, width, **kwargs)
        elif sl_type == "Pie":
            width = kwargs.pop("width", 1)
            new_roi = PieROI(cen, radius, movable=False, **kwargs)
        elif sl_type == "Center":
            if center is None:
                return
            new_roi = pg.ScatterPlotItem()
            new_roi.addPoints(x=[center[0]], y=[center[1]], symbol="+", size=15)
        else:
            raise TypeError(f"type not implemented. {sl_type}")

        new_roi.sl_mode = sl_mode

        if label is None:
            label = f"roi_{self.roi_idx:06d}"
            self.roi_idx += 1
        self.roi_record[label] = new_roi
        self.addItem(new_roi)
        if sl_type != "Center":
            new_roi.sigRemoveRequested.connect(lambda: self.remove_roi(label))
        return label

    def remove_rois(self, filter_str: str | None = None) -> None:
        """Remove tracked ROIs matching an optional prefix.

        Args:
            filter_str: If provided, only ROIs whose labels start with this string are removed.
        """
        # if filter_str is None; then remove all rois
        keys = list(self.roi_record.keys()).copy()
        if filter_str is not None:
            keys = list(filter(lambda x: x.startswith(filter_str), keys))
        for key in keys:
            self.remove_roi(key)

    def remove_roi(self, roi_key) -> None:
        """Remove a single tracked ROI by label.

        Args:
            roi_key: The label string of the ROI to remove.
        """
        t = self.roi_record.pop(roi_key, None)
        if t is not None:
            self.removeItem(t)

    def get_roi_list(self) -> list[dict]:
        """Extract ROI parameters from all tracked (non-Center) ROIs.

        Returns:
            List of parameter dicts with keys ``sl_type``, and optionally ``radius``,
            ``angle_range``, ``dist``, and ``pos`` depending on the ROI type.
        """
        parameter = []
        for key, roi in self.roi_record.items():
            if key == "Center":
                continue
            elif key.startswith("RingB"):
                temp = {
                    "sl_type": "Ring",
                    "radius": (
                        roi.getState()["size"][1] / 2.0,
                        self.roi_record["RingA"].getState()["size"][1] / 2.0,
                    ),
                }
                parameter.append(temp)
            elif key.startswith("roi"):
                temp = roi.get_parameter()
                parameter.append(temp)
        return parameter


class PlotWidgetDev(GraphicsLayoutWidget):
    """Extended ``GraphicsLayoutWidget`` with dynamic canvas resizing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize with a white background."""
        super().__init__(*args, **kwargs)
        self.setBackground("w")

    def adjust_canvas_size(self, num_col: int, num_row: int) -> None:
        """Resize the widget's minimum height for a *num_col* x *num_row* plot grid."""
        adjust_canvas_size(self, num_col, num_row)


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
        """Initialize the equilateral-triangle ROI with scale and rotation handles.

        Args:
            pos: Origin coordinates ``[x, y]`` in pixel space.
            size: Edge length of the triangle.
            **args: Extra keyword arguments forwarded to :class:`pg.ROI`.
        """
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

    def create_poly(self, width: float = 1.0, height: float = 1.0) -> None:
        """Create the equilateral-triangle polygon for display.

        Args:
            width: Triangle base width in normalised units.
            height: Triangle height in normalised units.
        """
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
        for pt in zip(x, y, strict=False):
            poly.append(QtCore.QPointF(*pt))
        self.poly = None
        self.poly = poly

    def get_parameter(self) -> dict:
        """Extract the Pie ROI's geometry parameters (angle range, distance, position).

        Returns:
            Dict with keys ``sl_type``, ``dist``, ``angle_range``, and ``pos``.
        """
        state = self.getState()
        angle_range = np.array([-1, 1]) * self.half_angle + state["angle"]
        # shift angle_range's origin to 6 clock
        angle_range = angle_range - 90
        angle_range = angle_range - np.floor(angle_range / 360.0) * 360.0
        size = state["size"]
        dist = np.hypot(size[0], size[1] / 2.0)
        ret = {
            "sl_type": "Pie",
            "dist": dist,
            "angle_range": angle_range,
            "pos": tuple(self.pos()),
        }
        return ret

    def paint(self, p, *args) -> None:
        """Draw the triangular ROI with anti-aliasing.

        Args:
            p: QPainter instance.
            *args: Additional positional arguments passed from ``pg.ROI.paint``.
        """
        r = self.boundingRect()
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.scale(r.width(), r.height())
        p.setPen(self.currentPen)
        p.drawPolygon(self.poly)

    def shape(self):
        """Return the painter path that defines the ROI's clickable area.

        Returns:
            A :class:`~PySide6.QtGui.QPainterPath` transformed to screen coordinates.
        """
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
        """Delegate to the parent ROI's arbitrary-shape array-region method.

        Args:
            *args: Passed through to ``pg.ROI._getArrayRegionForArbitraryShape``.
            **kwds: Passed through to ``pg.ROI._getArrayRegionForArbitraryShape``.

        Returns:
            The array region masked by this ROI's shape.
        """
        return self._getArrayRegionForArbitraryShape(*args, **kwds)
