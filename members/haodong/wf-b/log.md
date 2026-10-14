# Session log: haodong / wf-b

One row per session. Fill it in straight after the session, not later.

| Session | Date | Agent time (min) | Tokens | Cost (USD, API-equivalent) | Commit | What the agent did | Questions it asked and our answers | Problems seen (with transcript line or commit) |
|---|---|---|---|---|---|---|---|---|
| s01 | 2026-10-04 / 2026-10-13 | ~5 (plan only) | not separable | not separable (shared session) | 8594d1efb, b9a4902c1 | Wrote REWRITE_PLAN.md: inventory by package, coexistence strategy, 10 stages with acceptance criteria, 8 risks. The member accepted it without changes. | None asked. | B1, B2 |
| s02 | 2026-10-13 | ~8 by container clock; understates | not separable | not separable | 2c17101b8 | Stage S1: Tortoise models for all 68 tables, storage-compatible fields, lifespan start-up with matching SQLite pragmas, S1 acceptance criteria written as permanent tests. All S1 criteria met (3179 passed, 0 failed, 0 mypy errors). | None asked. | B3, B4, B5 |
| s03 | 2026-10-13 / 2026-10-14 | short | not separable | not separable | c9623f6c4 | Stage S2 (partial): exported the implicit behaviour and wrote INVENTORY.md with counts. Behaviour tests and generic nested writes not done. Suite still 3179 passed, 0 failed. | None asked. | B6 |

## Problems to watch for

Write down each one as soon as you see it, with the commit or transcript line:

- Loss of context in long sessions (forgets earlier decisions, repeats work, re-reads files)
- Hallucinated APIs (calls Tortoise methods or options that do not exist)
- Tests deleted, skipped or weakened (also check the integrity columns in progress.csv)
- Premature claims of completion (says done; measure.sh disagrees)
- Drift from project conventions (naming, layering, style)

## Problems and observations

- **B1 The human review did not happen.** The plan was shown with four review questions (place of the users/auth stage S6, PostgreSQL tested only at S10, whether to split S8 and S10 now, and whether "0 failing tests" is a usable gate when another member found the suite flaky). Under time pressure the member chose to proceed without changes (commit b9a4902c1 records this). The four questions remain open risks in the plan. The step that makes Workflow B different from A was skipped, which is itself evidence about the cost of human review.
- **B2 Acceptance criteria became tests.** Because the plan stated S1's criteria precisely ("every model reads the migrated database", "rows round-trip between ORMs"), they were written as permanent tests (`tests/unit_tests/test_tortoise_models.py`) that every later stage re-checks. In Workflow A the same checks were one-off scripts that were not kept.
- **B3 Order effect.** S1 finished in one session with none of the s01/s02 problems of Workflow A (journal mode lock, missing Tortoise context, relation names). The agent already knew them from A, so this speed cannot be credited to the workflow (see setup.md, Deviation for wf-b).
- **B4 The plan was not followed exactly.** Relationship names were generated in S1, although the plan lists them under S2, because the agent knew from A that changing them later forces rework. A plan written before execution is still overridden by what the executor knows.
- **B5 Agent's own test error.** The first round-trip test compared a UUID with a string and failed; the code was correct. Fixed in the test before the commit.
- **B6 Stopped at S2 for the deadline.** The workflow was stopped after the S2 inventory so the report could be written. Of the plan's 10 stages, S1 is complete and S2 is half done (inventory written; behaviour tests and generic nested writes missing). The plan's own size estimates were never tested.
