# Workflow notes: jianjun / wf-a

Run as a fresh session with no prior project context, so this is "single instruction, fresh agent".
One session on 2026-10-09. Terminated early because the API budget was exceeded.

## Final numbers

Last row of progress.csv (s01, commit 496f0e57a): 0 passed, no-report (test environment
unimportable), 0 mypy errors, test functions 1158 (unchanged), asserts 3837 (unchanged),
skip markers 12, test setup lines changed 5669. 0 of 35 repositories served from Tortoise;
0 Tortoise models exist; 109 files still import SQLAlchemy; 56 SQLAlchemy models unchanged.
Cost NZ$6.10, 21.7M input tokens, 21.9K output tokens.

## The three most important things that happened

1. The agent tried to run Workflow B inside Workflow A: it generated an 8-stage migration plan
   and paused to ask for approval. I replied only `continue` per the rules.
2. It chose a destructive strategy: `rm -rf mealie/alembic`, moved migration scripts to
   `tests/data/alembic_versions/`, and edited `LOCALES_DIR` in the copied scripts
   (`parents[2]` → `parents[3]`) to make old tests pass rather than fixing the real error.
3. It spent 99.9% of the token budget on sandbox testing in `/tmp` (20+ `uv run python -c`
   commands, 7 temp SQLite databases) and re-reading model files, but wrote zero Tortoise
   models. Input: 21.7M; output: 21.9K; cache reads: 19.4M (89%).

## Why I think they happened

Gemini 3.8 Flash has weak long-context reasoning. Without a human-provided plan and without
a coexistence strategy, it defaulted to "delete everything, then figure out how to rebuild".
It could not hold the whole 56-model codebase in working memory, so it kept re-reading files
(89% cache reads). When its sandbox tests failed to reproduce the real project's async event
loop, it spent more tokens trying variations instead of committing to a design.

## Did the agent's behaviour seem specific to this tool or model?

Yes, likely. The agent showed three behaviours I did not expect:
- It generated a full plan and asked for approval even though the workflow forbade decomposition.
- It never produced a single line of Tortoise model code despite reading every model file.
- It auto-enabled `auto-accept edits` (I had to press `Shift+Tab` to return to manual mode).

A direct comparison with haodong's run (Claude, coexistence plan, 4/35 repositories migrated,
tests green) suggests both model capability and prior session context matter.

## What I would change if I ran this workflow again

Never allow `rm -rf` without an explicit backup. Set a hard token cap and force session end
at 50% of budget. Give the agent the old ORM's implicit behaviours (cascades, proxies, type
annotations) before any code changes, not after. Or simply use Workflow B or C — Workflow A
on a fresh session with a fast model is not viable for this codebase size.

## Anything about the Mealie codebase that made this easier or harder

Harder: data access leaks past `mealie/repos` (proxies, `auto_init` in `mealie/db/models/_model_utils`,
relationship cascades in `mealie/db/models/**`), and 327 synchronous route handlers for an
async-only ORM. The Alembic migration history is tightly coupled to the tests, so any removal
breaks the suite.
Easier: the codebase is large enough that the failure modes were visible quickly, and the
fast test suite made the "0 passed" result unambiguous within minutes.
