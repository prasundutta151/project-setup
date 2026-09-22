import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from project_setup import cli, data


class DataDirModes(unittest.TestCase):
    def test_default_root(self):
        destination, subfolders, tree, label = cli.data_dir_args([])
        self.assertIsNone(destination)
        self.assertIsNone(subfolders)
        self.assertIsNone(tree)
        self.assertIn('/Volumes/Work/Data', label)

    def test_directory_entries(self):
        destination, subfolders, tree, label = cli.data_dir_args(['raw', 'images/plots'])
        self.assertIsNone(destination)
        self.assertEqual(subfolders, ['raw', 'images/plots'])
        self.assertIsNone(tree)
        self.assertIn('directory entries', label)

    def test_absolute_root_with_entries(self):
        destination, subfolders, tree, label = cli.data_dir_args(['/mnt/work/Data', 'raw', 'cal'])
        self.assertEqual(destination, Path('/mnt/work/Data'))
        self.assertEqual(subfolders, ['raw', 'cal'])
        self.assertIsNone(tree)
        self.assertIn('data root', label)

    def test_absolute_root_alone(self):
        destination, subfolders, tree, label = cli.data_dir_args(['/mnt/work/Data'])
        self.assertEqual(destination, Path('/mnt/work/Data'))
        self.assertIsNone(subfolders)
        self.assertIsNone(tree)
        self.assertIn('data root', label)

    def test_directory_list_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / 'dirs.txt'
            listing.write_text('# comment\nraw\nnested/tree\n\n')
            destination, subfolders, tree, label = cli.data_dir_args([str(listing)])
            self.assertIsNone(destination)
            self.assertIsNone(subfolders)
            self.assertEqual(tree, listing)
            self.assertIn('directory-list file', label)
            self.assertEqual(data.read_tree(tree), ['raw', 'nested/tree'])

    def test_directory_list_file_with_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / 'dirs.txt'
            listing.write_text('raw\nproducts/tables\n')
            destination, subfolders, tree, label = cli.data_dir_args([str(listing), '/mnt/work/Data'])
            self.assertEqual(destination, Path('/mnt/work/Data'))
            self.assertIsNone(subfolders)
            self.assertEqual(tree, listing)
            self.assertIn('under data root', label)

    def test_missing_list_file_rejected(self):
        with self.assertRaises(cli.Error):
            cli.data_dir_args(['/no/such/dirs.txt'])
        with self.assertRaises(cli.Error):
            cli.data_dir_args(['missing.txt'])
        with self.assertRaises(cli.Error):
            cli.data_dir_args(['missing.json', '/mnt/work/Data'])

    def test_conflicting_values_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / 'dirs.txt'
            listing.write_text('raw\n')
            with self.assertRaises(cli.Error):  # file plus entries
                cli.data_dir_args([str(listing), 'raw'])
            with self.assertRaises(cli.Error):  # two roots
                cli.data_dir_args(['/root/one', '/root/two'])
            with self.assertRaises(cli.Error):  # two files
                cli.data_dir_args([str(listing), str(listing)])
        with self.assertRaises(cli.Error):  # parent escapes are entries, not paths
            cli.data_dir_args(['../escape'])
        with self.assertRaises(cli.Error):
            cli.data_dir_args(['/root', '/other'])


class PathChecks(unittest.TestCase):
    def test_exists_and_will_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cli.path_state(Path(tmp)), 'exists')
            self.assertEqual(cli.path_state(Path(tmp) / 'a' / 'b'), 'will create')

    def test_file_where_directory_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'f.txt'
            target.write_text('x')
            with self.assertRaises(cli.Error):
                cli.path_state(target)

    def test_permission_blocked(self):
        if os.geteuid() == 0:
            self.skipTest('root ignores permission bits')
        with tempfile.TemporaryDirectory() as tmp:
            locked = Path(tmp) / 'locked'
            locked.mkdir()
            locked.chmod(0o555)
            try:
                with self.assertRaises(cli.Error) as caught:
                    cli.path_state(locked / 'sub')
                self.assertIn('Permission denied', str(caught.exception))
            finally:
                locked.chmod(0o755)

    @unittest.skipIf(os.path.ismount('/Volumes/Work'), 'default volume is mounted here')
    def test_unmounted_volume_blocked(self):
        with self.assertRaises(cli.Error) as caught:
            cli.path_state('/Volumes/Work/Data')
        self.assertIn('not mounted', str(caught.exception))

    def test_json_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'data-path.json'
            self.assertEqual(cli.json_state(target), 'will create')
            target.write_text('{}')
            self.assertEqual(cli.json_state(target), 'exists')
            with self.assertRaises(cli.Error):
                cli.json_state(Path(tmp))


class WorkspaceIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *cmd, cwd=None, ok=True):
        result = subprocess.run([sys.executable, '-c',
                                 'from project_setup.cli import setup_main; setup_main()', *cmd],
                                cwd=cwd, env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def test_data_dir_entries_create_workspace(self):
        root = self.base / 'data'
        result = self.call('--project', 'demo', '--proj-dir', str(self.base),
                           '--data-dir', str(root), 'raw', 'images/plots')
        self.assertTrue((root / 'demo' / 'raw').is_dir())
        self.assertTrue((root / 'demo' / 'images' / 'plots').is_dir())
        config = json.loads((self.base / 'demo' / 'data-path.json').read_text())
        self.assertEqual(Path(config['data_root']), root.resolve())
        self.assertEqual(Path(config['data_path']), (root / 'demo').resolve())
        self.assertEqual(config['subfolders'], ['raw', 'images/plots'])
        self.assertIn('Check:', result.stdout)
        self.assertIn('[will create]', result.stdout)
        self.assertIn('Data workspace ready', result.stdout)
        self.assertIn('Configuration:', result.stdout)
        self.assertTrue((self.base / 'demo' / 'AGENTS.md').is_file())

    def test_data_dir_list_file_with_root(self):
        listing = self.base / 'dirs.txt'
        listing.write_text('# one directory per line\nraw\nproducts/tables\n')
        root = self.base / 'dl'
        self.call('--project', 'demo', '--proj-dir', str(self.base),
                  '--data-dir', str(listing), str(root))
        self.assertTrue((root / 'demo' / 'raw').is_dir())
        self.assertTrue((root / 'demo' / 'products' / 'tables').is_dir())
        config = json.loads((self.base / 'demo' / 'data-path.json').read_text())
        self.assertEqual(config['subfolders'], ['raw', 'products/tables'])

    @unittest.skipIf(os.path.ismount('/Volumes/Work'), 'default volume is mounted here')
    def test_default_root_blocked_before_creation(self):
        result = self.call('--project', 'demo', '--proj-dir', str(self.base),
                           '--data-dir', ok=False)
        self.assertIn('not mounted', result.stderr)
        self.assertFalse((self.base / 'demo').exists())

    @unittest.skipIf(os.geteuid() == 0, 'root ignores permission bits')
    def test_permission_failure_reported_before_creation(self):
        locked = self.base / 'locked'
        locked.mkdir()
        locked.chmod(0o555)
        try:
            result = self.call('--project', 'demo', '--proj-dir', str(self.base),
                               '--data-dir', str(locked / 'data'), ok=False)
        finally:
            locked.chmod(0o755)
        self.assertIn('Permission denied', result.stderr)
        self.assertFalse((self.base / 'demo').exists())

    def test_json_path_inside_project(self):
        self.call('--project', 'demo', '--proj-dir', str(self.base),
                  '--data-dir', str(self.base / 'droot'),
                  '--json', str(self.base / 'demo' / 'json' / 'data-path.json'))
        target = self.base / 'demo' / 'json' / 'data-path.json'
        self.assertTrue(target.is_file())
        self.assertEqual(json.loads(target.read_text())['project_name'], 'demo')

    def test_json_path_outside_project_refused(self):
        self.call('--project', 'demo', '--proj-dir', str(self.base),
                  '--data-dir', str(self.base / 'droot'),
                  '--json', str(self.base / 'outside.json'), ok=False)
        self.assertFalse((self.base / 'demo').exists())

    @unittest.skipIf(os.path.ismount('/Volumes/Work'), 'default volume is mounted here')
    def test_dry_run_reports_blocked_default_root(self):
        result = self.call('--project', 'demo', '--proj-dir', str(self.base),
                           '--data-dir', '--dry-run')
        self.assertIn('Dry run', result.stdout)
        self.assertIn('BLOCKED', result.stdout)
        self.assertIn('not mounted', result.stdout)
        self.assertFalse((self.base / 'demo').exists())

    def test_dry_run_previews_creation(self):
        result = self.call('--project', 'demo', '--proj-dir', str(self.base),
                           '--data-dir', str(self.base / 'droot'), 'raw', 'raw/calib', '--dry-run')
        self.assertIn('Setup directories:', result.stdout)
        self.assertIn('will create', result.stdout)
        self.assertIn(str(self.base / 'droot' / 'demo' / 'raw'), result.stdout)
        self.assertIn('configuration JSON', result.stdout)
        self.assertFalse((self.base / 'demo').exists())
        self.assertFalse((self.base / 'droot').exists())

    def test_dry_run_without_data_notes_default(self):
        result = self.call('--project', 'demo', '--proj-dir', str(self.base), '--dry-run')
        self.assertIn('not requested', result.stdout)
        self.assertFalse((self.base / 'demo').exists())

    def test_show_existing_project(self):
        self.call('--project', 'demo', '--proj-dir', str(self.base))
        result = self.call('--project', 'demo', '--proj-dir', str(self.base), '--show')
        self.assertIn('Setup directories:', result.stdout)
        self.assertIn('script: present', result.stdout)
        self.assertIn('JSON folder:', result.stdout)
        self.assertIn('Data workspace: not configured', result.stdout)
        self.assertIn('Configuration:', result.stdout)
        self.assertTrue((self.base / 'demo' / 'AGENTS.md').is_file())  # read-only

    def test_show_with_data_config(self):
        root = self.base / 'data'
        self.call('--project', 'demo', '--proj-dir', str(self.base), '--data-dir', str(root))
        result = self.call('--project', 'demo', '--proj-dir', str(self.base), '--show')
        self.assertIn('Data workspace:', result.stdout)
        self.assertIn('Root: ' + str(root.resolve()), result.stdout)
        self.assertIn('[exists]', result.stdout)

    def test_show_missing_project_fails(self):
        result = self.call('--project', 'absent', '--proj-dir', str(self.base), '--show', ok=False)
        self.assertIn('does not exist', result.stderr)

    def test_json_flag_prints_configuration_path(self):
        self.call('--project', 'demo', '--proj-dir', str(self.base))
        result = self.call('--project', 'demo', '--proj-dir', str(self.base), '--json')
        self.assertIn(str(self.base / 'demo' / 'data-path.json'), result.stdout)
        self.assertIn('not created', result.stdout)

    def test_show_and_dry_run_rejected_together(self):
        self.call('--project', 'demo', '--proj-dir', str(self.base), '--show', '--dry-run', ok=False)

    def test_data_dir_rejected_with_refresh(self):
        self.call('--refresh', 'demo', '--proj-dir', str(self.base),
                  '--data-dir', str(self.base / 'd'), ok=False)


class UpdaterEmbed(unittest.TestCase):
    def test_standalone_updater_imports_without_data_module(self):
        """The embedded script/project-update must run without the package context."""
        updater = Path(cli.__file__).parent.parent / 'script' / 'project-update'
        source = updater.read_text()
        self.assertIn('def update_main', source)
        result = subprocess.run([sys.executable, str(updater), '--help'],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--lock', result.stdout)


if __name__ == '__main__':
    unittest.main()
