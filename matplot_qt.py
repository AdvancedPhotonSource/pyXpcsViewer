from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5.1, height=3.2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.axes = None

    def subplots(self, n, m, **kwargs):
        self.axes = self.fig.subplots(n, m, **kwargs)

