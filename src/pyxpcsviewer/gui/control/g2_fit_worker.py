# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging

from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot

from ...core.fitting import fit_g2_batch

logger = logging.getLogger(__name__)


class G2FitSignals(QObject):
    """Custom signal class for the background G2 fitting worker."""

    progress = QtCore.Signal(int, int)
    finished = QtCore.Signal()


class G2FitWorker(QtCore.QRunnable):
    """Background worker that fits g2 data for multiple files in parallel.

    Extracts each file's g2 data on the worker thread (cheap, numpy-only),
    then fits every file's data in a separate process pool via
    :func:`~pyxpcsviewer.core.fitting.fit_g2_batch`, so the Qt event loop
    never blocks on ``scipy.optimize.curve_fit``.
    """

    def __init__(self, xf_list, q_range, t_range, bounds, fit_flag, fit_func) -> None:
        """Initialize the fitting worker with the files and fit parameters.

        Args:
            xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instances to fit.
            q_range: ``(q_min, q_max)`` filter or ``None`` for all Q values.
            t_range: ``(t_min, t_max)`` filter on the elapsed time axis.
            bounds: Fitting bounds as ``(lower, upper)``.
            fit_flag: Tuple of bools — ``True`` to fit, ``False`` to hold fixed.
            fit_func: Either ``"single"`` or ``"double"`` exponential model.
        """
        super().__init__()
        self.xf_list = xf_list
        self.q_range = q_range
        self.t_range = t_range
        self.bounds = bounds
        self.fit_flag = fit_flag
        self.fit_func = fit_func
        self.signals = G2FitSignals()

    @Slot()
    def run(self) -> None:
        """Entry point for the :class:`QRunnable` — fit every file, then signal completion."""
        file_inputs = [xf.get_g2_data(qrange=self.q_range, trange=self.t_range) for xf in self.xf_list]
        results = fit_g2_batch(
            file_inputs,
            self.bounds,
            self.fit_flag,
            self.fit_func,
            self.q_range,
            self.t_range,
            progress_callback=lambda done, total: self.signals.progress.emit(done, total),
        )
        for xf, fit_summary in zip(self.xf_list, results, strict=True):
            xf.fit_summary = fit_summary
        self.signals.finished.emit()
