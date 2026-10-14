# Workflow notes: yibing / wf-a

## Final numbers

The last row of `progress.csv` is s01, commit `827d7d186`: 3,182 passed, 0 failed, 0 errors, 16 skipped and 0 mypy errors. SQLAlchemy files/models fell from 109/56 to 0/0. The shared regex counted one Tortoise base model; a supplemental AST check found 56 concrete Tortoise model subclasses. Test functions increased from 1,158 to 1,161, assertions from 3,837 to 3,847, and skip markers stayed at 12. AI time was 47.104 minutes. Parent usage was 24,250,109 input tokens (23,727,488 cached) and 56,398 output tokens. API-equivalent dollar cost was unavailable. Evidence: `progress.csv`, `log.md`, and `transcripts/s01.meta.json`.

## The three most important things that happened

1. A single broad instruction produced a complete-looking async rewrite and removed SQLAlchemy imports under `mealie/`. The agent delegated models, repositories and services to three native Codex children (`transcripts/s01-native/session-tree.json`).
2. The agent self-corrected a run with 37 failures and 20 setup errors, then the external SQLite measurement passed 3,182 tests with mypy exit 0 (`log.md`, "In-session failures and self-correction").
3. A separate Codex source review found two PostgreSQL fuzzy-search tests that return before their assertions because they compare Tortoise's `postgres` dialect with the old `postgresql` name (`log.md`, "Completion claim versus evidence"). Live PostgreSQL was not tested.

## Why you think they happened

The broad prompt left decomposition and integration order to the agent. Parallel mechanical changes were fast, while repeated runtime feedback repaired model registration, database URL and async-caller failures. The PostgreSQL defect survived because the validation environment used SQLite, and unchanged test/assertion counts cannot show that a database-specific branch returned early. The likely root cause is a mechanical accessor conversion that retained the SQLAlchemy dialect string.

## Did the agent's behaviour seem specific to this tool or model?

Possibly. Codex independently used three child agents even though `multi_agent=false` was requested, which increased speed and coordination risk. This is only one Codex run, so the experiment cannot separate tool behaviour from the model, prompt, environment or project.

## What you would change if you ran this workflow again

Prepare all dependencies before starting, verify the effective permission/subagent settings, and require live SQLite and PostgreSQL checks. Add a control-flow check proving every database-specific assertion executes. For practical work, use smaller accepted stages and review API semantics, tenant scoping and test adequacy before the next stage.

## Anything about the Mealie codebase that made this easier or harder

The large pytest suite and repository/service/controller structure helped the agent locate regressions. The rewrite was harder because SQLAlchemy behaviour was spread across `mealie/db/models/`, `mealie/repos/`, schemas, migrations and test fixtures. Async propagation crossed many synchronous callers, and PostgreSQL-specific logic in `tests/unit_tests/repository_tests/test_search.py` and `test_recipe_repository.py` was invisible to SQLite-only execution.

## Limitations

This was one Codex run with agent-chosen parallelism. Operator dependency preparation occurred during A, later workflows had a warmer cache, runtime measurement was SQLite-only, and post-session review was AI-assisted rather than an independent human review. The 47.104 minutes excludes setup and external measurement time.
