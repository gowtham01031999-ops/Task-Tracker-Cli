"""Append-only lifecycle logging."""

import os
import sys
from pathlib import Path
from typing import Any

from task_tracker.infrastructure.clock import SystemClock


class LifecycleLogger:
    """Writes one-line lifecycle events to the configured log file."""

    def __init__(self, log_path: Path, clock: SystemClock) -> None:
        self._log_path = log_path
        self._clock = clock

    def log(self, event: str, **fields: Any) -> None:
        """Append a lifecycle event and keep logging failures non-fatal."""

        parts = [f"{self._clock.now_iso()} event={event}"]
        for key, value in sorted(fields.items()):
            parts.append(f"{key}={self._sanitize(value)}")
        line = (" ".join(parts) + "\n").encode("utf-8", errors="replace")
        try:
            fd = os.open(str(self._log_path), os.O_APPEND | os.O_CREAT | os.O_WRONLY)
            try:
                os.write(fd, line)
            finally:
                os.close(fd)
        except OSError as exc:
            # Logging failure must not compromise task persistence or command handling.
            print(f"Warning: failed to write log file '{self._log_path.name}': {exc}", file=sys.stderr)

    @staticmethod
    def _sanitize(value: Any) -> str:
        return str(value).replace("\r", "\\r").replace("\n", "\\n")
