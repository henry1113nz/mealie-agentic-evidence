# Session log: haodong / wf-a

One row per session. Fill it in straight after the session, not later.

| Session | Date | Agent time (min) | Tokens | Cost (USD, API-equivalent) | Commit | What the agent did | Questions it asked and our answers | Problems seen (with transcript line or commit) |
|---|---|---|---|---|---|---|---|---|
| s01 | 2026-10-04 | ~6 by container clock (08:11-08:17 UTC); see note | not separable | not separable: shared long session, /cost covers the whole conversation | baa01a65f | Chose a coexistence plan: generated Tortoise models for all 56 tables + 12 many-to-many tables from the SQLAlchemy metadata, added custom GUID / naive-UTC datetime fields so both ORMs share one database, started Tortoise in the app lifespan, made the test client run the lifespan. No repository, service or route converted yet. | None asked. | See problems P1-P7 below. Run in an existing long session with prior project context (setup.md, Deviation). |

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
