"""Domain models for tasks and persisted state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from task_tracker.enums import TaskStatus
from task_tracker.exceptions import SchemaValidationError, TaskNotFoundError
from task_tracker.validators import normalize_description, require_integer, require_non_empty_string


@dataclass
class Task:
    """Single task entity with domain behavior."""

    id: int
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str

    def rename(self, new_description: str, timestamp: str) -> None:
        """Update the task description and refresh the modification time."""

        self.description = normalize_description(new_description)
        self.updated_at = timestamp

    def mark_in_progress(self, timestamp: str) -> None:
        """Move the task to the in-progress state."""

        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = timestamp

    def mark_done(self, timestamp: str) -> None:
        """Move the task to the done state."""

        self.status = TaskStatus.DONE
        self.updated_at = timestamp

    def to_dict(self) -> dict[str, Any]:
        """Serialize the task into the persisted JSON shape."""

        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "Task":
        """Hydrate a task from persisted JSON data."""

        if not isinstance(payload, dict):
            raise SchemaValidationError("Each task must be a JSON object.")
        required = {"id", "description", "status", "createdAt", "updatedAt"}
        if not required.issubset(payload):
            raise SchemaValidationError("Each task must contain id, description, status, createdAt, updatedAt.")
        task_id = require_integer(payload["id"], "Task ID")
        description = require_non_empty_string(payload["description"], "Task description")
        created_at = require_non_empty_string(payload["createdAt"], "Task createdAt")
        updated_at = require_non_empty_string(payload["updatedAt"], "Task updatedAt")
        try:
            status = TaskStatus(payload["status"])
        except ValueError as exc:
            raise SchemaValidationError("Task status must be one of: todo, in-progress, done.") from exc
        return cls(
            id=task_id,
            description=description,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class TaskStoreState:
    """In-memory representation of the persisted task store."""

    version: int
    next_id: int
    tasks: list[Task] = field(default_factory=list)

    def create_task(self, description: str, timestamp: str) -> Task:
        """Create and register a new task using the next available ID."""

        task = Task(
            id=self.next_id,
            description=normalize_description(description),
            status=TaskStatus.TODO,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.tasks.append(task)
        self.next_id += 1
        return task

    def remove_task(self, task_id: int) -> None:
        """Delete a task from the state."""

        task = self.get_task(task_id)
        self.tasks.remove(task)

    def get_task(self, task_id: int) -> Task:
        """Return a task by ID or raise if it is missing."""

        for task in self.tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f"Task {task_id} was not found.")

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """Return tasks filtered by status and ordered by ID."""

        selected = [task for task in self.tasks if status is None or task.status == status]
        return sorted(selected, key=lambda task: task.id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full store into the persisted JSON shape."""

        return {
            "version": self.version,
            "nextId": self.next_id,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "TaskStoreState":
        """Hydrate the task store from persisted JSON data."""

        if not isinstance(payload, dict):
            raise SchemaValidationError("Storage state must be a JSON object.")
        version = payload.get("version")
        next_id = payload.get("nextId")
        tasks_payload = payload.get("tasks")
        if not isinstance(version, int):
            raise SchemaValidationError("Storage field 'version' must be an integer.")
        require_integer(next_id, "Storage field 'nextId'")
        if not isinstance(tasks_payload, list):
            raise SchemaValidationError("Storage field 'tasks' must be a list.")

        tasks = [Task.from_dict(task_payload) for task_payload in tasks_payload]
        seen_ids: set[int] = set()
        max_id = 0
        for task in tasks:
            if task.id in seen_ids:
                raise SchemaValidationError(f"Duplicate task ID found: {task.id}.")
            seen_ids.add(task.id)
            max_id = max(max_id, task.id)
        if next_id <= max_id:
            raise SchemaValidationError("Storage field 'nextId' must be greater than existing task IDs.")
        return cls(version=version, next_id=next_id, tasks=tasks)
