# Starting text for the Workflow C context file

Append this to the end of AGENTS.md in your `<member>/wf-c` branch before session 1.

```markdown
## Tortoise ORM rewrite

This branch is replacing SQLAlchemy with Tortoise ORM one module at a time. Read this
section at the start of every session and update it at the end.

### Fixed decisions
- Tortoise ORM (async). Nothing under mealie/ imports SQLAlchemy at the end.
- Both SQLite and PostgreSQL stay supported.
- Alembic is replaced by Aerich in the last step. Upgrading old databases is out of scope.
- The HTTP API and the Pydantic schemas in mealie/schema do not change.
- Database access becomes async where needed.
- Tests may change how they set up the database, but tests, assertions and expected values
  are never deleted, skipped or weakened.
- Test command: uv run pytest -n 4 --dist loadfile

### Conventions
(Add naming, model, query and session conventions here as they are decided.)

### Decisions log
(One line per decision: session, decision, reason.)

### Progress
| Step | Module | Status | Session | Failing tests after |
|---|---|---|---|---|
| C1 | Foundation | not started | | |
| C2 | server | not started | | |
| C3 | users | not started | | |
| C4 | group | not started | | |
| C5 | household | not started | | |
| C6 | recipe | not started | | |
| C7 | Remove SQLAlchemy and Alembic, add Aerich | not started | | |
```
