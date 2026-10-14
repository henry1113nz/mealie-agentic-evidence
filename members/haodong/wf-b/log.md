# Session log: haodong / wf-b

One row per session. Fill it in straight after the session, not later.

| Session | Date | Agent time (min) | Tokens | Cost (USD, API-equivalent) | Commit | What the agent did | Questions it asked and our answers | Problems seen (with transcript line or commit) |
|---|---|---|---|---|---|---|---|---|
| s01 | 2026-10-04 / 2026-10-13 | ~5 (plan only) | 9,258 output; 3.4M context re-read (cached); 11,027 cache write | not reported by the tool (subscription); see usage.csv | 8594d1efb, b9a4902c1 | Wrote REWRITE_PLAN.md: inventory by package, coexistence strategy, 10 stages with acceptance criteria, 8 risks. The member accepted it without changes. | None asked. | B1, B2 |
| s02 | 2026-10-13 | ~8 by container clock; understates | 13,529 output; 5.6M context re-read (cached); 19,428 cache write | not reported by the tool (subscription); see usage.csv | 2c17101b8 | Stage S1: Tortoise models for all 68 tables, storage-compatible fields, lifespan start-up with matching SQLite pragmas, S1 acceptance criteria written as permanent tests. All S1 criteria met (3179 passed, 0 failed, 0 mypy errors). | None asked. | B3, B4, B5 |
| s03 | 2026-10-13 / 2026-10-14 | ~10 active (window spans an overnight break) | 8,905 output; 3.2M context re-read (cached); 1,230,652 cache write | not reported by the tool (subscription); see usage.csv | c9623f6c4 | Stage S2 (partial): exported the implicit behaviour and wrote INVENTORY.md with counts. Behaviour tests and generic nested writes not done. Suite still 3179 passed, 0 failed. | None asked. | B6 |
| s04 | 2026-10-14 | short | 9,838 output; 4.6M context re-read (cached); 17,775 cache write | not reported by the tool (subscription); see usage.csv | 134118a94 | Completed S2: `behaviour.py` (relation loading, nested writes, delete cascade/nulling, proxy scoping) and three acceptance tests comparing Tortoise with SQLAlchemy (label delete, notifier options, recipe household scope). All S2 criteria met: 3182 passed, 0 failed, 0 mypy errors, test functions 1163, asserts 3856, skip markers 12. | None asked. | B7 |

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
- **B6 Paused for the deadline, then S2 finished.** The workflow was paused after the S2 inventory (c9623f6c4) to leave time for the report, then S2 was completed in s04 after the group agreed each member only needs one of B or C. Final state: S1 and S2 of 10 stages done. The plan's size estimates for later stages ("S8 and S10 are each larger than one session") were never tested.
- **B7 Acceptance criteria written before the code caught nothing, but proved they could.** All three S2 tests passed on the first run. To check they could fail, the nulling rule was removed; the label test failed with "FOREIGN KEY constraint failed", and the rule was restored. With criteria fixed in the plan, the agent wrote the checks before the code; in Workflow A the equivalent checks were added after problems appeared.

## Token usage note

Token counts come from the session log (usage.csv, transcripts/). Because this workflow ran inside a
long existing session, every agent step re-read the whole conversation as context: about 13-14
million cached context tokens per Workflow A session for about 30,000 output tokens. A fresh session
would carry far less context per step. This is the cost side of "an agent with prior project context".
