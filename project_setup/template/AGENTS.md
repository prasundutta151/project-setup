# Shared project instructions

These instructions apply to all agents working in this project.

## Required project contract
Read docs/PROJECT_REQUIREMENTS.md before implementation. It defines the folder
layout, executable installation, JSON configuration, science validation and Git
workflow. Keep docs/requirements.txt and docs/requirements.html synchronized
with it when changing the contract. To create a project from this template, read
docs/CREATE_PROJECT.txt. Local checkpoint commits are authorized by this contract.

## Project facts
- Purpose: Astronomy software; TODO — specify the scientific task.
- Language/framework: TODO.
- Setup command: TODO.
- Test command: TODO.
- Build command: TODO.
- Until these are specified, inspect the project and ask for missing requirements;
  do not invent commands or claim tests passed.

## One editing session at a time
1. Read this file. Reading files and reviewing code do not require a lock.
2. Before changing files or running commands that may change them, acquire the
   lock from the project root:
   `python3 script/agent_lock.py acquire --agent opencode`
   Replace `opencode` with your application name. Retain the returned session ID
   in your session context. The handoff stamper records it as attribution,
   never as permission for another session to reuse it.
3. If acquisition fails, do not edit, wait indefinitely, or remove the lock.
   Report the owner and let the user resolve the existing session.
4. Follow docs/CONTEXT_WORKFLOW.md: run agent_context.py check at each new
   prompt/resume. New sessions or changed state require context reading; unchanged
   sessions retain context. Acknowledge only the fingerprint actually reviewed.
   Context loss always requires rereading. Inspect Git state and relevant diffs.
5. Preserve existing changes. Do not reset, clean, overwrite, or silently stash
   someone else's work. Do not switch branches with unresolved changes.
6. Keep the lock throughout the editing session. Do not reacquire or rewrite it
   for each action. Before resuming after a pause, confirm ownership using:
   `python3 script/agent_lock.py check --session YOUR_SESSION_ID`
   Stop editing if ownership cannot be confirmed.
7. Only one session may own this checkout, including across different apps.
   Do not launch independent editing agents against this checkout.

## Documentation and Git setup
Read docs/DOCUMENTATION_RULES.md. Generate HTML/TXT user manuals only when
explicitly requested through the external project-document workflow; do not
rebuild them at each coding prompt. CLI help, development notes, current handoff
and essential setup instructions remain maintained. Record pending manual changes.
Read docs/GIT_SETUP.txt: initialize a new project's own repository immediately
at creation; guide remote setup when missing, without guessing or publishing.

## Working practices
- Make changes relevant to the user's request; preserve unrelated work.
- Follow existing project conventions and keep changes reviewable.
- Run appropriate checks and report actual results, including checks not run.
- Never commit credentials, API keys, downloaded models, or local lock state.
- Do not push, publish, deploy, or message others unless authorized.
- Keep instructions stable; put temporary task progress in HANDOFF.md.

## Development log
Follow the Development record section of docs/PROJECT_REQUIREMENTS.md.
Maintain developer/DEV_NOTES.md using its timestamped format for each substantive
request: original prompt (redacted as needed), summary, objective, agent/version,
model if known, computer, changes, verification and status. Preserve history.
Update the log while holding the lock and include it in the related checkpoint.
Never invent missing agent metadata or copy template history into a new project.

## Handoff
Before another application takes over:
1. Stop or finish all commands and background tasks that can modify files.
2. Complete the developer/DEV_NOTES.md entry, then update HANDOFF.md with the objective, completed and remaining work,
   changed files, actual test results, risks, and the next recommended action.
3. Run `python3 script/agent_context.py stamp --session YOUR_SESSION_ID` after
   updating the summary. Then, if checkpoint commits are authorized, review and stage only relevant files,
   then commit. Otherwise describe the uncommitted changes in the handoff.
4. Release ownership last:
   `python3 script/agent_lock.py release --session YOUR_SESSION_ID`
5. Do not make further edits after releasing. A new editing session must acquire
   a new lock and reread the current project state.

## Limitations and recovery
This is a cooperative local lock, not an operating-system write barrier.
It does not coordinate separate clones on other computers. Never infer that a
lock is abandoned solely from its age. Follow README.md for crash recovery.
