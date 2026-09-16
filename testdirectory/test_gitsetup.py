import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from project_setup import gitsetup

class GitSetupTests(unittest.TestCase):
    def test_guide(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): gitsetup.main(['guide'])
        self.assertIn('gh auth login',output.getvalue())
    def test_identity_isolated_config(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=str(Path(d)/'gitconfig')
            with patch.dict(os.environ,{'GIT_CONFIG_GLOBAL':cfg}):
                gitsetup.main(['configure','--name','Test User','--email','test@example.invalid'])
                name=subprocess.check_output(['git','config','--global','user.name'],text=True).strip()
                self.assertEqual(name,'Test User')
    @patch.object(gitsetup,'github',return_value='alice')
    def test_account_inference(self,gh):
        self.assertEqual(gitsetup.repo_name('demo',Path.cwd()),'alice/demo')
    def test_invalid_repo(self):
        with self.assertRaises(gitsetup.Error): gitsetup.repo_name('../bad',Path.cwd())
    @patch.object(gitsetup,'ensure_remote')
    def test_new_initializes(self,ensure):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'repo'
            gitsetup.main(['new','alice/demo','--directory',str(root)])
            self.assertTrue((root/'.git').is_dir())
            ensure.assert_called_once_with(root.resolve(),'https://github.com/alice/demo.git')
    @patch.object(gitsetup,'ensure_remote')
    def test_preserves_existing_origin(self,ensure):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(['git','init','-q',d],check=True)
            subprocess.run(['git','-C',d,'remote','add','origin','https://example.com/existing'],check=True)
            with self.assertRaises(SystemExit): gitsetup.main(['new','alice/demo','--directory',d])
            ensure.assert_not_called()
            remote=subprocess.check_output(['git','-C',d,'remote','get-url','origin'],text=True).strip()
            self.assertEqual(remote,'https://example.com/existing')
    @patch.object(gitsetup,'git')
    def test_clone_existing_destination_refused(self,git):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit): gitsetup.main(['clone','alice/demo','--directory',d])
            git.assert_not_called()
    @patch.object(gitsetup,'transfer')
    def test_update(self,transfer):
        gitsetup.main(['update','--directory','/tmp','--message','Test update'])
        transfer.assert_called_once_with(Path('/tmp').resolve(),'push',None,'Test update')
