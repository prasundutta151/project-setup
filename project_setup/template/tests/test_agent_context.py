"""Integration checks use disposable repos and isolated HOME caches."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project with spaces'
        (self.root / 'script').mkdir(parents=True)
        for name in ('agent_lock.py', 'agent_context.py'):
            shutil.copy2(SOURCE / 'script' / name, self.root / 'script' / name)
        self.env = dict(os.environ, HOME=str(Path(self.tmp.name) / 'home'),
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        self.run_cmd('git', 'init', '-b', 'main')
        self.run_cmd('git', 'config', 'user.name', 'Test')
        self.run_cmd('git', 'config', 'user.email', 'test@example.invalid')
        (self.root / '.gitignore').write_text('.agent-state/\n')
        (self.root / 'HANDOFF.md').write_text('# Handoff\nActual summary.\n')
        (self.root / 'code.py').write_text('one\n')
        self.run_cmd('git', 'add', '.')
        self.run_cmd('git', 'commit', '-m', 'initial')
        self.session = json.loads(self.lock('acquire', '--agent', 'test', '--agent-version', '1').stdout)['session_id']

    def run_cmd(self, *args):
        r = subprocess.run(args, cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def lock(self, *args):
        return self.run_cmd(sys.executable, 'script/agent_lock.py', *args)

    def context(self, command, expected=0, *extra):
        r = subprocess.run([sys.executable, 'script/agent_context.py', command,
                            '--session', self.session, *extra], cwd=self.root,
                           env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, expected, r.stderr + r.stdout)
        return r

    def acknowledge(self):
        state = json.loads(self.context('check', 2).stdout)
        self.context('ack', 0, '--fingerprint', state['fingerprint'])
        return state

    def test_new_changed_same_dirty_and_new_session(self):
        state = self.acknowledge()
        self.assertFalse(Path(state['cache']).is_relative_to(self.root))
        self.context('check')
        (self.root / 'code.py').write_text('two\n')
        self.acknowledge()
        before = self.run_cmd('git', 'status', '--porcelain').stdout
        (self.root / 'code.py').write_text('six\n')
        self.assertEqual(before, self.run_cmd('git', 'status', '--porcelain').stdout)
        self.acknowledge()  # Same status, different bytes must invalidate.
        self.lock('release', '--session', self.session)
        self.session = json.loads(self.lock('acquire', '--agent', 'test').stdout)['session_id']
        self.context('check', 2)

    def test_race_untracked_branch_index_and_cache_corruption(self):
        state = json.loads(self.context('check', 2).stdout)
        (self.root / 'new.txt').write_text('untracked')
        self.context('ack', 1, '--fingerprint', state['fingerprint'])
        state = self.acknowledge()
        self.run_cmd('git', 'add', 'new.txt')
        self.acknowledge()
        self.run_cmd('git', 'checkout', '-b', 'other')
        state = self.acknowledge()
        Path(state['cache']).write_text('broken json')
        self.context('check', 2)
        Path(state['cache']).write_text('[]')
        self.context('check', 2)

    def test_stamping_and_foreign_owner(self):
        first = json.loads(self.context('stamp').stdout)
        second = json.loads(self.context('stamp').stdout)
        self.assertNotEqual(first['handoff_id'], second['handoff_id'])
        self.assertEqual(second['agent_version'], '1')
        body = (self.root / 'HANDOFF.md').read_text()
        self.assertEqual(body.count('<!-- agent-handoff:start -->'), 1)
        self.assertIn('Actual summary.', body)
        f = self.root / '.agent-state/lock/owner.json'
        owner = json.loads(f.read_text()); owner['host'] = 'different-machine'
        f.write_text(json.dumps(owner))
        self.context('check', 1)
        r = subprocess.run([sys.executable, 'script/agent_lock.py', 'release', '--session', self.session], cwd=self.root, env=self.env, capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(f.exists())


if __name__ == '__main__':
    unittest.main()
