# DOCUMENTATION.md — documentation rule file (test_project)

- Manuals in this directory are generated/refreshed ONLY on explicit
  `complex: document` or `general: document` requests. Never auto-rebuild.
- Full on-demand rules: `src/docs/DOCUMENTATION_RULES.md` is absent in this
  project (no ARX source); the AGENT file summary applies instead:
  HTML/TXT only on request; external `project-document` tool via its real
  interface only (unavailable at v0.0.2 — manuals written directly);
  session-lock ownership required (held by documenting session);
  content derived from current source, `--help`, and tested examples;
  links and rendered HTML validated; never publish automatically.
- Structure: `index.html` (tree) → `README.html` (+ `README.txt` equivalent),
  `test_project-step-by-step.html/txt`, `chisq_fit.html/txt` per-command ref,
  `style.css`, `LICENSE.html/txt`. No MODEL_LICENSE (no ML model ships).
- Every HTML page carries license footer lines linking to `LICENSE.html`.
- Core docs work offline (local CSS, system fonts, no CDN/JS).
- Software version + generation date recorded in each manual.
- Pending manual changes are tracked in HANDOFF/DEV_NOTES until requested.
