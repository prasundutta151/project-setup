"""Portable project scaffolding and release management; Python 3.9+."""
from __future__ import annotations
import argparse
import json
import socket
import uuid
from datetime import datetime, timezone
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
DIRS = ('script', 'version', 'docs', 'pipeline', 'json', 'plot', 'developer', 'tests', 'data', 'lisence')


class Error(Exception):
    pass

class DataError(Error):
    """Data-workspace failure raised after the project scaffold already exists."""
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

def version_path(root):
    modern = root / 'version' / 'VERSION'
    return modern if modern.is_file() else root / 'VERSION'

def write_version(root, version):
    path = version_path(root)
    history = path.read_text().splitlines()
    if history[0] == version:
        return
    fd, name = tempfile.mkstemp(prefix='.VERSION-', dir=path.parent)
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
                if version_path(root).read_text().splitlines()[0] != target:
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
            if any(part in ('versions', '.git', '.agent-state', '__pycache__', '.venv', 'build', 'dist') or part.endswith('.egg-info') for part in relative.parts):
                continue
            if p.is_symlink():
                raise Error(f'Release symlinks are refused: {relative}')
            if p.is_file() and not any(fnmatch.fnmatch(p.name, pattern) for pattern in ('.env', '.env.*', '.agent_lock', '*.pyc', '*.pyo', '.DS_Store')):
                selected.add(relative)
    destination = root / 'version' / 'dist' if (root / 'version' / 'VERSION').is_file() else root / 'versions'
    if destination.is_symlink():
        raise Error('versions/ must not be a symlink.')
    destination.mkdir(parents=True, exist_ok=True)
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


def write_updater(root):
    updater = root / 'script/project-update'
    updater.parent.mkdir(parents=True, exist_ok=True)
    updater.write_text('#!/usr/bin/env python3\n' + Path(__file__).read_text() + '\nif __name__ == "__main__":\n    update_main(root=Path(__file__).resolve().parent.parent)\n')
    updater.chmod(0o755)


def read_description(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = Path(value[1:] if value.startswith('@') else value).expanduser()
    explicit_file = value.startswith('@') or ('\n' not in value and value.lower().endswith('.txt'))
    try:
        try:
            is_file = candidate.is_file() if len(value) < 4096 and '\n' not in value else False
        except OSError:
            if explicit_file: raise
            is_file = False
        if explicit_file or is_file:
            if not is_file:
                raise Error('Description file not found: ' + str(candidate))
            value = candidate.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        raise Error('Cannot read description text file: ' + str(exc))
    if not value.strip() or '\x00' in value:
        raise Error('Project description must be nonempty plain text without NUL bytes.')
    return value.strip()


DEFAULT_DATA_ROOT = '/Volumes/Work/Data'
DATA_FILE_SUFFIXES = ('.txt', '.lst', '.list', '.json')


def data_module():
    """Import the bundled data-workspace module lazily; standalone updaters never import it."""
    from . import data
    return data


def absolute(value) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def data_dir_args(values):
    """Resolve --data-dir values to (destination, subfolders, tree_file, label).

    One existing file selects a directory-list file (ASCII lines or a JSON
    preset); one absolute or ~ path is the data root, where the project
    directory is created; every other value is a relative directory entry.
    With no values the default root /Volumes/Work/Data is used.
    """
    if not values:
        return None, None, None, 'default root ' + DEFAULT_DATA_ROOT
    files, roots, entries = [], [], []
    for value in values:
        path = Path(value).expanduser()
        try:
            is_link, is_file = path.is_symlink(), path.is_file()
        except OSError:
            # Unreadable parents (for example /root) are classified by their name.
            is_link, is_file = False, False
        if is_link:
            raise Error('Refusing a symbolic-link --data-dir path: ' + str(path))
        if is_file:
            files.append(value)
        elif value.startswith(('/', '~')):
            roots.append(value)
        else:
            entries.append(value)
        if path.suffix.lower() in DATA_FILE_SUFFIXES and not path.exists():
            raise Error('--data-dir directory-list file not found: ' + str(absolute(value)))
    if len(files) > 1:
        raise Error('--data-dir accepts at most one directory-list file.')
    if len(roots) > 1:
        raise Error('--data-dir accepts at most one absolute data root.')
    if files and entries:
        raise Error('--data-dir: directory entries cannot be combined with a directory-list file; list them inside the file.')
    for entry in entries:
        try:
            data_module().valid_tree_path(entry)
        except (ValueError, argparse.ArgumentTypeError) as exc:
            raise Error(str(exc))
    destination = absolute(roots[0]) if roots else None
    tree = absolute(files[0]) if files else None
    if tree:
        label = 'directory-list file ' + str(tree)
        if destination:
            label += ' under data root ' + str(destination)
    elif destination:
        label = 'data root ' + str(destination)
        if entries:
            label += ' with directory entries'
    elif entries:
        label = 'directory entries under default root ' + DEFAULT_DATA_ROOT
    else:
        label = 'default root ' + DEFAULT_DATA_ROOT
    return destination, (entries or None), tree, label


def path_state(path) -> str:
    """Return 'exists' or 'will create'; raise Error when the path is blocked."""
    path = absolute(path)
    parts = path.parts
    if len(parts) >= 3 and parts[1] == 'Volumes':
        volume = Path(parts[0], parts[1], parts[2])
        if not os.path.ismount(volume):
            raise Error(f'Volume is not mounted: {volume}. Mount it or choose another root with a single --data-dir PATH.')
    if path.exists():
        if not path.is_dir():
            raise Error(str(path) + ' exists and is not a directory.')
        return 'exists'
    try:
        if path.is_symlink():
            raise Error(str(path) + ' is a broken symbolic link.')
    except OSError as exc:
        raise Error('Permission denied: cannot inspect ' + str(path) + ' (' + str(exc) + ').')
    ancestor = path.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.exists():
        raise Error('No existing parent directory for ' + str(path) + '.')
    if not ancestor.is_dir():
        raise Error(str(ancestor) + ' exists and is not a directory.')
    if not os.access(ancestor, os.W_OK | os.X_OK):
        raise Error('Permission denied: cannot create ' + str(path) + ' (no write permission at ' + str(ancestor) + ').')
    return 'will create'


def json_state(path) -> str:
    """State of the configuration JSON file target: exists, will create or Error."""
    path = absolute(path)
    if path.is_symlink():
        raise Error('Refusing a symbolic-link configuration: ' + str(path))
    if path.exists() and not path.is_file():
        raise Error(str(path) + ' exists and is not a file.')
    if path.exists():
        return 'exists'
    return path_state(path)


def report_check(path, state: str, label: str) -> None:
    print('Check: ' + str(path) + ' [' + state + '] (' + label + ')')


def dry_check(path, label: str) -> None:
    try:
        state = path_state(path)
    except Error as exc:
        print('Check: ' + str(path) + ' [BLOCKED: ' + str(exc) + '] (' + label + ')')
    else:
        report_check(path, state, label)


def data_plan(args, project: Path):
    """Pre-flight data validation; returns the workspace plan or None when not requested."""
    json_value = args.json if isinstance(args.json, str) and args.json else None
    if args.data_dir is None and json_value is None:
        return None
    dm = data_module()
    destination, subfolders, tree_file, source = data_dir_args(args.data_dir or [])
    json_path = absolute(json_value) if json_value else None
    if json_path is not None:
        target = dm.config_file(project, json_path)
        resolved = project.resolve()
        if resolved != target.parent and resolved not in target.parent.parents:
            raise Error('--json must name a file or directory inside the project: ' + str(target))
    try:
        config = dm.setup(project, destination, subfolders, tree_file, json_path, dry_run=True)
    except (ValueError, argparse.ArgumentTypeError) as exc:
        message = str(exc)
        if 'pass --destination' in message:
            message = message.replace('pass --destination.', 'choose another root with a single --data-dir PATH.')
        raise Error(message)
    except OSError as exc:
        raise Error(str(exc))
    return {'source': source, 'destination': destination, 'subfolders': subfolders,
            'tree_file': tree_file, 'json_path': json_path, 'config': config}


def materialize_data(project: Path, plan) -> None:
    """Create the data workspace and write its configuration after the scaffold exists."""
    dm = data_module()
    try:
        target = dm.config_file(project, plan['json_path'])
        # The configuration may name a nested file; its directory lives inside the project.
        target.parent.mkdir(parents=True, exist_ok=True)
        config = dm.setup(project, plan['destination'], plan['subfolders'], plan['tree_file'],
                          plan['json_path'], dry_run=False)
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        raise DataError('Data workspace could not be created: ' + str(exc) +
                        ' Project files remain at ' + str(project) + '.')
    print('Data workspace ready')
    print('Data root: ' + config['data_root'])
    print('Data: ' + config['data_path'])
    print('Subfolders: ' + ', '.join(config['subfolders']))
    print('Configuration: ' + str(dm.config_file(project, plan['json_path'])))


def print_config_path(args) -> None:
    """Give the path of the data configuration JSON file without changing anything."""
    dm = data_module()
    project = Path(args.proj_dir).expanduser().resolve() / args.project if args.project else Path.cwd()
    if not project.is_dir():
        raise Error('Project directory does not exist: ' + str(project))
    json_value = args.json if isinstance(args.json, str) and args.json else None
    config = dm.config_file(project, absolute(json_value) if json_value else None)
    note = '' if config.is_file() else ' (not created; add --data-dir to create the workspace)'
    print('Configuration: ' + str(config) + note)


def show_setup(args) -> None:
    """Read-only report of setup directories, data workspace and configuration paths."""
    dm = data_module()
    project = Path(args.proj_dir).expanduser().resolve() / args.project if args.project else Path.cwd()
    if not project.is_dir():
        raise Error('Project directory does not exist: ' + str(project))
    print('Project: ' + str(project))
    version = version_path(project)
    print('Version: ' + (version.read_text().splitlines()[0] if version.is_file() else '(none)'))
    print('Setup directories:')
    for name in DIRS:
        print('  ' + name + ': ' + ('present' if (project / name).is_dir() else 'missing'))
    json_folder = project / 'json'
    print('JSON folder: ' + str(json_folder) + ('' if json_folder.is_dir() else ' (missing)'))
    json_value = args.json if isinstance(args.json, str) and args.json else None
    json_path = absolute(json_value) if json_value else None
    try:
        config = dm.read_config(project, json_path)
        config_file = dm.config_file(project, json_path, for_show=True)
    except ValueError as exc:
        raise Error(str(exc))
    if config:
        data_path = Path(config['data_path'])
        print('Data workspace:')
        print('  Root: ' + config['data_root'])
        print('  Data: ' + str(data_path) + (' [exists]' if data_path.is_dir() else ' [missing]'))
        print('  Subfolders: ' + ', '.join(config['subfolders']))
    else:
        print('Data workspace: not configured (create one with --data-dir).')
    print('Configuration: ' + str(config_file) + ('' if config_file.is_file() else ' (not created)'))


def dry_run_setup(args) -> None:
    """Preview the project and data directories a creation would make; writes nothing."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.project or ''):
        raise Error('PROJECT must be a single directory name starting with a letter or digit.')
    args.description = read_description(args.proj_description if args.proj_description is not None else args.objective)
    parent = Path(args.proj_dir).expanduser().resolve()
    root = parent / args.project
    print('Dry run: no files or directories will be created.')
    print('')
    print('Project: ' + str(root))
    dry_check(parent, 'parent directory')
    if root.exists() or root.is_symlink():
        print('Check: ' + str(root) + ' [BLOCKED: destination exists; project-setup never overwrites] (project directory)')
    else:
        dry_check(root, 'project directory')
    print('Setup directories: ' + ', '.join(DIRS) + ' (inside the project)')
    git_line = 'Git: initialize, stage and commit the scaffold'
    if args.remote:
        git_line += '; configure remote ' + args.remote
    elif args.create_remote:
        git_line += '; create a private GitHub repository'
    if args.git_push:
        git_line += '; push the initial commit'
    print(git_line)
    print('Description file: PROJECT_DESCRIPTION.txt')
    print('')
    blocked = None
    try:
        plan = data_plan(args, root)
    except Error as exc:
        blocked, plan = str(exc), None
    if plan:
        config = plan['config']
        print('Data workspace: ' + plan['source'])
        dry_check(absolute(config['data_root']), 'data root')
        data_path = absolute(config['data_path'])
        dry_check(data_path, 'project data directory')
        for folder in config['subfolders']:
            dry_check(data_path / folder, 'subfolder')
        try:
            target = data_module().config_file(root, plan['json_path'])
            state = json_state(target)
        except Error as exc:
            print('Check: configuration JSON [BLOCKED: ' + str(exc) + ']')
        else:
            report_check(target, state, 'configuration JSON')
    elif blocked:
        print('Data workspace: BLOCKED: ' + blocked)
    else:
        print('Data workspace: not requested (add --data-dir; default root ' + DEFAULT_DATA_ROOT + ')')
        if args.json == '':
            config_file = data_module().config_file(root, None)
            print('Configuration: ' + str(config_file) + ' (not created; add --data-dir to create the workspace)')
    print('')
    print('Dry run complete: nothing was created.')


def clone_project(args):
    name = args.from_git
    # An explicit remote permits any Git host/local URL while retaining a simple name.
    if args.remote:
        project = args.project or name.rsplit('/', 1)[-1]
        remote = args.remote
    else:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*(?:/[A-Za-z0-9][A-Za-z0-9_.-]*)?', name):
            raise Error('--from-git expects NAME or OWNER/REPO; use --remote URL for other hosts.')
        repo = name if '/' in name else github(Path.cwd(), 'api', 'user', '--jq', '.login') + '/' + name
        project = args.project or repo.rsplit('/', 1)[-1]
        remote = 'https://github.com/' + repo + '.git'
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', project):
        raise Error('Project destination must be a single directory name.')
    parent = Path(args.proj_dir).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    if git(parent, 'rev-parse', '--show-toplevel', check=False):
        raise Error('Choose a clone destination outside an existing Git repository.')
    root = parent / project
    if root.exists() or root.is_symlink():
        raise Error('Destination already exists; use its existing checkout or a new name.')
    git(parent, 'clone', '--', remote, str(root))
    if args.description is not None:
        target = root / 'PROJECT_DESCRIPTION.txt'
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.read_text(encoding='utf-8').strip() != args.description)):
            raise Error('Clone retained at ' + str(root) + '; existing PROJECT_DESCRIPTION.txt differs. It was not overwritten.')
        if not target.exists():
            target.write_text(args.description + '\n', encoding='utf-8')
            print('Added PROJECT_DESCRIPTION.txt as an uncommitted local change; review and commit when ready.')
    print(f'Cloned: {root}\nOrigin: {remote}')
    print('Existing source, history and project rules preserved. No scaffold overlay, dependencies installed, or project code executed.')
    if (root/'startup-prompt.txt').is_file():
        print(f'Next: ask your agent to read {root / "startup-prompt.txt"}.')
    else:
        print('Next: ask your agent to inspect README and any AGENTS.md; use installed project-update in this checkout for Git synchronization.')


def scaffold(args):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.project):
        raise Error('PROJECT must be a single directory name starting with a letter or digit.')
    parent = Path(args.proj_dir).expanduser().resolve()
    report_check(parent, path_state(parent), 'parent directory')
    parent.mkdir(parents=True, exist_ok=True)
    if git(parent, 'rev-parse', '--show-toplevel', check=False):
        raise Error('Choose a destination outside an existing Git repository.')
    root = parent / args.project
    if root.exists() or root.is_symlink():
        raise Error('Destination already exists: ' + str(root) + '; project-setup never overwrites.')
    report_check(root, path_state(root), 'project directory')
    # Validate the data workspace before creating anything: unmounted volumes and
    # missing permissions are reported here, while the project still does not exist.
    plan = data_plan(args, root)
    if plan:
        config = plan['config']
        report_check(absolute(config['data_root']), path_state(config['data_root']), 'data root')
        report_check(absolute(config['data_path']), path_state(config['data_path']), 'project data directory')
        target = data_module().config_file(root, plan['json_path'])
        report_check(target, json_state(target), 'configuration JSON')
    root.mkdir()  # exclusive, never overwrite
    try:
        git(root, 'init', '-b', 'main')  # first operation before scaffold copying
        template = Path(__file__).parent / 'template'
        if not template.is_dir():
            raise Error('Bundled template missing; reinstall project-setup.')
        shutil.copytree(template, root, dirs_exist_ok=True)
        for directory in DIRS:
            (root / directory).mkdir(exist_ok=True)
            if not any((root / directory).iterdir()):
                (root / directory / '.gitkeep').touch()
        objective = args.description or 'Define the astronomy objective with the user.'
        (root/'PROJECT_DESCRIPTION.txt').write_text(objective + '\n', encoding='utf-8')
        for name in ('README.md', 'HANDOFF.md', 'developer/DEV_NOTES.md'):
            f = root / name
            f.write_text(f.read_text().replace('__PROJECT__', args.project).replace('__OBJECTIVE__', objective))
        rules = root / 'AGENTS.md'
        rules.write_text(rules.read_text().replace('TODO — specify the scientific task.', objective))
        # Compatibility pointer; there is only one authoritative rule set.
        (root / 'developer/AGENT_RULES.md').write_text('Read and follow ../AGENTS.md at the project root. Do not use the old boolean .agent_lock protocol.\n')
        (root / 'startup-prompt.txt').write_text('Continue this project from the directory containing this file. Read AGENTS.md and docs/CONTEXT_WORKFLOW.md. Acquire a fresh session lock, check context and read HANDOFF.md and recent developer/DEV_NOTES.md as required. Follow docs/DOCUMENTATION_RULES.md; generate manuals only on request. Ask for missing science requirements and perform the user-requested task. Do not recreate this project or copy Model_Project again.\n')
        (root / 'release-files.txt').write_text('version/VERSION\nversion/CHANGELOG.txt\nREADME.md\nPROJECT_DESCRIPTION.txt\nscript\ndocs\nlisence\njson\npipeline\nplot\nrelease-files.txt\n')
        write_updater(root)
        stamp = datetime.now().astimezone().isoformat()
        notes = root / 'developer/DEV_NOTES.md'
        with notes.open('a') as f:
            f.write(f'\n## {stamp}\n\nAgent / Environment\n- project-setup 1.5.0; computer {socket.gethostname()}; model not applicable.\n\nPrompt / Request\n- CLI scaffold request for {args.project}.\n\nObjective\n- {objective}\n\nChanges Made\n- Created agent-aware scaffold and standalone updater; initialized Git before copying files.\n\nVerification\n- Scaffold files written; application tests not run (no application yet).\n\nNotes\n- Initial creation; remote setup depends on explicit options.\n')
        lock_result = subprocess.run([sys.executable, str(root/'script/agent_lock.py'), 'acquire', '--agent', 'project-setup', '--agent-version', '1.5.0'], capture_output=True, text=True, check=True)
        session = json.loads(lock_result.stdout)['session_id']
        try:
            subprocess.run([sys.executable, str(root/'script/agent_context.py'), 'stamp', '--session', session], capture_output=True, text=True, check=True)
        finally:
            subprocess.run([sys.executable, str(root/'script/agent_lock.py'), 'release', '--session', session], capture_output=True, text=True, check=True)
        git(root, 'add', '--all')
        if git(root, 'var', 'GIT_AUTHOR_IDENT', check=False):
            commit(root, 'Initialize agent-aware project')
        else:
            print('Git initialized and files staged. Set repository-local git config user.name and user.email, then commit.')
        if args.remote or args.create_remote or args.git_push:
            ensure_remote(root, args.remote)
        if args.git_push:
            transfer(root, 'push', None, 'Initialize project')
    except (Error, OSError):
        setup_guidance(root, args.remote)
        raise
    # Outside the guidance block: a data failure must not print Git recovery steps.
    if plan:
        materialize_data(root, plan)
    print(f'Created: {root}')
    print(f'Next: ask your agent to read {root / "startup-prompt.txt"} and follow it.')
    if not git(root, 'remote', 'get-url', 'origin', check=False):
        print('No remote configured. Follow these steps:')
        print((root / 'docs/GIT_SETUP.txt').read_text())
    if args.json == '' and not plan:
        print_config_path(args)


def startup_guide():
    print("""project-setup 1.5.0 — agent-aware projects for macOS and Linux
1. Choose a project name, parent directory and astronomy objective.
2. Create it (no existing files are overwritten):
   project-setup --project NAME --proj-dir ~/Projects --objective "Describe the task"
   Or clone existing work: project-setup --from-git OWNER/REPO --proj-dir ~/Projects
   Description: --proj-description "Text" or --proj-description /path/description.txt
3. Ask any coding agent: Read /absolute/project/path/startup-prompt.txt and follow it.
4. The agent reads rules, acquires ownership, checks context and records development notes.
5. At handoff: finish notes, stamp handoff, commit, synchronize, then release ownership.
6. For remote setup: git-setup guide (or project-setup --git-setup guide).
7. For versions/releases: /absolute/project/path/script/project-update --help.
8. User manuals are generated only on an explicit external project-document request.
9. Data workspace: add --data-dir [FILE|PATH|name ...]; preview with --dry-run, inspect with --show.
No service or background agent is started. Python 3.9+ and Git 2.28+ are required.
""")


def setup_main():
    p = argparse.ArgumentParser(description='Create a portable project with Git and release tooling. For Git helpers: project-setup --git-setup [guide|configure|new|clone|update].')
    p.add_argument('--git-setup', nargs=argparse.REMAINDER, metavar='COMMAND',
                   help='Git helpers: guide, configure, new, clone, update. Example: project-setup --git-setup guide; put helper arguments after this option.')
    p.add_argument('--refresh', metavar='PROJECT', help='Prepare an AI migration of an existing project to this template; first copies it to PROJECT/PROJECT.org (asks permission above 100 MB)')
    p.add_argument('--ai', choices=['antigravity', 'chatgpt', 'claude', 'opencode', 'manual'], help='Refresh agent; interactive menu if omitted, manual for noninteractive use')
    p.add_argument('--ai-command', help='Refresh agent command containing {prompt_file}; optional {project_dir}, no shell. Default: PROJECT_SETUP_AI_COMMAND')
    p.add_argument('--project', help='New project name, or optional clone destination name')
    p.add_argument('--from-git', metavar='PROJECT', help='Clone NAME or OWNER/REPO without overlaying the template')
    p.add_argument('--proj-description', help='Description text or UTF-8/ASCII text-file path; @PATH explicitly selects a file')
    p.add_argument('--guide', action='store_true', help='Show numbered agent project setup instructions')
    p.add_argument('--objective', help='Scientific objective recorded in the new project')
    p.add_argument('--proj-dir', default='.')
    p.add_argument('--remote', help='Git remote URL to configure as origin')
    p.add_argument('--create-remote', action='store_true', help='Create a private GitHub repository if missing; defaults to authenticated account/PROJECT')
    p.add_argument('--git-push', action='store_true', help='Ensure remote exists, commit and push the new project')
    p.add_argument('--data-dir', nargs='*', metavar='PATH_OR_NAME',
                   help='Plan an external data workspace: no value uses the default root /Volumes/Work/Data; a single FILE lists directories (one line each or a JSON preset); one absolute PATH is the data root and the project directory is created inside it; other values are directory entries (use / for nesting). One root may be combined with one FILE or entries.')
    p.add_argument('--dry-run', action='store_true',
                   help='Preview everything project-setup would create (project, setup directories, data workspace and configuration paths) without writing anything; every path is reported as exists, will create or BLOCKED with the reason.')
    p.add_argument('--show', action='store_true',
                   help="Show an existing project's setup: version, setup directories, data workspace, JSON folder path and configuration path; makes no changes.")
    p.add_argument('--json', nargs='?', const='', metavar='PATH', default=None,
                   help='Path to the data configuration JSON file (or a directory containing data-path.json), inside the project; implies data workspace creation. Without a value, print the configuration file path.')
    args = p.parse_args()
    if args.git_setup is not None:
        from .gitsetup import main
        main(args.git_setup)
        return
    if args.guide or len(sys.argv) == 1:
        startup_guide()
        return
    if args.proj_description is not None and args.objective is not None:
        p.error('Use --proj-description or its older --objective alternative, not both.')
    if args.refresh and (args.project or args.from_git or args.remote or args.create_remote or args.git_push):
        p.error('--refresh is an existing-project mode; do not combine it with creation/cloning/remote options.')
    if (args.ai_command or args.ai) and not args.refresh:
        p.error('--ai/--ai-command require --refresh.')
    if args.ai_command and (args.ai is None or args.ai == 'manual'):
        p.error('--ai-command requires an explicit non-manual --ai selection.')
    if args.from_git and (args.create_remote or args.git_push):
        p.error('--from-git cannot create remotes or push during cloning.')
    json_value = args.json if isinstance(args.json, str) and args.json else None
    json_print = args.json == ''
    create_data = args.data_dir is not None or json_value is not None
    if args.show and args.dry_run:
        p.error('--show reports an existing project and --dry-run previews creation; use one.')
    if args.show and (args.from_git or args.refresh or args.remote or args.create_remote or args.git_push
                      or args.proj_description is not None or args.objective is not None or args.data_dir is not None):
        p.error('--show is read-only; run it alone against an existing project.')
    if args.dry_run and (args.from_git or args.refresh):
        p.error('--dry-run previews --project creation; cloning and refresh are not previewed.')
    if create_data and (args.from_git or args.refresh):
        p.error('--data-dir workspace creation requires --project mode; configure data after cloning or refreshing.')
    if args.dry_run and not args.project:
        p.error('--dry-run previews creation; supply --project NAME.')
    if not args.project and not args.from_git and not args.refresh and not (args.show or args.dry_run or json_print):
        p.error('--project or --from-git is required; run without arguments for the guide')
    if args.show:
        run(lambda: show_setup(args))
        return
    if args.dry_run:
        run(lambda: dry_run_setup(args))
        return
    creation_intent = (args.proj_description is not None or args.objective is not None or args.remote
                       or args.create_remote or args.git_push or create_data)
    if json_print and args.project and not args.refresh and not args.from_git and not creation_intent \
            and (Path(args.proj_dir).expanduser().resolve() / args.project).is_dir():
        # --json alone on an existing project reports the configuration path.
        run(lambda: print_config_path(args))
        return
    if json_print and not args.project and not args.from_git and not args.refresh:
        run(lambda: print_config_path(args))
        return
    def create():
        args.description = read_description(args.proj_description if args.proj_description is not None else args.objective)
        if args.refresh:
            from .refresh import refresh_project
            refresh_project(args)
            if json_print:
                print_config_path(args)
        elif args.from_git:
            clone_project(args)
            if json_print:
                print_config_path(args)
        else:
            scaffold(args)
    run(create)

def manage_lock(project: Path, action: str, session: str | None,
                agent: str, agent_version: str) -> None:
    """Manage the same cooperative lock used by agent_lock.py."""
    lock = project / '.agent-state/lock'
    owner_file = lock / 'owner.json'
    if action in ('acquire', 'aquire'):
        if session:
            raise Error('Acquire creates a fresh session; do not supply --session.')
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock.mkdir()
        except FileExistsError:
            raise Error('Project is already locked. Inspect with --lock status; do not overwrite ownership.')
        owner = {'agent': agent, 'agent_version': agent_version,
                 'session_id': str(uuid.uuid4()), 'host': socket.gethostname(),
                 'started_utc': datetime.now(timezone.utc).isoformat(),
                 'project': str(project.resolve())}
        # Retain the directory on interrupted/failed metadata writes (fail closed).
        with owner_file.open('x') as handle:
            json.dump(owner, handle, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        print(json.dumps(owner, indent=2))
        return
    if not lock.exists():
        print('UNLOCKED')
        return
    try:
        owner = json.loads(owner_file.read_text())
        if not isinstance(owner, dict) or not owner.get('session_id') or not owner.get('host'):
            raise ValueError('Incomplete metadata')
    except (OSError, ValueError):
        raise Error('Lock metadata unavailable/corrupt. Stop all writers and use the documented manual recovery; no lock removed.')
    if action == 'status':
        print(json.dumps(owner, indent=2))
        return
    if owner['host'] != socket.gethostname():
        raise Error('Lock belongs to another computer: ' + str(owner['host']) + '. Release there after stopping its writer; no lock removed.')
    if session:
        if owner['session_id'] != session:
            raise Error('Session mismatch; no lock removed.')
    else:
        print(json.dumps(owner, indent=2))
        if not sys.stdin.isatty():
            raise Error('Noninteractive release requires --session OWNER_SESSION_ID. Stop the owning writer first.')
        answer = input('Stop the owning agent and its modifying tasks first. Type release to unlock: ')
        if answer.strip() != 'release':
            raise Error('Release cancelled; lock retained.')
    # Confirm metadata still matches what was displayed/approved.
    try:
        current = json.loads(owner_file.read_text())
    except (OSError, ValueError):
        raise Error('Ownership metadata changed during release; no lock removed.')
    if current != owner:
        raise Error('Ownership changed during release; no lock removed.')
    owner_file.unlink()
    lock.rmdir()
    print('RELEASED')


def update_summary(action: str, result: str) -> None:
    """Two terminal lines; keep structured stdout usable by scripts."""
    sys.stdout.flush()
    print('Action: ' + ' '.join(action.split()), file=sys.stderr)
    print('Result: ' + ' '.join(result.split()), file=sys.stderr)


class UpdateParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        update_summary('Show project-update help' if status == 0 else 'Validate project-update arguments',
                       'Help displayed; no operations run.' if status == 0 else 'FAILED: invalid arguments; no operations run.')
        raise SystemExit(status)


def update_main(root=None):
    p = UpdateParser(description='Update version, release, and synchronize Git, in that order (pull runs first).')
    p.add_argument('--version', nargs='?', const='minor')
    p.add_argument('--release', action='store_true')
    p.add_argument('--lock', choices=['acquire', 'aquire', 'release', 'status'], help='Manage project ownership; aquire is an alias for acquire')
    p.add_argument('--agent', default='manual', help='Owner label for --lock acquire')
    p.add_argument('--agent-version', default='unknown', help='Owner application version for --lock acquire')
    p.add_argument('--session', help='Owner session ID required when an agent lock is active')
    p.add_argument('--git-push', nargs='?', const='')
    p.add_argument('--git-pull', nargs='?', const='')
    p.add_argument('--massage', '--message', dest='message', nargs='?', const=None)
    args = p.parse_args()
    requested = []
    if args.lock: requested.append('lock ' + ('acquire' if args.lock == 'aquire' else args.lock))
    if args.git_pull is not None: requested.append('Git pull ' + (args.git_pull or 'current branch'))
    if args.version is not None: requested.append('version ' + args.version)
    if args.release: requested.append('create release archive')
    if args.git_push is not None: requested.append('Git push ' + (args.git_push or 'current branch'))
    action = '; '.join(requested) or 'Show project-update help'
    completed = []
    def work():
        if not requested:
            p.print_help()
            completed.append('Help displayed; no operations run')
            return
        project = root or Path(git(Path.cwd(), 'rev-parse', '--show-toplevel'))
        if args.lock:
            if args.version is not None or args.release or args.git_push is not None or args.git_pull is not None:
                raise Error('--lock must run separately from version, release or Git operations.')
            existed = (project / '.agent-state/lock').exists()
            manage_lock(project, args.lock, args.session, args.agent, args.agent_version)
            if args.lock in ('acquire', 'aquire'):
                completed.append('Lock acquired; ownership details and session ID printed above')
            elif args.lock == 'release':
                completed.append('Lock released' if existed else 'Already unlocked; nothing changed')
            else:
                completed.append('Project is locked; owner details printed above' if existed else 'Project is unlocked')
            return
        if args.git_pull == 'show' or args.git_push == 'show':
            if args.version is not None or args.release or (args.git_pull not in (None, 'show')) or (args.git_push not in (None, 'show')):
                raise Error('show cannot be combined with modifying operations.')
            print(git(project, 'branch', '--all'))
            completed.append('Listed known branches; no files or remote refs changed')
            return
        lock = project / '.agent-state/lock'
        if lock.exists():
            try:
                owner = json.loads((lock / 'owner.json').read_text())
                if not isinstance(owner, dict): raise ValueError('Invalid metadata')
            except (OSError, ValueError):
                raise Error('Lock metadata unavailable; recover ownership before updating.')
            if owner.get('session_id') != args.session or owner.get('host') != socket.gethostname():
                raise Error('Active agent lock: supply the owning --session on the same computer.')
        message = args.message if args.message is not None else datetime.now().strftime('%d:%m:%y|%H-%M-%S')
        if args.git_pull is not None:
            transfer(project, 'pull', args.git_pull, message)
            completed.append('Fetched tag ' + args.git_pull if VERSION_RE.fullmatch(args.git_pull or '') else 'Fast-forward pull completed for ' + (args.git_pull or current_branch(project)))
        version = validate(version_path(project).read_text().splitlines()[0]) if args.version is not None or args.release else None
        if args.version is not None:
            before = version
            version = next_version(version, args.version)
            write_version(project, version)
            print(f'Version: {version}')
            completed.append('Version unchanged at ' + version if before == version else 'Version ' + before + ' -> ' + version)
        if args.release:
            release(project, version, message)
            destination = project/'version/dist' if (project/'version/VERSION').is_file() else project/'versions'
            completed.append('Archive created: ' + str(destination/(project.name+'-'+version+'.tar.gz')))
        if args.git_push is not None:
            transfer(project, 'push', args.git_push, message)
            completed.append('Pushed tag v' + args.git_push if VERSION_RE.fullmatch(args.git_push or '') else 'Pushed branch ' + (args.git_push or current_branch(project)) + ' to origin')
    try:
        work()
    except (Error, OSError, ValueError, IndexError, EOFError, subprocess.CalledProcessError) as exc:
        progress = '; '.join(completed) if completed else 'No operation confirmed complete'
        update_summary(action, 'FAILED: ' + str(exc) + ' Completed: ' + progress + '. Earlier local changes may remain; inspect state before retrying.')
        raise SystemExit(1)
    update_summary(action, '; '.join(completed) + '.')


def run(action):
    try:
        action()
    except (Error, OSError, IndexError, subprocess.CalledProcessError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
