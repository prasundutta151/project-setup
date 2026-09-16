import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io

from project_setup import cli

class Versions(unittest.TestCase):
    def test_rollovers(self):
        for start, action, expected in [('0.0.1','minor','0.0.2'),('0.0.99','minor','0.1.0'),('0.99.99','minor','1.0.0'),('2.99.4','middle','3.0.0'),('2.3.4','middle','2.4.0'),('2.3.4','major','3.0.0'),('1.2.3','4.5.6','4.5.6')]:
            self.assertEqual(cli.next_version(start, action), expected)
    def test_invalid(self):
        for value in ['../evil', '01.2.3', '1.100.0', '1.2', '-1.0.0', '1.2.3\n']:
            with self.assertRaises(cli.Error): cli.validate(value)

class RemoteCreation(unittest.TestCase):
    @patch.object(cli, 'git')
    @patch.object(cli, 'github')
    def test_missing_remote_created_private(self, gh, git):
        gh.side_effect = ['alice', '', cli.Error('not found'), '']
        cli.ensure_remote(Path('/tmp/demo'), None)
        self.assertIn(unittest.mock.call(Path('/tmp/demo'), 'repo', 'create', 'alice/demo', '--private'), gh.call_args_list)
        git.assert_called_once_with(Path('/tmp/demo'), 'remote', 'add', 'origin', 'https://github.com/alice/demo.git')
    @patch.object(cli, 'git')
    @patch.object(cli, 'github')
    def test_existing_remote_not_created(self, gh, git):
        cli.ensure_remote(Path('/tmp/demo'), 'git@github.com:alice/existing.git')
        self.assertFalse(any('create' in c.args for c in gh.call_args_list))
        gh.assert_any_call(Path('/tmp/demo'), 'repo', 'view', 'alice/existing', '--json', 'name')
    @patch.object(cli, 'git')
    @patch.object(cli, 'github', side_effect=cli.Error('not authenticated'))
    def test_auth_failure_does_not_configure_remote(self, gh, git):
        with self.assertRaises(cli.Error): cli.ensure_remote(Path('/tmp/demo'), None)
        git.assert_not_called()
    def test_guidance_uses_absolute_quoted_path(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output): cli.setup_guidance(Path('/tmp/my project'))
        self.assertIn("git -C '/tmp/my project'", output.getvalue())
        self.assertIn('gh auth login', output.getvalue())
        self.assertIn('git config --global user.name', output.getvalue())

class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
        self.call(sys.executable, '-c', 'from project_setup.cli import setup_main; setup_main()', '--project','demo','--proj-dir',str(self.base))
        self.root = self.base / 'demo'
    def tearDown(self): self.temp.cleanup()
    def call(self, *cmd, cwd=None, ok=True):
        result = subprocess.run(cmd, cwd=cwd, env=self.env, capture_output=True, text=True)
        if ok: self.assertEqual(result.returncode, 0, result.stderr)
        else: self.assertNotEqual(result.returncode, 0)
        return result
    def update(self, *args, ok=True):
        return self.call(str(self.root/'script/project-update'), *args, cwd=self.base, ok=ok)
    def git(self, *args): return self.call('git','-C',str(self.root),*args).stdout.strip()
    def remote(self):
        remote = self.base/'remote.git'
        self.call('git','init','--bare',str(remote))
        self.git('remote','add','origin',str(remote))
    def test_scaffold_and_refusal(self):
        for name in cli.DIRS: self.assertTrue((self.root/name).is_dir())
        self.assertEqual((self.root/'VERSION').read_text(),'0.0.1\n')
        self.call(sys.executable,'-c','from project_setup.cli import setup_main; setup_main()','--project','demo','--proj-dir',str(self.base),ok=False)
        self.assertEqual((self.root/'VERSION').read_text(),'0.0.1\n')
    def test_first_push_on_unborn_branch(self):
        self.remote()
        # Remove the sole test commit's branch ref to recreate an unborn branch.
        self.git('update-ref', '-d', 'refs/heads/main')
        self.update('--git-push', '--message', 'First commit')
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'First commit')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.git('rev-parse', 'origin/main'))
    def test_missing_parent(self):
        parent = self.base/'nested'/'parent'
        self.call(sys.executable, '-c', 'from project_setup.cli import setup_main; setup_main()',
                  '--project', 'created', '--proj-dir', str(parent))
        self.assertEqual((parent/'created/VERSION').read_text(), '0.0.1\n')
    def test_parent_is_file(self):
        parent = self.base/'file'
        parent.write_text('preserve')
        self.call(sys.executable, '-c', 'from project_setup.cli import setup_main; setup_main()',
                  '--project', 'created', '--proj-dir', str(parent), ok=False)
        self.assertEqual(parent.read_text(), 'preserve')
    def test_history_release(self):
        self.update('--version')
        self.update('--version','0.99.99')
        self.update('--version','--release','--massage','A release')
        self.assertEqual((self.root/'VERSION').read_text(),'1.0.0\n0.99.99\n0.0.2\n0.0.1\n')
        archive = self.root/'versions/demo-1.0.0.tar.gz'
        with tarfile.open(archive) as t:
            names = t.getnames()
            self.assertIn('demo-1.0.0/script/project-update', names)
            self.assertFalse(any('/versions/' in n or '/.git/' in n for n in names))
            self.assertIn('A release',t.extractfile('demo-1.0.0/RELEASE.txt').read().decode())
        self.update('--release',ok=False)
        self.assertTrue(archive.exists())
    def test_manifest_safety(self):
        (self.root/'release-files.txt').write_text('../remote\n')
        self.update('--release',ok=False)
        (self.root/'data/link').symlink_to('/etc/passwd')
        (self.root/'release-files.txt').write_text('data\n')
        self.update('--release',ok=False)
    def test_symlink_parent_manifest(self):
        external = self.base/'external'
        external.mkdir()
        (external/'secret').write_text('private')
        (self.root/'linked').symlink_to(external, target_is_directory=True)
        (self.root/'release-files.txt').write_text('linked/secret\n')
        self.update('--release',ok=False)
    def test_default_parent(self):
        code = 'import sys; sys.path.insert(0, ' + repr(str(Path(cli.__file__).resolve().parent.parent)) + '); from project_setup.cli import setup_main; setup_main()'
        self.call(sys.executable,'-c',code,'--project','default-parent',cwd=self.base)
        self.assertTrue((self.base/'default-parent/VERSION').is_file())
        self.call(sys.executable,'-c',code,'--project','../escape',cwd=self.base,ok=False)
    def test_push_pull_tags_and_branch(self):
        self.remote()
        self.update('--version','--release','--git-push','--message','publish')
        self.assertEqual(self.git('log','-1','--format=%s'),'publish')
        self.update('--git-push','0.0.2')
        before = self.git('rev-parse','HEAD')
        self.update('--git-pull','0.0.2')
        self.assertEqual(before,self.git('rev-parse','HEAD'))
        self.assertEqual(self.git('branch','--show-current'),'main')
        self.git('branch','other')
        self.update('--git-push','other')
        self.update('--git-pull','other',ok=False)
        (self.root/'dirty').write_text('keep')
        self.update('--git-pull',ok=False)
        self.update('--git-push','show','--version',ok=False)
        self.assertEqual((self.root/'dirty').read_text(),'keep')
        self.assertIn('other',self.update('--git-push','show').stdout)
    def test_fast_forward_pull(self):
        self.remote()
        self.update('--git-push')
        clone = self.base/'clone'
        self.call('git','clone','--branch','main',str(self.base/'remote.git'),str(clone))
        (clone/'new.txt').write_text('upstream')
        self.call('git','-C',str(clone),'add','.')
        self.call('git','-C',str(clone),'commit','-m','upstream')
        self.call('git','-C',str(clone),'push')
        self.update('--git-pull')
        self.assertEqual((self.root/'new.txt').read_text(),'upstream')
    def test_default_message(self):
        self.remote()
        (self.root/'new').touch()
        self.update('--git-push','--massage')
        self.assertRegex(self.git('log','-1','--format=%s'),r'^\d{2}:\d{2}:\d{2}\|\d{2}-\d{2}-\d{2}$')

if __name__ == '__main__': unittest.main()
