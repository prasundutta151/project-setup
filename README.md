# project-setup

Create consistent Python-friendly projects on macOS and Linux. Runtime uses only
Python's standard library. Requires Python 3.9+ and Git 2.28+ on PATH.

## Install

```sh
python3 install.py
# If ~/.local/bin is not already on PATH, add this to your shell profile:
export PATH="$HOME/.local/bin:$PATH"
```

The installer copies the package to `~/.local/lib/project-setup/` and puts two
commands in `~/.local/bin/`. Re-run to upgrade; unrelated commands are never
overwritten. A custom prefix is supported: `python3 install.py --prefix /path`.
Alternatively install using `python3 -m pip install .` in a virtual environment.
To uninstall the stdlib installation, remove the two managed launchers and the
`~/.local/lib/project-setup` directory.

## Create a project

```sh
project-setup --project my-project
project-setup --project my-project --proj-dir /path/to/parent
project-setup --project my-project --remote git@github.com:USER/REPO.git --git-push
```

`--project` is required. `--proj-dir` defaults to the current directory. Missing parent
directories are created automatically; an existing project directory is always refused, even if empty.
For GitHub, `--remote` checks for the repository and creates it privately if missing.
Use `--create-remote` without a URL to create `YOUR_ACCOUNT/PROJECT` using the
account authenticated in GitHub CLI (`gh`). `--git-push` also ensures that remote
exists, commits, and pushes, so a URL is optional:

```sh
project-setup --project my-project --git-push
project-setup --project my-project --create-remote
```

GitHub provisioning requires `gh` and `gh auth login`. Existing repository visibility
is preserved. Other Git hosts/local remotes are configured but not automatically
provisioned. If Git initialization, remote creation, or push fails, the terminal
prints numbered installation, identity, authentication, and recovery commands.
These use absolute project paths and work from any directory. Files remain intact;
do not rerun setup against that existing project.
Git identity is inherited from your configuration; if missing, files remain staged
and the command explains how to finish the commit. Git failures retain local files.

```text
my-project/
  VERSION                    # newest version first, initially 0.0.1
  README.md
  .gitignore
  release-files.txt           # explicit distribution file list
  script/project-update      # executable, standalone Python updater
  docs/                      # HTML and Markdown documentation
  data/                      # application data
  versions/                  # release staging directories and tarballs (ignored)
  developer/DEV_NOTES.md      # structured agent handoff and decision log
  developer/AGENT_RULES.md    # load once per session, reload on changes/context loss
  testdirectory/             # test code and fixtures
```

The generated updater is self-contained and works even if project-setup is later
uninstalled. Run it from anywhere; it finds its project from its own location.
The installed `project-update` command finds the repository containing your current
working directory. Empty directories contain `.gitkeep` so Git preserves them.

## Update and release

```sh
./script/project-update --version
./script/project-update --version middle
./script/project-update --version major
./script/project-update --version 2.3.4
./script/project-update --version --release --git-push --message "Publish update"
```

The format is `MAJOR.MIDDLE.MINOR`. Here **minor means the rightmost component**,
as requested, rather than conventional semantic-version terminology. With no value,
`--version` means minor. Rightmost 99 rolls to 0 and increments middle; middle 99
rolls to 0 and increments major. Middle increments reset minor; major increments
reset both. Explicit versions must have three nonnegative integers, no leading
zeros, and middle/minor between 0 and 99. Setting the current version is a no-op;
other changes prepend the new value and retain all history, including revisits.

Releases copy the paths in `release-files.txt` into `versions/PROJECT-VERSION/`, then
create `versions/PROJECT-VERSION.tar.gz`. One project-relative file or directory
per line; blank lines and `#` comments are allowed. No globs. Edit this manifest to
include your install script, package code, dependencies, and assets. The scaffolder
cannot infer a future application's installation requirements. Releases of this
software include `install.py` and can be installed after extraction.

Versions, Git metadata, caches, build output, and `.env` files are excluded.
Symlinks and parent traversal are refused. Review the manifest before distributing:
it is an allowlist, not a general secret scanner. Existing releases are never
replaced. `RELEASE.txt` records the version and message in the staging directory.

## Git synchronization

| Argument | Push | Pull |
| --- | --- | --- |
| No value | Commit all nonignored changes and push current branch | Fast-forward current branch from origin |
| Branch | Push that existing local branch; commit only if it is current | Fast-forward only if already on that branch |
| `show` | List local and known remote branches | Same |
| Version, e.g. `1.2.3` | Push existing `v1.2.3` tag, or commit and create it when VERSION matches | Fetch `v1.2.3` tag without checkout |

Tags are annotated when created. Existing tags are never moved. Fetching a version
makes it available for inspection with `git show v1.2.3` without changing local
files. `show` cannot be combined with mutations. Pull requires a clean working tree
and refuses merges, rebases, branch switches, and non-fast-forward updates.
Pushes use origin and never force. Branch pushes do not automatically create tags;
use a version target when a version tag is desired.

Operations compose in this order: **pull → version → release → commit/push**.
Failures stop subsequent operations, but completed steps remain: this is not a
transaction across disk and a remote server. For example, a failed push retains the
local release and commit. Retry with just `--git-push`; do not repeat a version bump.
Only one updater should run against a project at a time.

`--massage` and `--message` are aliases. Omit the value (or the option) to use local
datetime `DD:MM:YY|HH-MM-SS`; otherwise the supplied text becomes the commit/release
message. Git push commits **all nonignored changes** on the current branch, so review
`git status` first. For values starting with a dash, use `--message=-text`.

## Development and validation

```sh
python3 -m unittest discover -s testdirectory -v
```

Tests cover rollover and validation, safe scaffolding, version history, release
contents, manifest rejection, commit messages, branch/tag publishing, clean-tree
checks, and fast-forward pulls against temporary local bare repositories.
Linux is verified locally; macOS is covered by the included CI workflow, which
must run remotely before macOS execution can be claimed.
