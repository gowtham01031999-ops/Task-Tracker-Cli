"""Application service for task lifecycle operations."""

from task_tracker.dtos import CommandResult
from task_tracker.enums import TaskStatus
from task_tracker.infrastructure.clock import SystemClock
from task_tracker.infrastructure.logger import LifecycleLogger
from task_tracker.models import Task
from task_tracker.repositories.task_repository import TaskRepository


class TaskService:
    """Owns task business logic while delegating storage to the repository."""

    def __init__(self, repository: TaskRepository, logger: LifecycleLogger, clock: SystemClock) -> None:
        self._repository = repository
        self._logger = logger
        self._clock = clock

    def add_task(self, description: str) -> CommandResult:
        """Create a new task."""

        with self._repository.locked_session() as state:
            task = state.create_task(description, self._clock.now_iso())
            self._repository.save(state)
            return CommandResult(message=f"Task added successfully (ID: {task.id})", changed=True)

    def update_task(self, task_id: int, description: str) -> CommandResult:
        """Rename an existing task."""

        with self._repository.locked_session() as state:
            task = state.get_task(task_id)
            task.rename(description, self._clock.now_iso())
            self._repository.save(state)
            return CommandResult(message=f"Task {task_id} updated successfully.", changed=True)

    def delete_task(self, task_id: int) -> CommandResult:
        """Delete an existing task."""

        with self._repository.locked_session() as state:
            state.remove_task(task_id)
            self._repository.save(state)
            return CommandResult(message=f"Task {task_id} deleted successfully.", changed=True)

    def mark_task_in_progress(self, task_id: int) -> CommandResult:
        """Set a task to in-progress."""

        with self._repository.locked_session() as state:
            task = state.get_task(task_id)
            task.mark_in_progress(self._clock.now_iso())
            self._repository.save(state)
            return CommandResult(message=f"Task {task_id} marked as in progress.", changed=True)

    def mark_task_done(self, task_id: int) -> CommandResult:
        """Set a task to done."""

        with self._repository.locked_session() as state:
            task = state.get_task(task_id)
            task.mark_done(self._clock.now_iso())
            self._repository.save(state)
            return CommandResult(message=f"Task {task_id} marked as done.", changed=True)

    def list_tasks(self, status_filter: str | None = None) -> list[Task]:
        """Return tasks filtered by status if requested."""

        with self._repository.locked_session() as state:
            status = TaskStatus(status_filter) if status_filter else None
            return state.list_tasks(status=status)
