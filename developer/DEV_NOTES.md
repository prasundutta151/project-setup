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
