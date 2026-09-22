# project-setup 1.6.0 — step-by-step guide

## 1. Install and discover commands

Download the release archive, extract it, and run `python3 install.py`.
Add `~/.local/bin` to PATH if necessary. Requires Python 3.9+ and Git 2.28+.

```sh
project-setup
project-setup --help
project-setup --git-setup guide
project-update --help
```

The bare command prints a getting-started overview: how to start a new project
or refresh an old one first, then every other functionality, ending with the
local documentation HTML path for reading more in a browser.

## 2. Create a project or clone existing work

```sh
project-setup --project MyProject --proj-dir ~/Projects --proj-description "Analyze stellar spectra"
project-setup --project MyProject --proj-dir ~/Projects --proj-description /path/description.txt
project-setup --from-git OWNER/REPOSITORY --proj-dir ~/Projects
```

Use one creation command, not all three against the same destination. Bare
repository names use the account authenticated in GitHub CLI. Cloning preserves
existing files/history and does not install dependencies or overlay agent files.
Text files may contain ASCII or UTF-8. The description populates
PROJECT_DESCRIPTION.txt and initial project context. Conflicting existing cloned
descriptions are preserved. See README for --remote and destination overrides.

## 3. Start an agent

For a newly scaffolded project, ask the agent to read its startup-prompt.txt.
It must follow AGENTS.md, inspect context and update developer/DEV_NOTES.md.
A cloned project may have different rules; inspect its README and instructions.

## 4. Control ownership

```sh
cd ~/Projects/MyProject
project-update --lock acquire
project-update --lock status
project-update --lock release
```

`aquire` is accepted as an alias. Acquisition prints a new session ID. Interactive
release displays the owner and asks for confirmation after you stop the writer.
Scripts/agents pass `--session OWNER_SESSION_ID`. Other hosts or mismatched IDs
cannot release ownership. These are cooperative local locks, not distributed
locks or evidence that iCloud sync is complete.

## 5. Request documentation

Ask the agent to read documentation-prompt.txt and follow the documentation rules.
The description and actual implemented commands inform the manuals. Full HTML/TXT
manuals are generated only when requested. External project-document is not bundled;
its installed interface must be checked before invocation. This software's own
README-based offline guide is built by developer/script/build_docs.py.

## 6. Version, release and synchronize

```sh
project-update --version
project-update --release
project-update --git-push --message "Describe the changes"
project-update --git-pull
```

Supply --session SESSION_ID if an agent owns the lock. Review changes before push:
push mode commits all nonignored changes. To stage only selected files, use ordinary
Git instead. Pull requires a clean tree and fast-forwards only. Git-only operations
work without VERSION; version/release operations require version/VERSION or legacy
root VERSION. Keep one authoritative version file. Default --version increments
the patch; legacy middle increments the feature component and major the first.

Each updater invocation ends with Action and Result lines on stderr; stdout
remains available for structured data. Failures report completed steps without
claiming rollback. Do not repeat successful version bumps when retrying a push.

## 7. Move to another computer

Finish notes, stamp HANDOFF, commit/push and release ownership. On the next machine,
clone once or pull, install its dependencies, then begin a fresh agent session.
Prefer separate ~/Projects clones outside iCloud. Refer to docs/CONTEXT_WORKFLOW.md
in a generated project for fingerprint checks and session cache details.

## 8. Refresh older project layouts

Run `project-setup --refresh NAME --proj-dir PARENT` and choose Antigravity,
ChatGPT, Claude, OpenCode or Manual. Manual (the noninteractive default) prints
a migration prompt for your agent. Automatic execution needs an explicitly
configured agent command and clean Git baseline. See refresh.md/refresh.html.
Review the resulting developer/REFRESH_REPORT.md and changes before committing.
No license change or automatic migration of every repository is performed.

## 9. Plan a data workspace

```sh
project-setup --project SKA --proj-dir ~/Documents --data-dir --dry-run
project-setup --project SKA --proj-dir ~/Documents --data-dir /mnt/work/Data raw calibrated
project-setup --project SKA --proj-dir ~/Documents --data-dir ~/lists/ska-dirs.txt
project-setup --project SKA --proj-dir ~/Documents --show
project-setup --project SKA --proj-dir ~/Documents --json
```

`--data-dir` accepts no value (default root `/Volumes/Work/Data`), one
directory-list file (one relative directory per line, or a JSON preset with a
`subfolders` list), one absolute data root where the project directory is
created, or directory entries that use `/` for nesting; one root may be
combined with one file or entries. `--dry-run` previews every path a run would
create — project, setup directories, Git steps, data root, data path,
subfolders and the configuration file — and writes nothing. `--show` reports an
existing project's version, setup directories, data workspace, `json/` folder
path and configuration path. `--json [PATH]` selects the data configuration
file inside the project (implying workspace creation) or, without a value,
prints the configuration file path. All paths are checked first: existing
paths report `exists`, missing paths are created when permitted, and blocked
volumes or permission failures are reported in the terminal before the project
is created. The workspace is recorded in `<project>/data-path.json`. See README
for the full rules and `project-data --help` for later reconfiguration.
