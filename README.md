# project-setup 1.0.1

Create agent-aware astronomy software projects on macOS and Linux. Run
`project-setup` without arguments for step-by-step instructions. The software
creates files and local Git history; it does not run an AI model or start a service.
Requires Python 3.9+ and Git 2.28+. Runtime uses Python's standard library.

## Install

Download and extract the versioned archive from
[GitHub Releases](https://github.com/prasundutta151/project-setup/releases), or:

```sh
git clone https://github.com/prasundutta151/project-setup.git
cd project-setup
git checkout v1.0.1
python3 install.py
export PATH="$HOME/.local/bin:$PATH"
project-setup
```

Add that PATH line to your shell profile if needed. The installer does not edit
shell configuration or require sudo. It installs three managed commands under
`~/.local/bin`: project-setup, project-update and git-setup; package and template
files go under `~/.local/lib/project-setup/`. `--prefix /path` selects another
prefix. Unrelated commands are refused. Re-run the installer to upgrade.
Alternatively use `python3 -m pip install .` in a virtual environment.
Uninstall by removing these three managed launchers, the installed
`lib/project-setup` directory and `share/project-setup` guide directory.

## Create a project

```sh
project-setup
project-setup --project StarAnalysis --proj-dir ~/Projects \
  --objective "Analyze stellar FITS images"
```

The first command prints the numbered guide; the second creates a project.
Use your actual name and scientific objective. `--proj-dir` defaults to the
current directory. Missing parents are created; existing destinations and nested
Git repositories are refused. Git initializes immediately, before copying the
scaffold. Configured identity allows an initial commit; otherwise the tool explains
how to finish it. No remote is created unless explicitly requested.

```text
StarAnalysis/
  AGENTS.md                     Shared agent rules
  HANDOFF.md                    Current state with fresh handoff ID
  startup-prompt.txt             Project-specific continuation prompt
  script/project-update         Standalone updater, executable from any directory
  script/agent_lock.py           Local cooperative ownership
  script/agent_context.py        Context checks and handoff stamping
  developer/DEV_NOTES.md         Fresh, attributed project history
  developer/AGENT_RULES.md       Pointer to authoritative AGENTS.md
  version/VERSION               Version history, newest first (initially 0.1.0)
  version/CHANGELOG.txt          User-visible changes
  version/dist/                 Generated release archives (ignored)
  docs/                         Protocols and on-demand documentation rules
  json/                         Setup/parameter JSON examples
  pipeline/                     Illustrative pipeline JSON
  plot/                         Reference plots; generated plots ignored
  tests/                        Context-helper tests and future science tests
  data/                         Local observations (ignored)
  release-files.txt              Distribution allowlist
```

Tell an agent with filesystem access:

```text
Read /absolute/path/to/StarAnalysis/startup-prompt.txt and follow it.
```

No local Model_Project or GDP checkout is required: the portable template and
GDP-derived documentation contract are bundled. Creation does not implement a
scientific algorithm, install scientific commands or generate scientific plots.
Those tasks belong to the project's subsequent development.

## Agent context and handoff

Each new conversation acquires a fresh lock and reads the current context.
Continuing sessions check a fingerprint and reuse context only when unchanged.
The fingerprint covers Git state and tracked/nonignored file contents. Large raw
observations should remain ignored. Cache lives in macOS `~/Library/Caches` or
Linux `~/.cache`, outside the project; do not sync it.

```sh
python3 script/agent_lock.py acquire --agent opencode --agent-version unknown
python3 script/agent_context.py check --session SESSION_ID
# Read/review context, then acknowledge the printed fingerprint:
python3 script/agent_context.py ack --session SESSION_ID --fingerprint HASH
# Finish DEV_NOTES and HANDOFF, then stamp before checkpointing:
python3 script/agent_context.py stamp --session SESSION_ID
python3 script/agent_lock.py release --session SESSION_ID
```

`check` exits 0 for unchanged, 2 for reload required and 1 for error. Acknowledgement
rejects intervening changes. Context loss always requires rereading. These are
instructions agents invoke, not automatic hooks into every AI application.
DEV_NOTES records each substantive request and results; handoff finalizes its
entry without duplicating it. Handoffs record computer, agent/version, session,
timestamp, unique ID and the prior commit.

Locks are cooperative local checks, not cross-computer enforcement. iCloud lock
visibility and context fingerprints do not prove syncing is complete. Stop the
previous writer and verify the expected handoff/commit before switching. Separate
local clones outside iCloud with Git push/pull are recommended for active projects.

## Documentation and scientific configuration

Commands developed in generated projects must support separate `--setup-file`
and `--parameter-file` JSON inputs, explicit CLI overrides and JSON-relative
paths. The full contract is in docs/PROJECT_REQUIREMENTS.md.

Generate full user HTML/TXT manuals only on an explicit external `project-document`
request. That tool is not bundled or installed. Agents must inspect its actual
interface; no command options are assumed. docs/DOCUMENTATION_RULES.md specifies
GDP-style navigation, workflow, command/options pages, product formats and real
sample plots. CLI help, essential setup facts, developer notes and handoffs remain
maintained during normal development.

## Git setup

When origin is absent, creation prints numbered guidance and supplies
`docs/GIT_SETUP.txt`. The existing helpers remain available:

```sh
git-setup guide
project-setup --git-setup guide
git-setup configure --name "Your Name" --email "your-email@example.com"
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

`configure` changes global identity only when explicitly invoked. Project-local
identity configuration is described in the guide. GitHub CLI is optional except
for automated GitHub provisioning. To explicitly create/publish a remote:

```sh
project-setup --project NAME --remote https://github.com/OWNER/REPO.git --git-push
git-setup new OWNER/REPO --directory /absolute/existing/project --push
```

`--create-remote` or `--git-push` without a URL uses the authenticated GitHub
account and project name. Missing GitHub repositories are created **private**;
existing visibility is preserved. Other hosts/local remotes are configured without
provisioning. The public visibility of project-setup itself does not make your
scientific projects public. Existing origin mismatches are refused by git-setup.

## Update and release

Every generated project gets its own executable `script/project-update`, with
implementation embedded so it works after project-setup is uninstalled. It resolves
the project from its own location. The installed `project-update` instead uses
the Git repository containing the current working directory.

```sh
/absolute/project/script/project-update --version
/absolute/project/script/project-update --version middle
/absolute/project/script/project-update --version major
/absolute/project/script/project-update --version 2.3.4 --release
/absolute/project/script/project-update --git-push --message "Describe changes"
```

For compatibility, version arguments retain MAJOR.MIDDLE.MINOR terminology:
`minor` (default) increments the rightmost component, `middle` increments the
middle, `major` increments the first. In conventional semantic versioning, use
`minor` for a patch and `middle` for a minor feature release. Middle/rightmost
components roll over after 99. Explicit versions are supported. Versions are
prepended to the history; setting the current version changes nothing.

Modern projects use version/VERSION and version/dist/. Older projects with root
VERSION retain that layout and versions/ archives. Both use one authoritative
version file; do not create a second one. Existing projects are not automatically
migrated or overwritten by installing this release.

If an agent lock is active, pass its owning `--session SESSION_ID` from the same
computer. Unknown/foreign ownership is rejected. Without a lock, the updater is
available for direct human use; keep other writers stopped. No distributed lock
or automatic context/handoff writing is performed by the updater.

`release-files.txt` is an explicit allowlist, not a secret scanner. Update it for
your application's runtime/install assets. Releases reject symlinks and traversal,
exclude Git/runtime/cache output and refuse existing release archives. Developer
logs are tracked but omitted from the default generated release manifest.

**Push commits all nonignored changes on the current branch.** Review `git status`
and diffs first; do not use it when unrelated work is present. Otherwise commit
only selected files with ordinary Git and push directly. `--message` and
`--massage` are aliases; omitted messages use a timestamp.

| Target | `--git-push` | `--git-pull` |
| --- | --- | --- |
| No value | Commit and push current branch | Fast-forward clean current branch |
| Branch | Push existing branch; commit if current | Only current branch; fast-forward |
| `show` | List branches | List branches |
| `1.2.3` | Push/create annotated v1.2.3 tag if version matches | Fetch tag, no checkout |

Order: pull, version, release, commit/push. Failures retain completed local work;
retry just the failed operation, not the version bump. No force pushes. Branch
pushes do not automatically publish tags. `show` cannot accompany mutations.

## Development and validation

```sh
python3 -m unittest discover -s testdirectory -v
```

The suite exercises scaffolding, refusal cases, standalone updater, modern/legacy
versions, archive boundaries, agent ownership and real Git transfers using local
bare repositories. Generated tests exercise context invalidation and handoff
stamping. The CI matrix runs Python 3.9/3.13 on Ubuntu/macOS. See the workflow's
actual results before claiming a particular OS run passed.

## Upgrade from 0.0.2

Install 1.0.0 using the same prefix. Existing project files remain unchanged.
New projects use the agent-aware structure and start at 0.1.0. The old root VERSION
layout remains supported by the installed updater. Back up and review an existing
project before deliberately replacing its standalone updater; never regenerate a
scaffold over existing work. No boolean .agent_lock is used in new projects.

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
