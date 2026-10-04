# Ground rules (included word for word in every workflow prompt)

These are the fixed decisions for the rewrite. They are the same for every member and every
workflow, so that differences between runs come from the workflow and the agent, not from
different goals. If an agent asks about something covered here, answer from this file.

```text
Goal: replace SQLAlchemy with Tortoise ORM across the Mealie backend.

Fixed decisions:
- Use Tortoise ORM, which is async. When the rewrite is finished, nothing under mealie/
  should import SQLAlchemy.
- Keep support for both SQLite and PostgreSQL.
- Replace Alembic with Aerich. Upgrading existing databases from the old Alembic history
  is out of scope.
- Keep the HTTP API and the Pydantic schemas in mealie/schema unchanged, so the frontend
  does not need to change.
- Database access becomes async. Make routes, services and scheduler tasks async where
  they need to be.
- You may change how the tests set up and access the database (tests/conftest.py,
  tests/fixtures/, and database setup code inside test files). You must not delete tests,
  skip them, mark them xfail, remove or weaken assertions, or change expected values.
- Run the tests with: uv run pytest -n 4 --dist loadfile
  (tests in the same file depend on each other, so they must run grouped by file).
- Do not push, and do not change git remotes or git configuration.
```

## Answering questions the agent asks

- Covered by the ground rules: answer from them, using the same wording.
- Not covered: give a short answer, write the question and your answer in your session log,
  and post both in the group chat so everyone answers the same way.
- Never give extra hints about how to do the rewrite. In Workflow A, if the agent stops and
  asks whether to continue, reply only `continue`.
