# Setup record: yawen

Completed retrospectively on 2026-10-15 using terminal checks, session metadata and experiment records. The initial extension version and every earlier session's settings were not independently archived.

| Item | Value |
|---|---|
| Agent tool and version | Codex extension for VS Code: openai.chatgpt@26.1007.21434, verified on 2026-10-15. Initial experiment version not separately recorded. |
| Model | gpt-6-luna, confirmed in current configuration and Workflow B s10 metadata. |
| Effort or reasoning level | low. |
| Subagents used? | Guardian auxiliary sessions appear in the records. I did not explicitly request task delegation. Identified guardian usage was recorded separately. |
| Plan / how cost is reported | Subscription/API billing arrangement pending confirmation. Tokens were extracted from session JSONL records. Cached input is included in input totals. API-equivalent cost was not calculated. |
| Where the agent runs | VS Code connected to Ubuntu under WSL2 on my Windows laptop. Code clones are under /home/luna/574Agentic/. The evidence repository is outside the code workspace. |
| Permission mode | on-request approval policy; workspace-write sandbox. Selected bounded diagnostics and tests ran outside the sandbox after explicit approval. |
| Commands the agent may run without asking | Routine inspection, edits and checks permitted by the sandbox/tool policy. A complete command allowlist was not captured. |
| Network access | Session sandbox metadata: network_access=false. Approved outside-sandbox checks accessed the dedicated local PostgreSQL endpoint. General unrestricted agent network access was not established. |
| How pushing is blocked | Code origin push URL: DISABLED. Prompts prohibit pushing and Git configuration/remote changes. A separate tool-level deny rule was not independently captured. I uploaded evidence manually. |
| Credentials available in the environment | GitHub CLI authentication was configured in WSL. GitHub credentials were present; their inaccessibility to the agent was not established. Code-repository push permission was denied; evidence-repository manual uploads succeeded. Dedicated local PostgreSQL test credentials were supplied. No credential values are included here. |
| Machine (CPU cores, RAM) | WSL-visible: 32 logical processors, approximately 15 GiB RAM and 4 GiB swap. Physical CPU core count and Windows host RAM were not independently recorded. |

## Verified configuration

Workflow B s10 session: 01a13d9e-927a-7170-b7b9-cec3b99e03d3.

- model: gpt-6-luna
- effort: low
- approval_policy: on-request
- sandbox_policy.type: workspace-write
- sandbox_policy.network_access: false
- sandbox_policy.exclude_slash_tmp: false
- sandbox_policy.exclude_tmpdir_env_var: false

Current selected config.toml values:

- model = "gpt-6-luna"
- model_reasoning_effort = "low"

These are extracted settings, not the complete permission-settings file. The full file and any additional command rules were not archived.

## Environment notes

Setup used Python 3.14.4 and uv 0.13.0 in WSL. Workflow A and B used separate code clones and branches.

Sandboxed async SQLite and FastAPI TestClient checks sometimes stalled. Identical bounded checks passed outside the sandbox after approval. The transcripts record these differences.

Docker Desktop integration with Ubuntu provided a dedicated PostgreSQL 16 test container during Workflow B. Agent code execution ran in WSL, not inside the Mealie container.

Earlier school-computer and Windows-VM setup attempts were abandoned. The Workflow A and B runs recorded here used my own laptop.
