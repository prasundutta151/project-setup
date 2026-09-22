#!/usr/bin/env python3
"""Install isolated command launchers using only Python's standard library."""
import argparse
from pathlib import Path
import shutil
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prefix', type=Path, default=Path.home()/'.local')
p.add_argument('--project-data-only', action='store_true', help='install only project-data and its setup-tree presets')
p.add_argument('--without-project-data', action='store_true', help='install the project toolkit without the project-data command')
a = p.parse_args()
if a.project_data_only and a.without_project_data:
    p.error('--project-data-only and --without-project-data cannot be combined')
prefix = a.prefix.expanduser().resolve()
source = Path(__file__).resolve().parent/'project_setup'
target = prefix/'lib/project-setup/project_setup'
bin_dir = prefix/'bin'
commands = ('project-data',) if a.project_data_only else ('project-setup', 'project-update', 'git-setup', 'project-lisence', 'project-data')
if a.without_project_data:
    commands = ('project-setup', 'project-update', 'git-setup', 'project-lisence')
for name in commands:
    path = bin_dir/name
    if path.exists() and (path.is_symlink() or '# project-setup managed launcher' not in path.read_text()):
        p.error(f'Refusing to overwrite unrelated command: {path}')
target.mkdir(parents=True, exist_ok=True)
shutil.copytree(source/'template', target/'template', dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
for file in source.glob('*.py'):
    if not a.project_data_only or file.name == 'data.py':
        shutil.copy2(file,target/file.name)
bin_dir.mkdir(parents=True, exist_ok=True)
launchers = [('project-data','data','main')] if a.project_data_only else [('project-setup','cli','setup_main'),('project-update','cli','update_main'),('git-setup','gitsetup','main'),('project-lisence','licensing','main'),('project-data','data','main')]
if a.without_project_data:
    launchers = [('project-setup','cli','setup_main'),('project-update','cli','update_main'),('git-setup','gitsetup','main'),('project-lisence','licensing','main')]
for name, module, function in launchers:
    path = bin_dir/name
    path.write_text(f'#!/usr/bin/env python3\n# project-setup managed launcher\nimport sys\nsys.path.insert(0, {str(target.parent)!r})\nfrom project_setup.{module} import {function}\n{function}()\n')
    path.chmod(0o755)
docs = source.parent / 'docs'
if docs.is_dir():
    shutil.copytree(docs, prefix/'share/project-setup/docs', dirs_exist_ok=True)
licenses = source.parent/'lisence'
if licenses.is_dir():
    shutil.copytree(licenses, prefix/'share/project-setup/lisence', dirs_exist_ok=True)
presets = source/'template/data-config'
if presets.is_dir():
    shutil.copytree(presets, prefix/'share/project-setup/data-config', dirs_exist_ok=True)
print('Installed ' + ', '.join(commands) + f' in {bin_dir}')
print(f'Ensure {bin_dir} is on PATH. Requires Python 3.9+ and Git 2.28+.')
