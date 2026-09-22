## 2026-09-22 09:24:53 IST

Prompt / Request
- Add a pre-refresh backup to --refresh: before any migration edits, copy the existing project to PROJECT/PROJECT.org inside the project, and if the project exceeds 100 MB print a warning and ask the user's permission before proceeding.

Changes Made
- refresh.py measures project size with an lstat walk (backup folder excluded), prints a WARNING with the measured size above BACKUP_LIMIT_BYTES (100 MB) and prompts y/yes in a terminal; without a terminal an over-limit project is refused, and a declined answer raises before any project file changes.
- The copy is written to PROJECT.org.partial and renamed on success, so an existing PROJECT.org is always a complete backup; a stale partial is reported and removed on the next run, and an existing backup is kept unchanged rather than overwritten.
- PROJECT.org/ is appended to .git/info/exclude so the backup never appears in git status, diffs or commits; the migration prompt gains a PRE-REFRESH BACKUP read-only rule (no edits, mapping, release-files.txt or commits) and request.json records the backup path.
- Updated the manual/prepared output wording, --refresh help text, README refresh section and docs/refresh.md (new Pre-refresh backup section replacing the "no target files change" guarantee); rebuilt offline HTML/TXT guides.

Verification
- PASS: 80 tests via python3 -m unittest discover -s testdirectory (75 existing plus 5 new backup tests: creation with Git exclusion, existing-backup reuse, permission granted, permission declined, non-terminal refusal, stale-partial cleanup).
- Regenerated docs with developer/script/build_docs.py.

Notes
- The backup deliberately changes the old "preparation/manual mode touches no target files" guarantee; documentation and tests updated together. Version bump and push deferred to the follow-up no-argument help release.

## 2026-09-22 08:59:19 IST

Prompt / Request
- Integrate the setup-data functionality into project-setup as --data-dir (ASCII directory-list file, a list of directories and subdirectories, or the default /Volumes/Work/Data root with the project directory created inside), plus --dry-run, --show and --json; check every requested path for existence/creatability and report permission or mount failures in the terminal; make the corresponding documentation, bump the middle version, push to Git and install locally.

Changes Made
- Added data-workspace planning to project-setup: mode resolution in data_dir_args, path probes (exists / will create / BLOCKED with the reason), pre-flight validation before any project file is written, materialization after the initial Git checkpoint with DataError kept separate from Git setup guidance, and a lazy data-module import so embedded standalone updaters keep working.
- Added --dry-run (full creation preview, writes nothing), --show (existing project: version, setup directories, data workspace, json/ folder path and configuration path) and --json [PATH] (configuration file selection inside the project; prints the path without a value).
- Fixed two pre-existing project_setup/data.py bugs found by the new tests: subfolder precedence on first setup discarded explicit entries/tree in favour of the defaults, and valid_subfolder rejected nested tree entries; relaxed the configuration write check to any path inside the project to match its own error text.
- New regression tests in testdirectory/test_data_dir.py (modes, path checks, permission and unmounted-volume blocks, dry-run/show/json behaviour, updater import isolation). README and docs/usage.md data-workspace sections; regenerated standalone/template updaters and offline HTML/TXT guides; version 1.5.0 (middle bump).

Verification
- PASS: 75 tests via python3 -m unittest discover -s testdirectory (46 existing plus 29 new data-directory tests).
- Smoke: dry-run preview reports the blocked default volume without writing; entries/root/file workspace creation, --show and --json outputs verified; permission-denied pre-flight stops before project creation; reinstalled commands exercised after install.py.

Notes
- External project-document is not installed; documentation was explicitly requested and rebuilt with the repository's own developer/script/build_docs.py under docs/DOCUMENTATION_RULES.md. data-path.json stays machine-specific; .gitignore was not edited. Committed as "Data directory setup implementation".

## 2026-09-21 08:43:44 IST

Prompt / Request
- Add project-lisence, custom licensing models and HTML author attribution; release version 1.3.0.

Changes Made
- Added metadata/text-template command, protected draft records, idempotent escaped HTML footers, installer and template integration.
- Added Prasun Dutta's supplied licensing contact to project-setup documentation.

Verification
- Licensing unit tests, full CLI tests, template context tests, installation and scaffold smoke checks.

Notes
- Agent: Codex; computer: comet. Custom terms remain draft pending author/legal review; no existing license replaced.

# project-setup Developer Notes

This file is the running developer log for project-setup. Add a new timestamped entry whenever the code, plans, packaging, or workflow changes.

Entry format:
```text
## YYYY-MM-DD HH:MM:SS TZ

Prompt / Request
- Polished summary of what was asked.

Changes Made
- What changed in code, plans, docs, data products, or packaging.

Verification
- Commands or checks run.

Notes
- Follow-up context, assumptions, or cautions.
```

## 2026-09-21 03:01:26 UTC

Prompt / Request
- Add AI-assisted --refresh for existing projects, offering Antigravity, ChatGPT, Claude, OpenCode and Manual prompt output; bump version and upload to Git.
- Explain a citation/permission-based licensing policy for use, modified releases and unchanged integration.

Changes Made
- Added refresh module, explicit agent selection/menu and configurable command invocation without shell evaluation.
- Manual/unconfigured modes print a full migration prompt and preserve target files.
- Automatic mode requires a clean baseline and ownership; checks required output paths, unchanged HEAD/remotes and leaves reviewable changes.
- Added refresh documentation and non-binding licensing design notes; no LICENSE or existing project rights changed.
- Version 1.2.0 and standalone updater refresh.

Verification
- PASS: 44 project tests plus 3 context tests; installed manual refresh preserved the target and printed the full prompt.
- Refresh adapter integration uses a simulated agent, not a live AI model.

Notes
- No real user project was migrated. No external AI command was configured or invoked on user projects.
- Documentation outlines licensing questions requiring rights-holder decisions/legal review; refresh preserves licenses.

## 2026-09-21 02:37:35 UTC

Prompt / Request
- Create a new version, update documentation and push to Git.

Changes Made
- Version 1.1.2 documentation release; refreshed numbered usage guide covering creation, cloning, descriptions, Git guide, lock controls, summaries and agent handoffs.
- Updated version metadata, offline HTML guide and standalone updater copies.

Verification
- PASS: 38 local tests; guide anchors and HTML/TXT source consistency checked.
- Rebuilt the offline main guide and linked step-by-step HTML/TXT guide.

Notes
- Used the repository's existing README-based documentation builder; external project-document is not installed.

## 2026-09-21 02:22:06 UTC

Prompt / Request
- Make project-setup --git-setup guide discoverable in --help.

Changes Made
- Registered --git-setup in the primary argparse options and forwarded the remaining helper arguments.
- Version 1.1.1; refreshed standalone updater copies and installation reference.

Verification
- PASS: focused help/dispatch regression test checks option listing, guide, no-subcommand guide and nested --help.

Notes
- Helper implementation unchanged; the previous early dispatch hid it from the options list.

## 2026-09-21 02:09:02 UTC

Prompt / Request
- Add --from-git PROJECT and --proj-description accepting quoted text or a text file; explain and retain built-in documentation instructions.

Changes Made
- Clone existing GitHub repositories by NAME/OWNER/REPO, or use explicit --remote; preserve history and refuse existing destinations.
- Store descriptions in PROJECT_DESCRIPTION.txt and seed new project context; do not overwrite cloned descriptions.
- Add portable documentation-prompt.txt and description-aware documentation rules.
- Allow Git-only updater operations on repositories without version files.
- Version 1.1.0; regenerated standalone updaters and installer documentation.

Verification
- PASS: 37 local tests including real local Git clones, preservation/conflict handling, literal/file/long descriptions and Git-only sync without VERSION.
- PASS: installed bare-name GitHub clone and text-file description scaffold; documentation prompt present.

Notes
- Clone mode does not inject the template or install/run cloned project code.
- Full manual generation remains on request; external project-document is not bundled.

## 2026-09-20 16:21:10 UTC

Prompt / Request
- Give every project-update option a two-line action/result summary, push to Git and reinstall.

Changes Made
- Added final Action/Result summaries for help, lock, versions, releases, Git operations, combined operations and errors.
- Kept structured stdout intact; summary lines use stderr. Report completed steps on partial failure without claiming rollback.
- Version 1.0.2, regenerated standalone/template updaters and documented summaries.

Verification
- PASS: 32 tests, with final summary assertions across updater operations and dedicated no-op, invalid-argument and partial-failure coverage.
- PASS: installed CLI help/status/release summaries in a disposable repository.

Notes
- No scientific operations or unrelated project files changed.

## 2026-09-20 16:15:26 UTC

Prompt / Request
- Add project-update --lock acquire/release (accept aquire), push to Git and install the new version on this computer.

Changes Made
- Added shared-format acquire/status/release operations and owner labels.
- Interactive manual release displays owner and requires explicit release input; noninteractive release requires matching session and host.
- Refuse competing acquire, mixed lock/mutation operations, wrong owner and corrupt metadata.
- Version 1.0.1; regenerated installed/bundled/Model_Project updater copies and documented CLI.

Verification
- PASS: 31 local tests including interactive release/cancellation, helper interoperability, competing acquisition, corrupt/foreign owners and mixed-operation refusal.
- PASS: installed 1.0.1 command exercised in a disposable Git repository (aquire, status, release).

Notes
- Existing boolean .agent_lock is not migrated; new commands use .agent-state/lock.
- No force release or distributed-lock claim.

## 2026-09-20 11:51:46 UTC

Prompt / Request
- Download the current project-setup from GitHub, install it and report whether it works.

Changes Made
- Fresh-cloned public main at d480301bb6904e3cdc01104f4f8058c732e65956.
- Installed from the downloaded source into an isolated prefix and then the user's normal local prefix.
- No application code changed during this verification.

Verification
- PASS: no-argument guide, new project creation, initial clean Git checkpoint, actual project name in notes and fresh handoff ID.
- PASS: all 3 context integration tests shipped with the generated project.
- PASS: standalone project-update performed major version bump and release creation after removing the isolated installation.
- PASS: remote CI run 35508937027, Ubuntu/macOS with Python 3.9 and 3.13 (28 project tests + 3 context tests per matrix job).

Notes
- Tested software version 1.0.0. Tests used disposable projects and isolated Git identity.
- Scientific commands and the external project-document tool are not bundled.

## 2026-09-20 11:47:14 UTC

Prompt / Request
- Publish a public major release of project-setup for Linux/macOS with agent-aware project creation, bundled Model_Project rules and a consistent standalone updater in every generated script directory.

Changes Made
- Version 1.0.0; no-argument setup guide, scientific objective option, immediate Git initialization and remote setup guidance.
- Bundled portable template with fresh development history, handoff metadata, context cache tools and GDP-style on-demand documentation contract.
- Standalone updater supports version/VERSION and version/dist plus legacy root VERSION/versions; active ownership checks require --session.
- Updated stdlib/wheel packaging, installation guide, CI and archive distribution.

Verification
- 28 project/Git/updater tests and 3 context integration tests passed locally.
- Extracted archive installed to an isolated prefix with spaces; scaffold and standalone updater verified after deleting installed package.
- Built and installed wheel in isolation; template assets and generated updater verified.
- Linux tested locally; macOS CI caught a legacy-layout fixture collision between VERSION and version/. Fixed the fixture to remove the modern directory before creating the legacy file; remote matrix rerun before publication.

Notes
- Existing public repository retained. No unrelated existing project migrated.
- project-document remains an external tool; it is not bundled.
- Template development histories/private runtime state excluded from generated projects.

## 2026-09-17 00:17:34 IST

Prompt / Request
- Port the account's gitsetup helpers to Python, integrate with project-setup, document in HTML, install and publish installable software.

Changes Made
- Added git-setup guide/configure/new/clone/update and project-setup --git-setup dispatch.
- Added an offline HTML guide and installed documentation; version 0.0.2.
- Preserved the source gitsetup repository and existing shell helper names.

Verification
- All 25 unit/integration tests pass locally; identity tests use isolated Git configuration.
- HTML navigation targets checked. Browser preview of local files was blocked by browser URL policy, so visual rendering was not verified.
- Release extraction and isolated installation are checked before publishing.

Notes
- GitHub operations require GitHub CLI authentication; runtime Python code uses stdlib only.


## 2026-09-16 22:44:56 IST

Prompt / Request
- Fix the invalid main reference error during an initial Git push.

Changes Made
- Commit current-branch changes before checking its Git reference, so unborn branches can be published.

Verification
- All 17 tests passed, including initial push to a temporary bare repository.
- Installed the fixed command and patched SetProject's standalone updater.

Notes
- SetProject currently points at the project-setup remote; awaiting the user's destination choice before publishing it.


## 2026-09-16 22:39:37 IST

Prompt / Request
- Base generated agent rules on GMRTCAL's rules, excluding documentation synchronization.

Changes Made
- Replaced the rules template and this repository's rules; adapted project names, paths, updater commands, and section numbering.
- Retained developer logging and once-per-session loading.

Verification
- Installed the updated CLI and generated RulesDemo in a temporary directory.
- Checked substituted names and paths, retained logging, and removal of the documentation-sync section.

Notes
- GMRTCAL source files and existing generated projects were not modified.

## 2026-09-16 22:32:22 IST

Prompt / Request
- Use the requested timestamped developer log template and substitute each project's name.

Changes Made
- Updated the scaffold template and reinstalled the local commands.
- Adopted the template for this repository, preserving earlier notes below.

Verification
- Created Example-Project with the installed command and checked the complete generated notes and both name substitutions.

Notes
- New projects receive the new template; existing generated projects are not automatically modified.

# Earlier developer notes (preserved)

# Developer notes

## Purpose and scope
Portable macOS/Linux CLI for scaffolding projects, preserving version history,
creating allowlisted release archives, and safely synchronizing Git.

## Current state
Version 0.0.1. Runtime uses Python stdlib and Git. Generated updaters embed the CLI
source so they remain independent of the installed scaffolder.

## Architecture and entry points
- project_setup/cli.py: setup/update entry points, Git wrapper, version and archive logic.
- install.py: stdlib installer with managed launcher collision checks.
- script/project-update: updater for this repository.
- release-files.txt: explicit distribution contents.

## Decisions
| Date | Decision | Reason |
| --- | --- | --- |
| 2026-09-16 | Use AGENT_RULES.md | Correct requested filename typo |
| 2026-09-16 | Version targets use v-prefixed Git tags | Preserve checkout and working state |
| 2026-09-16 | Release allowlist and no symlinks | Avoid accidental recursive/external packaging |
| 2026-09-16 | Private GitHub repository | No public visibility requested |

## Validation
2026-09-16 Linux: 10 unittest cases pass, including temporary bare-remote integration.
Installed command and extracted-release installation smoke tests are run separately.
CI tests Linux and macOS on Python 3.9 and 3.13.

## Known limitations
Operations are ordered but not globally transactional. Use one updater per project.
Default manifests must be adjusted for each project's actual runtime/install assets.
Git pushes intentionally stage all nonignored changes on the current branch.

## Next steps
Extend the manifest to match any future added runtime assets. Retain regression tests.

## Session handoff
Initial implementation, documentation, packaging, installation, and tests complete.

## Parent directory update
Missing --proj-dir parents are now created recursively. Existing projects remain
protected. All 12 tests and the installed CLI nested-parent smoke test passed on Linux.

## GitHub provisioning update
GitHub remotes are created privately when missing. --git-push can infer the remote
from the authenticated account. Failure guidance includes terminal setup and recovery.
Remote behavior is tested with mocked GitHub responses; no disposable remote is created.
