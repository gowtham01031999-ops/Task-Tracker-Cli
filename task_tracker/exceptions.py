"""Typed exception hierarchy for the CLI."""


class TaskCliError(Exception):
    """Base exception for known CLI failures."""

    exit_code = 1


class UsageError(TaskCliError):
    """Raised when user input is invalid."""

    exit_code = 2


class TaskNotFoundError(TaskCliError):
    """Raised when a referenced task does not exist."""


class LockAcquisitionError(TaskCliError):
    """Raised when the storage lock cannot be acquired."""


class StorageReadError(TaskCliError):
    """Raised when persisted state cannot be read."""


class SchemaValidationError(TaskCliError):
    """Raised when persisted state is malformed."""


class StorageWriteError(TaskCliError):
    """Raised when persisted state cannot be written safely."""
