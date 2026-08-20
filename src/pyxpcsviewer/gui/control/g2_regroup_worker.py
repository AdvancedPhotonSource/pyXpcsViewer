# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Background worker moving G2 outlier-rejection regrouping off the GUI thread.

Even after vectorizing find_g2_pixel_outliers, a regroup with outlier
rejection enabled is a multi-second numpy computation; running it directly
on the Qt main thread (as PlotController.process_G2_regroup previously was)
freezes the whole window for that duration.
"""

from typing import Any

from PySide6 import QtCore

from .plot_controller import PlotController


class G2RegroupWorkerSignals(QtCore.QObject):
    """Signals for :class:`G2RegroupWorker` (a QRunnable cannot emit signals itself)."""

    #: Emitted exactly once when the job ends: ``None`` on success, or an
    #: error message string if ``process_G2_regroup`` raised. A single signal
    #: (rather than separate finished/failed signals) so this worker can be
    #: driven through the same ``WorkerSlot.start(..., on_finished=...)``
    #: bookkeeping AverageToolbox/G2FitWorker already use.
    finished = QtCore.Signal(object)


class G2RegroupWorker(QtCore.QRunnable):
    """Run :meth:`PlotController.process_G2_regroup` on a QThreadPool thread."""

    def __init__(self, plots: PlotController, kwargs: dict[str, Any]) -> None:
        """Store the target :class:`PlotController` and its call kwargs.

        Args:
            plots: The ``PlotController`` instance whose
                :meth:`~pyxpcsviewer.gui.control.plot_controller.PlotController.process_G2_regroup`
                should be run in the background.
            kwargs: Keyword arguments forwarded to ``process_G2_regroup``.
        """
        super().__init__()
        self._plots = plots
        self._kwargs = kwargs
        self.signals = G2RegroupWorkerSignals()

    @QtCore.Slot()
    def run(self) -> None:
        """Entry point for the :class:`QRunnable`."""
        try:
            self._plots.process_G2_regroup(**self._kwargs)
        except Exception as exc:
            self.signals.finished.emit(f"{type(exc).__name__}: {exc}")
            return
        self.signals.finished.emit(None)
