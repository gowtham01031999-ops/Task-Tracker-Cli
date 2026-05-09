"""CLI parsing, dependency wiring, and process-level error handling."""

from __future__ import annotations

import argparse
import sys

from task_tracker.dtos import CommandRequest
from task_tracker.exceptions import TaskCliError
from task_tracker.formatter import TaskFormatter
from task_tracker.infrastructure.clock import SystemClock
from task_tracker.infrastructure.file_lock import FileLock
from task_tracker.infrastructure.json_store import JsonStore
from task_tracker.infrastructure.logger import LifecycleLogger
from task_tracker.infrastructure.paths import PathResolver
from task_tracker.repositories.task_repository import TaskRepository
from task_tracker.services.task_service import TaskService
from task_tracker.validators import normalize_description


class CliRunner:
    """Coordinates CLI parsing, service execution, logging, and exit handling."""

    def __init__(self) -> None:
        self._paths = PathResolver()
        self._clock = SystemClock()
        self._logger = LifecycleLogger(self._paths.log_path(), self._clock)
        self._repository = TaskRepository(
            store=JsonStore(self._paths.storage_path()),
            file_lock=FileLock(self._paths.lock_path()),
            logger=self._logger,
        )
        self._service = TaskService(self._repository, self._logger, self._clock)
        self._formatter = TaskFormatter()

    def run(self, argv: list[str] | None = None) -> int:
        """Parse command-line arguments and execute the request."""

        parser = build_parser()
        args = parser.parse_args(argv)
        request = self._build_request(args)
        try:
            self._log_command_start(request)
            output = self._dispatch(request)
            self._logger.log("command_completed", changed=self._is_mutating(request.command), command=request.command)
            print(output)
            return 0
        except TaskCliError as exc:
            self._logger.log("command_failed", command=request.command, error_type=exc.__class__.__name__)
            print(str(exc), file=sys.stderr)
            return exc.exit_code
        except Exception as exc:  # noqa: BLE001
            self._logger.log("command_failed", command=request.command, error_type=exc.__class__.__name__)
            print(f"Unexpected error: {exc}", file=sys.stderr)
            return 1

    def _dispatch(self, request: CommandRequest) -> str:
        """Route a normalized request to the appropriate service behavior."""

        if request.command == "add":
            self._logger.log("persistence_started", storage_path=self._paths.storage_path())
            result = self._service.add_task(request.description or "")
            self._logger.log("persistence_succeeded", storage_path=self._paths.storage_path())
            return result.message
        if request.command == "update":
            self._logger.log("persistence_started", storage_path=self._paths.storage_path())
            result = self._service.update_task(request.task_id or 0, request.description or "")
            self._logger.log("persistence_succeeded", storage_path=self._paths.storage_path())
            return result.message
        if request.command == "delete":
            self._logger.log("persistence_started", storage_path=self._paths.storage_path())
            result = self._service.delete_task(request.task_id or 0)
            self._logger.log("persistence_succeeded", storage_path=self._paths.storage_path())
            return result.message
        if request.command == "mark-in-progress":
            self._logger.log("persistence_started", storage_path=self._paths.storage_path())
            result = self._service.mark_task_in_progress(request.task_id or 0)
            self._logger.log("persistence_succeeded", storage_path=self._paths.storage_path())
            return result.message
        if request.command == "mark-done":
            self._logger.log("persistence_started", storage_path=self._paths.storage_path())
            result = self._service.mark_task_done(request.task_id or 0)
            self._logger.log("persistence_succeeded", storage_path=self._paths.storage_path())
            return result.message
        tasks = self._service.list_tasks(status_filter=request.status_filter)
        return self._formatter.render_tasks(tasks)

    def _build_request(self, args: argparse.Namespace) -> CommandRequest:
        """Convert argparse output into a normalized request DTO."""

        if args.command in {"add", "update"}:
            description = normalize_description(args.description)
        else:
            description = None
        return CommandRequest(
            command=args.command,
            task_id=getattr(args, "id", None),
            description=description,
            status_filter=getattr(args, "status", None),
        )

    def _log_command_start(self, request: CommandRequest) -> None:
        """Emit the standard lifecycle events at request start."""

        self._logger.log("command_started", command=request.command, mutating=self._is_mutating(request.command))
        self._logger.log("command_resolved", command=request.command)
        self._logger.log("storage_path_resolved", storage_path=self._paths.storage_path())
        self._logger.log("log_path_resolved", log_path=self._paths.log_path())
        self._logger.log("lock_acquire_started", lock_path=self._paths.lock_path())

    @staticmethod
    def _is_mutating(command: str) -> bool:
        return command != "list"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(prog="task-cli.py", description="Task Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a task")
    add_parser.add_argument("description")

    update_parser = subparsers.add_parser("update", help="Update a task description")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("description")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int)

    progress_parser = subparsers.add_parser("mark-in-progress", help="Mark a task as in progress")
    progress_parser.add_argument("id", type=int)

    done_parser = subparsers.add_parser("mark-done", help="Mark a task as done")
    done_parser.add_argument("id", type=int)

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("status", nargs="?", choices=["done", "todo", "in-progress"])
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    """Execute the CLI and return a process exit code."""

    return CliRunner().run(argv)
