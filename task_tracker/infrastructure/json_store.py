"""Filesystem-backed JSON storage with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from task_tracker.constants import APP_VERSION
from task_tracker.exceptions import SchemaValidationError, StorageReadError, StorageWriteError
from task_tracker.models import TaskStoreState


class JsonStore:
    """Manages the persisted JSON file used by the task tracker."""

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path

    def ensure_exists(self) -> None:
        """Create an empty persisted state file if none exists."""

        if self._storage_path.exists():
            return
        self.write_state(TaskStoreState(version=APP_VERSION, next_id=1, tasks=[]))

    def load_state(self) -> TaskStoreState:
        """Load and validate the current persisted state."""

        try:
            self.ensure_exists()
        except OSError as exc:
            raise StorageWriteError(f"Failed to create storage file '{self._storage_path.name}': {exc}") from exc

        try:
            with self._storage_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise SchemaValidationError(f"Storage file '{self._storage_path.name}' contains malformed JSON.") from exc
        except OSError as exc:
            raise StorageReadError(f"Failed to read storage file '{self._storage_path.name}': {exc}") from exc

        return TaskStoreState.from_dict(payload)

    def write_state(self, state: TaskStoreState) -> None:
        """Persist the full state using a temp-file-and-replace commit."""

        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=self._storage_path.parent,
                prefix=f"{self._storage_path.stem}.",
                suffix=".tmp",
                encoding="utf-8",
            ) as handle:
                json.dump(state.to_dict(), handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = handle.name
            os.replace(temp_path, self._storage_path)
        except OSError as exc:
            raise StorageWriteError(f"Failed to write storage file '{self._storage_path.name}': {exc}") from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
