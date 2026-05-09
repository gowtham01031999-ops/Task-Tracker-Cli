"""Data transfer objects passed between layers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandRequest:
    """Normalized command request built from CLI arguments."""

    command: str
    task_id: int | None = None
    description: str | None = None
    status_filter: str | None = None


@dataclass(frozen=True)
class CommandResult:
    """User-facing command result."""

    message: str
    changed: bool
