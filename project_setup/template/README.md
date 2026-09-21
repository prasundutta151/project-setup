# __PROJECT__

__OBJECTIVE__

Read AGENTS.md and startup-prompt.txt to work with an agent.
See docs/GIT_SETUP.txt for remote setup and docs/CONTEXT_WORKFLOW.md for handoffs.
Run script/project-update --help for version/release/Git operations.

## Manual lock commands

```sh
project-update --lock acquire
project-update --lock aquire   # accepted spelling alias
project-update --lock status
project-update --lock release
```

The installed command uses the current Git repository. To work from anywhere,
use /absolute/project/script/project-update instead. Acquisition prints a fresh
session ID; --agent NAME and --agent-version VERSION label its owner. This is
the same .agent-state/lock used by agent_lock.py. Run lock commands separately
from version, release and Git operations.

Interactive release displays ownership and asks you to stop the writer, then
type release. Agents/scripts must supply --session OWNER_SESSION_ID; wrong
sessions, foreign computers and corrupt metadata are refused. An already unlocked
project reports UNLOCKED. No automatic timeout or force release is introduced.
The old boolean .agent_lock file is not managed by these commands.

## Operation summaries
Every project-update invocation ends with two summary lines: Action and Result.
This covers versions (including unchanged versions), archives, Git push/pull and
branch listings, locks, help and failures. Combined operations share one final
summary. Failures name completed steps and retain a nonzero exit status; changes
made before a failure are not rolled back. Summaries go to stderr so existing
structured stdout (such as lock ownership JSON) remains machine-readable.

## Clone existing software and supply descriptions

```sh
project-setup --from-git MyProject --proj-dir ~/Projects
project-setup --from-git OWNER/REPO --proj-dir ~/Projects
project-setup --from-git MyProject --remote https://example.com/owner/repo.git --proj-dir ~/Projects
project-setup --project NewProject --proj-description "Analyze stellar spectra"
project-setup --project NewProject --proj-description /path/description.txt
```

A bare GitHub name uses the account authenticated through gh; OWNER/REPO does not
require gh to resolve the name (private Git access still needs authentication).
--project can optionally rename the local clone directory. --proj-dir is its
parent. Existing destinations are refused. Clone mode preserves history, rules
and files without overlaying the template or executing project installation code.
It does not install dependencies. --create-remote/--git-push cannot accompany cloning.
Git-only updater push/pull works without a VERSION file; version/release operations
still require one.

--proj-description accepts literal text, an existing file path, or @PATH for an
explicit file. A value ending in .txt is treated as a file path and must exist.
Files are read as UTF-8 (ASCII is supported). Empty descriptions and binary NUL
content are rejected before project creation. --objective remains supported as
an alternative; do not supply both options.

New projects store the description in PROJECT_DESCRIPTION.txt and initially
reflect it in README, HANDOFF, AGENTS and development notes. This file is the
authoritative description for future documentation tasks; it does not execute
instructions from its text. Agents should read it as project requirements.
On cloning, the description is left unchanged unless explicitly supplied. A new
description is an uncommitted local change; an existing different description
or symlink is refused and the clone is retained for review. No existing README,
agent instructions or description is overwritten during cloning.

New projects include documentation-prompt.txt. When documentation is requested,
an agent reads this prompt, PROJECT_DESCRIPTION.txt and docs/DOCUMENTATION_RULES.md.
The prompt defines what to document and the GDP-style structure. It does not
bundle a document generator; project-document remains external and its real
interface must be inspected before use. Manuals are not automatically regenerated
for every code change.
