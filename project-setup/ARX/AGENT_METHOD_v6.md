# AGENT METHOD

## 1. Purpose

This file defines the standard operating method for the project agent. It controls
project organization, complex-task processing, planning, execution, archival,
documentation, versioning, release creation, Git updates, and context efficiency.

The agent MUST NOT automatically advance between complex-task stages. Every stage
requires an explicit user command.

---

## 2. Project Structure

```text
PROJECT_ROOT/
├── scripts/
├── user_methods/
├── user_functions/
├── data/
├── test/
├── plots/
├── docs/
├── PPT/
├── release/
├── tmp/
├── VERSION
└── AGENT_METHOD.md
```

### scripts/
All main executable scripts are stored here.

- Main scripts should be Python 3 unless another language is explicitly required.
- Directly executable Python scripts normally use `#!/opt/anaconda3/bin/python3`.
- Executable scripts must have executable permission.
- Executable Python commands should normally have no `.py` extension.
- CLI handling should use `argparse` in a function separate from `main`.
- Use JSON configuration for directory/input/output settings where appropriate.

### user_methods/
Store reusable user-specific methods and methodology/helper modules here.

### user_functions/
Store user-defined Python function modules here, normally with `.py` extension.

### data/
Store persistent project input, intermediate, and output data here.

### test/
Store user-supplied test data used to validate the software here.

The agent must never treat `test/` as disposable temporary storage. Original
user-supplied test data must not be overwritten or deleted during testing.

### plots/
Store persistent plots and figures here.

### docs/
Store project HTML/TXT documentation here.

### PPT/
Store permanent Prompt–Task–Plan workflow archives here.

### release/
Store releasable/installable software packages here.

### tmp/
Store all temporary and working files here, including:

```text
tmp/PROMPT.txt
tmp/TASK.md
tmp/PLAN.md
```

---

## 3. Agent Instantiation

Command:

```text
instantiate: AGENT
```

When this command is received:

1. Locate and read `AGENT_<PROJECT>.md`. Here it has to make sure <PROJECT> is the upper case name of the current project, other `AGENT_` files will not be read and used.
2. Load its rules ONCE as session-level agent state.
3. Reset workflow interpretation to the current method.
4. Initialize and verify the standard project environment.
5. Create any missing standard directories: `scripts/`, `user_methods/`, `user_functions/`, `data/`, `test/`, `plots/`, `docs/`, `PPT/`, `release/`, and `tmp/`.
6. If `VERSION` does not exist, create it with initial version `0.0.1`. If it already exists, preserve it exactly and never overwrite its history during instantiation.
7. Do NOT automatically create `tmp/PROMPT.txt`, `tmp/TASK.md`, or `tmp/PLAN.md`; these are workflow files created or supplied only when needed.
8. Never delete, clear, or overwrite existing project directories or their contents during instantiation. Instantiation must be idempotent and safe to repeat.
9. Do not execute any pending stage automatically.
10. Report that the method is loaded.
11. Report which directories/files already existed and which were created.
12. Report the current VERSION.
13. Report the current workflow state if known.
14. Show currently available commands.

### Method Caching Rule

After successful instantiation:

- Do NOT reread `AGENT_METHOD.md` for every command or stage.
- Treat the loaded method as valid for the active agent/session.
- Reread it only when:
  1. the user explicitly gives `instantiate: AGENT` again;
  2. `AGENT_METHOD.md` is known or detected to have changed; or
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
you want the agent to use in the test/ directory.
```

The agent should report whether `test/` is empty or already contains test material,
without reading all test-data contents merely for this reminder.
 It means **load the agent method + initialize/verify the project environment**.

### Instantiation Safety

Repeated `instantiate: AGENT` commands must be safe. Existing directories, VERSION history, source code, data, documentation, archives, releases, and temporary workflow files must not be destroyed or reset. Only missing standard infrastructure is created.

---

## 4. Complex Mode

The controlled complex workflow begins ONLY with:

```text
start: complex
```

and ends ONLY with:

```text
end: complex
```

The agent must not infer complex mode merely because a task appears difficult.

When `start: complex` is received:

1. enter COMPLEX MODE;
2. record workflow start time;
3. ensure `tmp/` exists;
4. inspect only enough state to identify possible next stages;
5. explain what each available next stage will do;
6. present numbered choices with exact commands;
7. remind the user to place any required test data in `test/`;
8. report whether `test/` appears empty or contains test material, using only a
   lightweight directory check;
9. STOP.

The reminder should be explicit:

```text
Before execution, place the test data to be used for validation in test/.
```

No stage is run automatically.

---

## 5. Mandatory Stage Control

During COMPLEX MODE, every stage is separately dispatched.

After EVERY stage the agent must:

1. report what it did;
2. report files created/modified;
3. report success/failure/limitations;
4. explain sensible next stages;
5. give numbered options;
6. include backward/repeat stages when useful;
7. show the exact command for every option;
8. STOP and wait.

Example:

```text
Available actions:

1. Process TASK
   Command: process: TASK
   Creates PLAN.md from the approved TASK.md.

2. Re-process PROMPT
   Command: process: PROMPT
   Rebuilds TASK.md from PROMPT.txt.

3. End workflow
   Command: end: complex
```

The numbered choice is informational. The agent acts only on the explicit command.

### Mandatory Go-Back Choice After Every Stage

After EVERY completed stage, including PROMPT, TASK, PLAN execution, archive,
documentation, version, release, and Git update, the agent must explicitly ask
the user whether they want to continue or go back to an earlier stage.

The menu must include applicable earlier stages, not only the next stage.

For example:

```text
What would you like to do next?

1. Continue to the next stage
   Command: <next-stage command>

2. Go back to PROMPT
   Command: process: PROMPT

3. Go back to TASK / planning
   Command: process: TASK

4. Go back to PLAN execution or end the workflow
   Command: process: PLAN   OR   end: complex
```

The exact choices must be adapted to the current stage. If more than three earlier
stages are meaningful, the agent may show more numbered options, but it must always
include the relevant backward paths.

The agent must not interpret a number alone as authorization. The user must send
the explicit command shown for the selected stage.

When going backward, the agent must explain which downstream artifacts may become
stale. For example, re-processing PROMPT may make the existing TASK, PLAN,
completion report, documentation, version/release, or Git state outdated. The
agent must not automatically regenerate those downstream stages.

---

## 6. PROMPT Stage

Command:

```text
process: PROMPT
```

Input:

```text
tmp/PROMPT.txt
```

Actions:

1. Read the original prompt.
2. Preserve its original contents for archival.
3. Rewrite it into a clearer and more efficient LLM specification.
4. Remove repetition without removing requirements.
5. Identify objective, inputs, outputs, constraints, relevant files, validation,
   and completion criteria.
6. Record unresolved important ambiguities rather than guessing.
7. Create/update `tmp/TASK.md`.

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

`TASK.md` defines WHAT must be achieved.

STOP after TASK.md is created. Do not create PLAN.md or execute the task.

---

## 7. TASK Stage

Command:

```text
process: TASK
```

Input:

```text
tmp/TASK.md
```

Actions:

1. Read the approved TASK.md.
2. Preserve the approved objective.
3. Determine required files, dependencies, operations, validation, and outputs.
4. Create/update `tmp/PLAN.md`.

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

`PLAN.md` defines HOW the task will be achieved.

STOP after PLAN.md is created. Do not execute it.

---

## 8. PLAN Execution Stage

Command:

```text
process: PLAN
```

Actions:

1. record execution start time;
2. read TASK.md and PLAN.md;
3. execute the approved plan;
4. put main executable programs in `scripts/`;
5. put reusable methods in `user_methods/`;
6. put user-defined Python function modules in `user_functions/`;
7. put persistent data in `data/`;
8. use user-supplied validation data from `test/` when relevant, without modifying the originals;
9. put persistent figures in `plots/`;
10. put temporary artifacts in `tmp/`;
11. test and validate, using suitable data from `test/` when available;
12. record failures and corrective actions;
13. record deviations from PLAN.md;
14. generate a completion report.

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
test/
```

The `test/` directory contains user-supplied data intended for testing and validation. The agent must identify which files are appropriate for the current task before using them.

### Testing Rule

During:

```text
process: PLAN
```

the agent must, when relevant:

1. inspect `test/` for test data related to the task;
2. use the provided test data to test newly created or modified software;
3. prefer supplied project test data over fabricated data when suitable test data
   already exists;
4. never modify or overwrite original test/input data unless the approved task
   explicitly requires it;
5. write temporary test outputs to `tmp/` unless the output is an intended
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

If no suitable test data exists in `test/`, the agent must report that fact. It may
use minimal synthetic test data only when useful and safe, and must clearly identify
that data as synthetic.

### Test Safety

Testing must not:

- destroy or overwrite the original files in `test/`;
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
archive: PTP
```

Purpose: archive Prompt–Task–Plan and completion information in `PPT/`.

Create a unique Markdown file, preferably:

```text
PPT/YYYY-MM-DD_HHMM_<task>.md
```

Required structure:

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

Do not automatically delete `tmp/` after archiving.

STOP and show next-stage options.

---

## 11. Documentation Stage

Command:

```text
documentation: project
```

Documentation is generated/refreshed ONLY when explicitly requested with this
command. Ordinary coding, creation, execution, commits, releases, and handoffs
must not automatically rebuild manuals.

Keep lightweight README setup facts, CLI help, agent instructions, HANDOFF, and
DEV_NOTES accurate. Record pending manual changes in HANDOFF/DEV_NOTES until
documentation is requested. Preserve existing manuals.

### External project-document boundary

When documentation is requested:

1. locate `project-document`;
2. inspect its real help/source before using it;
3. do not invent options;
4. do not install/substitute a similarly named tool;
5. do not claim it ran when unavailable;
6. if absent, report that and request its location;
7. pass this documentation contract and selected project using its supported
   interface;
8. report if the tool cannot consume these rules;
9. writing documentation requires project ownership/lock;
10. never allow two writing agents to edit the same checkout concurrently.

### docs/ structure

Use the project's `docs/` directory:

```text
docs/index.html
docs/README.html
docs/README.txt
docs/<project>-step-by-step.html
docs/<project>-step-by-step.txt
docs/<command>.html
docs/<command>.txt
docs/<project>-product-<name>.html
docs/<project>-product-<name>.txt
docs/style.css
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

Validate links, anchors, sample JSON, command names, and rendered HTML. Record
actual checks and limitations. Update DEV_NOTES with the documentation request,
tool/version when known, files changed, and validation. Do not publish
automatically.

STOP after documentation and show next-stage options.

---

## 12. Version Stage

Command:

```text
version: update
```

The root `VERSION` file uses:

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

When `version: update` is received:

1. read VERSION;
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
8. validate VERSION;
9. report the new version;
10. STOP and show next-stage options.

Versioning does not automatically create a release or Git update.

---

## 13. Release Stage

Command:

```text
release: project
```

Actions:

1. read current version from the first line of VERSION;
2. determine project name;
3. create release output under `release/`;
4. include project name and version in the release name.

Recommended:

```text
release/<project>-<aa.bb.cc>/
release/<project>-<aa.bb.cc>.tar.gz
```

The release must:

- contain only required releasable files;
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

STOP and show next-stage options.

---

## 14. Git Update Stage

Command:

```text
git: update
```

Actions:

1. confirm this is a Git repository;
2. inspect Git status/diff;
3. report changed/new/deleted files;
4. exclude secrets, credentials, caches, temporary junk, and inappropriate local files;
5. respect `.gitignore`;
6. include intended project files and `release/` where applicable;
7. do not discard unrelated user changes;
8. run relevant validation where practical;
9. show what the update intends to include;
10. request commit/push details or authorization when required;
11. perform only explicitly authorized Git actions;
12. report commit ID and push result when applicable.

Do not automatically publish to external package registries or release services.

STOP and show next-stage options.

---

## 15. Ending Complex Mode

Command:

```text
end: complex
```

Actions:

1. record workflow end time;
2. report state of PROMPT, TASK, PLAN, execution, archive, documentation, VERSION,
   release, and Git;
3. warn about important unfinished/unarchived state;
4. do not automatically run missing stages;
5. leave COMPLEX MODE;
6. preserve files unless cleanup is separately authorized.

---

## 16. Minimal-Context / Token-Efficiency Rules

The workflow is designed to reduce repeated reasoning and token use.

### General

- Do not reread AGENT_METHOD.md after instantiation unless required by Section 3.
- Do not rewrite TASK.md unless `process: PROMPT` is requested.
- Do not regenerate PLAN.md unless `process: TASK` is requested.
- Do not reread unrelated project files.
- Treat TASK.md as authoritative for WHAT.
- Treat PLAN.md as authoritative for HOW.
- Keep temporary working artifacts in `tmp/`.
- Never automatically archive, document, version, release, or Git-update.

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
- During `process: PLAN`, begin with TASK.md, PLAN.md, relevant `test/` data, and only source/data files
  required by the current execution step.
- During `documentation: project`, inspect only source, `--help`, examples, outputs,
  and related material required by the documentation contract.
- During `version: update`, use VERSION plus minimum change information.
- During `release: project`, inspect release-relevant source, config, dependencies,
  installation, docs, and packaging files only.
- During `git: update`, prefer Git status/diff/metadata rather than rereading file
  contents unless content inspection is needed.
- Reuse facts already established in the active session.
- Summarize large inspected material into compact TASK/PLAN/completion records when
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
process: PROMPT
    requires tmp/PROMPT.txt

process: TASK
    requires tmp/TASK.md

process: PLAN
    requires tmp/TASK.md + tmp/PLAN.md

archive: PTP
    requires available Prompt/Task/Plan material

documentation: project
    requires an inspectable project

version: update
    requires VERSION or an explicit initialization decision

release: project
    requires a valid VERSION and releasable project state

git: update
    requires a Git repository
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
    Read/reload AGENT_METHOD.md, cache it for the active session, create any missing standard project directories, and initialize VERSION to 0.0.1 only if VERSION is absent.

start: complex
    Enter controlled complex mode.

process: PROMPT
    Refine tmp/PROMPT.txt and create/update tmp/TASK.md.

process: TASK
    Create/update tmp/PLAN.md from approved TASK.md.

process: PLAN
    Execute the approved PLAN.md.

archive: PTP
    Archive Prompt–Task–Plan and completion information in PPT/.

documentation: project
    Generate/refresh project HTML/TXT documentation in docs/.

version: update
    Update VERSION after explicit high/middle/low selection.

release: project
    Build a versioned installable macOS/Linux release in release/.

git: update
    Update the Git repository with explicitly authorized project/release changes.

end: complex
    Report workflow state and leave complex mode.
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
start: complex
        |
        +--> process: PROMPT --> STOP
        |
        +--> process: TASK   --> STOP
        |
        +--> process: PLAN   --> STOP
        |
        +--> archive: PTP    --> STOP
        |
        +--> documentation: project --> STOP
        |
        +--> version: update --> STOP
        |
        +--> release: project --> STOP
        |
        +--> git: update --> STOP
        |
        +--> return/repeat an earlier stage when explicitly commanded
        |
        v
end: complex
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
