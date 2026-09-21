#!/usr/bin/env python3
"""Rebuild the standalone HTML guide. Development dependency: Markdown."""
from __future__ import annotations
from pathlib import Path
import markdown

root = Path(__file__).resolve().parents[2]
body = markdown.markdown((root/'README.md').read_text(), extensions=['fenced_code', 'tables', 'toc'])
page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>project-setup — User Guide</title><style>
:root{color-scheme:light;--ink:#182b3a;--accent:#075e69}*{box-sizing:border-box}body{margin:0;background:#f2f5f7;color:var(--ink);font:17px/1.65 system-ui,sans-serif}header{background:#123640;color:white;padding:42px max(24px,calc((100% - 960px)/2))}header p{margin:0;opacity:.85}.badge{font-size:13px;text-transform:uppercase;letter-spacing:2px}main{max-width:1000px;margin:0 auto;padding:32px 32px 80px;background:white}h1{font-size:2.5rem;line-height:1.15}h2{margin-top:2.3em;border-bottom:1px solid #dbe3e6;padding-bottom:.4em}h3{margin-top:2em}a{color:var(--accent)}pre{background:#102d38;color:#e8f2f5;padding:20px;border-radius:8px;overflow:auto;font-size:14px;line-height:1.6}code{font-family:ui-monospace,monospace;font-size:.88em}p code,li code,td code{background:#edf2f4;padding:2px 4px;border-radius:3px}table{border-collapse:collapse;width:100%;font-size:15px}th,td{border:1px solid #dbe3e6;padding:10px;text-align:left;vertical-align:top}th{background:#eaf1f3}nav{display:flex;flex-wrap:wrap;gap:16px;padding:14px 0}footer{max-width:960px;margin:20px auto;padding:20px;color:#4b626c}@media(max-width:600px){main{padding:20px 16px}h1{font-size:2rem}table{display:block;overflow:auto}}@media print{body,main{background:white}pre{white-space:pre-wrap}header{padding:20px}a{color:inherit}}
</style></head><body><header><p class="badge">macOS + Linux · Python 3.9+</p><h1>Projects, ready to build.</h1><p>project-setup 1.1.2 · Installation, Git setup, versioning and releases</p></header><main><nav><a href="usage.html">Step-by-step guide</a><a href="#install">Install</a><a href="#create-a-project">Create a project</a><a href="#git-setup">Git helpers</a><a href="#update-and-release">Releases</a><a href="#git-setup">Git reference</a></nav>'''+body+'''</main><footer>Offline user guide · project-setup · <a href="https://github.com/prasundutta151/project-setup">Source and releases</a></footer></body></html>'''
(root/'docs/index.html').write_text(page)

# Maintain a portable step-by-step guide in both HTML and plain text.
usage = (root/'docs/usage.md').read_text()
(root/'docs/usage.txt').write_text(usage)
usage_html = markdown.markdown(usage, extensions=['fenced_code', 'tables', 'toc'])
(root/'docs/usage.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>project-setup step-by-step guide</title><style>body{max-width:1000px;margin:40px auto;padding:0 20px;font:16px/1.6 system-ui}pre{background:#edf2f4;padding:16px;overflow:auto}a{color:#075e69}</style></head><body><nav><a href="index.html">Main documentation</a></nav>'+usage_html+'</body></html>\n')
