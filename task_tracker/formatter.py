"""User-facing text formatting utilities."""

from task_tracker.models import Task


class TaskFormatter:
    """Formats domain objects into CLI-friendly text."""

    def render_tasks(self, tasks: list[Task]) -> str:
        """Render tasks as a readable aligned table."""

        if not tasks:
            return "No tasks found."

        headers = ["ID", "Status", "Description", "Created", "Updated"]
        rows = [
            [str(task.id), task.status.value, task.description, task.created_at, task.updated_at]
            for task in tasks
        ]
        widths = [max(len(header), max(len(row[index]) for row in rows)) for index, header in enumerate(headers)]
        lines = [
            "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
            "  ".join("-" * widths[index] for index in range(len(headers))),
        ]
        for row in rows:
            lines.append("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
        return "\n".join(lines)
