"""Python successor to prasundutta151/gitsetup's shell helpers."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import subprocess
from typing import Optional, List
from .cli import Error, git, github, ensure_remote, transfer, run

GUIDE = '''Git and GitHub setup (run from any directory)
1. Install Git and GitHub CLI:
   macOS with Homebrew: brew install git gh
   Ubuntu/Debian: sudo apt update && sudo apt install git gh
   Other systems: https://git-scm.com/downloads and https://cli.github.com/
2. Configure your identity, replacing these examples:
   git config --global user.name "Your Name"
   git config --global user.email "your-email@example.com"
   Or: git-setup configure --name "Your Name" --email "your-email@example.com"
3. Authenticate interactively:
   gh auth login --hostname github.com --git-protocol https --web
   gh auth setup-git
   gh auth status
4. Create a project and publish it privately:
   project-setup --project my-project --git-push
   Or publish an existing directory:
   git-setup new my-repo --directory /absolute/path/to/project --push
5. Clone or update:
   git-setup clone OWNER/REPO --directory /absolute/path/to/new-folder
   git-setup update --directory /absolute/path/to/project --message "Describe changes"
Authentication stays in GitHub CLI; this utility never asks for or stores tokens.
'''

def repo_name(value: str, root: Path) -> str:
    if '/' not in value:
        value = github(root, 'api', 'user', '--jq', '.login') + '/' + value
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise Error('Repository must be NAME or OWNER/NAME.')
    return value

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command')
    commands.add_parser('guide', help='Print numbered computer setup instructions')
    config = commands.add_parser('configure', help='Set global Git identity explicitly')
    config.add_argument('--name', required=True)
    config.add_argument('--email', required=True)
    new = commands.add_parser('new', help='Initialize a directory and ensure a private GitHub remote')
    new.add_argument('repository', help='NAME or OWNER/NAME')
    new.add_argument('--directory', type=Path, default=Path.cwd())
    new.add_argument('--push', action='store_true')
    clone = commands.add_parser('clone', help='Clone a GitHub repository')
    clone.add_argument('repository', help='NAME or OWNER/NAME')
    clone.add_argument('--directory', type=Path, help='New destination; defaults to repository name')
    update = commands.add_parser('update', help='Commit nonignored changes and push current branch')
    update.add_argument('--directory', type=Path, default=Path.cwd())
    update.add_argument('--message', '--massage', default='Update repository')
    args = parser.parse_args(argv)
    def work() -> None:
        try:
            if args.command in (None, 'guide'):
                print(GUIDE)
            elif args.command == 'configure':
                if not args.name.strip() or not args.email.strip():
                    raise Error('Name and email must not be empty.')
                git(Path.cwd(), 'config', '--global', 'user.name', args.name)
                git(Path.cwd(), 'config', '--global', 'user.email', args.email)
                print('Global Git identity configured.')
            elif args.command == 'clone':
                repo = repo_name(args.repository, Path.cwd())
                destination = (args.directory or Path(repo.split('/')[1])).expanduser().absolute()
                if destination.exists():
                    raise Error('Clone destination already exists; choose a new directory.')
                destination.parent.mkdir(parents=True, exist_ok=True)
                git(destination.parent, 'clone', '--', 'https://github.com/' + repo + '.git', str(destination))
                print(f'Cloned: {destination}')
            elif args.command == 'new':
                root = args.directory.expanduser().resolve()
                repo = repo_name(args.repository, Path.cwd())
                remote = 'https://github.com/' + repo + '.git'
                root.mkdir(parents=True, exist_ok=True)
                if not (root / '.git').exists():
                    enclosing = git(root, 'rev-parse', '--show-toplevel', check=False)
                    if enclosing:
                        raise Error('Directory is inside another repository; choose its root or a separate directory.')
                    git(root, 'init', '-b', 'main')
                existing = git(root, 'remote', 'get-url', 'origin', check=False)
                if existing and existing != remote:
                    raise Error(f'Origin already points to {existing}; it will not be replaced automatically.')
                if not existing:
                    ensure_remote(root, remote)
                else:
                    try:
                        github(root, 'repo', 'view', repo, '--json', 'name')
                    except Error:
                        github(root, 'repo', 'create', repo, '--private')
                if args.push:
                    transfer(root, 'push', None, 'Initialize repository')
                print(f'Repository ready: {root}\nOrigin: {remote}')
            else:
                root = args.directory.expanduser().resolve()
                transfer(root, 'push', None, args.message)
                print('Current branch pushed.')
        except (Error, OSError):
            print(GUIDE)
            raise
    run(work)
