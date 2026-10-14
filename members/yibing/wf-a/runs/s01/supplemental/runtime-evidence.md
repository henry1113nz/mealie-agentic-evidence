# Workflow A: runtime failure and repair evidence

Read-only assessment of the completed experiment, dated 5 October 2026. No tests or diagnostics were rerun and no experimental code was changed. Current code references are to commit `827d7d1868ecde35844fea1521c92311a6cf2274`; baseline references are to `e365efc71d04677324b9a4aa262b040de33d8676`. Timestamps below are UTC; application log times use New Zealand daylight time (UTC+13).

## Evidence keys

All transcript references are **physical, one-based JSONL lines** in `evidence/members/yibing/wf-a/transcripts/s01-native/`:

- **R**: `01a1098e-d3c0-7c91-8205-f60d644adb1a.visible.jsonl` (main experimental agent).
- **M**: `01a1098f-446c-7590-b918-37d73fab4366.visible.jsonl` (model changes).
- **Q**: `01a1098f-65da-79d0-867e-e4ac138e175e.visible.jsonl` (repository/query changes and driver installation).
- **S**: `01a1098f-8334-7440-825e-66ac6612b8d9.visible.jsonl` (services/backup changes).

Existing raw logs were copied byte-for-byte to `controller/a-runtime-raw/`. `provenance.json` records original paths, SHA-256 hashes, file timestamps, and the exact transcript command/result references. `selected-transcript-events.json` retains relevant visible events with their original line numbers. These are after-session copies, not claims of cryptographic sealing during execution. Temporary diagnostic logs can be overwritten: the preserved backup smoke log is the final invocation at S:281, not its earlier failed version.

## Recorded progression

| Run | Actual command/output provenance | Actual result |
|---|---|---|
| First recorded full suite | R:266 starts `UV_NO_SYNC=1 uv run pytest -n 4 --dist loadfile` at 01:26:28.836; R:283 reads its result at 01:27:56.220. | `37 failed, 3125 passed, 16 skipped, 20 errors in 59.24s`; raw `mealie-wf-a-pytest-1.txt:4311`. |
| Focused recipe/user regression run | R:328 names four test files; R:331 contains the tool result. | `130 passed in 13.71s`; raw `mealie-wf-a-pytest-focused.txt:7`. |
| Second focused run | R:332 names repository, cookbook, meal-plan and webhook test files; R:337 contains the result. | `2 failed, 179 passed in 10.85s`; raw `mealie-wf-a-pytest-focused-2.txt:210`. Both remaining failures concern cookbook updates. |
| Second full suite | R:346 starts it; R:359 reports it. | `5 failed, 3177 passed, 16 skipped in 52.22s`; raw `mealie-wf-a-pytest-2.txt:278`. |
| Final full suite within A | R:372 starts it at 01:40:17.910; R:383 reports it at 01:41:32.075. | `5 failed, 3177 passed, 16 skipped in 56.95s`; raw `mealie-wf-a-pytest-final.txt:278`. |

These numbers come from **tool outputs and their surviving raw files**, not the agent's progress messages. The final five failing node IDs are socket-based `safehttp/test_transport.py` cases; their tracebacks report `PermissionError: [Errno 1] Operation not permitted`. This supports an environment-related explanation for those specific failures. It does not establish complete migration correctness, PostgreSQL compatibility, or deployment readiness. The independent test-integrity audit also found two silently bypassed PostgreSQL tests; see `controller/a-audit/audit.md`.

## Episode 1: shared model persistence lost existing recipe semantics

**Observed failure.** The first suite failed both ZIP reimport tests and the read-only rating test (R:285). The raw reimport trace follows `RecipeService.create_from_zip` through `RepositoryGeneric.create`, `TortoiseModel.create_from_data` and `_update_children`, then reports `UNIQUE constraint failed: recipe_instructions.id` (`mealie-wf-a-pytest-1.txt:1204–1250`). A separate assertion shows a direct recipe PATCH changing a rating from `4.916320151567925` to `1.8011124445702773` instead of preserving it (raw lines 1986–2020, test assertion at `tests/integration_tests/user_recipe_tests/test_recipe_ratings.py:367`). M:263–264 records the agent reading these failures.

**Repair recorded in the tool call.** At 01:29:45.249, M:269 adds two targeted changes: ignore `rating` in ordinary updates of an existing recipe, and remove an excluded nested child's incoming `id` when creating a new child. M:270 confirms the patch operation and its static checks. The resulting code is `mealie/db/models/_model_base.py:181–183` and `:269–273`; `mealie/db/models/recipe/instruction.py:58–60` declares ID exclusion and generated UUIDs.

**Supported cause.** This was not merely missing `await`. The baseline `RecipeInstruction.model_config` excluded incoming IDs (`instruction.py:44–49`), while the baseline `RecipeModel` had a SQLAlchemy `before_update` event that recomputed ratings from user ratings (`recipe.py:291–306`). A replacement generic persistence method did not initially preserve those two behaviors. The failure trace and repair directly support that local explanation; broader claims about model intelligence or attention are not established.

**Outcome and limit.** The focused four-file run including `test_recipe_crud.py` and `test_recipe_ratings.py` passed all 130 cases (R:328,331). The subsequent full run no longer lists either failure. Several edits occurred between runs, so this is regression evidence after the repair, not an isolated causal experiment for each changed line.

## Episode 2: cookbook validation and tenant context required two repair passes

**Observed failure.** A request creating a cookbook with an empty query filter returned 422 instead of 201 (raw first-run lines 2032–2075; R:285 lists the node). The response identifies `query_filter_string`, input `''`, and `Invalid query filter string`. The rewritten `_consolidate_group` raises on an empty group (`mealie/services/query_filter/builder.py:238–240`); the schema validator turns errors from query construction into a field-validation error (`mealie/schema/cookbook/cookbook.py:45–54`).

**First repair and remaining defect.** Q:277 at 01:32:40.771 adds the empty-filter fast path, now `builder.py:341–342`. The next focused run still produced **two failures, 179 passes**. Its raw log shows cookbook PUT returning 400, with missing `groupId` and `householdId` during `SaveCookBook.model_validate` in `RepositoryCookbooks.update` (raw focused-2 lines 9–54; R:337). These are server-side tenant fields required by `SaveCookBook`, while the route's update input does not supply them.

**Second repair.** Q:301 at 01:35:56.662 changes the repository to load the existing cookbook, merge its `group_id` and `household_id` with update values, then validate; Q:302 records patch/check success. This is current `mealie/repos/repository_cookbooks.py:33–39`. The second and final full suites have only the five transport failures (R:359,383), providing evidence that these cookbook cases subsequently passed.

**Supported cause.** Preserving field declarations and route paths did not preserve the behavior of the schema–query-builder–repository boundary. Empty filter handling and tenant context reconstruction are concrete examples of contracts spread across layers. The two-pass sequence also shows why the first successful partial diagnostic did not settle API compatibility.

## Episode 3: historical backups required data transformations as well as current models

**Observed failure.** The first suite's `test_database_restore_data` failed while restoring historical data: `recipes_to_tags` insertion violated the `(recipe_id, tag_id)` unique constraint (raw first-run lines 4063–4208; S:225–226 reads that trace). The trace reaches `AlchemyExporter._replace_rows` via `BackupV2.restore`, so the failure occurs during actual insertion rather than a simulated check.

**Repair sequence.** S:227 at 01:30:43.525 replaces simple reference filtering with pair deduplication in the legacy importer, now `mealie/services/backups_v2/legacy_import.py:260–275`. Subsequent diagnostics exposed additional legacy-conversion mismatches: S:246 contains a query-filter ordering assertion failure, and S:256 contains a shopping-list label-settings assertion failure. S:241 records enum conversion and moving query-filter generation after reference cleanup. This episode therefore required several repairs; deduplication alone should not be credited with the final result.

**Supported cause.** The historical migration `2023-10-04-14.29.26_dded3119c1fe_added_unique_constraints.py` explicitly removed duplicate many-to-many rows before adding constraints (current test-fixture copy lines 176–201, 219, 252–253). The new restore route had to reproduce this historical transformation. The baseline current SQLAlchemy model already had the same unique pair constraint (`mealie/db/models/recipe/tag.py:19–25`), so it would be inaccurate to say Tortoise newly invented the uniqueness requirement. Replacing the migration engine required preserving old data-conversion behavior, not only generating the latest schema.

**Outcome and limit.** S:281 reruns a script that calls the existing restore test against all nine fixture backups; S:286 reports `PASS all nine legacy fixture restores and unchanged migration-data assertions` at 01:36:56.729. The raw final smoke log is preserved. Because this PASS string is printed by an agent-written script, it is corroboration rather than an independent pytest summary. The later full pytest summaries provide stronger confirmation that `test_database_restore_data` no longer failed. This covers the available SQLite backup fixtures, not every production backup or PostgreSQL restore.

## Exact driver repair attribution

The experimental agent installed a **source-built wheel from the upstream `omnilib/aiosqlite` tag `v0.21.0`**, using fetched `pypa/flit` tag `3.10.1` source. At **01:26:14.171**, Q:227 runs:

```text
uv pip install --no-deps --offline /private/tmp/mealie-authentic-built-wheels/aiosqlite-0.21.0-py3-none-any.whl
uv run --no-sync python -c 'import aiosqlite; print(aiosqlite.__version__)'
```

Q:228 at **01:26:14.409** reports successful removal of `aiosqlite==0.22.1`, installation of `0.21.0` from that local wheel, and version output `0.21.0`. Q:211–226 preserves the source-fetch/build chain. This is earlier than the 01:26:27 progress claim and the 01:26:28 first full-suite command. The coordinator's separately reported **02:09** PyPI-cache operation occurred after A ended and cannot explain this repair.

Earlier diagnostics monkeypatched `aiosqlite.Connection.start` inside their processes; those results must be described as bridge-assisted, separately from this persistent installation. The more detailed `controller/a-driver-provenance.md` also preserves an adherence concern: an `apply_patch` source-save attempt was rejected at Q:219–220, followed by shell Python writes at Q:221–222. The successful dependency repair should not be presented as an uncomplicated ordinary package download.

## Suitable analysis claim for Section 2.1

The broad prompt led to an extensive first implementation, but actual execution exposed behavior distributed across ORM events, nested model construction, tenant-scoped validation and historical migrations. Existing integration and backup tests supplied concrete feedback that the agent used in several repair passes. This supports the value of executable feedback during Workflow A; it does not show that a one-shot prompt produced a correct migration on its first attempt or that the final passing counts guarantee semantic preservation.
