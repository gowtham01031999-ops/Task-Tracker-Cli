# Task Tracker CLI Execution Lifecycle

## 1. Summary

The Task Tracker CLI is a synchronous, short-lived command processor with a single persistence boundary: the local JSON file in the current working directory. Each invocation executes one unit of work from argument parsing through response output and process exit.

The v1 design intentionally avoids asynchronous execution, background jobs, remote integrations, and distributed coordination. The only external dependencies are local filesystem and operating system primitives used for path resolution, file locking, file reads, temporary file writes, atomic replace, terminal output, and append-only file logging.

## 2. Runtime Model

### Process Shape

- One CLI invocation handles one user request.
- The process starts, performs all work synchronously, prints a result, and exits.
- There is no long-running worker, daemon, server, or scheduler in v1.

### Request Context

Each invocation should build an in-memory request context containing:

- command name
- parsed arguments
- current working directory
- resolved storage path
- invocation timestamp
- whether the command is read-only or mutating
- resolved log file path

This context exists only for the lifetime of the process and is not persisted.

## 3. Complete Execution Lifecycle

### 3.1 Request Entry

Execution begins when a user runs a command such as:

```text
task-cli.py add "Buy groceries"
task-cli.py update 1 "Buy groceries and milk"
task-cli.py list done
```

The root `task-cli.py` entrypoint receives raw input through `sys.argv` and delegates execution into the package-level CLI runner.

### 3.2 CLI Validation

The CLI layer validates user input before any business logic runs.

Checks include:

- command exists
- required arguments are present
- numeric task IDs are valid integers
- description values are non-empty for commands that require them
- list filters are limited to supported values

Failures at this stage are terminal and must return a non-zero exit code without touching persisted task state.

### 3.3 Storage Resolution

The storage layer resolves the JSON file path in the current working directory, typically `tasks.json`.

At this stage the process determines:

- whether the file already exists
- whether it must be created on first use
- whether directory and file permissions allow the required operation
- where the append-only log file will be written, typically `task-cli.log`

### 3.4 Lock Acquisition

All commands acquire the best-effort lock before state load.

This includes read-only commands such as `list`.

The lock is shared across all commands because some platforms, especially Windows, can deny the atomic replace step if a concurrent reader still has the storage file open.

If the lock cannot be acquired:

- no state change is allowed
- the command fails with a clear error
- the process returns a non-zero exit code

### 3.5 State Load and Validation

After storage is available and any required lock is held, the CLI loads the JSON document into memory.

Validation includes:

- valid JSON syntax
- presence of `version`, `nextId`, and `tasks`
- correct top-level types
- valid task object structure
- allowed status values only
- integer `nextId`

If the file does not exist, the CLI may initialize a valid empty state.

If the file exists but is malformed or structurally invalid:

- execution stops immediately
- the existing file is preserved
- no repair or overwrite is attempted

### 3.6 Business Logic Dispatch

Once the state is loaded and validated, the orchestration layer dispatches to the task service layer, which works with domain objects instead of raw dictionaries.

Business logic by command:

- `add`
  - read `nextId`
  - create a new task with `status=todo`
  - set `createdAt` and `updatedAt`
  - append the task to `tasks`
  - increment `nextId`
- `update`
  - locate task by ID
  - replace `description`
  - update `updatedAt`
- `delete`
  - locate task by ID
  - remove the task
  - leave `nextId` unchanged
- `mark-in-progress`
  - locate task by ID
  - set `status` to `in-progress`
  - update `updatedAt`
- `mark-done`
  - locate task by ID
  - set `status` to `done`
  - update `updatedAt`
- `list`
  - optionally filter tasks by status
  - format the in-memory view for output
  - do not mutate state

### 3.7 Persistence

Mutating commands persist changes only after business logic succeeds fully in memory.

The write sequence is:

1. serialize the full in-memory state
2. write to a temporary file in the same directory
3. flush and close the temporary file
4. atomically replace the original JSON file
5. release the lock

This is the transaction commit boundary for v1.

### 3.8 Response Generation

Response rendering happens only after the command result is known.

Success responses:

- mutating commands emit a short confirmation
- list commands emit readable table-like text

Failure responses:

- print one concise error message
- avoid stack traces by default
- return a non-zero exit code

For mutating commands, success must mean the atomic replace step completed successfully.

## 4. Sync vs Async Decisions

### Chosen Model

The entire v1 execution path is synchronous.

### Why Synchronous

- the application is local and single-user oriented
- there are no remote calls or long-latency integrations
- every invocation performs one small unit of work
- synchronous control flow is easier to reason about for correctness, locking, and failure handling

### Async Boundaries That Do Not Exist

The design explicitly avoids:

- background workers
- event loops
- promises/futures
- queue-based retries
- eventual consistency

### External Contention Boundary

The only quasi-asynchronous behavior comes from the environment:

- another process may already hold the lock
- filesystem operations may fail or stall
- OS scheduling may delay execution

These are handled through blocking calls and explicit failure paths, not async orchestration.

## 5. State Changes

### Where State Changes Occur

State changes occur in exactly two places:

- in memory after the JSON document is loaded and before persistence
- on disk when the temporary file is atomically swapped into place

### Where State Changes Do Not Occur

- during CLI argument validation
- during schema validation
- during read-only list operations
- across multiple files or multiple systems

### Consistency Boundary

The JSON file replacement is the only persisted commit point. If execution fails before that step, the original file should remain unchanged.

## 6. Transaction Handling

### Transaction Unit

Each CLI invocation is the transaction boundary.

### Mutating Transaction Flow

1. acquire lock
2. load current state
3. validate state
4. apply one command’s business mutation in memory
5. write new full state to temporary file
6. atomically replace the original file
7. release lock

### Consistency Model

There is no database transaction manager. Correctness depends on:

- best-effort exclusive access during mutation
- atomic replace for the commit step
- no partial in-place file updates

## 7. Retry Handling

### Default Posture

Retries should be minimal and explicit.

### Safe Retry Cases

- lock contention where no mutation has been committed
- transient temporary file write failures when the original file is known to be unchanged

### Non-Retry Cases

- invalid user input
- malformed JSON
- schema validation failure
- task not found
- unknown atomic replace outcome

### Consistency Rule for Retries

Retries are only acceptable when the previous attempt is known not to have committed. If commit status is unclear, the command should fail and require an operator rerun rather than risk duplicate or conflicting state changes.

## 8. Failure Propagation

### Failure Classes

Failures should be identified in the layer where they occur and propagated upward without being swallowed.

Recommended categories:

- usage or input validation error
- task-not-found error
- storage read error
- schema or corruption error
- lock acquisition error
- storage write error

### Propagation Rule

- lowest responsible layer detects the issue
- intermediate layers attach context if useful
- top-level CLI boundary converts the failure into stderr output and an exit code

### User-Facing Failure Behavior

- one clear message
- no partial success output
- non-zero exit code
- no silent fallback or auto-repair

## 9. Failure Points

Failures can occur at these points in the lifecycle:

### Request Entry

- unsupported command
- malformed arguments

### Validation

- missing required argument
- invalid task ID
- empty description
- invalid list filter

### Storage Resolution

- directory inaccessible
- file permission failure

### Locking

- lock already held
- stale lock handling issue

### Read and Parse

- file missing in an unexpected state
- malformed JSON
- schema mismatch

### Business Logic

- task ID not found

### Write Path

- temporary file creation failure
- disk full
- file flush failure
- atomic replace failure
- lock release failure

### Output

- stdout or stderr write issues

Output failures are lower priority than persistence integrity, but they should still surface where practical.

## 10. External Integrations

The v1 CLI has no network or service dependencies.

External integrations are limited to:

- current working directory resolution
- file existence checks
- JSON file read and write
- temporary file creation
- atomic file replacement
- lock-file creation and removal or equivalent
- stdout and stderr output

This keeps the architecture simple, but also concentrates risk in local filesystem behavior.

## 11. Logging and Tracing

### Logging Expectations

Logging is always enabled in v1 and should be lightweight and local.

Useful events include:

- command started
- command type and storage path
- log file path
- whether the command is mutating
- lock acquire success or failure
- state load success or failure
- state write success or failure
- command completed
- command failed

### Logging Destination

- lifecycle logs must be appended to `task-cli.log` in the current working directory
- normal list and success output must remain clean and readable on `stdout`
- `stderr` is reserved for user-facing error messages and warnings such as log-write failures

### Tracing Model

There is no distributed trace model in v1. The request path is linear within one process, so lightweight local event correlation is sufficient.

## 12. Monitoring Hooks

There is no continuously running service to monitor, but the architecture should leave clear hook points for future observability.

Recommended hook points:

- command started
- command completed
- command failed
- lock contention detected
- corrupt JSON detected

These hooks can later support:

- verbose diagnostics
- audit logging
- metrics counters
- wrapper scripts
- scheduler integrations

## 13. Public Interfaces and Types

### Commands

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

### State Schema

```text
version: int
nextId: int
tasks: list[task]
task = {
  id: int,
  description: str,
  status: "todo" | "in-progress" | "done",
  createdAt: str,
  updatedAt: str
}
```

## 14. Test Scenarios

The implementation should be validated with these execution-flow scenarios:

- successful add, update, delete, mark, and list requests from parse through response
- file creation on first use
- lock contention on concurrent mutating commands
- corrupt JSON stopping execution before business logic
- task-not-found errors propagating cleanly to the CLI boundary
- failed lock acquisition followed by a later successful retry without duplicate state change
- failed persistence before atomic replace leaving the original file intact
- list commands never mutating state
- mutating commands only reporting success after persistence commit

## 15. Implementation Guidance

The code should preserve a clear internal layering:

- CLI/parser layer for request entry, validation, exit codes, and output
- domain model layer for task and store-state objects
- task service layer for domain behavior
- repository layer for lock-scoped persistence coordination
- infrastructure layer for path resolution, schema load/validation, locking, logging, and atomic persistence

This separation keeps the runtime lifecycle understandable and prevents filesystem concerns from leaking into business logic.
