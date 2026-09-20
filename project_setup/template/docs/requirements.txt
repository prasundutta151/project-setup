# Astronomy software requirements

This is the reusable project contract. Agents must read it together with
AGENTS.md before implementing software. A user's explicit project instructions
can override defaults; record significant deviations in docs/decisions.txt.

## Directory layout
- script/: Python 3, shell and Swift scripts, C++/Swift source and CLI launchers.
  Keep agent_lock.py here as development tooling, not a scientific command.
- version/: VERSION and CHANGELOG.txt; Git stores historical source versions.
  Do not duplicate source trees for every version. Release bundles only when
  requested; generated archives belong in an ignored version/dist/ directory.
- docs/: rules and setup guides; HTML/TXT user manuals generated only when
  explicitly requested through project-document (see DOCUMENTATION_RULES.md).
- pipeline/: sample pipeline descriptions in JSON, with documented step order.
- json/: sample setup and scientific-parameter JSON files, and schemas if used.
- plot/: small sample/reference plots. Generated plots go in ignored plot/generated/.
- developer/: Git-tracked DEV_NOTES.md recording requests, objectives, agent
  attribution, changes and validation.
- tests/: meaningful CLI, configuration and scientific validation tests.
- bin/, build/, .venv/: generated local executables, build output and environments;
  ignored by Git. Raw observations and routine outputs go in ignored data/ and output/.

## Executable commands from any working directory
Every user-facing scientific command must work independently of the current
working directory. Use a project-prefixed command name to avoid name collisions.
Python/shell/interpreted Swift entry points need a correct shebang and executable
permission. C++ and compiled Swift require a documented build step; their source
files are not themselves executables. Package Python commands with console entry
points where appropriate, or install a launcher that selects the project's own
interpreter. Never assume whichever `python3` is on PATH has the dependencies.

Provide an idempotent user-local installer when the first scientific command is
implemented. Install launchers or links in ~/.local/bin (or an explicitly selected
prefix); preserve existing unrelated commands and refuse collisions. Document
how to add that directory to PATH, uninstall, and reinstall after moving the
project. Do not require sudo or silently modify shell startup files. Resolve
project resources from the installed package/executable or project location,
never from the caller's working directory. Test the installed command from a
temporary directory outside the project, including paths containing spaces.

## CLI and two JSON files
Every scientific command must provide --help, --version, --setup-file PATH,
--parameter-file PATH, and --print-config. Internal development helpers such as
agent_lock.py, agent_context.py and project-update are exempt. There cannot be two different options both named
--setup-file; --parameter-file is the distinct name for scientific parameters.

The setup JSON contains schema_version, input_file, output_path, plot_path and
parameter_file. Add documented command-specific path fields when needed. The
parameter JSON contains schema_version and a parameters object with named
scientific settings. Each command defines its accepted settings, types, defaults,
units and valid ranges. Samples are examples, not mandatory science choices.

Configuration precedence, highest first:
1. Explicit CLI flags for individual values.
2. Values in the parameter JSON selected by explicit --parameter-file; if absent,
   use the parameter_file referenced by the setup JSON.
3. Built-in, documented defaults.
Setup JSON supplies path defaults; explicit path flags override those defaults.
The explicitly selected parameter file REPLACES the setup-referenced parameter
file; do not merge both silently. Omitted CLI flags must not overwrite JSON with
parser defaults. Preserve explicit false, zero and empty-list values when valid.
No setup file is required if CLI/defaults supply all required inputs.

Resolve paths inside each JSON relative to THAT JSON file's parent directory.
Resolve CLI paths relative to the caller's working directory. Document any home
expansion; do not silently expand environment variables. In particular, resolve
setup.parameter_file relative to the setup JSON, not the project or shell folder.

Validate JSON syntax, schema version, unknown keys, types, ranges, required
values and input existence before scientific processing. Report actionable
errors and nonzero exits. Never evaluate JSON as executable code. Document which
paths are files vs directories; output_path and plot_path are directories by
default. Do not overwrite scientific results without an explicit overwrite flag.
--print-config prints the resolved effective configuration and exits without
processing or creating output directories.

## Scientific reproducibility and pipeline examples
Document physical units, coordinate frames, time scales, array conventions,
missing-data handling, and numerical assumptions wherever applicable. Record
software version, effective configuration, input identifiers and random seed
when applicable beside generated results. Do not invent scientific algorithms
or silently change calibration conventions. Include small synthetic fixtures
and known-answer checks where useful; exclude large observations from Git.

Pipeline JSON is declarative sample documentation unless a runner is actually
implemented. Each step names a command and its setup/parameter file. A future
runner must define relative paths against the pipeline JSON directory, construct
argument arrays without shell eval, stop/report failed steps, and pass each
command the documented configuration flags. Label non-runnable examples clearly.

## Git and versions
At the beginning of project creation, before copying/customizing the scaffold,
initialize its own Git repository following docs/GIT_SETUP.txt, excluding
any template .git and .agent-state directories. Honor existing repositories.
Start VERSION at 0.1.0; scientific commands obtain --version from this one source
(or a generated build/package value derived from it). Update CHANGELOG.txt for
meaningful user-visible changes. Bump semantic versions for intentional releases:
patch for compatible fixes, minor for compatible features, major for incompatible
changes. Do not bump versions for every edit or claim tags exist before creation.

The user authorizes local checkpoint commits of relevant project work after
validation and at handoff. Review staged diffs, exclude unrelated files and
secrets, and use informative messages. If validation fails, fix it or clearly
label an unfinished checkpoint and record failures. If Git identity is missing,
report the required configuration without inventing an author. Do not commit
on every file write and do not install automatic background commit hooks.

A local commit is not an upload. Push only when the user has specified a remote
and authorized pushing; never guess the account, remote or branch. Record a
failed commit/push honestly. Use annotated release tags only for an intentional
release. Git is the history; version/ is release metadata.

## Development record
Read recent developer/DEV_NOTES.md entries at session start alongside HANDOFF.md.
For each substantive project request, record its original user wording (redact
secrets/private data and mark omissions), a polished summary, objective, actual
changes with file paths, verification results and remaining work. Group related
follow-up prompts in one entry only if each request remains identifiable. Log
planning/workflow changes too; do not create an entry for every tool call.

Use the timestamped format in developer/DEV_NOTES.md, including timezone and UTC
offset, agent application/version, model when exposed, computer/OS, branch and
starting commit. Use "unknown" for unavailable metadata; never infer the model
from a product name. Log user requests, not hidden reasoning or internal prompts.

Update the entry before checkpointing or handoff, while holding the project lock.
Keep newest entries first and preserve history. Correct prior errors with an
explicit dated correction rather than silently rewriting history. Record failed
or incomplete work honestly. The entry's own commit hash is not known before
commit; Git history identifies it. Do not create recursive hash-update commits.

Commit this log with related changes and synchronize it with the repository
between computers. It is an agent-maintained record, not an automatic capture or
a tamper-proof audit trail. Resolve Git conflicts by preserving both entries.
HANDOFF.md contains current state; DEV_NOTES.md preserves chronological history.
New projects retain the format, substitute their actual name in the title and
introduction, and start with their own creation entry. Never carry over the
template's historical entries or erase an existing project's development log.

## Context, documentation and remote setup protocols
Follow docs/CONTEXT_WORKFLOW.md for session cache, fingerprint checks and attributed
handoff UUIDs. A new session always reloads context; an unchanged continuing session
can reuse it. Update DEV_NOTES for each substantive prompt; finalizing at handoff
must not duplicate the same request. Cache lives outside the synced project.

Follow docs/DOCUMENTATION_RULES.md for GDP-style user manuals generated only when
explicitly requested via project-document. Ordinary coding and creation do not
trigger HTML/TXT regeneration. Maintain operational notes, CLI help and lightweight
setup instructions; record pending manual changes. Template contract HTML/TXT
mirrors are administrative reference copies, not generated application manuals.

Follow docs/GIT_SETUP.txt at creation: initialize local Git immediately, make a
reviewed scaffold checkpoint before implementation when identity is configured,
and provide remote-link guidance if none exists. Do not invent a remote or push
without authorization. Never confuse a local checkpoint with an uploaded one.

## Standalone project updater
Every project must retain executable script/project-update. It resolves the
project from its own location and works after project-setup is uninstalled.
Use version/VERSION as the single source of version history and version/dist/
for releases; the updater also supports older root VERSION/versions layouts.
With an active agent lock, pass --session SESSION_ID. For legacy CLI naming,
--version minor increments the patch component, --version middle increments
the feature component, and --version major increments the major component.
The no-value --version defaults to a patch increment. Keep CHANGELOG accurate.
--git-push stages all nonignored changes: review first and use ordinary Git
with explicit file staging if unrelated changes exist. Release only allowlisted
paths from release-files.txt; never include observations or private notes by
default. Updater does not automatically write handoff summaries or developer logs.
