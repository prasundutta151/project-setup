# On-demand project documentation contract

Generate or refresh user-facing HTML/TXT manuals ONLY when explicitly requested,
including a documentation task dispatched by the external project-document tool.
Ordinary coding, creation, commits and handoffs must not automatically rebuild
manuals. Keep lightweight README setup facts, CLI help, agent instructions,
HANDOFF and DEV_NOTES accurate at all times. Record pending manual changes in
HANDOFF/DEV_NOTES until documentation is requested. Existing manuals are preserved.
This rule supersedes the template's earlier automatic HTML/TXT generation rule.

## External tool boundary
When documentation is requested, locate project-document and inspect its help or
source to learn its real interface before invoking it. Do not invent options,
install a different similarly named program, or claim it ran when unavailable.
If absent, report the missing tool and request its location; continue independent
work, but do not silently replace the requested external workflow. Pass this
contract and the selected project to the external tool using its supported
interface. If it cannot consume rules, report that integration gap. Read-only
inspection does not need ownership; writing documentation requires the project
lock. If an external agent writes, stop the original writer and hand over ownership
rather than having two editing sessions use the same checkout concurrently.

## GDP-derived structure (portable; GDP need not be installed)
Reference inspected: Documents/GDP/doc/README.html, gdp-step-by-step.html,
gdp-flag.html, gdp-product-gains.html and style.css. Adapt the layout to the actual
project; do not copy GDP commands, science assumptions or observations.
Use this project's docs/ directory (GDP uses doc/):
- index.html linking to README.html, the main overview; README.txt as plain text.
- <project>-step-by-step.html and .txt: workflow table with step, goal and command,
  followed by numbered actions, command examples, expected output patterns and
  verification/recovery steps.
- One <command>.html and .txt for each implemented public command: title and short
  description, Documentation Tree navigation, Product Formats links where relevant,
  link to the step-by-step guide, Purpose, Usage, Options, Inputs/Outputs,
  Examples, scientific assumptions and troubleshooting.
- Options tables include type, default, required/optional status, units, ranges
  and precedence; explain both setup/parameter JSON files and relative paths.
- <project>-product-<name>.html and .txt for each actual output format: filename
  convention, fields/arrays, dtype, shape, units, coordinate/time conventions,
  missing values, provenance/version metadata and a reading example.
- Shared local style.css: readable system font, light background, restrained
  colored sections, centered width around 1000px, readable tables, contrasting
  command/output blocks and responsive narrow-screen layout. Follow GDP's
  linked documentation tree and code/table organization, not a monolithic dump.
- Real sample plots with captions, parameter context and regeneration commands;
  use relative links to plot/ samples or local documented assets. Do not fabricate
  results or run expensive science solely to fill documentation without scope.

## Generation and validation
Derive documentation from current source, --help and tested examples. Include the
software version and generation date; distinguish illustrative output from actual
runs. HTML and TXT must cover equivalent facts from a shared source where feasible.
Keep core navigation and content usable offline without CDN dependencies or
JavaScript-only content. Do not export personal paths, secrets or private data.
Check links, anchors, sample JSON and command names; render/visually inspect HTML
and record actual checks and limitations. Update DEV_NOTES with the request,
tool/version when known, files changed and validation. Commit reviewed output
with the authorized local checkpoint. Do not publish automatically.
