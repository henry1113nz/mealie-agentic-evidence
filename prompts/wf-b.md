# Workflow B: written plan, human review, staged execution

**Decomposition:** the agent writes a staged plan; a human reviews and corrects it; then one
stage per session.
**Context:** the ground rules plus the reviewed plan (`REWRITE_PLAN.md` in the branch).
**Verification:** each stage has acceptance criteria written in the plan, checked at the end
of the stage with `measure.sh`.
**Human role:** review and correct the plan; decide whether each stage met its criteria.

Branch: `<member>/wf-b`. Time budget: about 6 hours of agent time in total, then stop.

## s01: write the plan (no code changes)

```text
<paste the text block from prompts/ground-rules.md here>

Do not change any code in this session. Read the backend (mealie/db, mealie/repos,
mealie/services, mealie/routes, mealie/schema, mealie/alembic, tests/conftest.py and
tests/fixtures) and write a migration plan to REWRITE_PLAN.md in the repository root.

The plan must:
1. List every place that depends on SQLAlchemy, grouped by package.
2. Split the work into stages, each small enough to finish in one session, in the order
   they should be done.
3. Give each stage acceptance criteria: what must be true, and which test results show it.
4. List the risks you expect, including SQLite and PostgreSQL differences.
```

After the session:

1. Commit the plan exactly as written: `[wf-b] s01: agent plan (unreviewed)`.
2. Review it. Fix what is wrong or missing, and add a `## Review notes` section at the end
   saying what you changed and why. Spend no more than 30 minutes on this.
3. Commit again: `[wf-b] s01: reviewed plan`. Copy both versions into your evidence folder.

## s02 onwards: one stage per session

```text
<paste the text block from prompts/ground-rules.md here>

Read REWRITE_PLAN.md. Carry out stage <N> and nothing else. When you finish, run the tests
and report whether each acceptance criterion for stage <N> is met. If the stage cannot be
finished, stop and explain why instead of working around it.
```

## After every session

Commit (`[wf-b] sNN: stage <N> - <what changed>`), run `measure.sh`, export the transcript,
fill in the log, and write down whether the stage met its criteria.

If you change the plan part way through, commit that on its own
(`[wf-b] sNN: revise plan - <reason>`).
