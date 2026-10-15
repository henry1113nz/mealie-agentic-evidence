# Workflow notes: yawen / wf-a

## Final numbers
Workflow A was ended early by the participant because of repeated stagnation; the rewrite was not completed. Final local code commit: ba55d682472c2cac88afa177526087694826dd22. Code was not pushed because the account lacked write permission.

The valid measurement recorded 2263 passed, 15 failed, 900 errors and 18 skipped; mypy reported 4 errors. SQLAlchemy-dependent files decreased from 109 to 101, but all 56 SQLAlchemy models remained. The script counted 1 Tortoise model, whereas the agent reported 57 registered models; this discrepancy remains unresolved and is not a verified conversion count. Test functions, assertions and skip markers remained 1158, 3837 and 12. Test-file and setup changes were 28 and 6 lines. Measurement duration was 122 seconds; total agent time and API-equivalent cost remain unavailable. A later inspection found a cumulative session total of 52,967,383 tokens. Because the run used an existing test conversation, this is a session-level figure rather than a verified task-only total; pre-prompt usage was not deducted.
Evidence: progress.csv, runs/s01-retry/, local code commit ba55d6824.

## The three most important things that happened
1. The agent added Tortoise/Aerich infrastructure and model definitions, then partially converted authentication, routes and scheduler tasks. SQLAlchemy remained widely used.
   Evidence: local commits 5db0402c8 and ba55d6824; transcripts/s01.md.
2. Repeated `continue` messages produced intermittent small changes and several turns that only described remaining dependencies. The participant ended the workflow early.
   Evidence: closing exchanges in transcripts/s01.md; log.md.
3. The completed measurement showed substantial test failures and errors despite some successful local checks reported by the agent. No deleted tests, new skip markers or weakened assertions were observed in the saved test diff.
   Evidence: runs/s01-retry/pytest-tail.log, mypy-summary.txt and tests.diff.

## Why you think they happened
The transcript suggests that the rewrite crossed tightly connected repository, controller, authentication and scheduler boundaries. Local conversions left the application using both ORMs, making integration difficult. This is an interpretation of the dependency inspection and partial changes, not a confirmed root cause of the 900 test errors.
Evidence: transcripts/s01.md; local code commit ba55d6824.

The test setup removed the previous database initialization call and changed TestClient lifecycle handling. These changes may have affected database fixtures, but the saved summary logs do not establish causality.
Evidence: runs/s01-retry/tests.diff.

## Did the agent's behaviour seem specific to this tool or model?
Codex with GPT-6 Luna Light frequently ended turns after small changes or dependency inspection, requiring repeated `continue` messages. A single run cannot establish whether this behaviour is specific to the tool or model.
Evidence: transcripts/s01.md.

## What you would change if you ran this workflow again
Use a fresh conversation, verify the exact prompt before starting, and record agent durations during execution. Agree with the group on a consistent stopping rule for repeated lack of progress. This run used an existing test conversation, performed intermediate checks, and ended before the planned time budget; these deviations limit comparison.
Evidence: log.md; opening and closing exchanges in transcripts/s01.md.

## Anything about the Mealie codebase that made this easier or harder
The shared repository layer, controller base classes, SQLAlchemy-based query filters and synchronous event bus made isolated async conversion difficult. Webhook operations provided a smaller surface for partial migration.
Evidence: transcripts/s01.md references to mealie/repos/repository_generic.py, mealie/routes/_base/base_controllers.py, mealie/services/query_filter/builder.py, mealie/services/event_bus_service/ and mealie/routes/households/controller_webhooks.py.
