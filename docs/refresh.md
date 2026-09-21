# Refresh existing projects with an AI agent

```sh
project-setup --refresh MyProject --proj-dir ~/Projects
project-setup --refresh MyProject --proj-dir ~/Projects --ai manual
```

The target is PARENT/PROJECT, not a new destination. Interactive use offers
Antigravity, ChatGPT, Claude, OpenCode and Manual. Without a terminal it defaults
to Manual. Use --ai antigravity|chatgpt|claude|opencode|manual to select explicitly.

Preparation reads the existing project and writes a migration prompt and request
metadata outside it, under macOS ~/Library/Caches/project-setup/refresh or Linux
~/.cache/project-setup/refresh. No target files change in preparation/manual mode.
The full prompt is printed for copying into an agent, and its file path is shown.
If using a browser/chat agent, give it filesystem access or provide the referenced
project/template files; a prompt alone cannot edit files on your computer.

## Automatic invocation (optional)

There is no assumed universal command for the listed applications. Configure the
actual installed agent interface, including how it reads a prompt file:

```sh
project-setup --refresh MyProject --proj-dir ~/Projects --ai opencode \
  --ai-command 'YOUR_AGENT_EXECUTABLE YOUR_ARGUMENTS {prompt_file}'
```

The uppercase words above are placeholders, not a working OpenCode command. Consult
your installed agent's --help and replace them with its actual arguments. You can
instead set PROJECT_SETUP_AI_COMMAND_OPENCODE (or _CLAUDE, _CHATGPT, _ANTIGRAVITY).
PROJECT_SETUP_AI_COMMAND is a shared fallback. The command is split into an argv
array, never run through a shell. {prompt_file} is required; {project_dir} is
optional. Quote executable paths with spaces. Shell pipelines/redirections are not
supported. No automatic model selection, API credentials, installation or permission
bypass is supplied. Manual mode always prints the prompt without starting a process.
A named agent with no command configured also prints the full handoff prompt and
reports PREPARED ONLY. Selection alone does not integrate with a desktop app.

Automatic execution requires a clean, committed Git repository at the target root.
It refuses occupied modern locks and busy legacy .agent_lock files. It holds a
local lock while invoking the configured agent; the session token is passed through
PROJECT_SETUP_REFRESH_SESSION. The child uses that ownership, must not release it,
and must stop all modifying background tasks before returning. The launcher checks
required outputs, unchanged HEAD/remotes, and releases only its own lock. It does
not provide distributed locking or sandbox the agent. If the command fails, partial
changes remain for inspection. No rollback, publication or commit is automatic.

## Migration instructions carried in the prompt

- Preserve scientific behavior, existing instructions, code, histories and data.
- Write developer/REFRESH_REPORT.md describing the plan, mapping, tests and blockers.
- Adapt script/version/docs/pipeline/json/plot/developer/tests without blind overlay.
- Preserve old commands through wrappers where needed; do not bulk-move observations.
- Preserve version history; handle root VERSION versus version/ collisions on macOS.
- Adapt lock/context helpers, updater, prompts, release manifest and ignore rules.
- Preserve licensing and author attribution; refreshing does not relicense software.
- Keep manuals on-demand; finish DEV_NOTES and handoff with actual verification.
- Leave changes uncommitted for review. Structural success is not scientific proof.

After manual mode, your chosen agent performs the migration. After automatic mode,
review REFRESH_REPORT.md, git diff and test results before committing. A failed run
may contain useful partial work; do not rerun blindly over it. --proj-description
can supply an explicit description override for the agent to apply during refresh.
