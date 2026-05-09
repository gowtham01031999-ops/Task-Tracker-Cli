"""Path resolution for current-directory artifacts."""

from pathlib import Path

from task_tracker.constants import LOCK_FILE, LOG_FILE, TASKS_FILE


class PathResolver:
    """Resolves storage, log, and lock file paths from a working directory."""

    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = cwd or Path.cwd()

    @property
    def cwd(self) -> Path:
        """Return the active working directory."""

        return self._cwd

    def storage_path(self) -> Path:
        """Return the JSON storage file path."""

        return self._cwd / TASKS_FILE

    def log_path(self) -> Path:
        """Return the lifecycle log file path."""

        return self._cwd / LOG_FILE

    def lock_path(self) -> Path:
        """Return the lock-file path."""

        return self._cwd / LOCK_FILE
