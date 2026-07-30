# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from collections.abc import Callable


class WorkerSlot:
    """Tracks at most one in-flight ``QRunnable`` job in a single slot.

    Both background jobs in this app (averaging, g2 fitting) need the same
    bookkeeping: refuse to start a second job while one is running, and
    forget the worker once it finishes. This is that bookkeeping, factored
    out so it isn't hand-rolled once per job type.
    """

    def __init__(self) -> None:
        """Initialize an empty (not busy) slot."""
        self._worker = None

    @property
    def worker(self):
        """The in-flight worker, or ``None`` if the slot is idle."""
        return self._worker

    @property
    def busy(self) -> bool:
        """``True`` while a worker occupies this slot."""
        return self._worker is not None

    def start(self, thread_pool, worker, on_finished: Callable | None = None) -> None:
        """Start *worker* on *thread_pool* and occupy the slot until it finishes.

        Connects to ``worker.signals.finished`` to clear the slot; *on_finished*
        (if given) is called afterward with whatever arguments that signal
        carries (some workers emit a success flag, some emit nothing).

        Args:
            thread_pool: ``QThreadPool`` to run the worker on.
            worker: A ``QRunnable`` with a ``signals.finished`` Qt signal.
            on_finished: Optional callback invoked after the slot is cleared.

        Raises:
            RuntimeError: If a worker is already occupying this slot.
        """
        if self.busy:
            raise RuntimeError("a job is already running in this slot")
        self._worker = worker

        def _handle_finished(*args) -> None:
            self._worker = None
            if on_finished is not None:
                on_finished(*args)

        worker.signals.finished.connect(_handle_finished)
        thread_pool.start(worker)
