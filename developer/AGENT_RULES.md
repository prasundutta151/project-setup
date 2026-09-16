# Agent rules
Load this file once at the start of each conversation/session. Retain its rules
in context; reload only when this file changes or context is lost.

- Read DEV_NOTES.md before changing the project; record decisions and validation.
- Preserve user files. Never overwrite existing projects, rewrite Git history,
  force push, discard changes, or expose credentials.
- Keep executable tools in script/, documentation in docs/, and tests in testdirectory/.
- Use script/project-update for version history and release operations.
- Maintain release-files.txt as an explicit list of distributable paths.
- Run relevant tests and report limitations honestly.
