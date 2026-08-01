# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PySide6 import QtCore

from pyxpcsviewer.core.fitting import create_fit_pool

from .average_toolbox import AverageToolbox
from .background_job import WorkerSlot
from .g2_fit_worker import G2FitWorker

logger = logging.getLogger(__name__)


class JobManager:
    """Owns the app's background jobs (averaging, g2 fitting) — at most one of each at a time.

    Holds the :class:`~pyxpcsviewer.gui.model.file_locator.FileLocator` it
    reads targets from, plus one :class:`~.background_job.WorkerSlot` per
    job type. Deciding what the UI does when a job finishes stays with the
    caller (via the ``on_finished`` callback) — this class only owns
    "is a job running" and the job-specific bookkeeping each one needs.
    """

    def __init__(self, model, thread_pool) -> None:
        """Initialize with the file model and the Qt thread pool to run jobs on.

        Args:
            model: :class:`~pyxpcsviewer.gui.model.file_locator.FileLocator` instance.
            thread_pool: ``QThreadPool`` to submit workers to.
        """
        self.model = model
        self.thread_pool = thread_pool
        self._avg = WorkerSlot()
        self._g2_fit = WorkerSlot()
        self.avg_jid = 0
        self.avg_worker_active = {}

        # Pre-warm the g2 fitting process pool in the background so the first
        # user-triggered fit doesn't pay the (measured ~100-360ms) pool-creation
        # cost. Left None until warm-up finishes; submit_g2_fit falls back to
        # fit_g2_batch's own fresh-pool-per-call behavior until then.
        self._fit_pool: ProcessPoolExecutor | None = None
        self.thread_pool.start(QtCore.QRunnable.create(self._warm_up_fit_pool))

    def _warm_up_fit_pool(self) -> None:
        """Create and warm the persistent fit pool (runs on a QThreadPool worker thread)."""
        self._fit_pool = create_fit_pool()

    def shutdown(self) -> None:
        """Release background resources owned by this manager. Call on app exit."""
        if self._fit_pool is not None:
            self._fit_pool.shutdown(wait=False, cancel_futures=True)

    @property
    def avg_worker(self):
        """The in-flight :class:`~.average_toolbox.AverageToolbox` worker, or ``None``."""
        return self._avg.worker

    @property
    def g2_fit_worker(self):
        """The in-flight :class:`~.g2_fit_worker.G2FitWorker`, or ``None``."""
        return self._g2_fit.worker

    def submit_average(self, status_bar, progress_bar, on_finished, *args, **kwargs):
        """Create, wire, and start an :class:`AverageToolbox` job for the current targets.

        Args:
            status_bar: ``QStatusBar`` for status messages.
            progress_bar: ``QProgressBar`` for progress updates.
            on_finished: Slot called (with the worker's ``finished`` signal
                args — a success flag) once the job completes.
            *args: Forwarded to ``AverageToolbox.setup()``.
            **kwargs: Forwarded to ``AverageToolbox.setup()``.

        Returns:
            The started :class:`AverageToolbox`, or ``None`` if a job is
            already running or no target files are selected.
        """
        if self._avg.busy:
            logger.error("average job is already running")
            return None
        if len(self.model.target) <= 0:
            logger.error("no average target is selected")
            return None

        worker = AverageToolbox(flist=self.model.target, jid=self.avg_jid)
        worker.setup(*args, **kwargs)
        worker.signals.status.connect(status_bar.showMessage)
        worker.signals.progress.connect(progress_bar.setValue)
        worker.signals.values.connect(self.update_avg_values)
        logger.info("create average job, ID = %s", worker.jid)
        self.avg_worker_active[worker.jid] = None
        self.avg_jid += 1
        self.model.target.clear()

        self._avg.start(self.thread_pool, worker, on_finished=on_finished)
        return worker

    def submit_g2_fit(self, q_range, t_range, bounds, fit_flag, fit_func, on_finished, rows=None):
        """Create and start a :class:`G2FitWorker` job to fit g2 data in parallel.

        Args:
            q_range: ``(q_min, q_max)`` filter or ``None`` for all Q values.
            t_range: ``(t_min, t_max)`` filter on the elapsed time axis.
            bounds: Fitting bounds as ``(lower, upper)``.
            fit_flag: Tuple of bools — ``True`` to fit, ``False`` to hold fixed.
            fit_func: Either ``"single"`` or ``"double"`` exponential model.
            on_finished: Slot called once the job completes.
            rows: List of target indices; ``None`` uses all multitau targets.

        Returns:
            The started :class:`G2FitWorker`, or ``None`` if a job is
            already running or no multitau target files are selected.
        """
        if self._g2_fit.busy:
            logger.error("a g2 fitting job is already running")
            return None

        xf_list = self.model.get_xf_list(rows=rows, filter_atype="Multitau")
        if not xf_list:
            logger.error("no multitau target is selected for g2 fitting")
            return None

        worker = G2FitWorker(xf_list, q_range, t_range, bounds, fit_flag, fit_func, executor=self._fit_pool)
        self._g2_fit.start(self.thread_pool, worker, on_finished=on_finished)
        return worker

    def update_avg_values(self, data: tuple) -> None:
        """Accumulate a streamed G2 value into the running average record.

        Args:
            data: Tuple of ``(jid, g2_value)`` emitted by an ``AverageToolbox`` worker.
        """
        key, val = data[0], data[1]
        if self.avg_worker_active[key] is None:
            self.avg_worker_active[key] = [0, np.zeros(128, dtype=np.float32)]
        record = self.avg_worker_active[key]
        if record[0] == record[1].size:
            new_g2 = np.zeros(record[1].size * 2, dtype=np.float32)
            new_g2[0 : record[0]] = record[1]
            record[1] = new_g2
        record[1][record[0]] = val
        record[0] += 1

    def update_avg_info(self) -> None:
        """Trigger an update of the averaging worker's baseline plot."""
        if self.avg_worker is None:
            return
        self.avg_worker.update_plot()
