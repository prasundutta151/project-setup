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
