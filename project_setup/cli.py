"""Portable project scaffolding and release management; Python 3.9+."""
import argparse
from datetime import datetime
import fnmatch
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tarfile
import tempfile

VERSION_RE = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]?)\.(0|[1-9][0-9]?)\Z')
DIRS = ('script', 'docs', 'data', 'versions', 'developer', 'testdirectory')
IGNORE = '.git/\nversions/*\n!versions/.gitkeep\n__pycache__/\n*.py[cod]\n.venv/\nbuild/\ndist/\n*.egg-info/\n.DS_Store\n.env\n.env.*\n'
RULES = '''# Guidelines & Rules for Coding Agents

This document defines mandatory guidelines for all AI coding assistants (Gemini, Codex, Claude, Cursor, Copilot, etc.) and human developers contributing to the {project} project.

Load this file once at the start of each conversation/session. Retain its rules in context; reload only when this file changes or context is lost.

---

## 1. Developer Log Maintenance (`developer/DEV_NOTES.md`)

Whenever a user request or task is given:
1. **Freshen Up the Prompt**: Clean up, structure, and refine the raw prompt into an unambiguous, professional specification.
2. **Append to `developer/DEV_NOTES.md`**: Add a new entry at the top of the log using the established project schema:

```markdown
## YYYY-MM-DD HH:MM:SS TZ

Prompt / Request
- Refined and structured description of the requested task.

Changes Made
- Concrete summary of code, configuration, or documentation modifications.

Verification
- Exact commands, tests, or inspection steps executed to verify correctness.

Notes
- Relevant context, edge cases, follow-ups, or cautions.
```

---

## 2. Code Style & Naming Conventions (`script/`)

All new code and modifications in `script/` must strictly conform to existing codebase patterns:

1. **Language & Environment**:
   - Python 3.9+ compatible.
   - Always include `from __future__ import annotations` at the top of Python modules.
   - Use standard library modules whenever possible (`pathlib.Path`, `argparse`, `json`, `subprocess`, `sys`, `shutil`, `typing`).

2. **File Naming & Executables**:
   - User-facing CLI tools in `script/` use the `{project}-<action>` pattern without `.py` extension (e.g. `script/{project}-setup`). The generated `script/project-update` is the standard updater and keeps its name.
   - CLI scripts must begin with `#!/usr/bin/env python3` and maintain executable permissions.

3. **Variable & Function Naming**:
   - **Functions & Methods**: `snake_case` (e.g. `load_config()`, `resolve_setup_file()`, `project_root()`).
   - **Variables & Arguments**: `snake_case` (e.g. `workdir`, `fitspath`, `mspath`, `target_dirs`).
   - **Constants & Configuration Sets**: `UPPER_SNAKE_CASE` (e.g. `CONFIG_NAME`, `WORKDIR_SUBDIRS`, `CLEAN_TARGETS`).
   - **Classes**: `PascalCase`.

4. **Type Annotations**:
   - Use comprehensive type annotations on all function signatures (`Path`, `Dict[str, object]`, `List[str]`, `str | None`, `bool`).

5. **Robust File Operations**:
   - Use `pathlib.Path` for filesystem operations.
   - Use atomic write patterns (write to `.tmp` then `replace`) when saving configuration JSON files.

6. **CLI Standards**:
   - Use `argparse` with descriptive flag names matching existing commands (e.g. `--fitspath`, `--mspath`, `--workdir`, `--clean`, `--dry-run`, `--config-file`, `--show`).
   - Provide clear, user-friendly help strings and stdout status formatting.

---

## 3. Multi-Agent Coordination & Safety (.agent_lock Protocol)

To prevent simultaneous execution, race conditions, and broken Git states when working with multiple AI agents (Gemini, Codex, Claude, etc.):

1. **The `.agent_lock` Protocol**:
   - The root file `.agent_lock` acts as a mutual-exclusion lock for all coding agents and Git operations.
   - **Default / Idle State (`True`)**: By default, when no agent is actively executing, `.agent_lock` contains `True` (meaning available / unlocked).
   - **Acquiring the Lock (`False`)**: Whenever an agent begins a task or prompt:
     - Check `.agent_lock`; initialize it to `True` if absent before starting work.
     - If it is `True`, immediately set the file content to `False` to signal that an agent is actively working.
     - If it is `False`, another agent is currently running; wait or abort to avoid conflicts.
   - **Releasing the Lock (`True`)**: When the agent finishes its task, verifications, and developer-log updates, it must reset `.agent_lock` back to `True`.

2. **Git & Pipeline Operations**:
   - The same `.agent_lock` check applies to any Git commands (`git add`, `git commit`, `git checkout`, `git push`) and pipeline executions to guarantee mutual exclusion.

3. **Sequential Execution & Fresh State**:
   - Always operate sequentially, never running prompts in parallel across multiple tools.
   - Read fresh file contents from disk before making edits to avoid stale context.
   - Create clean Git commits or stashes before switching tools.

4. **Git Staging & Release Tar Boundaries**:
   - The `developer/` directory (including `DEV_NOTES.md`, `AGENT_RULES.md`, and `developer/script/`) as well as `guide/` are tracked in Git and staged/committed whenever Git actions (`script/project-update --git-push`, `git add`) are performed.
   - The `developer/` and `guide/` directories are **strictly excluded** from release distribution archives created with `--release` (`versions/{project}-*.tar.gz`); keep these paths out of `release-files.txt`.

---

## 4. Temporary Developer Scripts (`developer/script/`)

Create a dedicated subdirectory `developer/script/` when needed for temporary scripts, scratch experiments, and prototyping tools:

1. **Relaxed Multi-Agent Read/Edit Concurrency**:
   - Files within `developer/script/` may be accessed in **read-only mode** by one agent while another agent modifies a **different file** in the same folder.
   - Multiple agents must never edit or overwrite the same temporary script simultaneously.

2. **Strict Scope Isolation**:
   - This relaxed concurrency exception applies **strictly and exclusively to `developer/script/`**.
   - Main production scripts (`script/`), pipeline definitions (`pipelines/`), documentation (`docs/`), and configuration/root files remain strictly bound to Section 3: **only one agent may execute at any given time** under the mutual-exclusion `.agent_lock` protocol.

---

## 5. Terminal Session Permission Lifecycle & Workspace Boundaries (Gemini)

To ensure seamless in-session developer workflow while maintaining strict workspace security:

1. **Session-Level Initial Authorization**:
   - When a Gemini session is opened in the terminal, permission is requested and established at the beginning of the session.

2. **Autonomous In-Session Execution Within Parent Directory**:
   - Once authorized, between the session start and its conclusion, the agent operates autonomously without repeatedly asking for per-action permissions for standard operations (reading, writing, editing files, running project commands, and running tests), **as long as all work is strictly confined to the project parent directory** (`{project_root}`).

3. **Strict Directory Boundary Enforcement**:
   - The agent is strictly prohibited from modifying, reading, or running commands on files outside the parent project root directory without explicit user instruction.

4. **Session Exit & Automatic Permission Revocation**:
   - Upon exiting, closing, or terminating the session, all granted permissions expire immediately.
   - The agent possesses no ongoing authority or permission to perform any actions once the session has ended.


'''
NOTES = '''# {project} Developer Notes

This file is the running developer log for {project}. Add a new timestamped entry whenever the code, plans, packaging, or workflow changes.

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
'''

class Error(Exception):
    pass

def git(root, *args, check=True):
    p = subprocess.run(['git', '-C', str(root), *args], text=True, capture_output=True)
    if check and p.returncode:
        raise Error(p.stderr.strip() or p.stdout.strip() or 'Git command failed')
    return p.stdout.strip()

def validate(value):
    if not VERSION_RE.fullmatch(value):
        raise Error('Version must be MAJOR.MIDDLE.MINOR: nonnegative integers, middle/minor 0–99, no leading zeros.')
    return value

def next_version(current, action):
    validate(current)
    a, b, c = map(int, current.split('.'))
    if action == 'major':
        a, b, c = a + 1, 0, 0
    elif action == 'middle':
        b, c = b + 1, 0
    elif action == 'minor':
        c += 1
    else:
        return validate(action)
    if c > 99:
        b, c = b + 1, 0
    if b > 99:
        a, b, c = a + 1, 0, 0
    return f'{a}.{b}.{c}'

def write_version(root, version):
    path = root / 'VERSION'
    history = path.read_text().splitlines()
    if history[0] == version:
        return
    fd, name = tempfile.mkstemp(prefix='.VERSION-', dir=root)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join([version, *history]) + '\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def commit(root, message):
    git(root, 'add', '--all')
    if git(root, 'status', '--porcelain'):
        git(root, 'commit', '-m', message)

def current_branch(root):
    branch = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if not branch:
        raise Error('A branch checkout is required.')
    return branch

def transfer(root, operation, target, message):
    if target == 'show':
        print(git(root, 'branch', '--all'))
        return
    git(root, 'remote', 'get-url', 'origin')
    if VERSION_RE.fullmatch(target or ''):
        tag = 'v' + target
        if operation == 'pull':
            git(root, 'fetch', 'origin', f'refs/tags/{tag}:refs/tags/{tag}')
            print(f'Fetched {tag}; working tree unchanged.')
        else:
            exists = git(root, 'tag', '--list', tag)
            if not exists:
                if (root / 'VERSION').read_text().splitlines()[0] != target:
                    raise Error('An unpublished version must match VERSION; use --version first.')
                commit(root, message)
                git(root, 'tag', '-a', tag, '-m', message)
            git(root, 'push', 'origin', f'refs/tags/{tag}:refs/tags/{tag}')
        return
    branch = target or current_branch(root)
    git(root, 'check-ref-format', '--branch', branch)
    if operation == 'pull':
        if branch != current_branch(root):
            raise Error('Pull into a different branch is refused; switch branches explicitly first.')
        if git(root, 'status', '--porcelain'):
            raise Error('Pull requires a clean working tree; commit or stash changes first.')
        git(root, 'pull', '--ff-only', 'origin', branch)
    else:
        if branch == current_branch(root):
            commit(root, message)
        git(root, 'show-ref', '--verify', f'refs/heads/{branch}')
        git(root, 'push', '--set-upstream', 'origin', f'refs/heads/{branch}:refs/heads/{branch}')

def release(root, version, message):
    manifest = root / 'release-files.txt'
    if not manifest.is_file():
        raise Error('Missing release-files.txt; list distributable files/directories, one per line.')
    selected = set()
    for line in manifest.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        rel = Path(line)
        if rel.is_absolute() or '..' in rel.parts:
            raise Error(f'Unsafe release path: {line}')
        source = root / rel
        if any((root / Path(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts) + 1)):
            raise Error(f'Release symlinks are refused: {line}')
        if not source.exists():
            raise Error(f'Missing release path: {line}')
        for p in [source, *source.rglob('*')] if source.is_dir() else [source]:
            relative = p.relative_to(root)
            if any(part in ('versions', '.git', '__pycache__', '.venv', 'build', 'dist') or part.endswith('.egg-info') for part in relative.parts):
                continue
            if p.is_symlink():
                raise Error(f'Release symlinks are refused: {relative}')
            if p.is_file() and not any(fnmatch.fnmatch(p.name, pattern) for pattern in ('.env', '.env.*', '*.pyc', '*.pyo', '.DS_Store')):
                selected.add(relative)
    destination = root / 'versions'
    if destination.is_symlink():
        raise Error('versions/ must not be a symlink.')
    destination.mkdir(exist_ok=True)
    name = f'{root.name}-{version}'
    stage, archive = destination / name, destination / (name + '.tar.gz')
    if stage.exists() or archive.exists():
        raise Error(f'Release {version} already exists; bump version first.')
    temporary = Path(tempfile.mkdtemp(prefix='.stage-', dir=destination))
    try:
        for rel in sorted(selected):
            out = temporary / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / rel, out)
        (temporary / 'RELEASE.txt').write_text(f'Version: {version}\nMessage: {message}\n')
        temporary.rename(stage)
        with tarfile.open(archive, 'x:gz') as tar:
            tar.add(stage, arcname=name)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        shutil.rmtree(stage, ignore_errors=True)
        archive.unlink(missing_ok=True)
        raise
    print(f'Release: {archive}')

def github(root, *args):
    if not shutil.which('gh'):
        raise Error('GitHub CLI (gh) is not installed.')
    result = subprocess.run(['gh', *args], cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise Error(result.stderr.strip() or 'GitHub operation failed.')
    return result.stdout.strip()

def ensure_remote(root, remote):
    if remote:
        match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?', remote)
        if not match:
            # Other Git hosts and local remotes remain supported, but are not provisioned.
            git(root, 'remote', 'add', 'origin', remote)
            return
        repo = match.group(1)
    else:
        login = github(root, 'api', 'user', '--jq', '.login')
        repo = login + '/' + root.name
        remote = 'https://github.com/' + repo + '.git'
    github(root, 'auth', 'status')
    try:
        github(root, 'repo', 'view', repo, '--json', 'name')
    except Error:
        # Creation fails safely if the name exists but this account cannot access it.
        github(root, 'repo', 'create', repo, '--private')
        print(f'Created private GitHub repository: {repo}')
    git(root, 'remote', 'add', 'origin', remote)

def setup_guidance(root, remote=None):
    location = shlex.quote(str(root))
    print(f"""
Git setup could not finish. Your project files are retained at {root}.
Run these steps in a terminal; the commands work from any directory.

1. Install Git and GitHub CLI if missing:
   macOS (with Homebrew): brew install git gh
   Ubuntu/Debian: sudo apt update && sudo apt install git gh
   Other Linux: install git and gh with your distribution's package manager.
   Install help: https://git-scm.com/downloads and https://cli.github.com/

2. Set your identity (replace the example values). --global applies to this computer:
   git config --global user.name "Your Name"
   git config --global user.email "your-email@example.com"

3. Sign in and enable Git authentication:
   gh auth login --hostname github.com --git-protocol https --web
   gh auth setup-git
   gh auth status

4. Initialize the retained project if Git initialization failed, then commit:
   git -C {location} init -b main
   git -C {location} add --all
   git -C {location} commit -m "Initialize project"
   If Git says there is nothing to commit, continue.

5. Create the repository if it is missing:
   gh repo create YOUR_ACCOUNT/{root.name} --private
   If the repository already exists, use its existing URL.

6. Check origin, then add it only if absent (replace YOUR_ACCOUNT):
   git -C {location} remote -v
   git -C {location} remote add origin https://github.com/YOUR_ACCOUNT/{root.name}.git
   If origin exists but is wrong, use 'remote set-url origin URL' instead.

7. Push the current branch:
   git -C {location} push --set-upstream origin HEAD
   Do not run project-setup again against this existing directory.
""", file=sys.stderr)
    if remote:
        print(f'Requested remote: {remote} (use its owner/name in steps 5–6).', file=sys.stderr)


def scaffold(args):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.project):
        raise Error('PROJECT must be a single directory name starting with a letter or digit.')
    parent = Path(args.proj_dir).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / args.project
    root.mkdir()  # exclusive: never overwrite or merge
    for directory in DIRS:
        (root / directory).mkdir()
        (root / directory / '.gitkeep').touch()
    (root / 'VERSION').write_text('0.0.1\n')
    (root / '.gitignore').write_text(IGNORE)
    (root / 'developer/DEV_NOTES.md').write_text(NOTES.format(project=args.project))
    (root / 'developer/AGENT_RULES.md').write_text(RULES.replace("{project}", args.project).replace("{project_root}", str(root)))
    (root / 'README.md').write_text(f'# {args.project}\n\nDescribe installation and usage here.\n')
    (root / 'release-files.txt').write_text('VERSION\nREADME.md\nscript\ndocs\ndata\nrelease-files.txt\n')
    updater = root / 'script/project-update'
    updater.write_text('#!/usr/bin/env python3\n' + Path(__file__).read_text() + '\nif __name__ == "__main__":\n    update_main(root=Path(__file__).resolve().parent.parent)\n')
    updater.chmod(0o755)
    try:
        git(root, 'init', '-b', 'main')
        git(root, 'add', '--all')
        if git(root, 'var', 'GIT_AUTHOR_IDENT', check=False):
            commit(root, 'Initialize project')
        else:
            print('Git initialized and files staged. Configure Git user.name/user.email to commit.')
        if args.remote or args.create_remote or args.git_push:
            ensure_remote(root, args.remote)
        if args.git_push:
            transfer(root, 'push', None, 'Initialize project')
    except (Error, OSError):
        setup_guidance(root, args.remote)
        raise
    print(f'Created: {root}')

def setup_main():
    p = argparse.ArgumentParser(description='Create a portable project with Git and release tooling.')
    p.add_argument('--project', required=True)
    p.add_argument('--proj-dir', default='.')
    p.add_argument('--remote', help='Git remote URL to configure as origin')
    p.add_argument('--create-remote', action='store_true', help='Create a private GitHub repository if missing; defaults to authenticated account/PROJECT')
    p.add_argument('--git-push', action='store_true', help='Ensure remote exists, commit and push the new project')
    args = p.parse_args()
    run(lambda: scaffold(args))

def update_main(root=None):
    p = argparse.ArgumentParser(description='Update version, release, and synchronize Git, in that order (pull runs first).')
    p.add_argument('--version', nargs='?', const='minor')
    p.add_argument('--release', action='store_true')
    p.add_argument('--git-push', nargs='?', const='')
    p.add_argument('--git-pull', nargs='?', const='')
    p.add_argument('--massage', '--message', dest='message', nargs='?', const=None)
    args = p.parse_args()
    def work():
        project = root or Path(git(Path.cwd(), 'rev-parse', '--show-toplevel'))
        if args.git_pull == 'show' or args.git_push == 'show':
            if args.version is not None or args.release or (args.git_pull not in (None, 'show')) or (args.git_push not in (None, 'show')):
                raise Error('show cannot be combined with modifying operations.')
            print(git(project, 'branch', '--all'))
            return
        if args.git_pull is None and args.git_push is None and args.version is None and not args.release:
            p.print_help()
            return
        message = args.message if args.message is not None else datetime.now().strftime('%d:%m:%y|%H-%M-%S')
        if args.git_pull is not None:
            transfer(project, 'pull', args.git_pull, message)
        version = validate((project / 'VERSION').read_text().splitlines()[0])
        if args.version is not None:
            version = next_version(version, args.version)
            write_version(project, version)
            print(f'Version: {version}')
        if args.release:
            release(project, version, message)
        if args.git_push is not None:
            transfer(project, 'push', args.git_push, message)
    run(work)

def run(action):
    try:
        action()
    except (Error, OSError, IndexError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
