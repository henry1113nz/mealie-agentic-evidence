# Session log: haodong / wf-a

One row per session. Fill it in straight after the session, not later.

| Session | Date | Agent time (min) | Tokens | Cost (USD, API-equivalent) | Commit | What the agent did | Questions it asked and our answers | Problems seen (with transcript line or commit) |
|---|---|---|---|---|---|---|---|---|
| s01 | 2026-10-04 | ~6 by container clock (08:11-08:17 UTC); see note | not separable | not separable: shared long session, /cost covers the whole conversation | baa01a65f | Chose a coexistence plan: generated Tortoise models for all 56 tables + 12 many-to-many tables from the SQLAlchemy metadata, added custom GUID / naive-UTC datetime fields so both ORMs share one database, started Tortoise in the app lifespan, made the test client run the lifespan. No repository, service or route converted yet. | None asked. | See problems P1-P7 below. Run in an existing long session with prior project context (setup.md, Deviation). |
| s02 | 2026-10-04 | ~23 by container clock (08:11-08:34 UTC incl. fix); understates, see P7 | not separable | not separable (shared session) | af419ec76, b08199785 | Wrote an async Tortoise repository with the same methods as RepositoryGeneric, an async CRUD helper and `controller.arepos`; moved the labels controller and service to it. 1 of 35 repositories now runs on Tortoise. Old SQLAlchemy code kept for the other callers (seeder, shopping lists). | None asked. | P8-P13 below. |

## Problems to watch for

Write down each one as soon as you see it, with the commit or transcript line:

- Loss of context in long sessions (forgets earlier decisions, repeats work, re-reads files)
- Hallucinated APIs (calls Tortoise methods or options that do not exist)
- Tests deleted, skipped or weakened (also check the integrity columns in progress.csv)
- Premature claims of completion (says done; measure.sh disagrees)
- Drift from project conventions (naming, layering, style)

## Problems seen in s01

- **P1 Composite primary keys.** 7 tables (e.g. `users_to_recipes`, `ingredient_units_aliases`) have composite primary keys; Tortoise has none. Reduced to `id` (uuid4, unique on its own). Found by the generator's warning, commit baa01a65f.
- **P2 Unbounded indexed strings.** Tortoise refuses an index or unique constraint on `TextField`. 35 columns that were unbounded `String` with an index became `CharField(max_length=255)`, so values over 255 characters are now rejected on save. Found when importing the generated models raised `ConfigurationError`.
- **P3 Implicit storage format.** Mealie stores UUIDs on SQLite as 32-character hex without hyphens (`GUID` type), and datetimes as naive UTC strings. Tortoise's built-in fields would write a different format, which SQLAlchemy could not read back during the migration. Needed custom fields in `mealie/db/tortoise/fields.py`; verified by writing with Tortoise and reading with SQLAlchemy.
- **P4 Link tables that are models.** `households_to_recipes` and `users_to_recipes` are used as many-to-many tables by SQLAlchemy but also carry their own columns (rating, favourite, last made). Tortoise many-to-many tables can only hold the two keys, so these stay as explicit models.
- **P5 Test client did not run the lifespan.** `tests/conftest.py` created `TestClient(app)` without entering it, so app start-up never ran in tests and each request ran in a new event loop. An async ORM's connections are bound to one loop, so the fixture now enters the client. The scheduler is skipped when `TESTING` is set so it does not run alongside tests.
- **P6 ORM-level cascades.** SQLAlchemy relationships use `cascade="all, delete-orphan"`, which runs in Python, not in the database. Tortoise will not do this, so deletes will need explicit handling when repositories are converted. Not yet handled.
- **P7 Note on timing.** The container clock shows about 6 minutes between the first and last command of s01. It does not include time spent generating responses between commands, so it understates the real session length.

## Problems seen in s02

- **P8 No TortoiseContext.** Requests failed with "No TortoiseContext is currently active". Tortoise 1.x keeps its state in a context variable; the app lifespan runs in a different task from requests. Needed `Tortoise.init(..., _enable_global_fallback=True)`. Found from the test error; this API is new in 1.x, so examples written for 0.x do not mention it.
- **P9 Implicit delete behaviour.** Deleting a label failed with "FOREIGN KEY constraint failed". The SQLAlchemy model deleted the label's shopping-list settings through `cascade="all, delete, delete-orphan"` and cleared the label on foods and list items through SQLAlchemy's default nulling of foreign keys. None of this is in the schema; it lives in relationship settings. Rewritten explicitly in `AsyncLabelRepository.delete`.
- **P10 Foreign keys enforced differently.** Tortoise turns on `PRAGMA foreign_keys` for SQLite; SQLAlchemy never did. The same database now rejects deletes that used to leave orphan rows silently. Kept on deliberately (matches PostgreSQL), but existing SQLite databases with orphan rows could now fail on delete.
- **P11 Journal mode changed by the ORM.** Tortoise sets `journal_mode=WAL` on connect. The test setup has SQLAlchemy set `journal_mode=MEMORY` on every new connection, which needs exclusive access, so tests failed with "database is locked" whenever Tortoise was connected. In production it would have switched every user's database to WAL, which Mealie only does when `SQLITE_MIGRATE_JOURNAL_WAL` is set. Fixed by giving Tortoise the same pragmas (commit b08199785).
- **P12 A green suite that was not green.** The first s02 measurement (af419ec76) showed 3177 passed, 0 failed, but the P11 bug was already there: it only appeared when the label tests ran without other test files in the same worker. Found by rerunning a subset after an unrelated change. One full run passing did not prove the change was correct.
- **P13 Lost behaviour the tests did not notice.** The Tortoise `page_all` does a plain `icontains` search instead of Mealie's normalized search, and rejects `queryFilter` with a 400. All label tests still passed, so no test covers either feature on this endpoint. Also the agent (me) stored random-order state on the repository instance, which mypy flagged (2 errors in af419ec76, fixed in b08199785).

## Progress note

`sqlalchemy_files` and `sqlalchemy_models` do not move yet because the old code stays until every caller is migrated. Progress so far is better described as: 1 of 35 repositories, 1 controller (5 routes) served by Tortoise.
