# Context and handoff protocol

This protocol is cooperative. No helper detects completion of iCloud syncing or
provides a distributed lock. Keep other computers' agents stopped during a switch;
verify expected handoff/commit and consistent files after sync before acquiring.
Never interpret an absent lock, a fixed delay, or UNCHANGED as proof of full sync.

## Start or resume
Acquire once per editing session (a new conversation needs a fresh ownership
session after the old session has stopped and released). Supply the actual agent:

    python3 script/agent_lock.py acquire --agent opencode --agent-version unknown
    python3 script/agent_context.py check --session SESSION_ID

Check exits 0 for UNCHANGED, 2 for RELOAD_REQUIRED, 1 for an error. It prints a
fingerprint and changed filenames. Errors block editing. A new session always
requires context reading, even if the same agent/computer was used previously.
On reload, read AGENTS.md, HANDOFF.md, recent relevant DEV_NOTES entries and changed
requirements/code; inspect branch, status and staged/unstaged diffs. Do not reread
the whole historical log unnecessarily. Check again after reading, and if the
fingerprint differs review the new changes. Acknowledge the fingerprint you read:

    python3 script/agent_context.py ack --session SESSION_ID --fingerprint HASH

ack refuses if the project changed since check. It records only a comparison
baseline, not evidence that an LLM actually read or understood the files. Never
acknowledge unseen changes. After context loss, reread regardless of UNCHANGED.
At each new prompt/resume use check; do not run it for every tool call. After your
own completed edits, check and acknowledge the state you just reviewed so the
next prompt avoids rereading those same changes. Never skip the ownership check.

The helper hashes tracked and nonignored untracked file contents, executable bits,
Git index, branch, HEAD and status. It detects dirty-content changes even when
Git's short status remains the same. It reads files, not a transactional snapshot;
stop other writers and retry if work/sync is still changing. Keep large raw data
and generated products ignored. Hashing large source trees has a cost. Nested
repositories/submodules require explicit review and currently fail closed.

Cache: macOS ~/Library/Caches/astronomy-agent-context; Linux
~/.cache/astronomy-agent-context. Keys include computer, absolute project path
and session UUID. Do not sync these directories. Cache loss/moving a project
causes a safe reload. No cache or transcript is copied into a new project.

## Finish a request versus hand off
DEV_NOTES records each substantive prompt and its results; finish the existing
entry rather than duplicating it at handoff. HANDOFF is a concise current summary.
At a meaningful checkpoint or actual handoff:
1. Stop modifying background processes; complete notes and HANDOFF content.
2. Run `python3 script/agent_context.py stamp --session SESSION_ID`.
3. Review/stage the relevant files and commit (push only if authorized).
4. If continuing in this same session, check/ack your reviewed final state.
5. If handing over, release the lock last; do not edit again afterward.

stamp adds/replaces a delimited metadata block in HANDOFF.md with a fresh UUID,
UTC timestamp, computer, application/version, session ID, branch and base commit.
The base commit is the commit BEFORE the handoff checkpoint, not its final hash;
Git history identifies the commit containing the handoff. UUIDs are attribution,
not passwords. Never reuse a previous session ID to inherit its cached context.

New projects must remove copied handoff metadata, retain the tools and protocol,
start their own Git repository and lock, and stamp their own first handoff.
The helper does not summarize work, write development entries, install application
hooks, stop external agents, or automatically run when the UI receives a prompt.
The agent follows these instructions and invokes it. Recovery for a crashed lock
must verify the prior owner is stopped; cross-computer recovery is human-controlled
as described in README.md. Never reuse a foreign computer's session token.
