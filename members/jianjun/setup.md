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
