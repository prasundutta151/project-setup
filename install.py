#!/usr/bin/env python3
"""Install isolated command launchers using only Python's standard library."""
import argparse
from pathlib import Path
import shutil
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prefix', type=Path, default=Path.home()/'.local')
a = p.parse_args()
prefix = a.prefix.expanduser().resolve()
source = Path(__file__).resolve().parent/'project_setup'
target = prefix/'lib/project-setup/project_setup'
bin_dir = prefix/'bin'
for name in ('project-setup', 'project-update', 'git-setup'):
    path = bin_dir/name
    if path.exists() and (path.is_symlink() or '# project-setup managed launcher' not in path.read_text()):
        p.error(f'Refusing to overwrite unrelated command: {path}')
target.mkdir(parents=True, exist_ok=True)
for file in source.glob('*.py'): shutil.copy2(file,target/file.name)
bin_dir.mkdir(parents=True, exist_ok=True)
for name, module, function in [('project-setup','cli','setup_main'),('project-update','cli','update_main'),('git-setup','gitsetup','main')]:
    path = bin_dir/name
    path.write_text(f'#!/usr/bin/env python3\n# project-setup managed launcher\nimport sys\nsys.path.insert(0, {str(target.parent)!r})\nfrom project_setup.{module} import {function}\n{function}()\n')
    path.chmod(0o755)
docs = source.parent / 'docs'
if docs.is_dir():
    shutil.copytree(docs, prefix/'share/project-setup/docs', dirs_exist_ok=True)
print(f'Installed project-setup, project-update and git-setup in {bin_dir}')
print(f'Ensure {bin_dir} is on PATH. Requires Python 3.9+ and Git 2.28+.')
