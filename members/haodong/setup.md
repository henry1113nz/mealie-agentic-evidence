# Setup record: haodong

Filled in before the first session. Section 1.3 and Appendix G of the report are written from it.

| Item | Value |
|---|---|
| Agent tool and version | Claude Code 2.1.287 (VS Code extension; same binary used from the terminal) |
| Model | Claude Opus 5.5 (`"model": "opus"` in ~/.claude/settings.json) |
| Effort or reasoning level | high |
| Subagents used? | Not requested in any prompt; record in the log if the agent starts any |
| Plan / how cost is reported | Subscription; API-equivalent cost from `/cost` at the end of each session |
| Where the agent runs | Mealie dev container (Docker on Windows 11 / WSL2). Each workflow has its own clone under `/home/vscode/rewrite/mealie-wf-{a,b,c}` on the container's own disk |
| Permission mode | Default: the agent asks before edits and before commands not already allowed |
| Commands the agent may run without asking | None added beyond Claude Code defaults |
| Network access | Yes (needed to install Tortoise ORM and Aerich from PyPI). No registry credentials are configured |
| How pushing is blocked | Push URL of `origin` set to `DISABLED` in each clone; `git push`, `git remote`, `git config` and `gh` denied in `.claude/settings.local.json` |
| Other access blocked | Read and Edit denied for the evidence repository, the other two workflow clones and `/workspaces/mealie`, so one run cannot see another run's code or the experiment design |
| Credentials available in the environment | VS Code forwards the host's git credentials into the container, so a git push would authenticate if it were not blocked. `gh` is not logged in. No PyPI, npm or production credentials |
| Global instructions | No user-level `~/.claude/CLAUDE.md`. The repository's own AGENTS.md (and CLAUDE.md, which points to it) is left as it is |
| Machine | 16 CPU cores, 7 GB RAM available to the container |

## Limits of the sandbox

The Read deny rules apply to Claude Code's file tools. A shell command such as `cat` on a
denied path is not covered by those rules, so isolation also relies on the agent having no
reason to look outside its own clone. Any access outside the clone seen in a transcript will
be recorded in the log.

## .claude/settings.local.json (mealie-wf-a; the other two deny each other the same way)

```json
{
  "permissions": {
    "deny": [
      "Bash(git push:*)",
      "Bash(git remote:*)",
      "Bash(git config:*)",
      "Bash(gh:*)",
      "Read(//home/vscode/rewrite/mealie-wf-b/**)", "Edit(//home/vscode/rewrite/mealie-wf-b/**)",
      "Read(//home/vscode/rewrite/mealie-wf-c/**)", "Edit(//home/vscode/rewrite/mealie-wf-c/**)",
      "Read(//home/vscode/rewrite/mealie-agentic-evidence/**)",
      "Edit(//home/vscode/rewrite/mealie-agentic-evidence/**)",
      "Read(//workspaces/mealie/**)",
      "Edit(//workspaces/mealie/**)"
    ]
  }
}
```

The file is ignored by git (`*.local.*` in .gitignore), so it never appears in the branch.
