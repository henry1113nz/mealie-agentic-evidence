# Workflow A independent test-integrity and API-shape audit

Audit date: 5 October 2026. Baseline: `e365efc71d04677324b9a4aa262b040de33d8676`. Audited snapshot: `827d7d1868ecde35844fea1521c92311a6cf2274` in `mealie-wf-a`; the working tree was clean. This was a read-only source review after the experimental session ended. No Mealie source was imported or executed, no test suite was run, and no clone files were modified. Results below are separate from the measurement run.

## Confirmed finding: two PostgreSQL tests silently stop testing fuzzy search

**Assessment: test coverage regression, high confidence from direct control-flow review.** In `tests/unit_tests/repository_tests/test_search.py:116` and `tests/unit_tests/repository_tests/test_recipe_repository.py:571`, the SQLAlchemy accessor `session.get_bind().name` was changed to Tortoise's `session.capabilities.dialect`, but the comparison value remained `"postgresql"`. Both functions immediately return when that value differs.

The installed Tortoise backend defines its PostgreSQL dialect as **`"postgres"`** in `.venv/lib/python3.14/site-packages/tortoise/backends/base_postgres/client.py:47–48`; `AsyncpgDBClient` inherits that backend at `tortoise/backends/asyncpg/client.py:34`. The migrated production `SearchFilter` correctly uses `"postgres"` in `mealie/schema/response/query_search.py:58`.

Consequently, on a normal Tortoise PostgreSQL connection, both guards return before calling the search or evaluating the unchanged assertions. Provided their fixtures complete, pytest reports these functions as passing rather than skipped. The unreachable assertions are the expected unit result `"Table Spoon"` (`test_search.py:123`) and recipe result `"Steinbock Sloop"` (`test_recipe_repository.py:578`). At baseline the guards used SQLAlchemy's correct `"postgresql"` value (`test_search.py:115`, `test_recipe_repository.py:564`). SQLite already returned early at baseline; this finding concerns the lost PostgreSQL coverage.

The exact failure mechanism is observed in source. The explanation that a mechanical accessor replacement overlooked the ORM-specific dialect name is an inference; the audit does not establish intent. Preserved assertion counts and skip-marker counts do **not** establish semantic preservation here. The experimental snapshot was left unchanged so this remains reportable evidence.

## Broad structural checks and their limits

The AST audit compared all tracked Python source under `tests`, `mealie/schema`, and `mealie/routes` against the baseline. For assertion comparison only, it normalizes `await` and the single-argument `run_db(...)` / `await_db(...)` bridges. The bridges themselves were reviewed: they await on the TestClient portal and do not substitute success values or swallow failures.

| Check | Baseline | Snapshot | Interpretation |
|---|---:|---:|---|
| Test-function definitions in `test_*.py` | 1,158 | 1,161 | Every existing qualified test name remains; three DB-URL tests were added. These are source definitions, not collected parametrized cases. |
| `assert` statements in `test_*.py` | 3,837 | 3,847 | All ten additions belong to the three new URL tests. |
| Explicit `pytest.skip`, `xfail`, and skip/xfail decorator calls | 11 | 11 | No AST changes; this excludes `importorskip` and silent returns. |
| Existing test decorator / parametrization changes | — | 0 | Expected values in these decorators remain unchanged. |
| Existing `pytest.raises`, `pytest.warns`, and `assert_*` call changes after bridge normalization | — | 0 | Structural preservation only. |
| Existing test branch-condition changes after bridge normalization | — | 2 | Both are the incorrect PostgreSQL guards above. |

The only changed existing assertion after bridge normalization substitutes `TortoiseModel.normalize` for `SqlAlchemyBase.normalize` at `test_search.py:156`; the expected value is unchanged. A fixture assertion that the TestClient portal exists was added at `tests/fixtures/fixture_database.py:45`. Changed constants in existing tests were also enumerated and inspected: URL/SQL adaptation, mock initialization, model metadata enumeration, and ORM relation saving account for them; no changed literal assertion expectation was found. This is a focused source audit, not a formal proof that every test retains equivalent runtime coverage.

## Other changes relevant to interpreting results

- **PostgreSQL exception fixtures:** `tests/utils/routes/test_mixins.py:11–14` replaces a `Mock(spec=psycopg2.Error)` / SQLAlchemy wrapper with a synthetic exception carrying `sqlstate`, wrapped in Tortoise's `IntegrityError`. The `23505 → True` and `23503 → False` expectations remain. The old `pytest.importorskip("psycopg2")` was removed, so two parametrized cases no longer depend on that optional driver. This can change pass/skip totals without adding integration coverage. It tests an exception shape, not a real asyncpg-generated exception. No incorrect result is established by this change alone.
- **Other mocked boundaries and setup:** reviewed transaction-context mocks, `AsyncMock` substitutions, ingredient-parser initialization flags, relation saves, and the admin household fixture change. Existing assertion outcomes are retained; these primarily adapt DB access and setup. No additional concrete weakening was established in those reviewed changes. Legacy Alembic files were copied into test fixtures for historical backup/migration data; their presence is not evidence of active production SQLAlchemy access.
- **SQL text assertions:** `tests/unit_tests/repository_tests/test_query_filter_builder.py:173` and `:192` normalize emitted SQL quoting and equality spacing before checking the existing expected substrings. This adapts compiler formatting; it does not independently demonstrate query-result equivalence.

## Schema and route preservation

No schema class was added or removed. AST comparison found no changes to class-level schema fields, defaults, aliases/configuration assignments, or base classes. No decorated route path/method metadata, arguments/defaults/annotations, or return annotations changed in this comparison. The generated frontend API type directory has no diff. These support **static public-shape preservation**, not verified runtime compatibility.

Schema source itself is not unchanged: 20 schema files and 39 helper methods changed, including 33 `loader_options` methods, two query validators, and search helpers. The substantial ORM rewrites at `mealie/schema/_mealie/mealie_model.py:138` and `mealie/schema/recipe/recipe.py:370` affect search behavior behind the same public fields. This audit did not establish an additional concrete schema-contract defect. It also did not compare generated OpenAPI at runtime or establish SQLite/PostgreSQL response and validation parity. If the assignment wording is interpreted as prohibiting any schema-file edits, these helper changes must be disclosed separately from the preserved public shape.

## Reproduction and evidence

`static_audit.py` and `control_audit.py` parse source only, using `git show` for baseline text. Their outputs are `static-audit.json` and `control-audit.json`. Full source diffs are preserved in `tests.diff` and `schemas.diff`; `finding-sources.txt` retains the relevant guards and installed-backend constant. Run these analysis scripts with `uv run --no-project --python <clone>/.venv/bin/python python <script>`; they do not invoke pytest.

Recommended report wording: “All existing test definitions and direct assertion expectations were retained, but independent review found that two PostgreSQL fuzzy-search tests returned before their assertions because the migrated dialect guard used SQLAlchemy's backend name. Thus unchanged test/skip counts were insufficient to establish that the test suite had not been weakened.”
