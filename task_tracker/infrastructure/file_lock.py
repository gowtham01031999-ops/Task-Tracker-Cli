"""Best-effort filesystem lock based on an exclusive lock file."""

import os
from pathlib import Path

from task_tracker.exceptions import LockAcquisitionError


class FileLock:
    """Acquires and releases the lock file used to serialize CLI work."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path

    def __enter__(self) -> "FileLock":
        try:
            fd = os.open(str(self._lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError as exc:
            raise LockAcquisitionError(
                "Could not acquire lock. Another task command may already be running."
            ) from exc
        except OSError as exc:
            raise LockAcquisitionError(f"Failed to acquire lock file '{self._lock_path.name}': {exc}") from exc
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        try:
            self._lock_path.unlink(missing_ok=True)
        except OSError:
            pass
