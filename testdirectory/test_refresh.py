from __future__ import annotations
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from argparse import Namespace
import contextlib
import io
from project_setup import cli, refresh


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'OldProject'
        self.root.mkdir()
        self.env = dict(os.environ, HOME=str(self.base/'home'), GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM='1', GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
        for key in list(self.env):
            if key.startswith('PROJECT_SETUP_AI_COMMAND'): del self.env[key]
        for args in [('init','-b','main'),]: self.git(*args)
        (self.root/'README.md').write_text('Preserve this science project.\n')
        (self.root/'.gitignore').write_text('.agent-state/\n')
        self.git('add','.');self.git('commit','-m','baseline')
        self.head=self.git('rev-parse','HEAD').strip()

    def git(self,*args):
        return subprocess.run(['git','-C',str(self.root),*args],env=self.env,text=True,capture_output=True,check=True).stdout

    def call(self,*args,code=0):
        r=subprocess.run([sys.executable,'-c','from project_setup.cli import setup_main; setup_main()',
                          '--refresh','OldProject','--proj-dir',str(self.base),*args],env=self.env,text=True,capture_output=True)
        self.assertEqual(r.returncode,code,r.stderr+r.stdout)
        return r

    def test_manual_preserves_project_and_prints_full_prompt(self):
        result=self.call('--ai','manual')
        self.assertIn('PREPARED ONLY',result.stdout)
        self.assertIn('MIGRATION, NOT BLIND COPY',result.stdout)
        self.assertEqual(self.git('status','--porcelain'),'')
        self.assertEqual(self.git('rev-parse','HEAD').strip(),self.head)
        self.assertIn('Preserve this science project.',(self.root/'README.md').read_text())
        prompt=next((self.base/'home').rglob('refresh-prompt.txt'))
        self.assertFalse(prompt.is_relative_to(self.root))

    def test_named_agent_without_command_falls_back_honestly(self):
        for name in ('antigravity','chatgpt','claude','opencode'):
            result=self.call('--ai',name)
            self.assertIn('PREPARED ONLY for '+name,result.stdout)
            self.assertIn('No automatic command configured',result.stdout)

    def test_menu_selection(self):
        args=Namespace(refresh='OldProject',proj_dir=str(self.base),ai=None,ai_command=None,description=None)
        with patch.dict(os.environ,self.env,clear=True),patch('sys.stdin.isatty',return_value=True),patch('builtins.input',return_value='2'),contextlib.redirect_stdout(io.StringIO()) as output:
            refresh.refresh_project(args)
        self.assertIn('PREPARED ONLY for chatgpt',output.getvalue())

    def make_agent(self,success=True):
        script=self.base/'fake agent.py'
        if success:
            script.write_text('''from pathlib import Path
import json,os,sys
root=Path.cwd()
owner=json.loads((root/'.agent-state/lock/owner.json').read_text())
assert owner['session_id']==os.environ['PROJECT_SETUP_REFRESH_SESSION']
assert Path(sys.argv[1]).is_file()
for name in '''+repr(refresh.REQUIRED_DIRS)+''': (root/name).mkdir(exist_ok=True)
for name in '''+repr(refresh.REQUIRED_FILES)+''':
    path=root/name
    if not path.exists(): path.write_text('fixture content\\n')
(root/'developer/REFRESH_REPORT.md').write_text('Simulated agent integration test; not a scientific migration.\\n')
''')
        else: script.write_text('raise SystemExit(7)\n')
        return shlex.join([sys.executable,str(script),'{prompt_file}'])

    def test_configured_agent_execution_and_validation(self):
        result=self.call('--ai','opencode','--ai-command',self.make_agent())
        self.assertIn('AI RUN FINISHED',result.stdout)
        self.assertFalse((self.root/'.agent-state/lock').exists())
        self.assertEqual(self.git('rev-parse','HEAD').strip(),self.head)
        self.assertIn('Preserve this science project.',(self.root/'README.md').read_text())

    def test_dirty_failed_and_incomplete_runs(self):
        command=self.make_agent(False)
        (self.root/'dirty').write_text('preserve')
        self.call('--ai','claude','--ai-command',command,code=1)
        self.assertFalse((self.root/'.agent-state/lock').exists())
        (self.root/'dirty').unlink()
        self.call('--ai','claude','--ai-command',command,code=1)
        self.assertFalse((self.root/'.agent-state/lock').exists())
        script=self.base/'no_op.py';script.write_text('pass\n')
        result=self.call('--ai','claude','--ai-command',shlex.join([sys.executable,str(script),'{prompt_file}']),code=1)
        self.assertIn('missing',result.stderr)
        self.assertFalse((self.root/'.agent-state/lock').exists())

    def test_invalid_combinations_and_busy_lock(self):
        self.call('--from-git','elsewhere',code=2)
        self.call('--ai-command','echo {prompt_file}',code=2)
        (self.root/'.agent-state/lock').mkdir(parents=True)
        result=self.call('--ai','opencode','--ai-command',self.make_agent(),code=1)
        self.assertIn('already locked',result.stderr)
        self.assertTrue((self.root/'.agent-state/lock').exists())


if __name__=='__main__': unittest.main()
