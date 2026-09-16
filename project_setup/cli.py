"""Portable project scaffolding and release management; Python 3.9+."""
import argparse
from datetime import datetime
import fnmatch
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

VERSION_RE = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]?)\.(0|[1-9][0-9]?)\Z')
DIRS = ('script', 'docs', 'data', 'versions', 'developer', 'testdirectory')
IGNORE = '.git/\nversions/*\n!versions/.gitkeep\n__pycache__/\n*.py[cod]\n.venv/\nbuild/\ndist/\n*.egg-info/\n.DS_Store\n.env\n.env.*\n'
RULES = '''# Agent rules
Load this file once at the start of each conversation/session. Retain its rules
in context; reload only when this file changes or context is lost.

- Read DEV_NOTES.md before changing the project; record decisions and validation.
- Preserve user files. Never overwrite existing projects, rewrite Git history,
  force push, discard changes, or expose credentials.
- Keep executable tools in script/, documentation in docs/, and tests in testdirectory/.
- Use script/project-update for version history and release operations.
- Maintain release-files.txt as an explicit list of distributable paths.
- Run relevant tests and report limitations honestly.
'''
NOTES = '''# Developer notes

## Purpose and scope
Describe the project goal and intended users.

## Current state
- Version: see ../VERSION (first line).
- Working features:
- Known limitations:

## Architecture and entry points
Describe modules, commands, dependencies, and data flow.

## Decisions
| Date | Decision | Reason |
| --- | --- | --- |

## Validation
Record commands, results, platform, and date.

## Next steps
List concrete remaining work and blockers.

## Session handoff
Summarize changes, files touched, and unresolved questions after each session.
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
        git(root, 'show-ref', '--verify', f'refs/heads/{branch}')
        if branch == current_branch(root):
            commit(root, message)
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
    (root / 'developer/DEV_NOTES.md').write_text(NOTES)
    (root / 'developer/AGENT_RULES.md').write_text(RULES)
    (root / 'README.md').write_text(f'# {args.project}\n\nDescribe installation and usage here.\n')
    (root / 'release-files.txt').write_text('VERSION\nREADME.md\nscript\ndocs\ndata\nrelease-files.txt\n')
    updater = root / 'script/project-update'
    updater.write_text('#!/usr/bin/env python3\n' + Path(__file__).read_text() + '\nif __name__ == "__main__":\n    update_main(root=Path(__file__).resolve().parent.parent)\n')
    updater.chmod(0o755)
    git(root, 'init', '-b', 'main')
    git(root, 'add', '--all')
    if git(root, 'var', 'GIT_AUTHOR_IDENT', check=False):
        commit(root, 'Initialize project')
    else:
        print('Git initialized and files staged. Configure Git user.name/user.email to commit.')
    if args.remote:
        git(root, 'remote', 'add', 'origin', args.remote)
    if args.git_push:
        transfer(root, 'push', None, 'Initialize project')
    print(f'Created: {root}')

def setup_main():
    p = argparse.ArgumentParser(description='Create a portable project with Git and release tooling.')
    p.add_argument('--project', required=True)
    p.add_argument('--proj-dir', default='.')
    p.add_argument('--remote', help='Git remote URL to configure as origin')
    p.add_argument('--git-push', action='store_true', help='Commit and push the new project (requires --remote)')
    args = p.parse_args()
    if args.git_push and not args.remote:
        p.error('--git-push requires --remote')
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
