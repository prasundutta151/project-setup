"""Prepare a reviewed migration prompt; optionally invoke a configured AI agent."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile

from .cli import Error, git, manage_lock

REQUIRED_DIRS = ('script', 'version', 'docs', 'pipeline', 'json', 'plot', 'developer', 'tests')
REQUIRED_FILES = ('AGENTS.md', 'HANDOFF.md', 'PROJECT_DESCRIPTION.txt',
                  'startup-prompt.txt', 'documentation-prompt.txt',
                  'developer/DEV_NOTES.md', 'script/project-update',
                  'script/agent_lock.py', 'script/agent_context.py',
                  'version/VERSION', 'version/CHANGELOG.txt', 'release-files.txt')

BACKUP_LIMIT_BYTES = 100 * 1024 * 1024
PARTIAL_SUFFIX = '.partial'


def _backup_size(root: Path, skip: Path) -> int:
    """Total file size under root, ignoring an existing/pre-existing backup directory."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if Path(dirpath, name) != skip]
        for name in filenames:
            try:
                total += (Path(dirpath) / name).lstat().st_size
            except OSError:
                continue
    return total


def _make_backup(root: Path) -> Path:
    """Copy the untouched project to <name>.org before refresh edits it."""
    backup = root / (root.name + '.org')
    if backup.is_dir():
        print('Pre-refresh backup already exists at ' + str(backup)
              + '; it is kept unchanged. Delete it first if you want a fresh copy.')
        return backup
    if backup.exists():
        raise Error('Backup target exists and is not a directory: ' + str(backup))
    partial = root / (root.name + '.org' + PARTIAL_SUFFIX)
    if partial.exists():
        print('Removing stale partial backup from an interrupted copy: ' + str(partial))
        shutil.rmtree(partial) if partial.is_dir() else partial.unlink()
    size = _backup_size(root, backup)
    if size > BACKUP_LIMIT_BYTES:
        print('WARNING: project size %.1f MB exceeds the %d MB pre-refresh backup limit.'
              % (size / (1024 * 1024), BACKUP_LIMIT_BYTES // (1024 * 1024)))
        if not sys.stdin.isatty():
            raise Error('The project is too large to back up without confirmation; '
                        're-run in a terminal to approve copying it to ' + backup.name + '.')
        if input('Copy the whole project to ' + backup.name + ' anyway? [y/N]: ').strip().lower() not in ('y', 'yes'):
            raise Error('Backup declined; refresh stopped before changing any project files.')
    try:
        # Copy to a temporary sibling first so an interrupted run never leaves a
        # directory that later refreshes would mistake for a complete backup.
        shutil.copytree(root, partial, symlinks=True,
                        ignore=shutil.ignore_patterns(backup.name, partial.name))
        partial.rename(backup)
    except BaseException:
        if partial.exists():
            shutil.rmtree(partial, ignore_errors=True)
        raise
    exclude = root / '.git' / 'info' / 'exclude'
    if exclude.parent.is_dir():
        entry = backup.name + '/'
        lines = exclude.read_text().splitlines() if exclude.is_file() else []
        if entry not in [line.strip() for line in lines]:
            exclude.write_text('\n'.join(lines + [entry]) + '\n')
    print('Pre-refresh backup created at: ' + str(backup))
    return backup


def refresh_project(args) -> None:
    import re
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.refresh):
        raise Error('--refresh expects one project directory name.')
    root = (Path(args.proj_dir).expanduser().resolve() / args.refresh).resolve()
    if not root.is_dir():
        raise Error('Existing project directory not found: ' + str(root))
    template = Path(__file__).resolve().parent / 'template'
    if not template.is_dir():
        raise Error('Bundled template missing; reinstall project-setup.')
    cache = Path.home() / ('Library/Caches' if sys.platform == 'darwin' else '.cache') / 'project-setup/refresh'
    cache.mkdir(parents=True, exist_ok=True)
    packet = Path(tempfile.mkdtemp(prefix='migration-', dir=str(cache)))
    top = git(root, 'rev-parse', '--show-toplevel', check=False)
    is_repo = bool(top) and Path(top).resolve() == root
    head = git(root, 'rev-parse', '--verify', 'HEAD', check=False) if is_repo else ''
    selected = args.ai
    if selected is None and sys.stdin.isatty():
        options = ['antigravity', 'chatgpt', 'claude', 'opencode', 'manual']
        print('Choose the AI for refresh:')
        for index, name in enumerate(options, 1): print(f'{index}. {name}')
        answer = input('Selection [5: manual]: ').strip().lower() or '5'
        selected = options[int(answer)-1] if answer in ('1','2','3','4','5') else answer
        if selected not in options: raise Error('Unknown AI selection.')
    selected = selected or 'manual'
    command = args.ai_command or os.environ.get('PROJECT_SETUP_AI_COMMAND_' + selected.upper()) or os.environ.get('PROJECT_SETUP_AI_COMMAND')
    if selected == 'manual': command = None
    metadata = {'project': str(root), 'template': str(template), 'initial_commit': head,
                'git_repository': is_repo, 'template_version': '1.5.0',
                'backup': str(root / (root.name + '.org')),
                'description_override': args.description, 'selected_ai': selected}
    (packet/'request.json').write_text(json.dumps(metadata, indent=2)+'\n')
    prompt = packet/'refresh-prompt.txt'
    prompt.write_text(f'''REFRESH AN EXISTING PROJECT — APPLY A REVIEWED MIGRATION

Project: {root}
Reference template: {template}
Request metadata (description override if supplied): {packet / 'request.json'}
Initial Git checkpoint: {head or 'none'}
Pre-refresh backup: {root / (root.name + '.org')}

This is the user's request to adapt this existing project to the current
project-setup format using your reasoning and editing tools. Do not just summarize
this prompt. Preserve its scientific behavior, existing history and user data.
Read the existing project instructions, README, description, current handoff and
recent developer notes before reading the reference template's AGENTS.md and
requirements. An existing project may contain different languages/build systems.
Resolve routine implementation choices within this request; ask only about real
conflicts, missing scientific decisions or actions outside this migration scope.

OWNERSHIP AND CHECKPOINT
If PROJECT_SETUP_REFRESH_SESSION is set, this launcher already owns the local
.agent-state/lock. Confirm its session ID and host; use that session for edits and
updater commands, do not reacquire or release it (the launcher releases it).
Otherwise follow this project's existing lock protocol, or the reference helper
if no protocol exists. Never remove a foreign lock. Before substantive edits,
ensure this project has its own Git repo and a reviewed baseline commit. Preserve
pre-existing modifications; if no safe baseline can be made, report the blocker.
Never push, publish, change a remote/license, or alter repository history.

PRE-REFRESH BACKUP
A complete copy of this project as it stood before this refresh exists at the
backup path above. Treat it as strictly read-only user rollback material: never
edit, migrate, map, package (release-files.txt), git add/commit, or delete it,
and keep it out of every migration mapping and validation run.

MIGRATION, NOT BLIND COPY
1. Inspect the actual layout and record a before/after mapping and migration plan
   in developer/REFRESH_REPORT.md. Compare against the bundled reference files.
2. Preserve custom AGENTS rules and all developer history. Merge project-specific
   rules with the shared workflows; do not replace the project's science rules or
   copy the template's developer history, descriptions, UUIDs or cache.
3. Establish script/, version/, docs/, pipeline/, json/, plot/, developer/, tests/.
   Prefer compatibility launchers/links and documented adapters over breaking
   existing command names/imports/data paths. Do not bulk-copy data, delete old
   directories, or move observations merely to match a diagram.
4. Move legacy root VERSION into version/VERSION preserving its entire history.
   On case-insensitive macOS, root VERSION collides with directory version: move
   through a temporary unique filename before creating version/. Retain existing
   release archives and update paths/references safely. Do not reset to 0.1.0.
   If no version exists, infer only from authoritative metadata or ask the user.
5. Adapt the current lock/context helpers, standalone project-update, startup and
   documentation prompts, release allowlist and Git ignore rules. Preserve
   existing dependency/build tooling and unrelated ignore patterns. Ensure new
   lock state, caches, environments and large generated outputs are not committed.
6. Write/retain PROJECT_DESCRIPTION.txt, using the explicit override if supplied;
   preserve history and reflect changed project facts in README/AGENTS/handoff.
   Maintain executable entry points and correct resource resolution. Check existing
   CLI flags before adding setup/parameter JSON support: maintain backward
   compatibility and record any migration needing user scientific decisions.
7. Add the on-demand documentation contract; do not regenerate user manuals unless
   separately asked. Do not change LICENSE, NOTICE, copyright or author attribution.

VALIDATE AND HAND OFF
Run relevant existing tests plus configuration/path/CLI checks affected by the
migration. Run helper tests and check installed command behavior from outside
the project where applicable. Update developer/DEV_NOTES.md with actual request,
objective, agent/model when known, host, changes and test outcomes. Update HANDOFF
with a fresh ID and current state; never pretend unseen tests passed. Complete
REFRESH_REPORT.md with changes, compatibility choices, tests, preserved items and
remaining blockers. Leave changes reviewable and UNCOMMITTED for the user. Stop
all modifying/background tasks before returning. Do not erase work if validation
fails. Release your lock only if you acquired it yourself, not a launcher session.
''')
    print('Refresh prompt: ' + str(prompt))
    if not command:
        _make_backup(root)
        print(f'PREPARED ONLY for {selected}: no project files changed except the {root.name}.org backup.')
        print('Copy the following prompt into your chosen agent (give it access to the referenced project/template files):')
        print(prompt.read_text())
        if selected != 'manual':
            print('No automatic command configured. Use --ai-command or PROJECT_SETUP_AI_COMMAND_' + selected.upper() + '; see docs/refresh.md.')
        return
    if not is_repo or not head:
        raise Error('Automatic refresh needs this project to have its own Git repository and baseline commit. Prompt retained for your agent.')
    if git(root, 'status', '--porcelain'):
        raise Error('Automatic refresh needs a clean working tree. Preserve/checkpoint existing changes first; prompt retained.')
    legacy = root/'.agent_lock'
    if legacy.exists() and legacy.read_text().strip() != 'True':
        raise Error('Legacy agent lock is busy or unknown. Stop its owner before automatic refresh.')
    argv = shlex.split(command)
    if not argv:
        raise Error('AI command is empty.')
    # Require the caller to specify how their agent consumes a prompt; no guessed CLI.
    if not any('{prompt_file}' in part for part in argv):
        raise Error('--ai-command must include {prompt_file}; tokens may also use {project_dir}. No shell is invoked.')
    argv = [part.replace('{prompt_file}', str(prompt)).replace('{project_dir}', str(root)) for part in argv]
    _make_backup(root)
    origin = git(root, 'remote', '-v')
    manage_lock(root, 'acquire', None, 'project-setup-refresh', '1.5.0')
    owner_path = root/'.agent-state/lock/owner.json'
    owner = json.loads(owner_path.read_text())
    env = dict(os.environ, PROJECT_SETUP_REFRESH_SESSION=owner['session_id'],
               PROJECT_SETUP_REFRESH_PROMPT=str(prompt))
    try:
        result = subprocess.run(argv, cwd=root, env=env)
        if result.returncode:
            raise Error('AI command failed; inspect retained changes and prompt. No automatic rollback performed.')
        current = json.loads(owner_path.read_text())
        if current != owner or current['host'] != socket.gethostname():
            raise Error('Ownership changed during refresh; inspect the project manually.')
        missing = [x for x in REQUIRED_DIRS if not (root/x).is_dir()]
        missing += [x for x in REQUIRED_FILES if not (root/x).is_file()]
        if not (root/'developer/REFRESH_REPORT.md').is_file(): missing.append('developer/REFRESH_REPORT.md')
        if missing:
            raise Error('AI exited, but required migration outputs are missing: ' + ', '.join(missing))
        if git(root, 'remote', '-v') != origin or git(root, 'rev-parse', 'HEAD') != head:
            raise Error('AI changed Git remote/history despite instructions; inspect before continuing.')
        print('AI RUN FINISHED: required files found. Review developer/REFRESH_REPORT.md, tests and git diff before committing.')
        print('Structural checks do not prove scientific correctness or full migration completeness.')
    finally:
        # Never delete a replacement owner's lock, even on failure.
        if owner_path.is_file():
            try:
                current = json.loads(owner_path.read_text())
                if current == owner:
                    manage_lock(root, 'release', owner['session_id'], owner['agent'], owner['agent_version'])
            except (OSError, ValueError, Error):
                print('Lock recovery requires inspection; ownership metadata could not be verified.', file=sys.stderr)
