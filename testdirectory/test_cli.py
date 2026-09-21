import os
import shutil
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

class Descriptions(unittest.TestCase):
    def test_long_literal_empty_and_explicit_missing(self):
        long_text = 'Scientific description. ' * 100
        self.assertEqual(cli.read_description(long_text),long_text.strip())
        for value in ['', '   ', '@missing-description', 'missing-description.txt', 'bad\x00text']:
            with self.assertRaises(cli.Error): cli.read_description(value)

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
    @patch.object(cli, 'git')
    @patch.object(cli, 'github', return_value='test-owner')
    def test_clone_short_name_resolution(self, gh, git):
        import argparse
        with tempfile.TemporaryDirectory() as tmp:
            git.return_value = ''
            args = argparse.Namespace(from_git='KnownProject', project=None, remote=None, proj_dir=tmp, description=None)
            with contextlib.redirect_stdout(io.StringIO()): cli.clone_project(args)
            self.assertIn(unittest.mock.call(Path(tmp).resolve(),'clone','--','https://github.com/test-owner/KnownProject.git',str(Path(tmp).resolve()/'KnownProject')),git.call_args_list)

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
        result = self.call(str(self.root/'script/project-update'), *args, cwd=self.base, ok=ok)
        lines = result.stderr.splitlines()
        self.assertTrue(lines[-2].startswith('Action: '), result.stderr)
        self.assertTrue(lines[-1].startswith('Result: '), result.stderr)
        return result
    def git(self, *args): return self.call('git','-C',str(self.root),*args).stdout.strip()
    def remote(self):
        remote = self.base/'remote.git'
        self.call('git','init','--bare','--initial-branch=main',str(remote))
        self.git('remote','add','origin',str(remote))
    def test_scaffold_and_refusal(self):
        for name in cli.DIRS: self.assertTrue((self.root/name).is_dir())
        self.assertEqual((self.root/'version/VERSION').read_text(),'0.1.0\n')
        self.call(sys.executable,'-c','from project_setup.cli import setup_main; setup_main()','--project','demo','--proj-dir',str(self.base),ok=False)
        self.assertEqual((self.root/'version/VERSION').read_text(),'0.1.0\n')
    def test_new_agent_files_and_standalone_updater(self):
        for name in ['AGENTS.md', 'HANDOFF.md', 'startup-prompt.txt', 'script/agent_context.py',
                     'script/agent_lock.py', 'developer/DEV_NOTES.md', 'docs/DOCUMENTATION_RULES.md']:
            self.assertTrue((self.root/name).is_file(), name)
        notes = (self.root/'developer/DEV_NOTES.md').read_text()
        self.assertIn('# demo Developer Notes', notes)
        self.assertNotIn('Model_Project Developer Notes', notes)
        self.assertNotIn('astrolab-pd', notes)
        self.assertFalse((self.root/'.agent-state/lock').exists())
        self.assertIn('handoff_id', (self.root/'HANDOFF.md').read_text())
        self.assertEqual(self.git('status','--porcelain'), '')
        self.update('--version','major')
        self.assertEqual((self.root/'version/VERSION').read_text().splitlines()[0], '1.0.0')

    def test_legacy_version_layout(self):
        history = (self.root/'version/VERSION').read_text()
        shutil.rmtree(self.root/'version')  # VERSION and version collide on macOS.
        (self.root/'VERSION').write_text(history)
        (self.root/'release-files.txt').write_text('VERSION\nscript\n')
        self.update('--version','--release')
        self.assertEqual((self.root/'VERSION').read_text().splitlines()[0], '0.1.1')
        self.assertTrue((self.root/'versions/demo-0.1.1.tar.gz').exists())

    def test_updater_respects_active_lock(self):
        import json
        lock = self.call(sys.executable, str(self.root/'script/agent_lock.py'), 'acquire', '--agent', 'test')
        session = json.loads(lock.stdout)['session_id']
        self.update('--version',ok=False)
        self.update('--version','--session',session)
        self.call(sys.executable, str(self.root/'script/agent_lock.py'), 'release', '--session', session)

    def test_manual_lock_commands(self):
        import json
        self.assertEqual(self.update('--lock','status').stdout.strip(), 'UNLOCKED')
        acquired = self.update('--lock','aquire','--agent','test-agent','--agent-version','2')
        owner = json.loads(acquired.stdout)
        token = owner['session_id']
        self.assertEqual(owner['agent_version'], '2')
        self.update('--lock','acquire',ok=False)
        self.update('--lock','release','--session','wrong',ok=False)
        self.update('--lock','release',ok=False)  # Noninteractive needs attribution.
        self.update('--lock','release','--session',token,'--version',ok=False)
        # Interoperates with agent helper and updater mutation guard.
        self.call(sys.executable,str(self.root/'script/agent_lock.py'),'check','--session',token)
        self.update('--version','--session',token)
        self.update('--lock','release','--session',token)
        self.assertEqual(self.update('--lock','release').stdout.strip(), 'UNLOCKED')

    def test_manual_lock_foreign_corrupt_and_helper_acquisition(self):
        import json
        owner = json.loads(self.call(sys.executable,str(self.root/'script/agent_lock.py'),'acquire','--agent','test').stdout)
        token = owner['session_id']
        self.update('--lock','release','--session',token)
        self.update('--lock','acquire')
        path = self.root/'.agent-state/lock/owner.json'
        owner = json.loads(path.read_text()); owner['host'] = 'foreign-computer'
        path.write_text(json.dumps(owner))
        self.update('--lock','release','--session',owner['session_id'],ok=False)
        self.assertTrue(path.exists())
        path.write_text('broken')
        self.update('--lock','release',ok=False)
        self.assertTrue(path.exists())

    def test_interactive_manual_release(self):
        self.update('--lock','acquire')
        lock = self.root/'.agent-state/lock'
        with patch('sys.stdin.isatty',return_value=True), patch('builtins.input',return_value='no'), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(cli.Error):
                cli.manage_lock(self.root,'release',None,'manual','unknown')
        self.assertTrue(lock.exists())
        with patch('sys.stdin.isatty',return_value=True), patch('builtins.input',return_value='release'), contextlib.redirect_stdout(io.StringIO()):
            cli.manage_lock(self.root,'release',None,'manual','unknown')
        self.assertFalse(lock.exists())

    def test_two_line_summaries(self):
        cases = [([], 'Help displayed'), (['--help'], 'Help displayed'),
                 (['--version','0.1.0'], 'unchanged'), (['--version'], '0.1.0 -> 0.1.1'),
                 (['--release'], 'Archive created'), (['--git-push','show'], 'Listed known branches'),
                 (['--lock','status'], 'unlocked')]
        for args, expected in cases:
            result = self.update(*args)
            lines = result.stderr.splitlines()
            self.assertEqual(len(lines),2,result.stderr)
            self.assertTrue(lines[0].startswith('Action: '))
            self.assertTrue(lines[1].startswith('Result: '))
            self.assertIn(expected,lines[1])
        result = self.update('--version','major','--git-push',ok=False)
        self.assertEqual(len(result.stderr.splitlines()),2)
        self.assertIn('FAILED:',result.stderr)
        self.assertIn('Version 0.1.1 -> 1.0.0',result.stderr)
        self.assertEqual((self.root/'version/VERSION').read_text().splitlines()[0], '1.0.0')
        result = self.update('--lock','invalid',ok=False)
        self.assertTrue(result.stderr.splitlines()[-2].startswith('Action: '))
        self.assertIn('invalid arguments',result.stderr.splitlines()[-1])

    def setup_cli(self, *args, ok=True):
        return self.call(sys.executable,'-c','from project_setup.cli import setup_main; setup_main()',*args,ok=ok)

    def test_description_text_and_file(self):
        description = self.base/'description with spaces.txt'
        description.write_text('Measure stars.\nReport calibrated fluxes.\n')
        self.setup_cli('--project','Described','--proj-dir',str(self.base),'--proj-description',str(description))
        project = self.base/'Described'
        self.assertEqual((project/'PROJECT_DESCRIPTION.txt').read_text(),description.read_text())
        self.assertIn('Measure stars.',(project/'README.md').read_text())
        self.assertIn('Report calibrated fluxes.',(project/'HANDOFF.md').read_text())
        self.setup_cli('--project','Inline','--proj-dir',str(self.base),'--proj-description','Analyze spectra')
        self.assertEqual((self.base/'Inline/PROJECT_DESCRIPTION.txt').read_text(),'Analyze spectra\n')
        self.setup_cli('--project','Missing','--proj-dir',str(self.base),'--proj-description',str(self.base/'missing.txt'),ok=False)
        self.assertFalse((self.base/'Missing').exists())

    def test_from_git_preserves_existing_project_and_git_only_update(self):
        self.remote()
        self.update('--git-push')
        self.setup_cli('--from-git','Copy','--remote',str(self.base/'remote.git'),'--proj-dir',str(self.base))
        # Bare test repository default branch is explicitly set below for portability.
        copy = self.base/'Copy'
        self.assertEqual(self.call('git','-C',str(copy),'rev-parse','HEAD').stdout.strip(),self.git('rev-parse','HEAD'))
        self.assertEqual((copy/'README.md').read_text(),(self.root/'README.md').read_text())
        self.assertEqual(self.call('git','-C',str(copy),'status','--porcelain').stdout.strip(),'')
        self.setup_cli('--from-git','Copy','--remote',str(self.base/'remote.git'),'--proj-dir',str(self.base),ok=False)
        # Git-only synchronization works even without a version file.
        (copy/'version/VERSION').unlink()
        self.call(str(copy/'script/project-update'),'--git-push','--message','Remove version',cwd=copy)
        self.call(str(copy/'script/project-update'),'--git-pull',cwd=copy)
        self.call(str(copy/'script/project-update'),'--version',cwd=copy,ok=False)

    def test_clone_description_conflict_retains_remote_content(self):
        self.remote(); self.update('--git-push')
        self.setup_cli('--from-git','Conflict','--remote',str(self.base/'remote.git'),'--proj-dir',str(self.base),'--proj-description','Different description',ok=False)
        self.assertEqual((self.base/'Conflict/PROJECT_DESCRIPTION.txt').read_text(),(self.root/'PROJECT_DESCRIPTION.txt').read_text())

    def test_git_setup_discoverable_help_and_dispatch(self):
        help_text = self.setup_cli('--help').stdout
        self.assertIn('--git-setup ...',help_text)
        self.assertIn('project-setup --git-setup guide',help_text)
        for args in [('--git-setup','guide'), ('--git-setup',)]:
            self.assertIn('Git and GitHub setup',self.setup_cli(*args).stdout)
        self.assertIn('configure',self.setup_cli('--git-setup','--help').stdout)

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
        self.assertEqual((parent/'created/version/VERSION').read_text(), '0.1.0\n')
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
        self.assertEqual((self.root/'version/VERSION').read_text(),'1.0.0\n0.99.99\n0.1.1\n0.1.0\n')
        archive = self.root/'version/dist/demo-1.0.0.tar.gz'
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
        self.assertTrue((self.base/'default-parent/version/VERSION').is_file())
        self.call(sys.executable,'-c',code,'--project','../escape',cwd=self.base,ok=False)
    def test_push_pull_tags_and_branch(self):
        self.remote()
        self.update('--version','--release','--git-push','--message','publish')
        self.assertEqual(self.git('log','-1','--format=%s'),'publish')
        self.update('--git-push','0.1.1')
        before = self.git('rev-parse','HEAD')
        self.update('--git-pull','0.1.1')
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
