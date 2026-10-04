# Workflow notes: haodong / wf-a

Run in an existing long session with prior project context (see setup.md, "Deviation"), so this is
"single instruction, agent with project knowledge", not a fresh agent. Four sessions on 2026-10-04.

## Final numbers

Last row of progress.csv (s04, commit 4a26893f5): 3180 passed, 0 failed (3177 at baseline plus 3
new tests), 0 mypy errors, test functions 1158 -> 1160, asserts 3837 -> 3838, skip markers 12, no
existing test file changed (only `tests/conftest.py` setup, 5 lines). 4 of 35 repositories served
from Tortoise; all 56 models exist in Tortoise but SQLAlchemy is not removed (109 files still import
it). Cost and time could not be separated from the shared session.

## The three most important things that happened

1. The agent chose a coexistence plan on its own: both ORMs on one database, Tortoise models
   generated from the SQLAlchemy metadata. This kept the suite green throughout and made a
   differential test possible (P21, P23).
2. Most of the work was recovering behaviour that the old code kept outside the schema: GUID
   storage format (P3), delete cascades and nulling (65 + 7 relations, P9, P16), lazy loading
   (P15), filterable columns (P20) and permission scoping through association proxies (P19).
3. A full green run hid a real bug once (P12, database locked only when tests ran in a certain
   grouping), and an early naming decision had to be redone two sessions later (P14).

## Why I think they happened

The rewrite is "replace a dependency", but Mealie's behaviour is partly stored in that dependency's
configuration (relationship settings, type annotations, association proxies, `auto_init`). A
single instruction gives no step at which anyone asks "what does the old ORM do implicitly?", so
each rule was found only when a test or an error happened to hit it. Verification only at the end
of a session (one full run) cannot catch problems that depend on test ordering.

## Did the agent's behaviour seem specific to this tool or model?

Hard to separate: this agent already knew the codebase and the failure modes the experiment looks
for, which probably explains why it built safety checks (scope check, differential test, mutation
check) without being asked. A fresh agent with the same prompt is the comparison to look at in the
other members' runs.

## What I would change if I ran this workflow again

Ask the agent, before any code, to list everything the current ORM does implicitly; most of the 24
problems were of that kind. Run each converted resource's tests in isolation as part of the end of
every session, not only the full suite.

## Anything about the Mealie codebase that made this easier or harder

Harder: data access leaks past `mealie/repos` (proxies, `auto_init` in `mealie/db/models/_model_utils`,
relationship cascades in `mealie/db/models/**`), and 327 synchronous route handlers for an async-only
ORM. Easier: a large, fast test suite (about 5 minutes, 3177 tests) and a clean parser/builder split
in `mealie/services/query_filter/builder.py`.
