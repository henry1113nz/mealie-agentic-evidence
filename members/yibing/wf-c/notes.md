# Workflow notes: yibing / wf-c

## Final numbers

The last `progress.csv` row is s09, commit `cf99f5eef`: 3,277 passed, 6 failed, 0 errors, 18 skipped and 0 mypy errors. SQLAlchemy files/models fell from 109/56 to 0/0. The shared regex counted one Tortoise base model; this count understates the concrete model subclasses. Test functions increased from 1,158 to 1,237, assertions from 3,837 to 4,434, and skip markers stayed at 12. Primary sessions s01–s08 used 104.528 minutes and 46,560,365 input tokens (45,654,144 cached) plus 144,023 output tokens. The validation follow-up added 0.900 minute but did not provide a separate token counter. API-equivalent dollar cost was unavailable. Evidence: `progress.csv`, `log.md`, and `transcripts/s01.meta.json` through `s08.meta.json`.

## The three most important things that happened

1. The staged module order made progress measurable: foundation, server tasks, users, groups, households, recipes, then removal/Aerich. AGENTS.md snapshots retained decisions between sessions (`agents-s00.md`, `agents-s02.md` through `agents-s08.md`).
2. The C1 gate caught a real connection-wrapper defect before C2. A focused repair changed the startup order and moved the external result from 3,217 passed/1 failed to 3,218 passed/0 failed (`progress.csv`, s01–s02).
3. The largest final stage still created an integration spike: after SQLAlchemy removal, s08 had 37 failures. The s09 follow-up reduced this to six, but five socket-permission failures and one historical backup regression remained. Live PostgreSQL was never tested (`runs/s08/failures.txt`, `runs/s09/failures.txt`).

## Why you think they happened

Module boundaries reduced the amount of code changed before each check, and the context file carried decisions about async lifecycle, compatibility bridges and repository behaviour into fresh sessions. This made early defects easier to localize. C7 was much larger than the earlier stages because removing the last ORM layer touched migrations, backups, query compatibility and many remaining callers at once. The context file improved consistency but could not replace runtime coverage. The remaining database uncertainty exists because the environment measured SQLite only.

## Did the agent's behaviour seem specific to this tool or model?

Codex followed the staged prompts and updated AGENTS.md consistently, but this is one run with one model. The experiment cannot separate the effect of Codex from the fixed module order, repeated tests, growing context file, warmed dependency cache or operator environment.

## What you would change if you ran this workflow again

Split C7 into smaller removal, migration, backup and compatibility stages. Run live PostgreSQL after the foundation, recipe and final stages. Define the test-count gate as “no existing test or assertion removed” so adding valid tests does not appear to violate a literal equal-count rule. Record the five socket-limited cases separately from application regressions while still keeping them in the raw failure count.

## Anything about the Mealie codebase that made this easier or harder

The repository/service/controller structure made domains suitable for staged conversion, and the test suite provided frequent feedback. The migration was harder because persistence behaviour crosses `mealie/db/models/`, `mealie/repos/`, schemas, background tasks and backup code. Tenant scoping and relationship behaviour are implicit in the old ORM. Historical Alembic/backup tests also remain relevant after production code switches to Aerich.

## Limitations

Workflow B implementation was skipped by participant decision, so this run cannot support a complete A/B/C comparison. C used a warmer dependency cache than A. The final suite was not clean, live PostgreSQL was untested, and the records include AI-assisted coordination outside the experimental session; that work is excluded from the reported agent time.
