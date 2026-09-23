# AGENT SAMPLE

This file is a template. A copy of it becomes `AGENT_<PROJECT>.md` in the
project root, where `<PROJECT>` is the upper-case name of the project. That
per-project agent file controls project organization, complex-task processing,
planning, execution, logging/archival, documentation, versioning, release
creation, Git updates, and context efficiency.

The agent MUST NOT automatically advance between complex-task stages. Every stage
requires an explicit user command.

---

## 1. Purpose

This file defines the standard operating method for the project agent. It controls
project organization, complex-task processing, planning, execution, archival,
documentation, versioning, release creation, Git updates, and context efficiency.

---

## 2. Project Structure

```text
PROJECT_ROOT/
├── AGENT_<PROJECT>.md        # (file) this agent file
├── .agent-state/             # exclusive session lock
│   └── lock/
│       └── owner.json        # agent, agent_version, session_id, host, started_utc
├── HANDOFF.md                # (file) handoff: objective, state, verification, next action
├── devl/                     # all development happens here
│   ├── methods/              # user-created methods
│   ├── tmp/                  # temporary PROMPT.md, TASK.md, PLAN.md, REPORT.md
│   ├── log/                  # logs by datetime: {datetime}_PROMPT/TASK/PLAN/REPORT
│   └── testdir/              # the developer runs tests from here
│       ├── data/             # test data
│       └── plots/            # test plots
├── src/
│   ├── scripts/              # all python source files
│   ├── src/                  # all C/C++ source files
│   ├── env/                  # additional directories given into release
│   ├── json/                 # all json files
│   ├── version/              # VERSION file and individual versions
│   └── docs/                 # documentation (DOCUMENTATION.md rules, LICENSE files)
└── release/
    ├── present/              # current version (what the public sees)
    └── old-versions/         # older releases
```

### Directory Responsibilities

### .agent-state/
Exclusive session lock. Project directories may be synchronized across machines
and edited with different AI agents; while one agent holds an editing session on
one machine, no other agent on any machine may edit.

- `.agent-state/lock/owner.json` — lock owner record: agent, agent_version,
  session_id, host, started_utc. Only the owning session may release the lock.
  Never remove or overwrite another session's lock.

### HANDOFF.md
Handoff file carrying objective, current state, verification, and next action,
plus a metadata block between `<!-- agent-handoff:start -->` and
`<!-- agent-handoff:end -->` (handoff_id, updated_utc, computer, agent,
session_id, base_commit, branch).

### devl/
All development happens here. Workflow files, user-created methods, logs, and
the test/validation workspace live under `devl/`.

- `devl/methods/` — reusable user-created methods and methodology/helper material.
- `devl/tmp/` — all temporary workflow files, including `PROMPT.md`, `TASK.md`,
  `PLAN.md`, `REPORT.md`, and any other temporary file generated during work.
- `devl/log/` — a chronological log of workflow activity, kept as dated files such
  as `YYYY-MM-DD_HHMM_PROMPT.md`, `YYYY-MM-DD_HHMM_TASK.md`,
  `YYYY-MM-DD_HHMM_PLAN.md`, `YYYY-MM-DD_HHMM_REPORT.md`.
- `devl/testdir/` — the test/validation workspace.
  - `devl/testdir/data/` — test data used for validation. Original user-supplied
    test data must not be overwritten or deleted during testing.
  - `devl/testdir/plots/` — test/validation plots and figures.

### src/
All source files created during development.

- `src/scripts/` — Python source files (main executables and user-defined Python
  function modules).
- `src/src/` — C/C++ source files.
- `src/env/` — additional directories that will be included in the release.
- `src/json/` — JSON configuration/settings files.
- `src/version/` — version information.
  - `src/version/VERSION` — the `VERSION` file and per-version snapshots.
- `src/docs/` — all project documentation, including:
  - `src/docs/DOCUMENTATION.md` — the documentation rule file.
  - Generated HTML/TXT documentation as produced by the documentation stage.

### release/
Releasable/installable software.

- `release/present/` — the current version. This is what the public git release
  exposes as the present version.
- `release/old-versions/` — older versions, kept as subdirectories of `release/`.

---

## 3. Agent Instantiation

Command:

```text
instantiate: AGENT
```

When this command is received:

1. Locate and read `AGENT_<PROJECT>.md`. Make sure `<PROJECT>` is the upper-case
   name of the current project; other `AGENT_` files will not be read and used.
2. Load its rules ONCE as session-level agent state.
3. Reset workflow interpretation to the current method.
4. Initialize and verify the standard project environment.
5. Create any missing standard directories: `.agent-state/lock/`, devl/methods/`, `devl/tmp/`,
   `devl/log/`, `devl/testdir/data/`, `devl/testdir/plots/`, `src/scripts/`,
   `src/src/`, `src/env/`, `src/json/`, `src/version/`, `src/docs/`, and
   `release/present/`.
6. If `src/version/VERSION` does not exist, create it with initial version `0.0.1`.
   If it already exists, preserve it exactly and never overwrite its history
   during instantiation.
7. Do NOT automatically create `devl/tmp/PROMPT.md`, `devl/tmp/TASK.md`, or
   `devl/tmp/PLAN.md`; these are workflow files created or supplied only when
   needed.
8. Never delete, clear, or overwrite existing project directories or their
   contents during instantiation. Instantiation must be idempotent and safe to
   repeat.
9. Do not execute any pending stage automatically.
10. Report that the method is loaded.
11. Report which directories/files already existed and which were created.
12. Report the current VERSION.
13. Report the current workflow state if known.
14. Show currently available commands.

### Session Lock and Handoff Check at Instantiation

At session start — and when resuming after a long inactive time — the agent must:

1. check `.agent-state/lock/` status with a lightweight status/ownership read only;
2. if the lock is held by another agent/host: report the owner from
   `.agent-state/lock/owner.json` (agent, agent_version, session_id, host,
   started_utc), refuse to start editing, and STOP;
3. if no lock exists: acquire it for this session (record this agent, host, and
   session id in `.agent-state/lock/owner.json`) before any editing;
4. if the lock is held by this session: proceed;
5. read `HANDOFF.md` for objective, current state, verification, and next action
   (metadata block between `<!-- agent-handoff:start -->` and
   `<!-- agent-handoff:end -->`); report the handoff state.

Only the owning session may release the lock, and only when its work is done.
Never remove or overwrite another session's lock.

### Method Caching Rule

After successful instantiation:

- Do NOT reread `AGENT_<PROJECT>.md` for every command or stage.
- Treat the loaded method as valid for the active agent/session.
- Reread it only when:
  1. the user explicitly gives `instantiate: AGENT` again;
  2. `AGENT_<PROJECT>.md` is known or detected to have changed; or
  3. the active session has lost the loaded method state.
- Prefer a lightweight timestamp/hash/metadata check over rereading the full file
  when checking whether the method changed.
- Do not repeatedly inject the full method text into prompts when it is already in
  active context.

`instantiate: AGENT` does not start complex mode.

### Test-Data Reminder at Instantiation

After initialization, the agent must explicitly tell the user:

```text
If this project requires software/data validation, please place the test data
you want the agent to use in devl/testdir/data/.
```

The agent should report whether `devl/testdir/data/` is empty or already contains
test material, without reading all test-data contents merely for this reminder.
It means **load the agent method + initialize/verify the project environment**.

### Instantiation Safety

Repeated `instantiate: AGENT` commands must be safe. Existing directories, VERSION
history, source code, data, documentation, archives, releases, and temporary
workflow files must not be destroyed or reset. Only missing standard
infrastructure is created.

---

## 4. Complex Mode

The controlled complex workflow begins ONLY with:

```text
complex: start
```

and ends ONLY with:

```text
complex: end
```

The agent must not infer complex mode merely because a task appears difficult.

When `complex: start` is received:

1. enter COMPLEX MODE;
2. record workflow start time;
3. ensure `devl/tmp/` exists;
4. inspect only enough state to identify possible next stages;
5. explain what each available next stage will do;
6. present numbered choices with exact commands;
7. remind the user to place any required test data in `devl/testdir/data/`;
8. report whether `devl/testdir/data/` appears empty or contains test material,
   using only a lightweight directory check;
9. STOP.

The reminder should be explicit:

```text
Before execution, place the test data to be used for validation in devl/testdir/data/.
```

No stage is run automatically.

### Holding Complex Mode

Command:

```text
complex: hold
```

When `complex: hold` is received while in COMPLEX MODE:

1. SAVE the full complex-mode status: current stage, pending stages, and the
   state of PROMPT/TASK/PLAN/REPORT material;
2. leave COMPLEX MODE temporarily;
3. accept non-complex commands;
4. confirm with a message stating that complex mode is on hold, the status was
   saved, and non-complex commands are now accepted.

### Restarting Complex Mode

Command:

```text
complex: restart
```

When `complex: restart` is received after a hold:

1. restore the last saved complex-mode status;
2. report where work was paused (current stage and pending stages);
3. present the available next-stage options with exact commands;
4. STOP and wait.

If no saved complex-mode status exists, explain that there is nothing to
restart and STOP.

### Working Outside Complex Mode

The archive, version, document, release, and git stages can also be run OUTSIDE
complex mode with the `general:` command set. No complex-mode status is required:

```text
general: archive
general: version
general: document
general: release
general: git
```

Each performs the same work as its `complex:` counterpart. `general:` commands
never enter, resume, or require COMPLEX MODE.

---

## 5. Mandatory Stage Control

During COMPLEX MODE, every stage is separately dispatched.

After EVERY stage the agent must:

1. report what it did;
2. report files created/modified;
3. report success/failure/limitations;
4. state which stage the task is currently in;
5. explain sensible next stages;
6. give numbered options;
7. include backward/repeat stages when useful;
8. show the exact command for every option;
9. STOP and wait.

Example:

```text
Current stage: TASK (approved, PLAN.md not yet created)

Available actions:

1. Process TASK
   Command: complex: TASK
   Creates PLAN.md from the approved TASK.md.

2. Re-process PROMPT
   Command: complex: PROMPT
   Rebuilds TASK.md from PROMPT.md.

3. End workflow
   Command: complex: end
```

The numbered choice is informational. The agent acts only on the explicit command.

### Mandatory Go-Back Choice After Every Stage

After EVERY completed stage, including PROMPT, TASK, PLAN execution, archive,
documentation, version, release, and Git update, the agent must explicitly ask
the user whether they want to continue or go back to an earlier stage.

The menu must include applicable earlier stages, not only the next stage.

For example:

```text
Current stage: PLAN (executed, REPORT.md written)

What would you like to do next?

1. Continue to the next stage
   Command: <next-stage command>

2. Go back to PROMPT
   Command: complex: PROMPT

3. Go back to TASK / planning
   Command: complex: TASK

4. Go back to PLAN execution or end the workflow
   Command: complex: PLAN   OR   complex: end
```

The exact choices must be adapted to the current stage. If more than three earlier
stages are meaningful, the agent may show more numbered options, but it must always
include the relevant backward paths.

The agent must not interpret a number alone as authorization. The user must send
the explicit command shown for the selected stage.

When going backward, the agent must explain which downstream artifacts may become
stale. For example, re-processing PROMPT may make the existing TASK, PLAN,
REPORT, documentation, version/release, or Git state outdated. The agent must not
automatically regenerate those downstream stages.

---

## 6. PROMPT Stage

Command:

```text
complex: PROMPT
```

Input (default; the user may optionally supply a full file path to use instead):

```text
devl/tmp/PROMPT.md
```

Actions:

1. Read the original prompt.
2. Preserve its original contents for archival.
3. Rewrite it into a clearer and more efficient LLM specification.
4. Remove repetition without removing requirements.
5. Identify objective, inputs, outputs, constraints, relevant files, validation,
   and completion criteria.
6. Record unresolved important ambiguities rather than guessing.
7. Create/update `devl/tmp/TASK.md`.

Recommended TASK structure:

```text
# TASK

## Objective
## Refined Prompt
## Requirements
## Inputs
## Expected Outputs
## Constraints
## Execution Rules
## Validation
## Completion Criteria
## Questions / Ambiguities
```

`devl/tmp/TASK.md` defines WHAT must be achieved.

STOP after TASK.md is created. Do not create PLAN.md or execute the task.

---

## 7. TASK Stage

Command:

```text
complex: TASK
```

Input (default; the user may optionally supply a full file path to use instead):

```text
devl/tmp/TASK.md
```

Actions:

1. Read the approved TASK.md.
2. Preserve the approved objective.
3. Determine required files, dependencies, operations, validation, and outputs.
4. Create/update `devl/tmp/PLAN.md`.

Recommended PLAN structure:

```text
# EXECUTION PLAN

## Objective
## Inputs
## Files to Inspect
## Execution Steps
## Files Expected to be Created
## Files Expected to be Modified
## Validation / Testing
## Expected Deliverables
## Risks / Decisions
## Completion Check
```

`devl/tmp/PLAN.md` defines HOW the task will be achieved.

STOP after PLAN.md is created. Do not execute it.

---

## 8. PLAN Execution Stage

Command:

```text
complex: PLAN
```

Actions:

1. record execution start time;
2. read the approved TASK.md and PLAN.md (defaults `devl/tmp/TASK.md` and
   `devl/tmp/PLAN.md`, or user-supplied full paths);
3. execute the approved plan;
4. put main executable programs and Python source in `src/scripts/`;
5. put C/C++ source in `src/src/`;
6. put user-created methods in `devl/methods/`;
7. put JSON configuration in `src/json/`;
8. put release extras in `src/env/`;
9. use user-supplied validation data from `devl/testdir/data/` when relevant,
   without modifying the originals;
10. put test/validation plots in `devl/testdir/plots/`;
11. put temporary working artifacts in `devl/tmp/`;
12. test and validate, using suitable data from `devl/testdir/data/` when available;
13. record failures and corrective actions;
14. record deviations from PLAN.md;
15. write `devl/tmp/REPORT.md`.

Completion report:

```text
COMPLETION REPORT

Status:
Execution start time:
Execution stop time:

Summary:
Actions performed:
Files created:
Files modified:
Tests/validation performed:
Results:
Problems encountered:
Changes from PLAN.md:
Unfinished items:
Final completion status:
```

Final status must be one of:

```text
COMPLETED
PARTIALLY COMPLETED
FAILED
```

Minor implementation changes are allowed. Major changes in objective, scope,
architecture, dependencies, destructive actions, or strategy require user approval.

Execution does NOT automatically archive, document, version, release, Git-update,
or end complex mode.

STOP after execution and show next-stage options.

---

## 9. Testing With Project Test Data

Testing is a required part of execution whenever suitable test data is available.

### Test Data Location

The agent must look for user-supplied test data in:

```text
devl/testdir/data/
```

The `devl/testdir/data/` directory contains user-supplied data intended for testing
and validation. The agent must identify which files are appropriate for the current
task before using them.

### Testing Rule

During:

```text
complex: PLAN
```

the agent must, when relevant:

1. inspect `devl/testdir/data/` for test data related to the task;
2. use the provided test data to test newly created or modified software;
3. prefer supplied project test data over fabricated data when suitable test data
   already exists;
4. never modify or overwrite original test/input data unless the approved task
   explicitly requires it;
5. write temporary test outputs to `devl/tmp/` unless the output is an intended
   persistent project result;
6. verify that the program completes successfully on the test data;
7. check important output files, formats, values, dimensions, metadata, or other
   task-specific expectations where applicable;
8. record the exact test data used and the validation performed in the completion
   report;
9. report failed tests rather than hiding or bypassing them;
10. distinguish a software failure from unsuitable, incomplete, or missing test
    data.

If suitable test data is present, the agent must not declare the implementation
`COMPLETED` without running the relevant tests unless the user explicitly instructs
the agent not to run them or testing is technically impossible.

If no suitable test data exists in `devl/testdir/data/`, the agent must report that
fact. It may use minimal synthetic test data only when useful and safe, and must
clearly identify that data as synthetic.

### Test Safety

Testing must not:

- destroy or overwrite the original files in `devl/testdir/data/`;
- silently replace user-supplied test data;
- run unnecessarily expensive processing when a representative subset is sufficient;
- expose private data in logs, documentation, archives, or releases.

When a representative subset of a large test dataset is sufficient, prefer the
subset to reduce runtime and LLM/tool overhead, and record that choice.

### Completion Report

The completion report should include:

```text
Test data used:
Test command(s):
Test outputs:
Validation checks:
Test result:
Limitations:
```

After testing and execution are complete, STOP and present the available next-stage
options.

---

## 10. Archive Stage

Command:

```text
complex: archive
```

Purpose: archive Prompt–Task–Plan and completion information in `devl/log/`.

Create a unique Markdown file, preferably:

```text
devl/log/YYYY-MM-DD_HHMMSS_PROMPT.md
devl/log/YYYY-MM-DD_HHMMSS_TASK.md
devl/log/YYYY-MM-DD_HHMMSS_PLAN.md
devl/log/YYYY-MM-DD_HHMMSS_REPORT.md
```

Required structure per file:

```text
============================================================
START / STOP INFORMATION
============================================================
Workflow start time:
Execution start time:
Execution stop time:
Archive time:
Duration:

============================================================
ORIGINAL PROMPT
============================================================

============================================================
REFINED PROMPT
============================================================

============================================================
TASK
============================================================

============================================================
PLAN
============================================================

============================================================
COMPLETION REPORT
============================================================

============================================================
END OF RECORD
============================================================
```

Do not automatically delete `devl/tmp/` after archiving.

Outside complex mode, the same archival can be run with `general: archive`
(see Section 4).

STOP and show next-stage options.

---

## 11. Documentation Stage

Command:

```text
complex: document
```

Documentation is generated/refreshed ONLY when explicitly requested with this
command. Ordinary coding, creation, execution, commits, releases, and handoffs
must not automatically rebuild manuals.

Keep lightweight README setup facts, CLI help, agent instructions, HANDOFF, and
DEV_NOTES accurate. Record pending manual changes in HANDOFF/DEV_NOTES until
documentation is requested. Preserve existing manuals.

Outside complex mode, documentation can be generated with `general: document`
(see Section 4).

### On-demand documentation rules

The full documentation rules live in `src/docs/DOCUMENTATION_RULES.md` (content
folded in from `ARX/files/DOCUMENTATION_RULES.md`). To keep routine context
small, load the full rules ONLY when a `document` command (`complex: document`
or `general: document`) is given — never preload them for other stages.
Summary of the rules: generate/refresh HTML/TXT manuals only on explicit
request; use the external `project-document` tool via its inspected real
interface (never invent options, never claim it ran when unavailable); writing
documentation requires owning the session lock in `.agent-state/lock/`;
follow the GDP-derived docs structure;
derive content from current source, `--help`, and tested examples; validate
links and rendered HTML; never publish automatically.

### src/docs/ structure

Use the project's `src/docs/` directory:

```text
src/docs/DOCUMENTATION.md                 # documentation rule file
src/docs/DOCUMENTATION_RULES.md           # full on-demand documentation rules
src/docs/index.html
src/docs/README.html
src/docs/README.txt
src/docs/<project>-step-by-step.html
src/docs/<project>-step-by-step.txt
src/docs/<command>.html
src/docs/<command>.txt
src/docs/<project>-product-<name>.html
src/docs/<project>-product-<name>.txt
src/docs/style.css
src/docs/LICENSE.html                     # full license and warranty agreement
src/docs/LICENSE.txt
src/docs/MODEL_LICENSE.txt
```

`index.html` links to `README.html`; `README.txt` is the plain-text equivalent.

The step-by-step guide should contain workflow tables, goals, commands, numbered
actions, examples, expected output patterns, verification, and recovery steps.

For each public command document Purpose, Usage, Options, Inputs/Outputs, Examples,
relevant scientific assumptions, troubleshooting, navigation, and product-format
links. Options tables should include type, default, required/optional status,
units, ranges, and precedence. Explain setup/parameter JSON and relative paths.

For each actual product format document filename conventions, fields/arrays, dtype,
shape, units, coordinate/time conventions, missing values, provenance/version
metadata, and a reading example.

Use local `style.css`, readable system fonts, light background, readable tables,
contrasting command/output blocks, responsive layout, and a linked documentation
tree. Do not make a monolithic dump.

Use real sample plots with captions, parameter context, regeneration commands, and
relative links. Do not fabricate results or run expensive science solely to fill
documentation unless explicitly in scope.

Derive documentation from current source, actual `--help`, and tested examples.
Include software version and generation date. Distinguish illustrative output from
actual runs. HTML and TXT should cover equivalent facts where feasible.

Core documentation must work offline without required CDN or JavaScript-only
content. Never export personal paths, secrets, or private data.

EVERY generated HTML page in `src/docs/` must carry the detailed license lines
in a footer at the bottom of the page, with a link to the full license and
warranty agreement (`LICENSE.html`).

Validate links, anchors, sample JSON, command names, and rendered HTML. Record
actual checks and limitations. Update DEV_NOTES with the documentation request,
tool/version when known, files changed, and validation. Do not publish
automatically.

STOP after documentation and show next-stage options.

---

## 12. Version Stage

Command:

```text
complex: version
```

The `src/version/VERSION` file uses:

```text
aa.bb.cc
```

where:

- `aa` = high/major;
- `bb` = middle/minor;
- `cc` = low/patch.

The newest/current version is the FIRST line. All previous versions remain below,
newest to oldest.

Example:

```text
2.1.0
2.0.4
2.0.3
```

When `complex: version` is received:

1. read `src/version/VERSION`;
2. report current version;
3. inspect only the minimum change information needed;
4. offer:

```text
1. High   -> aa+1, bb=0, cc=0
2. Middle -> bb+1, cc=0
3. Low    -> cc+1
4. Cancel / return
```

5. STOP unless the level was already explicitly specified;
6. after selection, prepend the new version;
7. preserve all older versions;
8. validate `src/version/VERSION`;
9. report the new version;
10. STOP and show next-stage options.

Versioning does not automatically create a release or Git update.

Outside complex mode, the version can be updated with `general: version`
(see Section 4).

---

## 13. Release Stage

Command:

```text
complex: release
```

Actions:

1. read current version from the first line of `src/version/VERSION`;
2. determine project name;
3. if `release/present/` already contains a previous release, move it to
   `release/old-versions/<project>-<aa.bb.cc>/`;
4. build the new release into `release/present/`, including project name and
   version in the release name where applicable.

Recommended:

```text
release/present/<project>-<aa.bb.cc>/
```

The release must:

- contain only required releasable files;
- ship a visible LICENSE file (from `ARX/files/lisence/`: `LICENSE.html`,
  `LICENSE.txt`, plus `MODEL_LICENSE.txt` where applicable);
- exclude temporary artifacts, caches, secrets, private data, and unrelated files;
- be installable on supported macOS and Linux systems;
- include an appropriate installation mechanism/instructions;
- check dependencies, permissions, paths, shebangs, and packaging;
- be tested in a clean/staged environment where practical;
- receive a basic post-install execution test.

Development scripts may use:

```text
#!/opt/anaconda3/bin/python3
```

but a portable macOS/Linux release must not depend on that private/local path
unless the installer explicitly establishes it.

Do not automatically run Git after release creation.

Outside complex mode, a release can be built with `general: release`
(see Section 4).

STOP and show next-stage options.

---

## 14. Git Update Stage

Command:

```text
complex: git
```

Actions:

1. confirm this is a Git repository;
2. inspect Git status/diff;
3. report changed/new/deleted files;
4. exclude secrets, credentials, caches, temporary junk, and inappropriate local files;
5. respect `.gitignore`;
6. the ENTIRE project is tracked in Git, including `devl/`, `src/`,
   `release/`;
7. do not discard unrelated user changes;
8. run relevant validation where practical;
9. show what the update intends to include;
10. request commit/push details or authorization when required;
11. perform only explicitly authorized Git actions;
12. report commit ID and push result when applicable.

### Public Release Visibility

The public git release exposes ONLY the `release/` directory. `release/present/`
is the current version available to everybody; `release/old-versions/` holds the
older releases. All other directories are tracked in Git for development but are
not part of the public-facing release.

Do not automatically publish to external package registries or release services.

Outside complex mode, the Git update can be run with `general: git`
(see Section 4).

STOP and show next-stage options.

---

## 15. Ending Complex Mode

Command:

```text
complex: end
```

Actions:

1. record workflow end time;
2. report state of PROMPT, TASK, PLAN, execution, archive, documentation, VERSION,
   release, and Git;
3. warn about important unfinished/unarchived state;
4. do not automatically run missing stages;
5. leave COMPLEX MODE;
6. preserve files unless cleanup is separately authorized.

To pause complex mode without ending it, so it can later be resumed, use
`complex: hold` instead (see Section 4).

---

## 16. Minimal-Context / Token-Efficiency Rules

The workflow is designed to reduce repeated reasoning and token use.

### General

- Do not reread AGENT_<PROJECT>.md after instantiation unless required by
  Section 3.
- Do not rewrite TASK.md unless `complex: PROMPT` is requested.
- Do not regenerate PLAN.md unless `complex: TASK` is requested.
- Do not reread unrelated project files.
- Treat TASK.md as authoritative for WHAT.
- Treat PLAN.md as authoritative for HOW.
- Keep temporary working artifacts in `devl/tmp/`.
- Never automatically archive, document, version, release, or Git-update.
- Do NOT re-check `.agent-state/lock/` status on every stage or command. Check
  only at session start, on resume after long inactivity, and where ownership is
  genuinely required (documentation writes, release, git). Prefer the lightweight
  status/ownership read over loading full lock or handoff content, so the context
  window stays small and the agent stays fast.

### Minimal-Context File Reading

For every stage, use the smallest sufficient context.

- Read only files required for the current stage.
- Do not scan the entire project tree unless genuinely required.
- Do not reread a file whose relevant contents are already in active context unless:
  1. it may have changed;
  2. validation requires the current on-disk version;
  3. a different section is required; or
  4. the user explicitly requests rereading it.
- Prefer targeted inspection of files, functions, sections, diffs, or metadata over
  loading complete large files.
- During `complex: PLAN`, begin with TASK.md, PLAN.md, relevant
  `devl/testdir/data/` content, and only source/data files required by the current
  execution step.
- During `complex: document`, inspect only source, `--help`, examples,
  outputs, and related material required by the documentation contract.
- During `complex: version`, use `src/version/VERSION` plus minimum change information.
- During `complex: release`, inspect release-relevant source, config, dependencies,
  installation, docs, and packaging files only.
- During `complex: git`, prefer Git status/diff/metadata rather than rereading file
  contents unless content inspection is needed.
- Reuse facts already established in the active session.
- Summarize large inspected material into compact TASK/PLAN/REPORT records when
  that prevents repeated context use without losing required information.

### Context Priority

When context must be constrained, prioritize:

```text
1. Current explicit user command
2. Approved TASK.md
3. Approved PLAN.md
4. Files directly required for the current execution step
5. Validation evidence
6. Other project context only when necessary
```

The goal is minimum token use without sacrificing correctness, validation, or
user control.

---

## 17. Stage Dependencies

Do not silently execute missing prerequisites.

Typical dependencies:

```text
complex: PROMPT
    requires devl/tmp/PROMPT.md

complex: TASK
    requires devl/tmp/TASK.md

complex: PLAN
    requires devl/tmp/TASK.md + devl/tmp/PLAN.md

complex: archive
    requires available Prompt/Task/Plan material

complex: version
    requires src/version/VERSION or an explicit initialization decision

complex: document
    requires an inspectable project

complex: release
    requires a valid VERSION and releasable project state

complex: git
    requires a Git repository

complex: hold
    requires active COMPLEX MODE

complex: restart
    requires a saved complex-mode status from complex: hold

general: archive / general: version / general: document / general: release / general: git
    perform the same work as their complex: counterparts; do NOT require
    active COMPLEX MODE
```

If a prerequisite is missing:

1. explain what is missing;
2. explain the command/action that can resolve it;
3. STOP.

---

## 18. Runaway-Agent Protection

Stop and ask before:

- substantially changing the approved objective;
- deleting important user data;
- overwriting important files when not explicitly required;
- making a major architectural change absent from PLAN;
- installing significant new dependencies not anticipated by PLAN;
- proceeding through a critical ambiguity;
- publishing externally;
- performing destructive Git operations.

Routine implementation decisions within an approved PLAN do not require another
approval unless one of these conditions applies.

---

## 19. Command Reference

```text
instantiate: AGENT
    Read/reload AGENT_<PROJECT>.md, cache it for the active session, create any missing standard project directories, initialize src/version/VERSION to 0.0.1 only if VERSION is absent, and check the session lock and HANDOFF.md.

complex: start
    Enter controlled complex mode.

complex: hold
    Save complex-mode status, pause complex mode, and accept non-complex commands.

complex: restart
    Restore the last saved complex-mode status and present next-stage options.

complex: PROMPT
    Refine devl/tmp/PROMPT.md and create/update devl/tmp/TASK.md.

complex: TASK
    Create/update devl/tmp/PLAN.md from approved TASK.md.

complex: PLAN
    Execute the approved PLAN.md and write devl/tmp/REPORT.md.

complex: archive
    Archive Prompt–Task–Plan and completion information in devl/log/.

complex: version
    Update src/version/VERSION after explicit high/middle/low selection.

complex: document
    Generate/refresh project HTML/TXT documentation in src/docs/.

complex: release
    Build a versioned installable macOS/Linux release in release/present/, moving the previous present release to release/old-versions/.

complex: git
    Update the Git repository with explicitly authorized project/release changes; the public release exposes only release/.

complex: end
    Report workflow state and leave complex mode.

general: archive / general: version / general: document / general: release / general: git
    Same work as the complex: counterparts; usable outside complex mode without complex-mode status.
```

---

## 20. Workflow Model

```text
instantiate: AGENT
        |
        v
load method once + initialize/verify project structure
        |
        v
complex: start
        |
        +--> complex: PROMPT --> STOP
        |
        +--> complex: TASK   --> STOP
        |
        +--> complex: PLAN   --> STOP
        |
        +--> complex: archive    --> STOP
        |
        +--> complex: version    --> STOP
        |
        +--> complex: document --> STOP
        |
        +--> complex: release --> STOP
        |
        +--> complex: git --> STOP
        |
        +--> complex: hold --> accept non-complex commands --> complex: restart --> STOP
        |
        +--> return/repeat an earlier stage when explicitly commanded
        |
        v
complex: end
```

No arrow implies automatic execution. Every stage requires an explicit user command.

---

## 21. Core Principle

```text
PROMPT defines the request.
TASK defines WHAT must be achieved.
PLAN defines HOW it will be achieved.
PROCESS: PLAN performs the approved work.

ARCHIVE preserves the workflow.
DOCUMENTATION describes the project.
VERSION identifies the software state.
RELEASE packages that state.
GIT records the intended project state.
```

Perform only the explicitly requested stage, use the minimum necessary context,
then STOP for user direction.
