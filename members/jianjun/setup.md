# Setup record: jianjun

Fill this in once, before your first session. Section 1.3 and Appendix G of the report are
written from it.

| Item | Value |
|---|---|
| Agent tool and version | Gemini CLI v0.63.0 |
| Model | gemini-3.8-flash |
| Effort or reasoning level | Default (no reasoning toggle exposed in CLI) |
| Subagents used? | No (only CLI-internal utility models: utility_loop_detector, utility_summarizer) |
| Plan / how cost is reported | Pay-as-you-go API Key; cost tracked via Gemini billing dashboard and CLI session summary (input/cache/output token counts) |
| Where the agent runs | WSL2 on Windows (Ubuntu Linux), terminal session in `~/lab_project/mealie-wf-c` |
| Permission mode | Ask before edits (manual mode; `Shift+Tab` set to manual, each Shell/Edit confirmed with "Allow once") |
| Commands the agent may run without asking | None — every Shell, Edit, WriteFile required explicit "Allow once" |
| Network access | Full (WSL2 host network; no proxy or firewall restrictions) |
| How pushing is blocked | `git remote set-url --push origin DISABLED` on the code repository; evidence repository kept outside the agent's working directory |
| Credentials available in the environment | GitHub Personal Access Token stored via `git config --global credential.helper store`; only used by the human for manual push; agent never had push access |
| Machine (CPU cores, RAM) | 8 cores, 16 GB RAM |

## Limits of the sandbox

Gemini CLI does not expose per-path read/edit deny rules. The only boundaries in place during a session were:

- the manual permission prompt (every command needed `Allow once`), and
- the prompt itself, which restricted the agent to the code repository.

No filesystem-level enforcement prevented the agent from reading `~/mealie-agentic-evidence/` if it tried. Isolation therefore relied on the human reviewer rejecting such commands at the permission prompt. Two attempts to read the evidence repository were rejected (log.md P11, P18).

## Deviations for jianjun

**Workflow A (s01).** The session began fresh (no prior project context), matching the Workflow A design. The agent then deviated from the workflow itself by generating an 8-stage plan and asking the human to approve it — behaviour that belongs to Workflow B (log.md P1).

**Workflow C (s01–s03).** Three sessions were run. The C1 gate was not passed. In s02 the human reviewer gave the agent direct solutions ("use `['aerich.models']`", "add a `TortoiseModelRegistry` placeholder model") rather than only checking the gate. This is a deviation from Workflow C's "human checks the gate only" rule and is recorded in log.md under "Human side notes". In s03 the agent made zero code changes.

**Workflow B.** Not run. The lecturer updated the experiment to two workflows per member partway through the semester; jianjun ran A and C.

## Permission settings

Gemini CLI has no per-project permissions file. The equivalent controls were:

- **Interaction mode**: manual (`Shift+Tab` to `manual`, not `auto-accept edits`).
- **Per-command prompt**: every shell invocation, edit and write required `Allow once`. The options `Allow for this session` and `Modify with external editor` were never used.
- **Push**: `origin` push URL set to `DISABLED` in both clones before session 1.
