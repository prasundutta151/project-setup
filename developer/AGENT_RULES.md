# Guidelines & Rules for Coding Agents

This document defines mandatory guidelines for all AI coding assistants (Gemini, Codex, Claude, Cursor, Copilot, etc.) and human developers contributing to the project-setup project.

Load this file once at the start of each conversation/session. Retain its rules in context; reload only when this file changes or context is lost.

---

## 1. Developer Log Maintenance (`developer/DEV_NOTES.md`)

Whenever a user request or task is given:
1. **Freshen Up the Prompt**: Clean up, structure, and refine the raw prompt into an unambiguous, professional specification.
2. **Append to `developer/DEV_NOTES.md`**: Add a new entry at the top of the log using the established project schema:

```markdown
## YYYY-MM-DD HH:MM:SS TZ

Prompt / Request
- Refined and structured description of the requested task.

Changes Made
- Concrete summary of code, configuration, or documentation modifications.

Verification
- Exact commands, tests, or inspection steps executed to verify correctness.

Notes
- Relevant context, edge cases, follow-ups, or cautions.
```

---

## 2. Code Style & Naming Conventions (`script/`)

All new code and modifications in `script/` must strictly conform to existing codebase patterns:

1. **Language & Environment**:
   - Python 3.9+ compatible.
   - Always include `from __future__ import annotations` at the top of Python modules.
   - Use standard library modules whenever possible (`pathlib.Path`, `argparse`, `json`, `subprocess`, `sys`, `shutil`, `typing`).

2. **File Naming & Executables**:
   - User-facing CLI tools in `script/` use the `project-setup-<action>` pattern without `.py` extension (e.g. `script/project-setup-setup`). The generated `script/project-update` is the standard updater and keeps its name.
   - CLI scripts must begin with `#!/usr/bin/env python3` and maintain executable permissions.

3. **Variable & Function Naming**:
   - **Functions & Methods**: `snake_case` (e.g. `load_config()`, `resolve_setup_file()`, `project_root()`).
   - **Variables & Arguments**: `snake_case` (e.g. `workdir`, `fitspath`, `mspath`, `target_dirs`).
   - **Constants & Configuration Sets**: `UPPER_SNAKE_CASE` (e.g. `CONFIG_NAME`, `WORKDIR_SUBDIRS`, `CLEAN_TARGETS`).
   - **Classes**: `PascalCase`.

4. **Type Annotations**:
   - Use comprehensive type annotations on all function signatures (`Path`, `Dict[str, object]`, `List[str]`, `str | None`, `bool`).

5. **Robust File Operations**:
   - Use `pathlib.Path` for filesystem operations.
   - Use atomic write patterns (write to `.tmp` then `replace`) when saving configuration JSON files.

6. **CLI Standards**:
   - Use `argparse` with descriptive flag names matching existing commands (e.g. `--fitspath`, `--mspath`, `--workdir`, `--clean`, `--dry-run`, `--config-file`, `--show`).
   - Provide clear, user-friendly help strings and stdout status formatting.

---

## 3. Multi-Agent Coordination & Safety (.agent_lock Protocol)

To prevent simultaneous execution, race conditions, and broken Git states when working with multiple AI agents (Gemini, Codex, Claude, etc.):

1. **The `.agent_lock` Protocol**:
   - The root file `.agent_lock` acts as a mutual-exclusion lock for all coding agents and Git operations.
   - **Default / Idle State (`True`)**: By default, when no agent is actively executing, `.agent_lock` contains `True` (meaning available / unlocked).
   - **Acquiring the Lock (`False`)**: Whenever an agent begins a task or prompt:
     - Check `.agent_lock`; initialize it to `True` if absent before starting work.
     - If it is `True`, immediately set the file content to `False` to signal that an agent is actively working.
     - If it is `False`, another agent is currently running; wait or abort to avoid conflicts.
   - **Releasing the Lock (`True`)**: When the agent finishes its task, verifications, and developer-log updates, it must reset `.agent_lock` back to `True`.

2. **Git & Pipeline Operations**:
   - The same `.agent_lock` check applies to any Git commands (`git add`, `git commit`, `git checkout`, `git push`) and pipeline executions to guarantee mutual exclusion.

3. **Sequential Execution & Fresh State**:
   - Always operate sequentially, never running prompts in parallel across multiple tools.
   - Read fresh file contents from disk before making edits to avoid stale context.
   - Create clean Git commits or stashes before switching tools.

4. **Git Staging & Release Tar Boundaries**:
   - The `developer/` directory (including `DEV_NOTES.md`, `AGENT_RULES.md`, and `developer/script/`) as well as `guide/` are tracked in Git and staged/committed whenever Git actions (`script/project-update --git-push`, `git add`) are performed.
   - The `developer/` and `guide/` directories are **strictly excluded** from release distribution archives created with `--release` (`versions/project-setup-*.tar.gz`); keep these paths out of `release-files.txt`.

---

## 4. Temporary Developer Scripts (`developer/script/`)

Create a dedicated subdirectory `developer/script/` when needed for temporary scripts, scratch experiments, and prototyping tools:

1. **Relaxed Multi-Agent Read/Edit Concurrency**:
   - Files within `developer/script/` may be accessed in **read-only mode** by one agent while another agent modifies a **different file** in the same folder.
   - Multiple agents must never edit or overwrite the same temporary script simultaneously.

2. **Strict Scope Isolation**:
   - This relaxed concurrency exception applies **strictly and exclusively to `developer/script/`**.
   - Main production scripts (`script/`), pipeline definitions (`pipelines/`), documentation (`docs/`), and configuration/root files remain strictly bound to Section 3: **only one agent may execute at any given time** under the mutual-exclusion `.agent_lock` protocol.

---

## 5. Terminal Session Permission Lifecycle & Workspace Boundaries (Gemini)

To ensure seamless in-session developer workflow while maintaining strict workspace security:

1. **Session-Level Initial Authorization**:
   - When a Gemini session is opened in the terminal, permission is requested and established at the beginning of the session.

2. **Autonomous In-Session Execution Within Parent Directory**:
   - Once authorized, between the session start and its conclusion, the agent operates autonomously without repeatedly asking for per-action permissions for standard operations (reading, writing, editing files, running project commands, and running tests), **as long as all work is strictly confined to the project parent directory** (`/home/astrolab-pd/Documents/project-setup`).

3. **Strict Directory Boundary Enforcement**:
   - The agent is strictly prohibited from modifying, reading, or running commands on files outside the parent project root directory without explicit user instruction.

4. **Session Exit & Automatic Permission Revocation**:
   - Upon exiting, closing, or terminating the session, all granted permissions expire immediately.
   - The agent possesses no ongoing authority or permission to perform any actions once the session has ended.


