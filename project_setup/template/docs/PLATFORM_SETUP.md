# Connecting your agent applications

Open the same Model_Project folder in each local application. Only one should
be editing at a time. Separate worktrees and cloud environments are different
checkouts; this local lock does not coordinate them.

## Codex and OpenCode
Both support project AGENTS.md instructions. Use a local session in this exact
folder. At first use, ask the agent to read AGENTS.md and explain the lock and
handoff procedure before starting work. Repeat the startup prompt when resuming
an old conversation whose view of the project may be outdated.

## Antigravity
Configure an always-on workspace rule using the application's current rule UI.
Use this text as the rule:

> Before working on this project, read and follow the root AGENTS.md. Before
> editing, acquire its session lock; then read HANDOFF.md and inspect Git status
> and diffs. If the lock is held, do not edit. Follow the handoff procedure before
> releasing the lock.

This template does not assume a particular Antigravity rule-directory version.

## Bionic
Open this directory as a coding project. Automatic discovery of AGENTS.md has
not been verified here. Put the startup prompt below into each new session,
 or persistent project instructions if your installed version provides them.

## Startup prompt for any application

Read AGENTS.md and follow it. Acquire the local lock using your application name.
If another session owns it, stop before editing and report the owner. After
acquiring it, read recent developer/DEV_NOTES.md entries and HANDOFF.md and inspect the current Git branch, status, and
staged/unstaged diffs. Preserve existing changes. Then continue this task:
[INSERT TASK HERE]. Keep the returned session ID for ownership checks and release.

## Handoff prompt for any application

Prepare this project for another agent. Stop or finish background work that can
modify files. Complete the timestamped developer/DEV_NOTES.md entry with the request, objective,
agent identity, changes and checks. Update HANDOFF.md with the objective, changes, outstanding work,
actual test results, and next step. Preserve unrelated changes. If I have
requested a checkpoint commit, review and commit the relevant files. Release
your session lock last, and report the handoff state. Make no further edits.

## Documentation
- Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- OpenCode: https://opencode.ai/docs/rules/
- Bionic projects: https://lmstudio.ai/docs/bionic/projects-and-sessions

## Every-session context protocol
Follow docs/CONTEXT_WORKFLOW.md at startup/resume: acquire a fresh session for a
new conversation, check state and reload only when required (always after context
loss), then acknowledge the reviewed fingerprint. At handoff update notes and
summary, stamp a fresh handoff ID, commit and release. Follow DOCUMENTATION_RULES.md
for on-demand project-document manuals and GIT_SETUP.txt for initial Git/remote
setup. These are agent instructions, not installed app hooks.
