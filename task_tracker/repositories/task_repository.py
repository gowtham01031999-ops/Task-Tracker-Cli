"""Repository for task state persistence and lock-scoped access."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from task_tracker.infrastructure.file_lock import FileLock
from task_tracker.infrastructure.json_store import JsonStore
from task_tracker.infrastructure.logger import LifecycleLogger
from task_tracker.models import TaskStoreState


class TaskRepository:
    """Coordinates persisted state access and lock scoping."""

    def __init__(self, store: JsonStore, file_lock: FileLock, logger: LifecycleLogger) -> None:
        self._store = store
        self._file_lock = file_lock
        self._logger = logger

    def load(self) -> TaskStoreState:
        """Load current state without mutating it."""

        self._logger.log("state_load_started")
        state = self._store.load_state()
        self._logger.log("state_load_succeeded", task_count=len(state.tasks))
        self._logger.log("state_validation_succeeded", next_id=state.next_id, version=state.version)
        return state

    def save(self, state: TaskStoreState) -> None:
        """Persist the provided in-memory state."""

        self._store.write_state(state)

    @contextmanager
    def locked_session(self) -> Iterator[TaskStoreState]:
        """
        Serialize command execution behind one lock boundary.

        All commands share the lock because Windows can deny atomic replace
        when a concurrent reader still has the storage file open.
        """

        with self._file_lock:
            self._logger.log("lock_acquire_succeeded")
            yield self.load()
