"""Generate custom draft licensing records and managed HTML attribution."""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import re
from typing import Optional
from urllib.parse import urlparse

MARKER = 'project-lisence managed draft'
BEGIN = '<!-- project-lisence footer begin -->'
END = '<!-- project-lisence footer end -->'
FIELDS = ('project', 'author', 'author_email', 'author_affil', 'doi_paper', 'link')

def atomic_write(path: Path, text: str) -> None:
    if path.is_symlink():
        raise ValueError(f'Refusing symlink: {path}')
    temp = path.with_name(path.name + '.tmp')
    if temp.exists() or temp.is_symlink():
        raise ValueError(f'Temporary path already exists: {temp}')
    try:
        with temp.open('x', encoding='utf-8') as stream:
            stream.write(text)
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()

def footer_pages(root: Path) -> list[Path]:
    pages = list(root.glob('*.html'))
    for folder in ('docs', 'doc', 'lisence'):
        base = root / folder
        if base.is_symlink():
            raise ValueError(f'Refusing symlink directory: {base}')
        if base.is_dir():
            pages.extend(base.rglob('*.html'))
    for page in pages:
        if page.is_symlink() or any((root/p).is_symlink() for p in page.relative_to(root).parents if p != Path('.')):
            raise ValueError(f'Refusing symlink: {page}')
        if not page.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Page outside project: {page}')
    return pages

def update_footers(root: Path, info: dict[str, str]) -> int:
    pages = footer_pages(root)
    for page in pages:
        link = Path(os.path.relpath(root/'lisence/LICENSE.html', page.parent)).as_posix()
        attribution = ' · '.join(info[key] for key in ('author', 'author_affil', 'author_email'))
        block = (BEGIN + '\n<footer aria-label="Licensing"><p>Copyright / licensing contact: '
                 + html.escape(attribution) + '. <a href="' + html.escape(link, quote=True)
                 + '">Custom source-available licensing draft</a> — pending author approval.</p></footer>\n' + END)
        text = page.read_text(encoding='utf-8')
        text = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\s*', '', text, flags=re.S)
        if re.search(r'</body\s*>', text, re.I):
            text = re.sub(r'</body\s*>', lambda m: block + '\n' + m.group(), text, count=1, flags=re.I)
        else:
            text += '\n' + block + '\n'
        atomic_write(page, text)
    return len(pages)

def generate(root: Path, info: dict[str, str], terms: str) -> int:
    for key in FIELDS:
        if not isinstance(info.get(key, ''), str):
            raise ValueError(f'{key} must be a string')
        info.setdefault(key, '')
    for key in ('project', 'author', 'author_email', 'author_affil'):
        if not info[key].strip() or info[key].startswith('YOUR_'):
            raise ValueError(f'Provide {key} in flags or the JSON model')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', info['author_email']):
        raise ValueError('Provide a valid author email')
    if info['link'] and (urlparse(info['link']).scheme not in ('http', 'https') or not urlparse(info['link']).netloc):
        raise ValueError('--link must be an HTTP(S) URL')
    folder = root/'lisence'
    if folder.is_symlink():
        raise ValueError('Refusing symlink lisence directory')
    folder.mkdir(exist_ok=True)
    outputs = [folder/name for name in ('license-info.json', 'LICENSE.txt', 'LICENSE.html')]
    for path in outputs:
        if path.is_symlink() or (path.exists() and MARKER not in path.read_text(encoding='utf-8')):
            raise ValueError(f'Refusing to replace unmanaged file: {path}')
    footer_pages(root)  # Validate paths before writing records.
    rendered = terms
    for key in FIELDS:
        rendered = rendered.replace('{{' + key + '}}', info[key] or '(not supplied)')
    record = dict(info, generator=MARKER, status='draft', terms_template=terms)
    text = MARKER + '\nDRAFT — NOT AN EFFECTIVE LICENSE GRANT; requires author and legal review.\n\n' + rendered
    atomic_write(outputs[0], json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    atomic_write(outputs[1], text)
    atomic_write(outputs[2], '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Licensing draft</title></head><body><main><h1>Licensing draft</h1><pre style="white-space:pre-wrap">' + html.escape(text) + '</pre></main></body></html>\n')
    return update_footers(root, info)

def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Project directory name')
    parser.add_argument('--proj-dir', type=Path, default=Path.cwd(), help='Parent directory, or the project directory itself')
    for flag in ('author', 'author-email', 'author-affil', 'doi-paper', 'link'):
        parser.add_argument('--'+flag)
    parser.add_argument('--lisence-file', '--license-file', type=Path, help='JSON metadata model or UTF-8 text terms template')
    args = parser.parse_args(argv)
    try:
        if args.project in ('.', '..') or Path(args.project).name != args.project:
            raise ValueError('--project must be a directory name')
        parent = args.proj_dir.expanduser().resolve()
        root = parent if parent.name == args.project else parent/args.project
        if not root.is_dir() or root.is_symlink():
            raise ValueError(f'Project directory not found or is a symlink: {root}')
        assets = Path(__file__).parent/'template/lisence'
        info = {}
        saved = root/'lisence/license-info.json'
        if saved.is_file() and not saved.is_symlink():
            info = json.loads(saved.read_text(encoding='utf-8'))
        terms = info.get('terms_template') or (assets/'MODEL_LICENSE.txt').read_text(encoding='utf-8')
        if args.lisence_file:
            path = args.lisence_file.expanduser()
            if path.suffix.lower() == '.json':
                model = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(model, dict):
                    raise ValueError('License model must be a JSON object')
                info.update(model)
                terms = model.get('terms_template') or terms
                if not isinstance(terms, str):
                    raise ValueError('terms_template must be a string')
            else:
                terms = path.read_text(encoding='utf-8')
        info = {key: getattr(args, key, None) if getattr(args, key, None) is not None else info.get(key, '') for key in FIELDS}
        count = generate(root, info, terms)
        print(f'Action: Created licensing draft for {args.project}.')
        print(f'Result: lisence/ records written; {count} HTML pages attributed; existing licenses unchanged.')
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(1, f'project-lisence: {exc}\n')

if __name__ == '__main__':
    main()
