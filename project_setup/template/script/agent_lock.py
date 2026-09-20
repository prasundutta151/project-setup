#!/usr/bin/env python3
"""Cooperative checkout lock. Python 3 standard library; macOS and Linux."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys
from datetime import datetime, timezone
import uuid

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / '.agent-state' / 'lock'
OWNER = LOCK / 'owner.json'


def read_owner():
    try:
        return json.loads(OWNER.read_text())
    except (OSError, ValueError):
        return None


def fail(message):
    print(message, file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    acquire = commands.add_parser('acquire')
    acquire.add_argument('--agent', required=True)
    acquire.add_argument('--agent-version', default='unknown')
    commands.add_parser('status')
    for name in ('check', 'release'):
        sub = commands.add_parser(name)
        sub.add_argument('--session', required=True)
    args = parser.parse_args()

    if args.command == 'acquire':
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        try:
            LOCK.mkdir()  # Atomic on a local filesystem; only one caller wins.
        except FileExistsError:
            return fail('LOCKED: ' + json.dumps(read_owner() or {
                'state': 'Owner metadata unavailable; do not remove automatically.'}))
        owner = {
            'agent': args.agent,
            'agent_version': args.agent_version,
            'session_id': str(uuid.uuid4()),
            'host': socket.gethostname(),
            'started_utc': datetime.now(timezone.utc).isoformat(),
            'project': str(ROOT),
        }
        # If interrupted here, retain the directory and fail closed.
        try:
            with OWNER.open('x') as handle:
                json.dump(owner, handle, indent=2)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            return fail(f'Lock directory retained; metadata write failed: {exc}')
        print(json.dumps(owner, indent=2))
        return 0

    if not LOCK.exists():
        if args.command == 'status':
            print('UNLOCKED')
            return 0
        return fail('No active lock; ownership cannot be confirmed.')
    owner = read_owner()
    if args.command == 'status':
        print(json.dumps(owner or {'state': 'LOCKED; owner metadata unavailable'}, indent=2))
        return 0
    if not owner or owner.get('session_id') != args.session or owner.get('host') != socket.gethostname():
        return fail('Ownership mismatch or missing metadata; no changes made.')
    if args.command == 'check':
        print('OWNED by this session')
        return 0
    # Only the cooperative owner should release. Do not use recursive deletion.
    try:
        OWNER.unlink()
        LOCK.rmdir()
    except OSError as exc:
        return fail(f'Release incomplete; inspect lock state: {exc}')
    print('RELEASED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
