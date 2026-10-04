# Workflow C: module by module, persistent context file, test gate

**Decomposition:** fixed by us, one module per session in the order below. Old and new code
run side by side until the last module.
**Context:** the ground rules plus a rewrite section in AGENTS.md that records conventions,
decisions and progress. The agent reads it at the start of every session and updates it at
the end.
**Verification:** the test suite is the gate. A module is done only when `measure.sh` shows
no more failures than before the session, the same number of test functions and asserts, and
no new skip markers.
**Human role:** check the gate after every session; do not start the next module until it
passes.

Branch: `<member>/wf-c`. Time budget: about 6 hours of agent time in total, then stop.

## Module order

| Step | Module |
|---|---|
| C1 | Foundation: Tortoise config, start-up and shut-down in the app, base model and mixins, test database setup. SQLAlchemy keeps working alongside. |
| C2 | `mealie/db/models/server` and the repositories, services and routes that use it |
| C3 | `mealie/db/models/users` and everything that uses it |
| C4 | `mealie/db/models/group` and everything that uses it |
| C5 | `mealie/db/models/household` and everything that uses it |
| C6 | `mealie/db/models/recipe` and everything that uses it |
| C7 | Remove SQLAlchemy and Alembic; add Aerich |

## Before s01: add the context file

Commit the section in `prompts/wf-c-context.md` to the end of AGENTS.md:
`[wf-c] s00: add rewrite context to AGENTS.md`.

## Every session

```text
<paste the text block from prompts/ground-rules.md here>

Read AGENTS.md first, especially the "Tortoise ORM rewrite" section. Then do step <C-n>
from that section and nothing else. Follow the conventions and decisions recorded there.
When you finish, run the tests, then update the "Tortoise ORM rewrite" section: record any
new convention or decision, and update the progress table.
```

## After every session

Commit (`[wf-c] sNN: <C-n> - <what changed>`), run `measure.sh`, export the transcript, fill
in the log. Copy AGENTS.md into your evidence folder as `agents-sNN.md` so its versions can
be compared.

If the gate fails, the next session fixes it before moving on:

```text
<paste the text block from prompts/ground-rules.md here>

Read AGENTS.md first. Step <C-n> did not pass the gate: <paste the numbers from measure.sh>.
Fix this before doing anything else, then update the progress table.
```
