# Workflow notes: haodong / wf-b

Run in the same long session as Workflow A, straight after it (see setup.md, "Deviation for wf-b").
Four sessions between 2026-10-04 and 2026-10-14.

## Final numbers

Last row of progress.csv (s04, commit 134118a94): 3182 passed, 0 failed (3177 at baseline plus 5 new
acceptance tests), 0 mypy errors, test functions 1158 -> 1163, asserts 3837 -> 3856, skip markers 12,
no existing test changed (only `tests/conftest.py` setup, 4 lines). Stages done: S1 and S2 of 10. No
repository is served from Tortoise yet; that starts at S3. Tokens: 9-14k output per session; see
usage.csv.

## The three most important things that happened

1. The human review step did not happen. The plan was accepted without changes under time pressure
   (commit b9a4902c1), so its four open questions (where auth sits, PostgreSQL only at S10, stage
   sizes, a 0-failure gate on a flaky suite) were never decided by a person (B1).
2. Writing acceptance criteria into the plan changed when checks were written: S1 and S2 criteria
   became permanent tests before or with the code (B2, B7). In Workflow A the same checks were
   written only after something broke.
3. The executor did not follow the plan exactly: it moved relation naming from S2 into S1 because it
   already knew from Workflow A that changing it later causes rework (B4).

## Why I think they happened

The plan made "done" concrete for each stage, so turning it into tests was the obvious next step.
The skipped review is a cost problem, not a tool problem: reviewing a 10-stage plan properly needs
time and knowledge of the codebase, and that was the scarcest resource at the time. The deviation
from the plan happened because the same agent had already met the problem; a plan is only as good
as what was known when it was written.

## Did the agent's behaviour seem specific to this tool or model?

Mostly to the setup: an agent that had just done Workflow A. The fast S1 (no journal-mode lock,
no missing Tortoise context) is an order effect and should not be credited to Workflow B.

## What I would change if I ran this workflow again

Book the review time in advance, and make the review a short checklist of decisions rather than
"read the plan". Run the 0-failure gate twice, since another member found the suite flaky.

## Anything about the Mealie codebase that made this easier or harder

Easier: the stage boundaries follow Mealie's packages (`mealie/db`, `repos`, `services`, `routes`),
so the plan could be cut along them. Harder: the inventory (mealie/db/tortoise/INVENTORY.md) shows
how much behaviour lives outside the schema: 65 cascade-delete relations, 22 proxies that decide
group/household scoping, 338 filterable columns.
