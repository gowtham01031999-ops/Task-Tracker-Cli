# Task Tracker CLI Requirements

## 1. Project Overview

### Business Goal
The Task Tracker CLI exists to help a local user manage day-to-day tasks from the command line with a simple, reliable workflow.

### V1 Scope
Version 1 is a single-user command-line application implemented in Python using only the standard library. It stores task data in a JSON file in the current working directory, uses a modular object-oriented package internally, and supports core task lifecycle operations.

### Non-Goals
The following are explicitly out of scope for v1:

- Multi-user runtime behavior
- Shared remote storage
- Database-backed persistence
- Web or GUI interfaces
- External libraries or frameworks
- Advanced metadata such as priority, due dates, tags, or assignees
- Backup rotation and recovery automation

## 2. Functional Requirements

The CLI must support the following commands:

- Add a task
- Update a task description
- Delete a task
- Mark a task as in progress
- Mark a task as done
- List all tasks
- List tasks with status `done`
- List tasks with status `todo`
- List tasks with status `in-progress`

### Functional Clarifications

- There is no dedicated `not-done` command in v1.
- The `update` command changes only the task description.
- Task status changes are handled only through dedicated status commands.
- The application is optimized for a human user in a local terminal session.

## 3. Task Data Model

Each task record must contain the following fields:

- `id`: integer
- `description`: non-empty string
- `status`: one of `todo`, `in-progress`, or `done`
- `createdAt`: timestamp string
- `updatedAt`: timestamp string

### ID Policy

- Task IDs must be monotonically increasing integers.
- Deleted task IDs must never be reused.

### JSON Storage Shape

The JSON file must use a top-level structure similar to the following:

```json
{
  "version": 1,
  "nextId": 3,
  "tasks": [
    {
      "id": 1,
      "description": "Buy groceries",
      "status": "todo",
      "createdAt": "2026-05-09T10:00:00Z",
      "updatedAt": "2026-05-09T10:00:00Z"
    },
    {
      "id": 2,
      "description": "Prepare weekly report",
      "status": "in-progress",
      "createdAt": "2026-05-09T10:05:00Z",
      "updatedAt": "2026-05-09T10:20:00Z"
    }
  ]
}
```

### Schema Notes

- `version` exists from v1 to support future schema evolution.
- `nextId` stores the next assignable task ID.
- `tasks` contains the full task list.
- The JSON format is an internal implementation detail, not a public compatibility contract.

## 4. Storage and File Behavior

### File Location

- The task file must live in the current working directory.
- V1 should use a fixed filename, such as `tasks.json`.
- Current-directory storage is an intentional requirement, not a temporary default.

### File Ownership Model

- The CLI is the sole supported writer to the JSON file.
- Users may inspect the file manually.
- External tools or scripts are not supported writers in v1.

### File Creation and Loading

- If the JSON file does not exist, the application must create it automatically with a valid empty structure.
- If the file exists, the application must load and validate it before operating on task data.

### Durability Expectations

- Writes must use an atomic replace pattern where practical:
  - write updated data to a temporary file
  - replace the original file with the temporary file
- The implementation should reduce the risk of partial writes or corruption during crashes.

### Concurrency Expectations

- V1 must provide best-effort protection against overlapping write operations from concurrent CLI invocations.
- A simple lock-file or equivalent standard-library-based locking approach is acceptable.
- Full multi-user conflict coordination is not required in v1.

### Path Abstraction

- The internal code should isolate path resolution behind a small storage abstraction.
- V1 does not expose a user-facing path override.
- The architecture should allow a future storage-path override without redesigning task logic.

## 5. Error Handling and CLI Contract

### Output Contract

- CLI output must be human-readable plain text.
- Output should be suitable for local terminal use and light scripting.
- Readable table-like output is preferred for task listings.
- Lifecycle logging must not appear on `stdout`.
- User-facing errors and warnings must go to `stderr`.

### Exit Behavior

- Successful commands must return a zero exit code.
- Failures must return a non-zero exit code.

### Required Failure Cases

The CLI must fail clearly and safely for:

- Invalid command usage
- Invalid task ID format
- Missing task for update, delete, or status change
- Empty task description
- Malformed or corrupt JSON storage
- Lock acquisition or concurrency failure

### Corruption Policy

- If the JSON file is malformed or unreadable, the CLI must stop and report the problem.
- The CLI must not auto-reset, auto-repair, or overwrite malformed data.
- Existing corrupted data must be preserved for manual recovery.

## 6. Operational Expectations

### Scale Assumptions

- V1 is optimized for a single local user.
- Expected task volume is low enough that whole-file JSON load and save operations are acceptable.
- Performance optimization for very large datasets is not required in v1.

### Security and Privacy

- Task data sensitivity depends on where the user runs the tool.
- Users may unintentionally place the JSON file in a shared, synced, or version-controlled directory.
- The CLI should not weaken default operating system file permissions.
- V1 does not require OS-specific permission hardening logic.

### Recovery Expectations

- If the storage file becomes malformed, execution must stop without modifying the file.
- V1 does not maintain historical backups or backup rotation.
- Recovery is a manual operator task outside the CLI’s v1 scope.

### Logging Expectations

- V1 must always write lifecycle logs to a fixed log file in the current working directory.
- The recommended log filename is `task-cli.log`.
- The log file must be append-only with no rotation in v1.
- Logs must be lifecycle-oriented and must not include full task payloads or raw JSON contents.
- Normal success output must remain on `stdout`.
- Routine lifecycle logs must not be written to `stderr`.
- If log-file writing fails, the CLI should continue the main request path when safe and emit a warning to `stderr`.

## 7. Architecture Expectations

The implementation should keep a modular object-oriented structure with a simple but explicit separation of concerns.

### CLI and Parsing Layer

- Parse commands and arguments
- Validate input shape
- Format human-readable output
- Set process exit codes
- Route user-facing errors and warnings to `stderr`
- Keep the root `task-cli.py` file as a thin executable entrypoint only

### Task Service Layer

- Apply task lifecycle rules
- Create, update, delete, and filter tasks
- Enforce status transitions and field update policy
- Use domain objects rather than raw task dictionaries in business logic

### Domain Model Layer

- Represent tasks as explicit objects with fields and behavior
- Represent persisted store state as an explicit object
- Encapsulate mutations such as rename, mark in progress, and mark done on the domain model

### Repository Layer

- Coordinate lock-scoped load and save behavior
- Keep persistence access separate from task business rules

### Storage Layer

- Resolve the storage path
- Create the storage file if missing
- Load and validate JSON state
- Save JSON state safely
- Handle best-effort locking
- Append lifecycle logs to the fixed log file

### Architectural Rationale

Storage concerns should be isolated from command handling so the JSON backend can later be replaced or extended without rewriting core task logic. The internal package should favor SRP, encapsulation, composition, and low coupling over a single-file script design.

## 8. Packaging Expectations

- V1 should keep `task-cli.py` as the executable entrypoint for compatibility.
- The implementation should be organized as a small package with multiple focused modules.
- The implementation must rely only on the Python standard library.
- No packaging system or installable distribution is required for the initial version.

## 9. Extensibility Expectations

V1 should remain simple, but the design should not block reasonable future evolution.

### Supported Future Direction

- Additional task metadata such as priority, due date, notes, or tags
- Alternate storage path configuration
- Improved output modes
- More structured internal modules if the script grows
- Alternate CLI frontends or additional interfaces that reuse the same service layer

### Deferred Future Direction

- Shared multi-user access
- Remote APIs
- Database migration
- Distributed locking or synchronization

The architecture should be lightly extensible, not heavily future-proofed.

## 10. Assumptions and Constraints

- Python is the implementation language.
- Only the Python standard library may be used.
- The storage file remains in the current directory by design.
- The JSON schema is private to the CLI implementation.
- Timestamps are included for auditability and debugging value.
- Multi-user support is deferred and is not part of v1 acceptance.
- The codebase is modular internally even though the CLI entrypoint remains a single root script.

## 11. Public Interfaces and Types

### Command Interface

The CLI should support a command structure similar to:

```text
task-cli.py add "<description>"
task-cli.py update <id> "<description>"
task-cli.py delete <id>
task-cli.py mark-in-progress <id>
task-cli.py mark-done <id>
task-cli.py list
task-cli.py list done
task-cli.py list todo
task-cli.py list in-progress
```

### Status Values

The only permitted task status values in v1 are:

- `todo`
- `in-progress`
- `done`

### Ownership Contract

- Supported: CLI-managed file creation and updates
- Supported: manual inspection of the JSON file
- Unsupported: external programs writing to the file
- Unsupported: treating the JSON schema as a stable public API

## 12. Acceptance Criteria

The v1 implementation is acceptable when all of the following are true:

- A first-time user can run `task-cli.py` in an empty directory and obtain a valid `tasks.json`.
- A first-time successful invocation creates `task-cli.log` in the current working directory.
- All required commands work correctly against the JSON file.
- Task IDs remain stable and are never reused.
- Status changes are correctly applied through dedicated commands.
- Corrupt JSON is detected and not overwritten.
- Concurrent writes are reduced through best-effort locking.
- Task listings are readable for zero, one, and many tasks.
- Log entries are appended across invocations rather than overwriting prior history.

## 13. Test Plan

The implementation should be validated against the following scenarios:

- Missing file creates clean storage on first use.
- Add creates a task with the correct default fields and increments `nextId`.
- Update changes only the description and `updatedAt`.
- Delete removes the task and does not reuse its ID.
- Mark-in-progress sets the correct status.
- Mark-done sets the correct status.
- List returns all tasks.
- Filtered list commands return only the expected statuses.
- Invalid task IDs fail cleanly.
- Missing task references fail cleanly.
- Empty descriptions fail cleanly.
- Malformed JSON fails safely without overwriting the existing file.
- Concurrent write attempts are blocked or fail clearly under the best-effort locking mechanism.
- Log file creation and append behavior work across repeated runs.
- Lifecycle failures are recorded in the log file when log writes succeed.
- Logging failures surface a warning to `stderr` without corrupting task state handling.
- The modular package structure preserves the same external CLI behavior as the prior single-file implementation.

## 14. Approved Decisions Summary

- Python implementation
- Thin root entrypoint plus modular package implementation
- Standard-library-only implementation
- Fixed JSON file in the current working directory
- Internal JSON contract, not a public schema
- Core fields only: `id`, `description`, `status`, `createdAt`, `updatedAt`
- Monotonic integer IDs that are never reused
- No dedicated `not-done` command
- Human-readable text output only
- Always-on append-only log file in the current working directory
- Atomic replace writes
- Best-effort locking for concurrent writes
- Schema version included from v1
- Light extensibility for future fields without committing to multi-user architecture
