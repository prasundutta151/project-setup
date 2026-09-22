# project-setup 1.5.0

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
git checkout v1.5.0
python3 install.py
export PATH="$HOME/.local/bin:$PATH"
project-setup
```

Add that PATH line to your shell profile if needed. The installer does not edit
shell configuration or require sudo. It installs five managed commands under
`~/.local/bin`: project-setup, project-update, git-setup, project-lisence and
project-data; package and template files go under `~/.local/lib/project-setup/`.
`--prefix /path` selects another prefix. `--without-project-data` or
`--project-data-only` limit the installed set. Unrelated commands are refused.
Re-run the installer to upgrade. Alternatively use `python3 -m pip install .`
in a virtual environment. Uninstall by removing these managed launchers, the
installed `lib/project-setup` directory and `share/project-setup` guide directory.

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

## Data workspace

`--data-dir` plans an external data workspace while creating a project, so code
stays in the project and data lives on another drive. The project's data
directory (`<root>/<project>`) is created inside the chosen root:

```sh
project-setup --project SKA --proj-dir ~/Documents --data-dir   # default root /Volumes/Work/Data
project-setup --project SKA --data-dir /mnt/work/Data           # one absolute PATH is the data root
project-setup --project SKA --data-dir raw calibrated images/plots   # directory entries; / nests
project-setup --project SKA --data-dir ~/lists/ska-dirs.txt     # ASCII file: one directory per line
project-setup --project SKA --data-dir /mnt/work/Data ~/lists/gdp.txt  # root and file together
```

Resolution rules for `--data-dir` values: no value uses the default root
`/Volumes/Work/Data` with the default tree `raw processed outputs cache`; one
existing file is a directory-list file (one relative directory per line, `#`
comments ignored; a JSON preset with a `subfolders` list also works, see the
bundled `data-config` presets); one absolute or `~` path is the data root where
the project directory is created; every other value is a relative directory
entry, and `/` describes nesting. At most one root and one file may be given,
and entries cannot be combined with a file. A missing `--data-dir` file with a
`.txt`/`.lst`/`.list`/`.json` suffix is reported instead of becoming a folder.
The default root must be mounted; an unmounted `/Volumes/<drive>` is refused
rather than silently creating a substitute on the internal disk. The workspace
and its subfolders are recorded in `<project>/data-path.json`.

Companion options:

```sh
project-setup --project SKA --proj-dir ~/Documents --data-dir /mnt/work/Data --dry-run
project-setup --project SKA --proj-dir ~/Documents --show
project-setup --project SKA --proj-dir ~/Documents --json
project-setup --project SKA --proj-dir ~/Documents --data-dir /mnt/work/Data \
  --json ~/Documents/SKA/data-path.json
```

- `--dry-run` previews everything a run would create — project directory, setup
  directories, Git steps, data root, data path, every subfolder and the
  configuration file — and writes nothing.
- `--show` reports an existing project without changing it: version, setup
  directories, the data workspace (root, data path, subfolders), the `json/`
  folder path and the configuration file path.
- `--json [PATH]` selects the configuration JSON file (a file or directory
  inside the project) and implies workspace creation; without a value it prints
  the configuration file path.

Every requested path is checked before anything is created: existing paths are
reported as `exists`, missing paths are created when permitted, and blocked
paths (unmounted volume, no permission, file where a directory belongs) are
reported in the terminal with the reason — creation stops before the project
directory is written. `data-path.json` is machine-specific; decide whether to
add it to `.gitignore`. For an already-created project, inspection and later
reconfiguration remain available through the installed `project-data` command
(`project-data --help`).

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

## Refresh an existing project with AI

```sh
project-setup --refresh MyProject --proj-dir ~/Projects
project-setup --refresh MyProject --proj-dir ~/Projects --ai manual
```

Interactive use offers Antigravity, ChatGPT, Claude, OpenCode or Manual. Manual
prints a complete migration prompt and changes no project files. Named choices
also print the prompt when no command is configured. Use --ai-command containing
{prompt_file}, or PROJECT_SETUP_AI_COMMAND_<AGENT>, for your actual installed
agent CLI. No app-specific invocation or model credentials are guessed.
See [refresh instructions](docs/refresh.md) for execution and ownership rules.
Automatic runs require a clean committed repository, preserve history/remotes,
leave changes uncommitted for review, and check required outputs before reporting
completion of the AI run. Exit zero is not proof of scientific correctness.

Refreshing never changes project licensing. See [licensing design notes](docs/LICENSING_OPTIONS.md)
for the requested citation/permission policy discussion; these are not license terms.

## Licensing records and HTML attribution

`project-lisence` creates a custom source-available **draft**, without changing
existing licenses. New projects include `lisence/model-license.json` and
`lisence/MODEL_LICENSE.txt`. Copy the JSON model, fill in your project metadata,
and run:

```sh
project-lisence --project my-project --proj-dir ~/Documents \
  --author "Author Name" --author-email "author@example.org" \
  --author-affil "Institution" --doi-paper "10.xxxx/example" \
  --link "https://github.com/owner/my-project" \
  --lisence-file ~/Documents/my-project/lisence/model-license.json
```

`--proj-dir` accepts the parent or the project directory. The DOI and repository
link are optional; do not invent a DOI. `--lisence-file` (also `--license-file`)
accepts a JSON metadata model or UTF-8 text terms template. Text placeholders are
`{{project}}`, `{{author}}`, `{{author_email}}`, `{{author_affil}}`, `{{doi_paper}}`
and `{{link}}`. Flags override saved/model metadata. Run while holding the project's
agent lock if using an agent; this command does not acquire ownership or push Git.

Outputs are `lisence/license-info.json`, `lisence/LICENSE.txt` and
`lisence/LICENSE.html`. Managed attribution is added to top-level HTML and every
HTML page under `docs/`, `doc/` and `lisence/`. Re-run after documentation generation.
Existing unmanaged licensing files are never overwritten. The command deliberately
keeps the policy marked draft; author approval and legal review precede adoption.
It does not grant scientific coauthorship, retract existing rights, or replace
third-party licenses. The proposed conditions permit use with credit, restrict
publication of modifications to written permission and approved project versions,
and allow unchanged inclusion with notices. See [licensing policy](docs/LICENSING_OPTIONS.md).
