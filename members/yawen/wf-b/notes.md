# Workflow notes: yawen / wf-b

## Final numbers

I concluded Workflow B after Stage 8. The overall rewrite remains incomplete. Eight of eighteen planned stages reached their recorded acceptance outcomes, equivalent to 44.4% of the plan by stage count. This is not an overall code-migration percentage. Stage 8 was verified on SQLite; live LDAP, live OIDC and PostgreSQL authentication behavior remain unverified.

Final local code commit: 0ba880506eef7a22c2bc34a6bcdcef10c53403ed. The final measurement recorded 3195 passed, 0 failed, 0 errors, 18 skipped and 0 mypy errors. SQLAlchemy-dependent files changed from 109 to 108; all 56 legacy models remained. The script identified 60 Tortoise models. Test functions/assertions/skip markers were 1176/3993/12, compared with baseline 1158/3837/12. Test-file/setup changes were 1330/41 lines relative to baseline.

Usage and agent durations are recorded per session in log.md. A complete reconciled workflow total and API-equivalent cost were not established. I used ChatGPT Plus.

Evidence: progress.csv, runs/s10-final/, log.md and the final code commit.

## The three most important things that happened

1. Planning exposed dependencies that required revised stage boundaries. Database invariants and migration work were brought forward, followed by registration-specific prerequisites.
   Evidence: plan-reviewed.md; s06, s07 and s10 transcripts and plan commits.

2. SQLite and PostgreSQL checks revealed missing constraints and altered composite-key semantics. Ordered migrations and surrogate-plus-unique mappings were implemented and tested.
   Evidence: runs/s07/STAGE5_MODEL_INVENTORY.md; s06 and s07 transcripts.

3. Independent measurement found five mypy errors after the Stage 8 test suite passed. These were corrected, and the final measurement passed both checks.
   Evidence: runs/s10/mypy-details.log and runs/s10-final/.

## Why I think they happened

The original stage boundaries underestimated shared lifecycle, schema and registration dependencies. Isolated model registration did not establish behavioral equivalence. Focused database checks exposed differences that the retained legacy regression suite alone could not reveal.

Some delays were environmental: identical SQLite and TestClient checks stalled inside the sandbox and passed outside it after approval. These observations distinguish execution-context failures from demonstrated application defects.

Evidence: s06–s10 transcripts and log.md.

## Did the agent's behaviour seem specific to this tool or model?

The agent sometimes stopped at dependency boundaries and omitted requested verification until prompted again. This single run cannot establish whether those behaviors are specific to Codex or gpt-6-luna. AI-assisted review and follow-up guidance also influenced the outcome.

Evidence: s09 and s10 transcripts; setup.md.

## What I would change if I ran this workflow again

I would validate request-lifecycle and schema-coexistence assumptions earlier, define smaller acceptance boundaries, and record durations and usage attribution during execution. I would also separate semantic correctness from performance requirements: the Stage 7 sorting implementation passed parity checks but materializes all matching rows and performs per-row related queries.

Evidence: plan-reviewed.md; s09 and s10 records.

## Anything about the Mealie codebase that made this easier or harder

Existing regression tests provided detailed behavioral specifications. Migration was complicated by filterability metadata, relation-heavy pagination, composite keys, cyclic foreign keys and registration spanning multiple services. The async repository and model graph became reusable foundations, but production SQLAlchemy paths remained widely present.

Evidence: mealie/services/query_filter/, mealie/repos/, the Tortoise model/migration files in the code history, and s07–s10 transcripts.

## Code availability update — 2026-10-15

The final measured code is now published in `henry1113nz/mealie`, branch `yawen/wf-b`, at verified commit `0ba880506eef7a22c2bc34a6bcdcef10c53403ed`. Publication preserved the existing Git history and did not change the recorded results or remaining limitations.
