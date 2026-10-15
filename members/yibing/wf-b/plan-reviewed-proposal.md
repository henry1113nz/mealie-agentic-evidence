# SQLAlchemy to Tortoise ORM rewrite plan

Planning baseline: commit **e365efc71**, inspected 2026-10-05. This session changes only this document. No application, schema, test, dependency, migration, frontend, or Git configuration changes were made. Tests have not been run in this planning session; all results below are **required future acceptance evidence**, not claimed passes.

## Scope and constraints

- Replace backend persistence with async Tortoise ORM; no file under mealie/ may import SQLAlchemy at completion, including migrations, type-only imports, scripts, and schema helpers. No runtime bridge may import it indirectly to implement persistence.
- Support SQLite and PostgreSQL throughout validation. Use Aerich for a **fresh migration history**. Do not build an in-place upgrade from existing Alembic databases.
- Preserve HTTP paths, methods, parameters, status/error behavior, permissions, pagination, response shapes, and Pydantic field/alias/default/validation/serialization contracts. No frontend or generated TypeScript changes should be needed.
- Preserve every existing test, assertion, and expected value. Only adapt database setup/access and necessary async invocation mechanics; add tests for coverage gaps. Never make an old test pass by emptying its input, substituting fake results, or running it against the old backend while claiming Tortoise coverage.
- Every pytest execution uses **uv run pytest -n 4 --dist loadfile**, followed by explicit file/directory targets for a focused run. Final runs omit targets. Do not use the current Taskfile's -n auto default for acceptance.
- Do not push or change remotes or Git configuration.

## Feasibility issues to settle before implementation

These findings do not prevent writing this plan. They do prevent honestly promising that a mechanical ORM substitution satisfies every literal constraint.

1. **Schema source files contain SQLAlchemy implementation.** Twenty files under mealie/schema directly import it. MealieModel.loader_options/filter_search_query, Recipe search/loading, SearchFilter, and cookbook/meal-plan filter validators depend on ORM expressions. A byte-for-byte freeze of those files and zero SQLAlchemy imports under mealie/ are incompatible. The proposed implementation preserves the Pydantic/API **contract**, moving loading/search machinery to repositories and replacing validator internals with equally strict, synchronous metadata validation. This interpretation was raised for clarification during planning; no answer is assumed. If the intended freeze is literal, resolve that conflict before changing these files. Do not use import aliases or monkeypatching to hide the dependency.
2. **Some tests assert ORM representation.** test_query_filter_builder.py asserts model/field identity and literal EXISTS SQL fragments, not just returned data. test_alchemy_exporter.py inspects SqlAlchemyBase.metadata and NaiveDateTime and expects an alembic_version export key. Establish truthful database-access/introspection adapters that preserve those assertions and values. If the target ORM cannot expose equivalent identity/query rendering, report that specific incompatibility before editing the tests; do not quietly change expected SQL, fake a compiler, or broaden the permitted test edits.
3. **Historical migrations remain test fixtures.** test_alembic.py imports and checks the full revision chain; image-backfill and structured-time tests import specific historical revisions. Preserve the complete nonempty historical artifacts outside mealie/ for these tests, including needed frozen helper dependencies, and adjust only the database-artifact locator. If changing tests/utils/alembic_reader.py is considered outside the allowed database setup scope, obtain that narrow clarification first. SQLAlchemy/Alembic may remain test-only dependencies for that archive; they must not remain production persistence dependencies.
4. **Legacy backup import is still exercised.** test_database_restore_data restores nine old ZIP backups and asserts historical data transformations. Excluding in-place old-database upgrades does not make those assertions disappear. Plan for a version-aware, SQLAlchemy-free **archive data importer** into the fresh schema. Keep the historical alembic_version field as backup-format compatibility metadata, distinct from actual Aerich migration state. Do not run the old Alembic chain in production. If legacy ZIP import was also intended to be excluded, the existing test constraint needs explicit resolution.

## Target architecture and staging method

Keep repository/service/controller separation. AllRepositories carries explicit group/household scope and an optional async transaction connection, rather than a SQLAlchemy Session. Preserve NOT_SET versus explicitly unscoped None. Repositories own queries, prefetch plans, projection to existing Pydantic models, and persistence primitives. Services own multi-repository transaction boundaries. Routes await services and translate repository errors into the existing HTTP contract.

Use explicit async graph writers for nested recipes, shopping lists, substitutions, users, and provider settings. Constructors and synchronous properties must not query the database. Replace association proxies with explicit joins for filters and materialized values for serialization; never duplicate a derived household ID without preserving behavior when ownership changes. Finish loading nested relationships before calling unchanged Pydantic validators. Keep pure parsers, formatters, cryptography, and DTO manipulation synchronous.

Initialize the connection registry on the application event loop; close it after stopping/awaiting scheduled work. Each background operation owns its transaction and reloads objects by IDs, rather than retaining a request's connection/model graph. Commit before dispatching side effects. Keep blocking LDAP, file/ZIP/image, HTTP-client, and scraper work off the event loop where appropriate, without handing a live DB connection to worker threads. Tortoise requires initialization and cleanup; test the precise lifecycle of the selected version. [Tortoise setup](https://tortoise.github.io/setup.html)

Use explicit transaction scopes and sequential nested graph changes. Do not run competing nested transaction operations with gather on one connection. Savepoint behavior must be verified on both engines. [Tortoise transactions](https://tortoise.github.io/transactions.html)

Pin a verified Python 3.14-compatible combination of Tortoise, Aerich, and async database drivers in pyproject.toml/uv.lock. Aerich remains the fixed choice even though current upstream also advertises Tortoise's own migration commands. Keep a simple importable ORM config with aerich.models, committed migrations, and deliberate dialect-specific DDL where needed. Do not assume a migration generated for one dialect runs unchanged on the other. [Aerich configuration and commands](https://github.com/tortoise/aerich)

Build model/repository foundations in temporary separate modules against disposable databases; keep the legacy baseline available only during development. Never let both ORMs manage one connection/transaction or dual-write the same data. Early component tests may inject the target repository explicitly. Once the complete model graph and repository core are ready, select Tortoise for the test process and port consumers in bounded slices. Intermediate branch states need not be deployable; document remaining failures without skips/xfails. A legacy-backed pass is baseline evidence only. Remove temporary namespaces/factories at final cutover.

Each numbered or lettered stage below is intended as one session with a concrete stopping point. A stage is complete only when its stated gate passes on the target implementation. Where any existing unit or integration file requires later model writers, fixtures, services or callers, run new direct component tests now and carry that **named whole-file gate forward** to its explicit closure stage; do not mark it passed prematurely. Revisit the size before starting a stage if its spike exposes additional work.

## Reviewed execution policy and scope decisions

This file is an AI-assisted review proposal awaiting the participant's approval. Do not execute until that approval is recorded by the coordinator.

Treat all 52 stages as a backlog, not a promise to finish. The cumulative budget is approximately 360 minutes of experimental AI time, including the 21.407-minute original planning session and agent-run tests. Operator measurements, approval waiting and exports are logged separately. Start with 01, then 02a, then 02b, then continue in the listed order while time remains. One stage per fresh execution session; preserve the prescribed prompt. Stop at the budget or when a stage cannot be finished and explain the exact blocker. No blocked, deferred or legacy-backed criterion may be marked passed.

For each criterion record stage, engine, actual backend exercised, test/component, met/failed/blocked/not-run status, raw evidence and named closure stage. Inspect control flow and fixtures as well as test/assert/skip counts. PostgreSQL-specific assertions must actually execute with the target driver. No live database or destructive restore command may target ordinary development/production data; use disposable test databases.

Scope answers proposed for human approval:
1. Preserve every public Pydantic/HTTP contract, including validation and serialization behavior, while allowing internal SQLAlchemy loader/search helpers to be replaced or moved. Byte-identical schema files are not required; contract changes are not authorized.
2. Permit truthful database setup/access/introspection adaptations while preserving original tests, assertions and expected values. If an ORM-representation assertion cannot be preserved honestly, stop and report it. Fabricated compiler results, silent early returns, weaker assertions and skips are prohibited.
3. Preserve historical Alembic artifacts as test-only fixtures outside mealie, with the minimal database-artifact locator adaptation in tests/utils/alembic_reader.py. Do not delete revision coverage; production no longer runs Alembic.
4. Preserve the existing legacy ZIP backup-import behavior and tests. Upgrading an existing live Alembic database remains out of scope.

## Test conventions and baseline evidence

In the stage list, U means tests/unit_tests/, I means tests/integration_tests/, and M means tests/multitenant_tests/. File names following a directory inherit that directory. All targets denote existing files unless explicitly labeled NEW. Run a whole file, preserving dependencies between its tests. For example:

```sh
uv run pytest -n 4 --dist loadfile tests/unit_tests/repository_tests/test_pagination.py
```

Run each database gate twice, with DB_ENGINE=sqlite and DB_ENGINE=postgres set in the environment. PostgreSQL also needs the existing POSTGRES_* settings, an isolated disposable base database, and privileges to create/drop worker databases. Do not point restore tests at an ordinary development or production database. The command in each configured environment remains:

```sh
uv run pytest -n 4 --dist loadfile
```

Use the team-supplied baseline for commit e365efc71: 3177 passed, 0 failed, 18 skipped; mypy 0 errors in 464 files; 109 SQLAlchemy-importing files excluding migrations, 56 SQLAlchemy model classes, 54 Alembic revisions; 1158 test functions, 3837 assertions and 12 skip markers. These are shared measurements, not a new local run or proof of two tested engines. Do not rerun the full baseline suite as preparation. Record the local lock/Python/environment provenance and preserve the static inventory. Capture only missing contract artifacts separately. Existing backend-conditional early returns mean a green SQLite run cannot prove PostgreSQL fuzzy search. Unavailable PostgreSQL is blocked/not-run evidence, not a pass. The coordinator still performs the prescribed post-session measurement separately.

Capture baseline OpenAPI and Pydantic JSON schemas plus representative request/response and validation-error fixtures. Compare field annotations, aliases, defaults, validators' observable behavior, computed fields, null/empty distinctions, and operation IDs. Existing test_openapi.py/schema tests are necessary but not a complete API equivalence oracle. No schema-contract change is planned, so code generation must produce no frontend/type diff.

For the async test harness, prefer a session-scoped TestClient used as a context manager so lifespan owns one running loop per xdist worker. Route synchronous fixture DB operations through a **test-only** portal into that same loop, or use explicitly scoped async fixtures when a file already permits it. Do not call asyncio.run for each query, share pools across loops, or put a synchronous compatibility facade in production. Preserve cookie isolation, fixture lifetimes, worker DATA_DIRs, per-worker PostgreSQL databases, and the destructive backup-test isolation. The current function-scoped pytest-asyncio default requires deliberate adjustment for pooled connections.

## Ordered implementation stages and acceptance criteria

### 01 — Baseline and constraint proofs

Read the dependency inventory and record a constraint/evidence ledger using the supplied shared baseline; do not rerun the full baseline suite. Record source commit, static test inventory and available contract artifacts. Identify the precise ORM-representation and legacy-fixture contracts statically. Apply the approved scope decisions below; explicitly list any remaining blocked or missing evidence. Executable Tortoise field/query adapters belong to stages 03/12/15 after dependency setup, and final historical-artifact proof belongs to 36. **Gate:** a concrete ledger of baseline provenance, original inventory, resolved/unresolved constraints and pending contract captures. Missing live PostgreSQL evidence is recorded without inventing a baseline. No application rewrite or broad test alteration belongs to this stage.

### 02a — Driver/configuration and lifecycle spike

Pin the dependency combination; build config translation and isolated async initialization/cleanup. Preserve public DB_URL formatting and redaction; translate to driver credentials internally, including encoded passwords, URL overrides, socket paths, TLS/query options, and SQLite paths. **Gate:** NEW lifecycle/rollback/connection-option tests pass on both engines; U/test_config.py retains its exact URL expectations. No leaked connection or cross-loop failures.

Before extensive model work, also prove the selected Aerich/Tortoise combination with a scratch model and isolated temporary migration history: initialize an empty disposable database, repeat initialization without destructive changes, and apply/reverse a small trial migration on SQLite and PostgreSQL. Preserve exact versions and actual logs. This spike is not the final Mealie history (stage 35 retains that work). If sandbox/engine availability blocks execution, report the blocked gate and hand the exact command to the coordinator for authorized validation; never change tools to complete a permission-denied action without approval.

### 02b — Worker-isolated async test harness

Implement database/loop ownership in tests/conftest.py and tests/fixtures/fixture_database.py: worker SQLite paths/PostgreSQL databases, explicit initialization/teardown, a TestClient context/portal, and test-only DB access adapters. Remove import-time DB initialization. Keep automatic wall-clock scheduling disabled through test setup, while real scheduler/jobs retain their dedicated tests; entering lifespan must not introduce background mutations into existing tests. Adapt other fixture DB calls as each repository becomes available. **Gate:** NEW harness tests perform a real DB fixture write, HTTP read and teardown on one loop in four workers on both engines, initially using a minimal ASGI application and scratch model. Stage 25a repeats this with Mealie's actual app/fixtures. No leaked pools, cross-worker rows or missing cookie isolation; a restore later refreshes connections on this same loop.

### 03 — Base model/metadata contracts

Implement UUID/integer identity rules, UTC timestamps, physical update_at mapping, normalization, explicit filterability metadata, and model registration conventions. Prove single-ID plus unique-pair alternatives to composite keys, FK cycles, checks, and through tables in scratch models before porting the whole graph. **Gate:** NEW model-contract tests on both engines; U/test_auto_init_config.py remains meaningful; U/schema_tests/test_mealie_model.py passes. Primary-key protection and normalization match the baseline.

### 04 — Identity and tenancy model definitions

Port group/group.py, preferences.py, household/household.py, preferences.py, users/users.py, password_reset.py, and the minimal FK endpoints needed for their cycles. No nested persistence yet. **Gate:** NEW direct-model tests prove default preferences, identity uniqueness, user-to-household/group links and intended deletion actions on both engines. Schema construction does not drop FK checks to work around cycles.

### 05 — Organizer and unit model definitions

Port category, tag, tool, label, unit/alias, household-on-hand joins and their extras. Copy actual constraints from migration history as well as model declarations. **Gate:** NEW integrity tests prove per-group name/slug uniqueness, nullable links, explicit join uniqueness, alias ordering, and no recipe deletion when an organizer is removed.

### 06 — Food and substitution model definitions

Port food/alias/extras, food substitutions, and recipe-substitution endpoints. Preserve note-only edges, non-self checks, optional target semantics, ordering, and both inbound and outbound deletion behavior. **Gate:** NEW direct-model integrity tests on both engines plus U/schema_tests/test_ingredient_food.py and test_ingredient_substitutions.py unchanged.

### 07 — Recipe aggregate model definitions

Port recipe core/settings/nutrition/assets/extras/notes/instructions/ingredient and note reference links, and ingredients. Define explicit ordering; do not rely on relation iteration order. **Gate:** NEW graph loading/constraint tests on both engines and U/schema_tests/test_recipe.py pass; fully loaded fixtures validate as the current Recipe/RecipeSummary without lazy I/O or coroutine values.

### 08 — Recipe interaction model definitions

Port user_to_recipe, household_to_recipe, comments, timeline, share tokens. Define the fields needed to compute ratings, favorites and last-made without SQLAlchemy events/proxies. **Gate:** NEW uniqueness/cascade/projection tests and U/schema_tests/test_recipe_timeline_event_timestamp.py pass. One favorite/rating row per pair and intended cross-household relationships survive.

### 09 — Shopping-list model definitions

Port lists/items/recipe-reference rows/label settings/extras with ordering and owner-derived scope. **Gate:** NEW graph/cascade/uniqueness tests pass on both engines; U/schema_tests/test_shopping_list_ingredient.py passes. Parent/item/reference cycles and nullable food/unit/label links are verified explicitly.

### 10a — Remaining household model definitions

Port cookbooks, meal plans/rules, invitations, event notifier/options, recipe actions and webhooks. This is declaration-only work; persistence and callers have later stages. **Gate:** NEW relation/default/constraint tests and U/schema_tests/test_meal_plan.py pass on both engines.

### 10b — Reports, exports and model coverage

Port reports/entries, group exports and server task; reconcile every table and association against the old metadata and migration history. **Gate:** NEW metadata coverage asserts all old tables have a disposition, all currently ported target relations resolve, and report/export cascade tests pass. Provider cycles remain the explicit next-stage work.

### 11 — AI provider model graph

Port providers, headers/parameters, settings and default/audio/image pointers, with explicit create/delete sequencing for cyclic FKs. **Gate:** NEW cycle/constraint tests plus U/schema_tests/test_ai_providers.py pass on both engines, including omitted-secret behavior and null/default pointers.

### 12 — Schema-independent loading and validation boundary

Subject to the schema-contract clarification, extract every loader_options/search hook to repository-side registries, leaving fields and observable validators unchanged. Introduce fully materialized DTO projection and synchronous filter metadata validation for cookbook/rule schemas. Preserve AuthMethod imports and UTC/normalization helpers through ORM-neutral modules. **Gate:** all U/schema_tests/ pass; stored Pydantic/OpenAPI comparison has no contract diff; no SQLAlchemy import remains in mealie/schema. Search execution itself follows in stage 17. During extraction, an explicitly temporary helper outside mealie/schema may delegate to the existing compiler; replace it with the pure metadata/target compiler in stage 15. Do not classify a legacy-backed execution as target-backend evidence.

### 13 — Scoped repository factory and basic reads

Port AllRepositories, factory construction, generic get/get-multi/exists/count and scope propagation, including derived scope joins. Audit unusual currently unscoped generic helpers; do not broaden access while porting them. **Gate:** NEW direct read/scope tests pass; constructor/scoping coverage in I/test_repository_factory.py is adapted through DB-access mechanics. Explicit None and NOT_SET retain different behavior, with wrong-group IDs returning no data.

### 14a — Generic transactional writes

Implement create/update/patch/delete/bulk primitives. Replace auto_init's ID-versus-alternate-key resolution, exclusions and collection clearing with explicit writer interfaces. Preserve missing-row/unique error categories and transaction semantics. **Gate:** NEW direct generic rollback/bulk/identity tests pass on both engines; no partial write persists after failure. Domain-specific graph writers follow later.

### 14b — Identity repositories

Port group/household/user writers, defaults, name/slug retry and password-state persistence on the generic primitives. **Gate:** U/repository_tests/test_group_repository.py and test_user_repository.py plus NEW household/default-graph tests pass on Tortoise. Membership and identity are stable across updates.

### 15 — Filter grammar, metadata, and relationship compiler

Keep the parser/JSON representation and error behavior. Replace mapper/association-proxy inspection, preserving the filterable allowlist; implement correlated EXISTS/anti-EXISTS and CONTAINS ALL through a query adapter where stock Tortoise filters are insufficient. **Gate:** U/repository_tests/test_query_filter_builder.py passes with unchanged assertions/expected strings and a truthful query-inspection adapter agreed in stage 01. Password/email/token traversal remains forbidden. NEW data-result tests prove that negation excludes a whole recipe and joins cannot duplicate rows.

### 16 — Pagination and ordering

Port page/count rules, per_page=-1, page=-1, multi-column order, explicit NULL placement, relationship min/max ordering, random seed and stable pagination. Count base entities before loading collections. **Gate:** NEW direct pagination tests pass on both engines and cover tied/null related values, page bounds and count-versus-items consistency. The existing whole U/repository_tests/test_pagination.py also needs recipe/shopping/seeder writers; run it at stage 24b once those dependencies exist, and close any fixture/HTTP prerequisite at stage 28c. Input PaginationQuery objects are not mutated.

### 17 — Search on both dialects

Port SearchFilter normalization/quoted phrases, general search, recipe ingredient text search, and food/unit alias search. PostgreSQL must retain pg_trgm operators/ranking and indexes; SQLite retains tokenized behavior. Set any threshold on the query's actual connection without leaking settings between requests. **Gate:** NEW direct search tests pass on SQLite **and PostgreSQL** with unchanged ranking/results. Carry the existing whole U/repository_tests/test_search.py and test_recipe_repository.py through recipe writers and derived fields (stages 18/21), and close their whole-file gates at stage 27b after HTTP-backed fixture setup is ready.

### 18 — Recipe graph creation and replacement

Implement recipe repository/service graph writers, default children, ordered updates, clear-versus-omitted lists, ingredient/note references, supplied create IDs and protected update IDs. Resolve organizer IDs in the owning group; use transaction-scoped collision recovery. **Gate:** NEW direct graph/identity and failure-in-the-middle rollback cases pass. The whole U/repository_tests/test_recipe_repository.py also exercises stage-21 computed state; its full-file gate closes at stage 27b. Carry I/user_recipe_tests/test_recipe_crud.py, test_recipe_ingredients.py, test_recipe_steps.py, test_recipe_owner.py into stage 26 for HTTP proof.

### 19 — Organizer and cookbook persistence

Port organizer creation/counts/empty searches/merges and cookbook name/slug collision handling. Preserve case-insensitive organizer resolution and race-safe creation. **Gate:** U/repository_tests/test_cookbook_repository.py and U/services_tests/test_organizer_resolver.py plus direct organizer-merge tests pass; related I/category_tag_tool_tests/ and cookbook HTTP gates follow stage 27.

### 20 — Food/unit reconciliation and mergers

Implement food/unit writes, aliases, on-hand associations and substitution reconciliation. Merge/repoint recipe and shopping references transactionally before deleting source rows; preserve notes and remove resulting self/duplicate edges. **Gate:** U/repository_tests/test_food_repository.py and test_unit_repository.py pass on both engines; NEW transaction-failure tests prove no half-merge. Preserve cross-group rejection and foreign-ID behavior.

### 21 — Ratings, favorites, last-made, and interaction persistence

Replace SQLAlchemy event listeners with transaction-bound derived-value updates; implement comment/timeline/share-token writers. Recompute mean positive ratings after create/update/delete. Preserve the observed last-made behavior: the current listener only advances global recipe.last_made via max(existing, household value), including on deletion; clearing/lowering a household value does not recompute the global date downward. **Gate:** relevant U/repository_tests/test_recipe_repository.py cases and NEW concurrent/recompute tests pass. Favorites cannot overwrite rating or vice versa; zero/NULL ratings do not enter the mean. Characterize last-made delete/clear/lower-date cases and preserve those results; changing that behavior is a separate feature/fix.

### 22 — Suggestions query

Port _recipe_suggestions.py independently: available tools/foods, recipe-level then food-level directional substitutions, grouped missing counts and deterministic ranking. **Gate:** I/user_recipe_tests/test_recipe_suggestions.py passes against Tortoise once its route is wired, or equivalent direct calls pass now and the full file remains an explicit carried gate. Note-only substitutes cannot satisfy a missing ingredient.

### 23 — Shopping-list transactional operations

Port repository_shopping_list.py, ShoppingListService and label coordination. Cover recipe scaling/add/remove, merging, ordering, label settings and parent timestamps on every item mutation. **Gate:** NEW direct operation tests plus DB-backed cases from I/user_household_tests/test_group_shopping_lists.py, test_group_shopping_list_items.py, test_shopping_list_labels.py pass through the target service. Parent timestamps and reference cleanup are asserted after deletion as well as insertion.

### 24a — Meal-plan and provider repositories

Port specialized meals/rules and AI-provider repositories. Preserve NULL/unset rule semantics, provider secret retention and pointer cleanup. **Gate:** NEW direct repository tests pass on both engines; omitted API keys survive updates, deleting a provider clears all selected-provider references, and date/rule results match the existing fixtures.

### 24b — Async seeding

Port seeder interfaces/generators and service loading over the completed repositories. Keep locale seed resources and fallback behavior. **Gate:** NEW direct seeder tests pass and default seeding twice creates no duplicates. Run the carried U/repository_tests/test_pagination.py whole-file gate when fixtures permit, closing remaining fixture prerequisites at stage 28c. Carry I/user_group_tests/test_group_seeder.py into its HTTP stage.

### 24c — Event dispatch and listeners

Convert EventBusService.dispatch, its fanout, publish_event caller helpers and DB-backed listeners before mutation routes call them. Give after-response jobs their own context and publish only after successful commit. **Gate:** U/services_tests/event_bus_service/ plus NEW real listener/fanout/rollback tests pass; a committed mutation completes its listener and a rolled-back one emits no side effect. No request transaction escapes into BackgroundTasks. Scheduler callback wrappers are separate stage-32 work.

### 24d — Async provider loading

Replace OpenAIService constructor DB queries with explicit awaited loading before provider/AI HTTP tests are activated. Keep provider selection/defaults and plain config data unchanged. **Gate:** U/services_tests/test_openai_service.py plus NEW settings-loader tests pass; no coroutine is stored as provider configuration and secrets remain excluded from public output.

### 25a — Application DI and controller base

Wire async database lifecycle/context into core dependencies, base controllers, HttpRepo and validators. Replace DB-bearing group/household properties with explicit loading. Implement driver-independent exception translation with existing HTTP semantics. **Gate:** U/core/test_dependencies.py, U/test_exceptions.py, I/test_validators.py and NEW DI/lifespan/controller tests pass. Coroutine endpoints are awaited; OpenAPI remains equal.

The whole existing I/test_validators.py depends on registration/user fixtures from 26a. Keep its full-file gate explicitly deferred to 26a; use truthful new component/DI tests here. Do not claim an old-backend pass as the target gate.

### 25b — Authentication providers

Convert security and credential/LDAP/OIDC DB calls, long-lived-token lookup and auth-cache invalidation. **Gate:** U/core/security/, U/core/test_security.py, U/test_security.py, U/test_session_cookie.py, I/user_tests/test_user_login.py and test_oidc_native.py pass. Preserve short read lifetimes and materialize users before connection release; blocking LDAP work does not block DB progress.

The whole existing I/user_tests/test_user_login.py exercises registration, password and API-token endpoints completed at 26a. Its whole-file gate is explicitly deferred to 26a; assess the available auth-provider components here and retain every original case.

### 26a — User services and HTTP

Convert registration/password/token/CRUD handlers and user services. Password change, reset-token consumption and token revocation must be atomic. **Gate:** I/user_tests/ and U/services_tests/user_services/test_user_service.py pass. Lockout, session cookies, images and API tokens retain their previous behavior.

Close the carried whole-file Tortoise gates for I/test_validators.py and I/user_tests/test_user_login.py from 25a/25b, including their existing fixtures, assertions and expected values. Record any additional fixture dependency rather than silently selecting convenient cases.

### 26b — Tenant lifecycle and management HTTP

Convert group/household creation/deletion, invitations, self-service and admin user/group/household actions. **Gate:** I/user_group_tests/test_group_registration.py and test_group_self_service.py; I/user_household_tests/test_group_invitation.py, test_household_self_service.py, test_household_permissions.py; I/admin_tests/test_admin_group_actions.py, test_admin_household_actions.py, test_admin_user_actions.py pass. No partial default tenant or over-consumed invitation persists on failure.

### 26c — Recipe CRUD and permission HTTP

Wire recipe CRUD/service permissions to the completed writers; port the raw permission query separately from generic scope. **Gate:** I/user_recipe_tests/test_recipe_crud.py, test_recipe_ingredients.py, test_recipe_steps.py, test_recipe_owner.py and test_recipe_cross_household.py pass. Preserve empty/missing slug behavior, fail-closed settings, owner-only delete versus collaborative editing, and supplied-create/protected-update identity rules.

### 27a — Organizer and food/unit HTTP

Await organizers, food/unit writers, merges, labels and seeding callers. **Gate:** I/category_tag_tool_tests/; I/user_recipe_tests/test_recipe_foods.py, test_recipe_units.py, test_recipe_substitutions.py; I/user_group_tests/test_group_seeder.py and I/user_household_tests/test_organize_permissions.py pass. Cross-group IDs remain rejected and no merge loses substitutions or notes.

### 27b — Recipe interactions and suggestions HTTP

Wire comments/timeline/share-token/ratings and suggestion routes to completed persistence. **Gate:** I/user_recipe_tests/test_recipe_ratings.py, test_recipe_comments.py, test_recipe_timeline_events.py, test_recipe_share_tokens.py, test_recipe_suggestions.py pass; complete U/repository_tests/test_recipe_repository.py and test_search.py pass on both engines. This closes the stage-21/22 carried gates.

### 27c — Cookbook, public explorer and SPA reads

Await cookbook and public explorer handlers plus SPA recipe metadata generation. **Gate:** I/user_household_tests/test_group_cookbooks.py, I/public_explorer_tests/, I/test_spa.py and U/test_spa_recipe_ingredients.py pass. Public/anonymous routes cannot leak private recipes; cookbook household scope and slug behavior are unchanged.

### 28a — Shopping-list HTTP

Wire shopping-list/list-item/label endpoints to stage-23 transactions and event dispatch. **Gate:** I/user_household_tests/test_group_shopping_lists.py, test_group_shopping_list_items.py and test_shopping_list_labels.py pass on both engines. Scaling, labels, ordering and parent timestamps remain correct through API mutations.

### 28b — Meal plans, actions, notifications and webhooks HTTP

Wire meal plans/rules, recipe actions, notifications and webhooks to async persistence and listeners. **Gate:** I/user_household_tests/test_group_mealplan.py, test_group_mealplan_rules.py, test_group_recipe_actions.py, test_group_notifications.py and test_group_webhooks.py pass. Preserve event payloads, date windows and rules.

### 28c — Provider/admin/application reads and scope closure

Wire provider configuration, group/household preferences/reports, app/admin information and analytics. **Gate:** I/user_group_tests/test_group_ai_providers.py and test_group_preferences.py; I/admin_tests/test_admin_ai_providers.py and test_admin_about.py; all I/user_household_tests/, full I/test_repository_factory.py, U/repository_tests/test_pagination.py and M/ pass. All previously carried scope/household gates now exercise Tortoise.

### 29 — Parser DB loading

Replace matcher/parser constructor/property DB queries with explicit awaited preloading; adapt the parser route and parser fixture DB access. Reuse stage-24d provider loading and keep pure NLP/matching calculations synchronous. **Gate:** U/services_tests/ingredient_parser/, U/services_tests/test_compile_source.py and test_transcription.py pass. Foods/units/aliases are loaded plain data, never coroutine-valued properties.

### 30a — Import/scraper and AI workflow

Propagate awaited repository/resolver access through import context, compiler/step callers, recipe scraper and AI creation. **Gate:** U/services_tests/test_recipe_import_workflow.py, test_organizer_resolver.py, U/services_tests/scraper_tests/; I/user_recipe_tests/test_recipe_create_from_ai.py, test_recipe_create_from_openai.py and test_recipe_create_from_video.py pass. Preserve URL deduplication and per-import reporting.

### 30b — Bulk, streaming and asset operations

Convert bulk recipe/scraper callers, SSE/background context ownership and file/asset DB coordination. **Gate:** U/services_tests/test_recipe_data_service.py; I/user_recipe_tests/test_recipe_bulk_action.py, test_recipe_bulk_import.py, test_recipe_asset_from_url.py and test_recipe_image_assets.py pass. NEW cancellation/failed-import tests prove connections close and partial graphs are rolled back while file behavior remains equivalent.

### 31a — Third-party recipe migrations

Port BaseMigrator's constructor lookups/rollback loop and DatabaseMigrationHelpers; update all inherited format entry points. These recipe imports are distinct from schema migrations. **Gate:** I/recipe_migration_tests/test_recipe_migrations.py and U/services_tests/test_paprika_migration.py pass. Preserve per-recipe success/failure reports and isolate each failure so PostgreSQL can continue importing.

### 31b — Recipe/group exports

Convert exporter interfaces, query-backed generators and export routes. Keep pure ZIP/template/file calculations out of DB transactions. **Gate:** I/user_recipe_tests/test_recipe_export_as.py and U/test_recipe_export_types.py pass; NEW export-lifetime tests prove streaming does not use a closed connection and exported content/tenant scope remains unchanged.

### 32a — Scheduler execution lifecycle

Make scheduler wrapper/registry/runner await DB callbacks and manage cancellation/shutdown. **Gate:** NEW runner tests prove invocation is awaited exactly once, errors are recorded, concurrent schedules cannot accidentally share a transaction, and shutdown drains/cancels jobs before closing pools. Stage-24c listeners are already asynchronous.

### 32b — Scheduled database tasks

Convert all eight DB task files, including password-reset/registration cleanup and locked-user reset. **Gate:** U/services_tests/scheduler/tasks/ passes; NEW tests cover the three cleanup/reset jobs without dedicated existing task tests. Preserve UTC midnight webhook boundaries, local meal-day selection, deduplication and expiry; each job owns fresh DB context.

### 33 — Native backup/export/restore

Replace reflection/engine/Table/insert/drop-create logic in alchemy_exporter.py with explicit Tortoise schema/table adapters and async transactional data export/import. Preserve ZIP layout, UUID/datetime/enum encoding, all join tables, ID sequences, and metadata coverage. Serialize backup-format compatibility metadata separately from Aerich state. After schema replacement, refresh connections on the existing application/test event loop; never initialize a second registry/loop to perform restore. **Gate:** U/services_tests/backup_v2_tests/test_alchemy_exporter.py, test_backup_file.py, native round-trip cases in test_backup_v2.py and I/admin_tests/test_admin_backup.py pass. Add a real deep-value round-trip check: the current test compares results of list.sort(), so its unchanged assertion alone is insufficient evidence.

### 34 — Historical archive-data import

Implement deterministic transformations for the nine existing backup versions, without replaying Alembic against an old live database. Port normalization, labels, slugs, ratings, household ownership/on-hand/last-made, cookbook/rule strings and unit standardization into the archive importer. Preserve exact fixture inputs and expectations. **Gate:** the complete U/services_tests/backup_v2_tests/test_backup_v2.py passes on both engines, especially test_database_restore_data, including pint standard_quantity=2 and standard_unit="cup". Add post-restore write/sequence and failure rollback tests. Passing on an empty imported data set is prohibited.

### 35 — Fresh Aerich baseline and startup/CLI

Create reviewed migrations from the complete current target schema, including FKs, checks, uniqueness, indexes and PostgreSQL extension ordering. Replace init_db/Alembic version detection/retries with Aerich initialization/upgrades and async idempotent seeding; retire old live-DB fix routines. Convert four maintenance scripts and launch boundaries; update task/package/container integration. **Gate:** NEW migration tests create an empty SQLite/PostgreSQL DB from committed migrations, verify head, restart unchanged, apply a subsequent test migration and reverse it on disposable data. No production startup uses generate_schemas as a substitute for migration history. Existing config/startup/admin tests pass; script smoke tests verify writes and cleanup.

### 36 — Historical test archive, removal, and complete acceptance

Move historical Alembic artifacts and their necessary frozen helpers outside mealie/; preserve revision identifiers and locale-data resolution. Update the database fixture locator and retain test-only legacy dependencies only if required. Remove obsolete SQLAlchemy models/helpers/adapters, production SQLAlchemy/Alembic/psycopg2 dependencies, unused imports and transitional selectors; retain ORM-neutral helper behavior that existing tests exercise. Update developer migration documentation and CI commands.

**Gate:** U/test_alembic.py, U/test_recipe_image_backfill.py, U/test_structured_recipe_times_migration.py, U/test_auto_init_config.py, U/test_code_generation.py and the entire suite pass with **uv run pytest -n 4 --dist loadfile** on **both** engines. Collected node IDs/assertions/expected values remain accounted for; no new skips/xfails or filtered full-suite run. AST plus textual audit finds zero SQLAlchemy imports under mealie/ (including type-only/dynamic imports) and no production Alembic invocation. A runtime-only install without legacy test dependencies starts, migrates, serves requests and shuts down. Pydantic/OpenAPI comparisons have no contract differences; frontend/generated files remain unchanged. Run task py:lint and task py:mypy; use the prescribed pytest command in place of Taskfile's different test worker count.

## New test artifacts for the stage gates

These are proposed files to create during implementation, not tests added or run in this planning session. All paths below are relative to **tests/unit_tests/tortoise_tests/**. Keep tests focused on observable data/transaction behavior, not a second copy of the implementation. Existing tests retain their assertions and expected values.

| Stage | Planned test file(s) and result required |
| --- | --- |
| 01 | test_query_access_contract.py: faithful field identity and real query rendering; test_legacy_archive_contract.py: full nonempty history and specific helper imports. |
| 02a | test_connections.py: both-engine config, connection options, rollback and shutdown. |
| 02b, 25a | test_fixture_lifecycle.py: four-worker fixture-write/HTTP-read/teardown on the same loop; final run uses Mealie app. |
| 03 | test_model_contracts.py: UUID/time/default/normalization/filter metadata and FK-cycle/through/check capability proofs. |
| 04 | test_identity_models.py: identity, preferences, membership, uniqueness and deletion. |
| 05 | test_organizer_models.py: joins, aliases, group uniqueness and cascade boundaries. |
| 06 | test_substitution_models.py: self/foreign/duplicate/note-only/ordered edges. |
| 07 | test_recipe_models.py: all child relations, ordering, constraints and current-schema serialization. |
| 08 | test_recipe_interaction_models.py: user/household pairs, cascades, projections. |
| 09 | test_shopping_models.py: references, labels, extras and owner-derived relations. |
| 10a–11 | test_auxiliary_models.py, test_model_coverage.py, test_provider_models.py: all remaining tables, defaults, constraints and provider cycles. |
| 12 | test_schema_contract.py: saved baseline field/JSON/validation/serialization contract; no lazy relation access. |
| 13–14b | test_scoped_repositories.py, test_generic_writes.py, test_identity_writes.py: scope sentinel, derived joins, bulk errors/rollback and identity protection. |
| 15–17 | test_filter_results.py, test_pagination_contract.py, test_search_contract.py: relationship existence/negation, no duplicate rows, NULL/order/count behavior and both dialect search paths. |
| 18–20 | test_recipe_graph_writes.py, test_organizer_writes.py, test_merge_transactions.py: nested replacement, organizer resolution and atomic food/unit merges. |
| 21–22 | test_recipe_derived_state.py, test_suggestions_contract.py: favorite/rating integrity, observed last-made semantics, concurrent updates and substitution ranking. |
| 23–24b | test_shopping_operations.py, test_auxiliary_repositories.py, test_seed_idempotence.py: timestamps/scaling, rules/provider pointers and repeated seeding. |
| 24c–24d | test_event_transactions.py, test_provider_loading.py: post-commit listeners with independent context and awaited config loading. |
| 30b–31b | test_background_import_lifecycle.py, test_export_lifecycle.py: cancellation/error cleanup, atomic graph writes and stream lifetime. |
| 32a–32b | test_scheduler_lifecycle.py, test_scheduled_cleanup.py: awaited execution, shutdown and missing task coverage. |
| 33–34 | test_backup_roundtrip.py, test_restore_atomicity.py: real deep-value/relational equality, cross-engine portability, sequence reuse and failure recovery. |
| 35–36 | test_aerich_lifecycle.py, test_cli_lifecycle.py, test_runtime_imports.py: fresh/repeated/subsequent migrations, script cleanup and SQLAlchemy-free runtime. |

## Risk register and required mitigations

| Risk | Concrete behavior to preserve and evidence |
| --- | --- |
| Schema contracts versus ORM helpers | Resolve the source-freeze interpretation. Prefetch/project outside Pydantic; preserve alias/default/validator/serialization behavior. Baseline schema/OpenAPI and nested response comparisons, not only import success. |
| Tortoise/Aerich/Python compatibility | Pin a proven combination, including wheels/drivers for Python 3.14 and deployment platforms. Test fresh/repeated migrations and runtime packaging before large model work. Never substitute another migration framework without changing the fixed decision. |
| Async event-loop ownership | Current tests initialize at import time; TestClient requests, async tests, threads and scheduler can otherwise use different loops. One initialized registry per owning loop, deterministic cleanup, no asyncio.run-per-query. Prove four-worker teardown without warnings/hangs. |
| SQLite write locks | SQLite serializes writers; short transactions, bounded lock handling and one database file per worker. Preserve appropriate WAL/foreign-key PRAGMAs for every connection. Avoid parallel writes on one transaction. Test cancellation and retry after rollback. |
| PostgreSQL isolation and connection state | Separate worker databases because restore drops/rebuilds tables. Close pools before database removal. Unique failures abort transactions until rollback/savepoint; search settings must not leak across pooled requests. Test concurrent slug/organizer creation. |
| UUID representation | SQLite historically stores CHAR(32); PostgreSQL uses native UUID. Preserve Python UUIDs and dashed HTTP/filesystem IDs. Verify raw queries, backups and the image-backfill test for UUID/dashed/hex inputs. |
| Date/time and revocation | Existing NaiveDateTime stores naive UTC and restores UTC; update_at is exposed as updatedAt. Preserve date-only/time/timedelta fields and microsecond/whole-second boundaries, especially tokens_valid_after and scheduler cutoffs, across both dialects. |
| Scalar types and defaults | SQLite affinity can accept data PostgreSQL rejects: ingredient quantity historically differs; enum names versus API values differ for AuthMethod. Test fractions, nulls, booleans, enum serialization, explicit IDs and integer sequence restoration. Keep public DB_URL expectations by translating config internally. |
| Constraints and cyclic FKs | Composite primary keys, explicit through tables and AI/user-recipe cycles cannot be assumed to map automatically. Preserve existing public IDs and business uniqueness with reviewed equivalent DDL. Food/unit uniqueness and GIN indexes are partly encoded in migrations rather than static metadata. |
| Cascades and orphan cleanup | SQLAlchemy delete-orphan/flush events exceed a simple ON DELETE clause. Test deletes of users, households, groups, recipes, organizers, labels, foods/units and substitutions on both engines. A food/organizer deletion must not accidentally delete recipes. |
| Derived tenancy | Recipe/shopping/meal household follows owner user; comments/timeline/ratings have derived group scope. Explicit join predicates must cover reads, writes, counts, search, suggestions and bulk operations. Owner reassignment and cross-household public/private tests are release gates. |
| Nested writes and concurrent derived values | No identity map/automatic flush to reconcile collections. Use explicit transaction sequencing for replacement/reorder, favorite/rating preservation, rating means, the observed monotonic global last-made value and list timestamps. Include failure injection and concurrent updates, not just CRUD happy paths. |
| Query semantics | Stock relation joins may multiply rows; NOT IN is not a row-level inequality. Preserve EXISTS/anti-EXISTS, CONTAINS ALL and aggregate relationship sorting. Test pagination/counts/NULL placement/seeded random order on both engines and truthful SQL inspection. |
| Search and collation | PostgreSQL fuzzy trigram ranking differs intentionally from SQLite tokenized fallback. Provision pg_trgm before its indexes; handle extension privileges. Preserve punctuation/transliteration/quotes/LIKE wildcard behavior and bounded ingredient queries. PostgreSQL-specific tests must actually execute. |
| Serialization cost and cycles | Tortoise relation managers are not ready Pydantic input. Explicit summary/full loading plans, recursion-bounded substitutions and extras-to-dict conversion. Check representative query counts and latency against the baseline to catch N+1 regressions. |
| Background side effects | A scheduler wrapper calling an async callback without await silently loses work. Background tasks must not retain request transactions. Await callbacks, own DB contexts, commit before publish, handle cancellation and keep blocking non-DB work off the loop. |
| Backups and old data | Native round-trip and historical ZIP imports remain required despite no live old-DB upgrades. Preserve all data/joins/metadata and parse versions explicitly. Test cross-engine portable archives, sequence repair and failed-restore recovery; never silently reset a populated database. |
| Migration lifecycle | SQLite ALTER/table-rebuild and PostgreSQL extension/DDL behavior differ. Review per-dialect Aerich SQL; verify migration head/model agreement and repeated startup. Serialize startup migration ownership across processes. Detect an old populated Alembic database and report unsupported upgrade; do not reset or stamp it as migrated. |
| Test-preservation conflicts | SQL identity/SQL text, reflection and history assertions need honest access adapters or explicit resolution. Preserve a nonempty legacy archive. SQLAlchemy may be present solely in test dependencies; verify the production distribution works without it. |

## Dependency inventory

The appendices below distinguish direct imports from indirect database consumers. File paths are grouped by package. A direct import inventory alone is insufficient: controllers inherit repository behavior, schema classes inherit MealieModel, and background/import/export workflows call synchronous services without spelling SQLAlchemy. Plain value helpers may remain unchanged after their shared dependency is removed.


### A. Direct SQLAlchemy/Alembic imports (exhaustive Python-file inventory)

AST inspection found 164 Python files importing SQLAlchemy and/or Alembic, including all 54 historical revision files. Imports inside functions and TYPE_CHECKING blocks are included. The migration template and non-Python configuration are listed separately below.

#### Runtime packages

| Package | Files |
| --- | --- |
| `mealie/core/dependencies` | `dependencies.py` |
| `mealie/core` | `exceptions.py` |
| `mealie/core/security/providers` | `auth_provider.py`, `credentials_provider.py`, `ldap_provider.py`, `openid_provider.py` |
| `mealie/core/security` | `security.py` |
| `mealie/db` | `db_setup.py`, `init_db.py` |
| `mealie/db/fixes` | `fix_group_with_no_name.py`, `fix_migration_data.py` |
| `mealie/db/models` | `_filterable_column.py`, `_model_base.py` |
| `mealie/db/models/_model_utils` | `auto_init.py`, `datetime.py`, `guid.py` |
| `mealie/db/models/group` | `ai_providers.py`, `exports.py`, `group.py`, `preferences.py`, `report.py` |
| `mealie/db/models/household` | `cookbook.py`, `events.py`, `household.py`, `household_to_recipe.py`, `invite_tokens.py`, `mealplan.py`, `preferences.py`, `recipe_action.py`, `shopping_list.py`, `webhooks.py` |
| `mealie/db/models/recipe` | `api_extras.py`, `assets.py`, `category.py`, `comment.py`, `ingredient.py`, `instruction.py`, `labels.py`, `note.py`, `nutrition.py`, `recipe.py`, `recipe_timeline.py`, `settings.py`, `shared.py`, `tag.py`, `tool.py` |
| `mealie/db/models/server` | `task.py` |
| `mealie/db/models/users` | `password_reset.py`, `user_to_recipe.py`, `users.py` |
| `mealie/repos` | `_recipe_suggestions.py`, `all_repositories.py`, `repository_ai_provider.py`, `repository_cookbooks.py`, `repository_factory.py`, `repository_foods.py`, `repository_generic.py`, `repository_group.py`, `repository_household.py`, `repository_meal_plan_rules.py`, `repository_meals.py`, `repository_recipes.py`, `repository_units.py`, `repository_users.py` |
| `mealie/routes/_base` | `base_controllers.py`, `mixins.py` |
| `mealie/routes/admin` | `admin_management_households.py` |
| `mealie/routes/app` | `app_about.py` |
| `mealie/routes/auth` | `auth.py` |
| `mealie/routes/recipe` | `recipe_crud_routes.py`, `shared_routes.py` |
| `mealie/routes/spa` | `__init__.py` |
| `mealie/routes/users` | `forgot_password.py` |
| `mealie/routes/validators` | `validators.py` |
| `mealie/schema/_mealie` | `mealie_model.py` |
| `mealie/schema/cookbook` | `cookbook.py` |
| `mealie/schema/group` | `ai_providers.py` |
| `mealie/schema/household` | `group_events.py`, `group_shopping_list.py`, `household.py`, `household_preferences.py` |
| `mealie/schema/meal_plan` | `new_meal.py`, `plan_rules.py` |
| `mealie/schema/recipe` | `recipe.py`, `recipe_category.py`, `recipe_comments.py`, `recipe_ingredient.py`, `recipe_share_token.py`, `recipe_timeline_events.py`, `recipe_tool.py` |
| `mealie/schema/reports` | `reports.py` |
| `mealie/schema/response` | `query_search.py` |
| `mealie/schema/user` | `user.py`, `user_passwords.py` |
| `mealie/scripts` | `reprocess_images.py` |
| `mealie/services/backups_v2` | `alchemy_exporter.py` |
| `mealie/services/event_bus_service` | `event_bus_listeners.py`, `event_bus_service.py` |
| `mealie/services/household_services` | `shopping_lists.py` |
| `mealie/services/migrations/utils` | `database_helpers.py` |
| `mealie/services/parser_services` | `_base.py`, `ingredient_parser.py` |
| `mealie/services/query_filter` | `builder.py` |
| `mealie/services/recipe` | `recipe_service.py` |
| `mealie/services/scheduler/tasks` | `create_timeline_events.py`, `purge_group_exports.py`, `purge_password_reset.py`, `purge_registration.py` |
| `mealie/services/user_services` | `password_reset_service.py` |

#### Historical migration package

| Package | Files |
| --- | --- |
| `mealie/alembic` | `env.py` |
| `mealie/alembic/versions` | All 54 files enumerated immediately below. |

Every path below is relative to `mealie/alembic/versions/`; preserve the full history in the test archive, not the production package.

- `2022-02-21-19.56.24_6b0f5f32d602_initial_tables.py`
- `2022-03-23-17.43.34_263dd6707191_convert_quantity_from_integer_to_float.py`
- `2022-03-27-19.30.28_f1a2dbee5fe9_add_original_text_column_to_recipes_.py`
- `2022-03-31-19.19.55_59eb59135381_add_tags_to_cookbooks.py`
- `2022-04-03-10.48.51_09dfc897ad62_add_require_all_for_cookbook_filters.py`
- `2022-06-01-11.12.06_ab0bae02578f_add_use_abbreviation_column_to_.py`
- `2022-06-15-21.05.34_f30cf048c228_add_new_webhook_fields.py`
- `2022-08-12-19.05.59_188374910655_add_login_attemps_and_locked_at_field_.py`
- `2022-08-13-17.07.07_089bfa50d0ed_add_is_ocr_recipe_column_to_recipes.py`
- `2022-08-29-13.57.40_44e8d670719d_add_extras_to_shopping_lists_list_items_.py`
- `2022-09-27-14.53.14_2ea7a807915c_add_recipe_timeline_events_table.py`
- `2022-11-03-13.10.24_1923519381ad_renamed_timeline_event_message_and_.py`
- `2022-11-22-03.42.45_167eb69066ad_add_recipe_scale_to_shopping_list_item_.py`
- `2023-01-21-16.54.44_165d943c64ee_add_related_user_to_mealplan.py`
- `2023-02-07-20.57.21_ff5f73b01a7a_add_missing_foreign_key_and_order_.py`
- `2023-02-10-21.18.32_16160bf731a0_add_more_indices_necessary_for_search.py`
- `2023-02-14-20.45.41_5ab195a474eb_add_normalized_search_properties.py`
- `2023-02-21-22.03.19_b04a08da2108_added_shopping_list_label_settings.py`
- `2023-02-22-21.45.52_38514b39a824_add_auth_method_to_user_table.py`
- `2023-04-13-06.47.04_b3dbb554ba53_postgres_fuzzy_search.py`
- `2023-08-06-21.00.34_04ac51cbe9a4_added_group_slug.py`
- `2023-08-14-19.30.49_1825b5225403_added_recipe_note_to_shopping_list_.py`
- `2023-08-15-16.25.07_bcfdad6b7355_remove_tool_name_and_slug_unique_.py`
- `2023-09-01-14.55.42_0341b154f79a_added_normalized_unit_and_food_names.py`
- `2023-10-04-14.29.26_dded3119c1fe_added_unique_constraints.py`
- `2023-10-19-19.22.55_ba1e4a6cfe99_added_plural_names_and_alias_tables_for_.py`
- `2024-02-23-16.15.07_2298bb460ffd_added_user_to_shopping_list.py`
- `2024-03-10-05.08.32_09aba125b57a_add_oidc_auth_method.py`
- `2024-03-18-02.28.15_d7c6efd2de42_migrate_favorites_and_ratings_to_user_.py`
- `2024-04-07-01.05.20_7788478a0338_add_group_recipe_actions.py`
- `2024-06-22-10.17.03_32d69327997b_add_staple_flag_to_foods.py`
- `2024-07-12-16.16.29_feecc8ffb956_add_households.py`
- `2024-09-02-21.39.49_be568e39ffdf_added_household_recipe_lock_setting_and_.py`
- `2024-09-18-14.52.55_1fe4bd37ccc8_add_households_filter_to_meal_plans.py`
- `2024-10-01-14.17.00_602927e1013e_add_the_rest_of_the_schema_org_.py`
- `2024-10-08-21.17.31_86054b40fd06_added_query_filter_string_to_cookbook_.py`
- `2024-10-20-09.47.46_3897397b4631_add_summary_to_recipe_instructions.py`
- `2024-10-23-15.50.59_b1020f328e98_add_recipe_yield_quantity.py`
- `2024-11-20-17.30.41_b9e516e2d3b3_add_household_to_recipe_last_made_.py`
- `2025-02-09-15.31.00_7cf3054cbbcc_remove_instructions_index.py`
- `2025-07-11-20.17.10_d7b3ce6fa31a_empty_migration_to_fix_food_flag_data.py`
- `2025-08-09-19.32.37_e6bb583aac2d_add_label_notifier_crud_bools.py`
- `2025-09-10-19.21.48_1d9a002d7234_add_referenced_recipe_to_ingredients.py`
- `2026-02-21-17.59.01_a39c7f1826e3_add_unit_standardization_fields.py`
- `2026-03-26-20.48.28_cdc93edaf73d_add_mealplan_updated_and_deleted_to_.py`
- `2026-03-27-20.19.07_4395a04f7784_add_announcements.py`
- `2026-05-10-18.44.53_c7427796f7b6_more_aggresive_normalization.py`
- `2026-05-18-16.27.05_2187537c52b8_add_table_for_ai_providers.py`
- `2026-08-24-16.31.43_69e942bab3aa_add_tokens_valid_after_column_to_users.py`
- `2026-08-25-09.00.00_b3f1c9a27d84_add_external_avatar_hash_to_users.py`
- `2026-09-03-14.20.00_f2191b69db2e_add_ingredient_substitutions.py`
- `2026-09-03-16.12.44_4b91d3a7c0e2_backfill_recipe_image_column.py`
- `2026-09-13-00.03.01_3527efeeec34_add_recipe_note_ref_link.py`
- `2026-09-24-13.16.56_27621d27c7e1_add_structured_recipe_times.py`

### B. Additional statically import-coupled backend files

This is the transitive closure of local Python import dependencies reaching the direct inventory, excluding the files already listed in A. It includes reexports, inherited schema consumers, and pure helpers sharing imports: inclusion does **not** mean every function needs async conversion or every file needs editing. The behavioral inventory in C identifies the actual persistence/async changes. Static imports cannot prove absence of runtime wiring; finish with textual and runtime audits too.

| Package | Files |
| --- | --- |
| `mealie` | `app.py`, `main.py` |
| `mealie/core/dependencies` | `__init__.py` |
| `mealie/core/security` | `__init__.py` |
| `mealie/db` | `migration_types.py` |
| `mealie/db/models` | `_all_models.py` |
| `mealie/db/models/group` | `__init__.py` |
| `mealie/db/models/household` | `__init__.py` |
| `mealie/db/models/recipe` | `__init__.py` |
| `mealie/db/models/server` | `__init__.py` |
| `mealie/db/models/users` | `__init__.py` |
| `mealie/repos` | `__init__.py`, `repository_shopping_list.py` |
| `mealie/repos/seed` | `_abstract_seeder.py`, `init_users.py`, `seeders.py` |
| `mealie/routes` | `__init__.py`, `utility_routes.py` |
| `mealie/routes/_base` | `__init__.py`, `checks.py`, `routers.py` |
| `mealie/routes/admin` | `__init__.py`, `admin_about.py`, `admin_backups.py`, `admin_debug.py`, `admin_email.py`, `admin_maintenance.py`, `admin_management_ai_providers.py`, `admin_management_groups.py`, `admin_management_users.py` |
| `mealie/routes/app` | `__init__.py` |
| `mealie/routes/auth` | `__init__.py` |
| `mealie/routes/comments` | `__init__.py` |
| `mealie/routes/explore` | `__init__.py`, `controller_public_cookbooks.py`, `controller_public_foods.py`, `controller_public_households.py`, `controller_public_organizers.py`, `controller_public_recipes.py` |
| `mealie/routes/groups` | `__init__.py`, `controller_group_ai_providers.py`, `controller_group_households.py`, `controller_group_reports.py`, `controller_group_self_service.py`, `controller_labels.py`, `controller_migrations.py`, `controller_seeder.py` |
| `mealie/routes/households` | `__init__.py`, `controller_cookbooks.py`, `controller_group_notifications.py`, `controller_group_recipe_actions.py`, `controller_household_self_service.py`, `controller_invitations.py`, `controller_mealplan.py`, `controller_mealplan_rules.py`, `controller_shopping_lists.py`, `controller_webhooks.py` |
| `mealie/routes/media` | `__init__.py`, `media_recipe.py`, `media_user.py` |
| `mealie/routes/organizers` | `__init__.py`, `controller_categories.py`, `controller_tags.py`, `controller_tools.py` |
| `mealie/routes/parser` | `__init__.py`, `ingredient_parser.py` |
| `mealie/routes/recipe` | `__init__.py`, `_base.py`, `bulk_actions.py`, `comments.py`, `exports.py`, `timeline_events.py` |
| `mealie/routes/shared` | `__init__.py` |
| `mealie/routes/unit_and_foods` | `__init__.py`, `foods.py`, `units.py` |
| `mealie/routes/users` | `__init__.py`, `_helpers.py`, `api_tokens.py`, `crud.py`, `images.py`, `ratings.py`, `registration.py` |
| `mealie/routes/validators` | `__init__.py` |
| `mealie/schema/_mealie` | `__init__.py` |
| `mealie/schema/admin` | `__init__.py`, `about.py`, `debug.py`, `email.py`, `maintenance.py` |
| `mealie/schema/analytics` | `__init__.py`, `analytics.py` |
| `mealie/schema/cookbook` | `__init__.py` |
| `mealie/schema/group` | `__init__.py`, `group.py`, `group_exports.py`, `group_migration.py`, `group_preferences.py`, `group_seeder.py`, `group_statistics.py` |
| `mealie/schema/household` | `__init__.py`, `group_recipe_action.py`, `household_permissions.py`, `household_statistics.py`, `invite_token.py`, `webhook.py` |
| `mealie/schema/labels` | `__init__.py`, `multi_purpose_label.py` |
| `mealie/schema/meal_plan` | `__init__.py`, `shopping_list.py` |
| `mealie/schema/recipe` | `__init__.py`, `recipe_asset.py`, `recipe_bulk_actions.py`, `recipe_notes.py`, `recipe_nutrition.py`, `recipe_scraper.py`, `recipe_settings.py`, `recipe_step.py`, `recipe_suggestion.py`, `request_helpers.py` |
| `mealie/schema/reports` | `__init__.py` |
| `mealie/schema/response` | `__init__.py`, `pagination.py`, `responses.py` |
| `mealie/schema/user` | `__init__.py`, `auth.py`, `registration.py` |
| `mealie/scripts` | `change_password.py`, `make_admin.py`, `reset_locked_users.py` |
| `mealie/services/analytics` | `service_analytics.py` |
| `mealie/services/backups_v2` | `backup_v2.py` |
| `mealie/services/event_bus_service` | `event_types.py`, `publisher.py` |
| `mealie/services/exporter` | `__init__.py`, `_abc_exporter.py`, `exporter.py`, `recipe_exporter.py` |
| `mealie/services/group_services` | `group_service.py`, `labels_service.py` |
| `mealie/services/household_services` | `household_service.py` |
| `mealie/services/migrations` | `__init__.py`, `_migration_base.py`, `chowdown.py`, `cookn.py`, `copymethat.py`, `mealie_alpha.py`, `myrecipebox.py`, `nextcloud.py`, `paprika.py`, `plantoeat.py`, `recipekeeper.py`, `tandoor.py` |
| `mealie/services/migrations/utils` | `migration_helpers.py` |
| `mealie/services/openai` | `__init__.py`, `openai.py`, `transcription.py` |
| `mealie/services/parser_services` | `__init__.py` |
| `mealie/services/parser_services/brute` | `__init__.py`, `process.py` |
| `mealie/services/parser_services/openai` | `__init__.py`, `parser.py` |
| `mealie/services/parser_services/parser_utils` | `__init__.py`, `unit_utils.py` |
| `mealie/services/recipe` | `ai_recipe_service.py`, `organizer_resolver.py`, `recipe_bulk_service.py`, `recipe_data_service.py`, `template_service.py` |
| `mealie/services/recipe/import_workflow` | `__init__.py`, `base.py`, `context.py`, `recipe_conversion.py`, `workflow.py` |
| `mealie/services/recipe/import_workflow/compilers` | `__init__.py`, `base.py`, `image.py`, `structured_data.py`, `transcription.py`, `web_page.py` |
| `mealie/services/recipe/import_workflow/steps` | `__init__.py`, `build_recipe.py`, `compile_source.py`, `resolve_organizers.py`, `translate_recipe.py` |
| `mealie/services/scheduler/tasks` | `__init__.py`, `delete_old_checked_shopping_list_items.py`, `post_webhooks.py`, `purge_expired_share_tokens.py`, `reset_locked_users.py` |
| `mealie/services/scraper` | `cleaner.py`, `recipe_bulk_scraper.py`, `recipe_scraper.py`, `scraped_extras.py`, `scraper.py`, `scraper_strategies.py` |
| `mealie/services/seeder` | `seeder_service.py` |
| `mealie/services/user_services` | `registration_service.py`, `user_service.py` |

### C. Behavioral dependencies and runtime wiring

The paths in A/B are the file inventory; this table records what must be replaced or reviewed in each package, including callback/configuration relationships that an import graph misses.

| Package/files | SQLAlchemy-dependent behavior or async propagation |
| --- | --- |
| mealie/db/db_setup.py, init_db.py | Global engine/sessionmaker, connection PRAGMAs, request generator/context manager, health retries, Alembic head detection/upgrades, pg_trgm setup, seed startup and cleanup. |
| mealie/db/fixes/*, migration_types.py | SQL expressions/reflection and data repair after old migrations; exported custom SQLAlchemy GUID/datetime types. Retire live-history repair; preserve necessary archive-import transformations separately. |
| mealie/db/models/_model_base.py, _filterable_column.py, _model_utils/*, _all_models.py and model package exports | Declarative metadata, mapped-column filterability, constructor/update mapper inspection, implicit nested resolution, type decorators, normalization, timestamp synonyms and model discovery. helpers.py is pure but supplies auto_init's constructor invocation. Empty package initializers need no persistence rewrite. |
| mealie/db/models/group, household, recipe, users, server | All mapped classes and association tables in A. Relationships, association proxies, hybrid properties, ordered collections, query expressions, checks, indexes, unique constraints, cascade/delete-orphan, events and defaults must be mapped explicitly. See stages 03–11 and the risk register. |
| mealie/repos/all_repositories.py, repository_factory.py | Session-bearing factory; group/household/None/NOT_SET scoping; category/tag counts, empty organizer queries and merges; dialect UUID conversion. Factory properties may remain synchronous if construction has no I/O. |
| mealie/repos/repository_generic.py, repository_shopping_list.py | CRUD, ORM graph construction/update, commit/rollback/refresh, missing/unique errors, schema loading, filtering, pagination/search and update delegates. _utils.py supplies ORM-neutral NOT_SET semantics and must remain equivalent. |
| mealie/repos/repository_group.py, repository_household.py, repository_users.py | Name/slug lookup/retry, ownership, counts, password mutation, ratings/favorites and household-to-recipe state. |
| mealie/repos/repository_recipes.py, _recipe_suggestions.py | Slug/organizer reconciliation, recipe writes/deletes/images, computed ratings/last-made, nested filtering, substitution-aware suggestions and deterministic ranking. |
| mealie/repos/repository_foods.py, repository_units.py | Scoped lookup, graph merges, substitution-edge reconciliation, selective flush sequencing, shopping-list repointing and deletion. |
| mealie/repos/repository_cookbooks.py, repository_meals.py, repository_meal_plan_rules.py, repository_ai_provider.py | Collision retry/savepoints, dates/today, OR/NULL rules, provider settings pointers and key-preserving writes. |
| mealie/repos/seed/_abstract_seeder.py, init_users.py, seeders.py; mealie/services/seeder/seeder_service.py | Sync DB interfaces and generators, default users, seed loads and fallback writes. Preserve locale data and seed values. |
| mealie/schema/_mealie/mealie_model.py, response/query_search.py, recipe/recipe.py | General/recipe search SQL, pg_trgm connection settings, normalization and eager-loading hints. MealieModel inheritance makes other schema files import-coupled even when they are pure DTOs. |
| Remaining directly dependent mealie/schema files in A | LoaderOption/joinedload/selectinload graphs, ORM-model imports, related projections. cookbook/cookbook.py and meal_plan/plan_rules.py validate filters by compiling SQLAlchemy queries. Preserve validation strictness without executing async DB calls in validators. |
| mealie/services/query_filter/builder.py | SQL expressions, mapper/type/relationship/proxy inspection, security filterability, correlated EXISTS and aggregate ordering. operators.py, keywords.py and package exports are ORM-neutral grammar dependencies. |
| mealie/core/dependencies/dependencies.py, security/security.py, security/providers/*, exceptions.py | Request/session injection, authentication/user materialization, credential/OIDC/LDAP queries, auth cache invalidation, SQLAlchemy exception categories. Async endpoints currently still call sync persistence. |
| mealie/routes/_base/base_controllers.py, mixins.py, controller.py | DB-bearing group/household properties, repository factories and CRUD delegation; Session rollback; sqlite3/psycopg2 unique detection; controller registration must preserve coroutine execution. checks.py acts on materialized schemas and can stay pure. |
| All controller consumers enumerated in B | Follow awaited repository/service calls through admin, explorer, groups, households, organizers, parser, recipe, shared, food/unit and user routes. Merely making the repository async is insufficient. admin_email/media helpers can retain pure email/file bodies while auth dependencies change. |
| mealie/routes/auth/auth.py, app/app_about.py, spa/__init__.py, users/forgot_password.py, validators/validators.py | Independent session injection and ORM queries, public/default-group startup reads, SPA recipe metadata, password/token work and registration/plan validation. Preserve anonymous-access behavior. |
| mealie/services/group_services/*, household_services/household_service.py, user_services/* | Multi-write tenant creation/deletion, invitations and registration, password reset/consume/revoke, label/list coordination and repository re-scoping via repos.session. Use operation-level transactions. |
| mealie/services/household_services/shopping_lists.py | Direct select plus complex recipe-reference/scaling/merge/order/label operations; checked/on-hand items and duplicated update IDs require existing arithmetic and scope semantics. |
| mealie/services/recipe/recipe_service.py | Raw permission CASE/COALESCE/COUNT/SUM queries, expanding IN/UUID conversion, recipe read/write/image/copy operations. Preserve missing/default settings, owner-only deletion versus collaborative updates and fail-closed access. |
| mealie/services/recipe/recipe_bulk_service.py, ai_recipe_service.py, organizer_resolver.py; import_workflow/context.py, steps/resolve_organizers.py and workflow/step callers in B | DB-backed context and resolution, bulk/SSE/background task lifetimes; preserve cancellation, report generation and transaction ownership. recipe_data_service.py/template_service.py are file/data helpers; do not make their pure work query the DB. |
| mealie/services/parser_services/_base.py, ingredient_parser.py, brute/__init__.py, brute/process.py, openai/parser.py; services/openai/openai.py | Matcher DB reads hidden in properties; provider settings queried in constructors; preload asynchronously and pass plain data into pure parsing. services/matching.py itself is pure. |
| mealie/services/scraper/recipe_bulk_scraper.py, recipe_scraper.py, scraped_extras.py, scraper.py, scraper_strategies.py | Existing-recipe lookup, enrichment/import and bulk persistence callers. Fetch/cleaner/network computations need only appropriate scheduling, not an ORM rewrite. |
| mealie/services/migrations/_migration_base.py, utils/database_helpers.py and all ten format subclasses in B | Constructor DB queries, sync per-recipe writes and rollback, reports and inherited entry points. Preserve per-recipe failure isolation; PostgreSQL must not retain an aborted transaction for the rest of an import. |
| mealie/services/exporter/_abc_exporter.py, exporter.py, recipe_exporter.py | Sync DB query/generator contracts for recipe/group exports. Preserve ZIP/JSON/template contents and response streaming lifetimes. |
| mealie/services/event_bus_service/event_bus_service.py, event_bus_listeners.py | Session injection, fanout queries, listener-owned contexts, subscriber filters, webhook meal selection. publisher.py and event_types.py are downstream side-effect/payload consumers, not database adapters. |
| mealie/services/scheduler/scheduler_service.py, runner.py, scheduler_registry.py, scheduled_func.py, __init__.py | Callback registry and wrapper currently call sync functions; await jobs, preserve error isolation and drain/cancel handles before DB shutdown. These runtime callback edges are not all visible in B. |
| mealie/services/scheduler/tasks/* | Eight tasks: create_timeline_events.py, delete_old_checked_shopping_list_items.py, post_webhooks.py, purge_expired_share_tokens.py, purge_group_exports.py, purge_password_reset.py, purge_registration.py, reset_locked_users.py plus exports. Preserve UTC midnight windows, local meal-day selection, deduplication, expiry and per-job context. |
| mealie/services/backups_v2/alchemy_exporter.py, backup_v2.py, backup_file.py | Reflection, table creation/drop, type serialization, sequence reset, constraints and old migration application. backup_file.py has no ORM import but reads alembic_version as an archive-format field. Preserve that compatibility separately from actual migration state. |
| mealie/services/analytics/service_analytics.py | Stores AllRepositories; currently little query logic. Update context typing and future callers without inventing new behavior. |
| mealie/scripts/change_password.py, make_admin.py, reset_locked_users.py, reprocess_images.py | Standalone session_context and raw SQL entry points; one outer async runner with initialize/close, no nested per-query loops. |
| mealie/app.py, mealie/main.py | Database startup and scheduler lifespan, launcher/CLI boundaries. Stop jobs before pool shutdown; avoid import-time connections. |
| mealie/core/settings/db_providers.py, settings.py, core/config.py | SQLAlchemy-style connection URLs, cached provider settings and SQLite journal flag. Keep public settings/URL expectations stable; adapt internal Tortoise connection configuration. These config dependencies do not themselves import SQLAlchemy. |

### D. Tests and fixtures

All existing HTTP tests indirectly exercise persistence. They remain in the final full-suite run. The following are the specifically ORM-coupled fixture/support files, followed by an exhaustive direct-import test inventory.

| Files/package | Required database adaptation |
| --- | --- |
| tests/conftest.py | Import-time init_db, SessionLocal override, SQLAlchemy admin connection to create/drop PostgreSQL worker databases; TestClient lifespan/event-loop ownership, cookie isolation and DATA_DIR cleanup. Keep separate DBs per gw worker and file-grouped execution. |
| tests/fixtures/fixture_database.py | Module-scoped Session/sessionmaker and unfiltered repository construction; replace with loop-owned async context and test access adapter. |
| tests/fixtures/fixture_users.py, fixture_admin.py, fixture_multitenant.py | Session annotations/context manager, scoped repositories, fixture registration/login and cleanup. Preserve all setup assertions and IDs/tokens. |
| tests/fixtures/fixture_recipe.py | Synchronous repository seeding/teardown and NoResultFound suppression. Await target operations or use the test-only portal; preserve seeded recipes and cleanup behavior. |
| tests/fixtures/fixture_shopping_lists.py | Session.get/expire workaround for stale identity-map cascades and exception handling. Query current target state and preserve deletion/cleanup coverage, without retaining a fake Session. |
| tests/fixtures/__init__.py | Fixture registration/reexports; keep all names and intended scopes. |
| tests/utils/alembic_reader.py | Historical database-artifact locator and version extraction; retain the full revision chain outside production and identical expected version metadata. Resolve edit-scope interpretation first. |
| tests/utils/fixture_schemas.py, seed_data.py, routes/test_mixins.py; tests/multitenant_tests/case_abc.py | Stored repositories, schema/data factories and generic CRUD/test helpers. Only database access mechanics change; preserve test cases and assertions. |
| tests/unit_tests/services_tests/ingredient_parser/conftest.py | Sync repository-backed parser setup and types; preload on the owning loop. |
| tests/unit_tests/test_alembic.py, test_recipe_image_backfill.py, test_structured_recipe_times_migration.py | Keep tests/expected values intact; historical import paths resolve through the nonempty archive. Correct relocated locale-data lookup without changing translations. |
| tests/unit_tests/test_auto_init_config.py | Preserve the pure exclusion/identity-protection helper contract even after removing mapper-dependent auto_init. |
| tests/unit_tests/test_config.py | Exact sqlite:/// and postgresql:// public URL assertions must stay unchanged; adapt internally. |
| tests/unit_tests/repository_tests/test_query_filter_builder.py | Mechanical query construction/inspection may change; field identity and literal SQL assertions may not be weakened. Stage-01 proof is mandatory. |
| tests/unit_tests/services_tests/backup_v2_tests/test_alchemy_exporter.py, test_backup_v2.py | Async invocation/introspection and data access adapters, JSON compatibility key and metadata coverage, nine old ZIP imports with original expectations. No skip/empty restore/legacy-only implementation counts as proof. |

#### Direct SQLAlchemy/Alembic imports

| Package | Files |
| --- | --- |
| `tests` | `conftest.py` |
| `tests/fixtures` | `fixture_admin.py`, `fixture_database.py`, `fixture_multitenant.py`, `fixture_recipe.py`, `fixture_shopping_lists.py`, `fixture_users.py` |
| `tests/integration_tests/admin_tests` | `test_admin_group_actions.py` |
| `tests/integration_tests` | `test_repository_factory.py` |
| `tests/integration_tests/user_recipe_tests` | `test_recipe_bulk_action.py`, `test_recipe_share_tokens.py` |
| `tests/unit_tests/repository_tests` | `test_food_repository.py`, `test_pagination.py`, `test_query_filter_builder.py`, `test_recipe_repository.py`, `test_search.py`, `test_unit_repository.py` |
| `tests/unit_tests/services_tests/backup_v2_tests` | `test_backup_v2.py` |
| `tests/unit_tests/services_tests/ingredient_parser` | `conftest.py` |
| `tests/utils/routes` | `test_mixins.py` |

#### Additional explicit DB/repository access consumers

| Package | Files |
| --- | --- |
| `tests/integration_tests/admin_tests` | `test_admin_about.py`, `test_admin_ai_providers.py`, `test_admin_household_actions.py`, `test_admin_user_actions.py` |
| `tests/integration_tests/public_explorer_tests` | `test_public_cookbooks.py`, `test_public_foods.py`, `test_public_households.py`, `test_public_organizers.py`, `test_public_recipes.py` |
| `tests/integration_tests` | `test_spa.py`, `test_validators.py` |
| `tests/integration_tests/user_group_tests` | `test_group_ai_providers.py`, `test_group_registration.py`, `test_group_seeder.py`, `test_group_self_service.py` |
| `tests/integration_tests/user_household_tests` | `test_group_cookbooks.py`, `test_group_mealplan.py`, `test_group_mealplan_rules.py`, `test_group_recipe_actions.py`, `test_group_shopping_list_items.py`, `test_group_shopping_lists.py`, `test_household_perferences.py`, `test_household_permissions.py`, `test_household_self_service.py`, `test_organize_permissions.py`, `test_shopping_list_labels.py` |
| `tests/integration_tests/user_recipe_tests` | `test_recipe_comments.py`, `test_recipe_create_from_ai.py`, `test_recipe_create_from_openai.py`, `test_recipe_create_from_video.py`, `test_recipe_cross_household.py`, `test_recipe_crud.py`, `test_recipe_owner.py`, `test_recipe_ratings.py`, `test_recipe_substitutions.py`, `test_recipe_suggestions.py` |
| `tests/integration_tests/user_tests` | `test_user_crud.py`, `test_user_login.py`, `test_user_password_services.py` |
| `tests/multitenant_tests` | `case_abc.py`, `test_multitenant_cases.py` |
| `tests/unit_tests/core/security/providers` | `test_credentials_provider.py`, `test_openid_provider.py` |
| `tests/unit_tests/repository_tests` | `test_cookbook_repository.py`, `test_group_repository.py`, `test_user_repository.py` |
| `tests/unit_tests/services_tests/backup_v2_tests` | `test_alchemy_exporter.py` |
| `tests/unit_tests/services_tests/ingredient_parser` | `test_brute_parser.py`, `test_nlp_parser.py`, `test_openai_parser.py` |
| `tests/unit_tests/services_tests/scheduler/tasks` | `test_delete_old_checked_shopping_list_items.py`, `test_post_webhook.py`, `test_purge_expired_share_tokens.py`, `test_purge_group_exports.py` |
| `tests/unit_tests/services_tests` | `test_organizer_resolver.py` |
| `tests/unit_tests/services_tests/user_services` | `test_user_service.py` |
| `tests/unit_tests` | `test_auto_init_config.py`, `test_security.py` |
| `tests/utils` | `alembic_reader.py`, `fixture_schemas.py`, `seed_data.py` |
### E. Migration/configuration/build support outside the Python import inventory

| Package/file | Dependency and disposition |
| --- | --- |
| mealie/alembic/alembic.ini | Alembic/SQLAlchemy configuration; replace production configuration with Aerich. |
| mealie/alembic/script.py.mako | Template emits SQLAlchemy/Alembic imports; remove from mealie/ at final cutover. |
| mealie/alembic/README | Rewrite migration guidance; historical material may live with the test archive. |
| pyproject.toml, uv.lock | SQLAlchemy, Alembic and psycopg2-binary dependency pins; pgsql extra, pytest loop settings and Alembic Ruff configuration. Add/pin Tortoise, Aerich and async drivers; isolate any historical-test dependencies in development. |
| Taskfile.yml | py:migrate invokes Alembic; setup/package tasks install/export pgsql; py:test currently uses -n auto. Replace migration command, preserve packaging support and use the required four-worker loadfile test invocation. |
| docker/Dockerfile | Dependency export/install includes the pgsql extra; prove the built runtime contains migrations/async driver dependencies but does not need historical-test dependencies. |
| .github/workflows/test-backend.yml | SQLite/PostgreSQL matrix, pgsql dependency install and task py:test. Keep both-engine execution and worker isolation; use four workers with loadfile for this rewrite's acceptance. |
| dev/code-generation/utils/anonymize_backups.py | Preserves Alembic version and enum fields in archive data; retain compatibility semantics while reviewing new backup metadata. |
| dev/code-generation/main.py and generated schema/type exports | Import/contract verification after internal refactoring. No Pydantic API schema changes or manually edited generated exports are planned. |
| docs/docs/contributors/developers-guide/database-changes.md | Alembic generation, reflection exclusions and upgrade guidance; replace with fresh Aerich workflow and both-engine review steps. |
| docs/docs/contributors/developers-guide/building-packages.md | pgsql dependency export instructions; keep consistent with the selected async driver extra. |

### F. Reproducing and closing the inventory

Use repository-local searches and AST inspection rather than only grep for import lines. The inventory above includes imports nested inside functions and indirect local-import consumers. At implementation completion:

```sh
rg -n -i 'sqlalchemy|alembic|SessionLocal|generate_session|session_context|SqlAlchemyBase' mealie
rg -n 'create_task|add_task|run_daily|run_hourly|run_minutely|\.session\b' mealie
rg -n -i 'sqlalchemy|alembic|psycopg2' pyproject.toml Taskfile.yml docker .github
```

Review every remaining hit: descriptive backup metadata/compatibility identifiers may legitimately contain the word Alembic, but imports, engine/session behavior and migration invocations in the runtime may not survive. Supplement searches with an AST import audit and a startup/request/scheduler/CLI smoke test in an environment with SQLAlchemy and Alembic absent. Verify that only permitted test database mechanics changed and every original assertion/expected value is retained. Finish with both full-suite reports, schema/API comparison, migration smoke results and a complete remaining-risk record.

## Review notes

Status: AI-assisted proposed changes, not yet human-approved. Original plan preserved at commit c1d2b7705caf3710642a9466ddbd206666cbc26d and plan-unreviewed.md. The original 52 stage IDs and inventory are retained.

Proposed corrections: reuse the supplied baseline and make01 a bounded evidence/constraint checkpoint; explicitly cap cumulative AI time at six hours; move a small Aerich compatibility proof into02a while leaving full history at35; carry whole login and validator tests to26a because their user-endpoint dependencies are not ready at25a/25b; answer the four scope questions without weakening contracts. The original author already repaired several earlier draft ordering problems, which are not counted as reviewer changes.

Review assistance was provided by Codex. The participant's actual decision and any human review time must be recorded after they respond; none is invented here.
