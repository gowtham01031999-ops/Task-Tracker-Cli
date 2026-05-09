# Task Tracker CLI

Task Tracker is a Python command-line application for managing day-to-day tasks with local JSON storage. It is implemented with the Python standard library only and uses a modular OOP structure internally so the codebase is easier to maintain and extend.

## Features

- Add, update, delete, and list tasks
- Mark tasks as `in-progress` or `done`
- Store data in `tasks.json` in the current working directory
- Write lifecycle logs to `task-cli.log`
- Protect file updates with atomic writes and a lock file

## Project Structure

```text
task-cli.py
task_tracker/
  cli.py
  constants.py
  dtos.py
  enums.py
  exceptions.py
  formatter.py
  models.py
  validators.py
  services/
  repositories/
  infrastructure/
REQUIREMENTS.md
EXECUTION_LIFECYCLE.md
requirements.txt
```

## How to Run

Use Python 3 from the project directory:

```powershell
python task-cli.py add "Buy groceries"
python task-cli.py update 1 "Buy groceries and milk"
python task-cli.py mark-in-progress 1
python task-cli.py mark-done 1
python task-cli.py list
python task-cli.py list done
```

## Files Created at Runtime

- `tasks.json`: persisted task state
- `task-cli.log`: append-only lifecycle log
- `tasks.json.lock`: temporary lock file while a command is running

## Design Overview

- `task-cli.py` is a thin entrypoint only.
- `task_tracker/cli.py` handles parsing, dependency wiring, and exit-code mapping.
- `task_tracker/models.py` defines the domain objects.
- `task_tracker/services/` contains business logic.
- `task_tracker/repositories/` coordinates lock-scoped persistence access.
- `task_tracker/infrastructure/` contains JSON storage, file locking, logging, clock, and path resolution.

## Dependencies

This project uses only the Python standard library. `requirements.txt` is present for clarity and currently does not list external packages.

## Documentation

- [REQUIREMENTS.md](</abs/path/c:/Users/gowth/Downloads/Roadmap Projects/Task Tracker/REQUIREMENTS.md>) contains the product, architecture, storage, logging, and acceptance requirements.
- [EXECUTION_LIFECYCLE.md](</abs/path/c:/Users/gowth/Downloads/Roadmap Projects/Task Tracker/EXECUTION_LIFECYCLE.md>) describes the runtime flow, locking, persistence, failures, retries, and observability behavior.
