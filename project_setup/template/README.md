# __PROJECT__

__OBJECTIVE__

Read AGENTS.md and startup-prompt.txt to work with an agent.
See docs/GIT_SETUP.txt for remote setup and docs/CONTEXT_WORKFLOW.md for handoffs.
Run script/project-update --help for version/release/Git operations.

## Manual lock commands

```sh
project-update --lock acquire
project-update --lock aquire   # accepted spelling alias
project-update --lock status
project-update --lock release
```

The installed command uses the current Git repository. To work from anywhere,
use /absolute/project/script/project-update instead. Acquisition prints a fresh
session ID; --agent NAME and --agent-version VERSION label its owner. This is
the same .agent-state/lock used by agent_lock.py. Run lock commands separately
from version, release and Git operations.

Interactive release displays ownership and asks you to stop the writer, then
type release. Agents/scripts must supply --session OWNER_SESSION_ID; wrong
sessions, foreign computers and corrupt metadata are refused. An already unlocked
project reports UNLOCKED. No automatic timeout or force release is introduced.
The old boolean .agent_lock file is not managed by these commands.
