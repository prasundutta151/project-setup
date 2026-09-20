#!/usr/bin/env python3
"""Session context detection and attributed handoffs; Python 3 standard library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- agent-handoff:start -->'
END = '<!-- agent-handoff:end -->'


def git(*args, optional=False):
    r = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True)
    if r.returncode and not optional:
        raise ValueError(r.stderr.decode(errors='replace').strip())
    return r.stdout if not r.returncode else b''


def owner(session):
    value = json.loads((ROOT / '.agent-state/lock/owner.json').read_text())
    if value.get('session_id') != session or value.get('host') != socket.gethostname():
        raise ValueError('Session or computer does not own this local lock.')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot():
    if Path(os.fsdecode(git('rev-parse', '--show-toplevel')).strip()).resolve() != ROOT:
        raise ValueError('Initialize this project as its own Git repository first.')
    names = set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0'))
    files = {}
    for raw in sorted(names - {b''}):
        name = os.fsdecode(raw)
        if name.startswith('.agent-state/'):
            continue
        path = ROOT / name
        if path.is_symlink():
            files[name] = 'link:' + digest(os.fsencode(os.readlink(path)))
        elif path.is_file():
            h = hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
            files[name] = f'{path.stat().st_mode & 0o111}:{h.hexdigest()}'
        elif path.is_dir():
            raise ValueError('Nested repository/submodule needs explicit review: ' + name)
        else:
            files[name] = 'missing'
    state = {
        'head': git('rev-parse', '--verify', 'HEAD', optional=True).decode().strip(),
        'branch': git('symbolic-ref', '--short', 'HEAD', optional=True).decode().strip(),
        'status': digest(git('status', '--porcelain=v1', '-z', '--untracked-files=all')),
        'index': digest(git('ls-files', '--stage', '-z')),
        'files': files,
    }
    state['fingerprint'] = digest(json.dumps(state, sort_keys=True).encode())
    return state


def cache_path(session):
    # Deliberately do not honor a potentially synchronized XDG_CACHE_HOME.
    base = Path.home() / ('Library/Caches' if sys.platform == 'darwin' else '.cache')
    key = digest((socket.gethostname() + '\0' + str(ROOT) + '\0' + session).encode())
    return base / 'astronomy-agent-context' / (key + '.json')


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('check', 'ack', 'stamp'):
        s = sub.add_parser(name)
        s.add_argument('--session', required=True)
        if name == 'ack':
            s.add_argument('--fingerprint', required=True)
    a = p.parse_args()
    who = owner(a.session)
    if a.command == 'stamp':
        f = ROOT / 'HANDOFF.md'
        body = f.read_text()
        if BEGIN in body or END in body:
            if body.count(BEGIN) != 1 or body.count(END) != 1 or body.index(END) < body.index(BEGIN):
                raise ValueError('Malformed handoff metadata; preserve and fix it manually.')
            start, tail = body.split(BEGIN, 1)
            _, tail = tail.split(END, 1)
            body = start + tail.lstrip('\n')
        meta = {'handoff_id': str(uuid.uuid4()),
                'updated_utc': datetime.now(timezone.utc).isoformat(),
                'computer': who['host'], 'agent': who['agent'],
                'agent_version': who.get('agent_version', 'unknown'),
                'session_id': a.session,
                'base_commit': git('rev-parse', '--verify', 'HEAD', optional=True).decode().strip() or 'unborn',
                'branch': git('symbolic-ref', '--short', 'HEAD', optional=True).decode().strip()}
        f.write_text(BEGIN + '\n```json\n' + json.dumps(meta, indent=2) + '\n```\n' + END + '\n\n' + body)
        print(json.dumps(meta, indent=2))
        return 0
    state = snapshot()
    path = cache_path(a.session)
    if a.command == 'ack':
        if state['fingerprint'] != a.fingerprint:
            raise ValueError('Project changed since check. Review it again before acknowledgement.')
        atomic_json(path, state)
        print('ACKNOWLEDGED: ' + str(path))
        return 0
    try:
        previous = json.loads(path.read_text())
        if not isinstance(previous, dict) or not isinstance(previous.get('files'), dict):
            previous = {}
    except (OSError, ValueError):
        previous = {}
    same = previous.get('fingerprint') == state['fingerprint']
    changed = sorted(k for k in set(previous.get('files', {})) | set(state['files'])
                     if previous.get('files', {}).get(k) != state['files'].get(k))
    print(json.dumps({'context': 'UNCHANGED' if same else 'RELOAD_REQUIRED',
                      'reason': 'same session and state' if same else ('new session/cache unavailable' if not previous else 'project state changed'),
                      'fingerprint': state['fingerprint'], 'head': state['head'],
                      'branch': state['branch'], 'changed_files': changed,
                      'cache': str(path),
                      'notice': 'Not a synchronization-completion or distributed-lock guarantee.'}, indent=2))
    return 0 if same else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
