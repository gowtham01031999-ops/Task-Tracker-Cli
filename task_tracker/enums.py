"""Enumerations used by the task tracker domain."""

from enum import Enum


class TaskStatus(str, Enum):
    """Allowed task lifecycle states."""

    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"
