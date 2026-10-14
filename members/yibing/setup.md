# Setup record: yibing

Filled for the experiment environment used for Yibing's runs. Section 1.3 and Appendix G of the report can use this record.

| Item | Value |
|---|---|
| Agent tool and version | Codex CLI 0.155.0-alpha.16 |
| Model | gpt-6-astra |
| Effort or reasoning level | ultra |
| Subagents used? | Yes. Workflow A unexpectedly spawned three native child agents even though `multi_agent=false` was requested. Their records are in `wf-a/transcripts/s01-native/session-tree.json`. Workflow C used fresh staged sessions; coordinating work outside those sessions is excluded from experiment time. |
| Plan / how cost is reported | ChatGPT/Codex subscription. Actual input, cached-input and output token counters come from the exported metadata. API-equivalent dollar cost was not provided, so cost is recorded as unavailable rather than estimated. |
| Where the agent runs | Local macOS on Apple Silicon. Each workflow used a separate Mealie clone under the Codex workspace; Python commands ran through `uv`. |
| Permission mode | Requested `on-request`; the non-interactive Codex execution reported effective `never` (fail-closed) inside a workspace-write sandbox. No bypass flag was used. |
| Commands the agent may run without asking | Read/search/edit inside its assigned clone and approved lint, type-check and test commands. Git push, remote/config changes, credential access, the evidence repository and other workflow clones were denied. |
| Network access | Shell network access disabled. During A, an existing GitHub connector was still available and the agent used it to read public dependency source; this exception is recorded in `settings-observation.json`. |
| How pushing is blocked | Each experiment clone's origin push URL was set to `DISABLED`; `git push`, `gh`, `git remote` and `git config` were denied in the tool rules. No experimental agent push occurred. A and C were published manually after the experiments. |
| Credentials available in the environment | Codex reused the existing app login. The sandbox denied `~/.codex/auth.json` and `~/.ssh`. No credential value was placed in a prompt. An existing authenticated GitHub connector capability was available during A. |
| Machine (CPU cores, RAM) | Apple Silicon arm64, 8 CPU cores. RAM was not obtained because `sysctl` was denied by the sandbox. |

## Permission settings

The exact settings are attached under `members/yibing/settings/`:

- `settings/wf-a/config.toml` and `settings/wf-a/rules/experiment.rules`
- `settings/wf-b/config.toml` and `settings/wf-b/rules/experiment.rules`
- `settings/wf-c/config.toml` and `settings/wf-c/rules/experiment.rules`

`settings-observation.json` records the difference between requested and effective settings. The same tool, model and reasoning level were retained for A, the B planning-only session and C.
