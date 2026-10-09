Here is the proposed migration plan to replace SQLAlchemy and Alembic with Tortoise ORM and Aerich across the Mealie backend:

```markdown
# Mealie Backend: SQLAlchemy & Alembic to Tortoise ORM & Aerich Migration Plan

## 1. Objective
Replace SQLAlchemy with Tortoise ORM across the Mealie backend (`mealie/`), making all database access async, keeping support for both SQLite and PostgreSQL, replacing Alembic with Aerich, maintaining identical HTTP API and Pydantic schemas in `mealie/schema`, and ensuring all existing tests pass when run with `uv run pytest -n 4 --dist loadfile`.

---

## 2. Key Architectural Decisions & Constraints
1. **Zero SQLAlchemy in `mealie/`**: When the rewrite is finished, `grep -ri "sqlalchemy" mealie/` will return zero matches.
2. **Async Database Access**: Tortoise ORM is fully async. All repository methods (`create`, `get_one`, `get_all`, `update`, `delete`, `page_all`, etc.) become `async def`. Routes, services, scheduler tasks, and event bus listeners become async where they access the DB.
3. **Database Support**:
   - SQLite via `aiosqlite` (`sqlite://...`).
   - PostgreSQL via `asyncpg` (`postgres://...`).
4. **Aerich Migrations**:
   - Replace Alembic with Aerich (`aerich init`, `aerich init-db`, `migrations/`).
   - Remove `mealie/alembic/`.
   - Move old Alembic migration scripts to `tests/data/alembic_versions` so existing migration unit tests (`test_alembic.py`, `test_recipe_image_backfill.py`, `test_structured_recipe_times_migration.py`) pass without altering assertions.
5. **Pydantic Schemas Unchanged**:
   - Remove SQLAlchemy imports (`LoaderOption`, `joinedload`, `selectinload`, etc.) from `mealie/schema`.
   - Preserve all fields, aliases, validators, and serialization logic so API responses remain 100% compatible.
6. **Synchronous Test Compatibility**:
   - Tests in `tests/` frequently call `unique_user.repos.recipes.create(...)` in synchronous test functions.
   - We will provide a synchronous execution wrapper/proxy for `AllRepositories` in `tests/fixtures/` (leveraging Starlette `TestClient.portal` / event loop) so tests do not need their thousands of assertions rewritten, while the backend itself remains purely async.
7. **Backups & Restores**:
   - Replace `AlchemyExporter` with a Tortoise ORM exporter/restorer that exports and imports table data to/from JSON while maintaining foreign keys and sequence integrity.

---

## 3. Phased Implementation Plan

### Phase 1: Dependencies & Aerich Setup
1. Update `pyproject.toml`:
   - Add `tortoise-orm>=1.1.8`, `aerich>=0.10.1`, `aiosqlite>=0.22.1`, `asyncpg>=0.31.0`.
   - Remove `SQLAlchemy`, `alembic`, `psycopg2-binary`.
   - Run `uv sync`.
2. Move `mealie/alembic/versions` to `tests/data/alembic_versions`.
   - Update `tests/utils/alembic_reader.py` to point to `tests/data/alembic_versions`.
   - Remove `mealie/alembic/`.

### Phase 2: Tortoise ORM Models (`mealie/db/models/`)
1. **Base Model** (`mealie/db/models/_model_base.py`):
   - Define `TortoiseBase(models.Model)` with:
     - `id = fields.UUIDField(pk=True, default=uuid4)` (or IntField for models with integer primary key).
     - `created_at = fields.DatetimeField(null=True, auto_now_add=True, index=True)`.
     - `update_at = fields.DatetimeField(null=True, auto_now=True)`.
     - `normalize(val)` text normalization helper.
     - `update(**kwargs)` in-memory update method.
2. **Model Implementations**:
   - **Recipe models** (`mealie/db/models/recipe/`):
     - `RecipeModel`: UUID id, slug, group, user, rating, timestamps, yield, times, normalized columns.
     - Related models: `Nutrition`, `RecipeSettings`, `RecipeAsset`, `Note`, `RecipeComment`, `RecipeTimelineEvent`, `RecipeShareTokenModel`, `ApiExtras`.
     - Ingredients & instructions: `RecipeIngredientModel`, `RecipeInstruction`, `RecipeIngredientSubstitutionModel`, `RecipeIngredientRefLink`, `RecipeNoteRefLink`.
     - Categorization & tools: `Category`, `Tag`, `Tool`, `MultiPurposeLabel`, and many-to-many through tables (`recipes_to_categories`, `recipes_to_tags`, `recipes_to_tools`).
     - Food & unit entities: `IngredientFoodModel`, `IngredientFoodAliasModel`, `IngredientFoodSubstitutionModel`, `IngredientUnitModel`, `IngredientUnitAliasModel`.
   - **Household models** (`mealie/db/models/household/`):
     - `Household`, `HouseholdPreferences`.
     - `CookBook` with M2M to categories, tags, tools.
     - `GroupMealPlan`, `GroupMealPlanRules`.
     - `ShoppingList`, `ShoppingListItem`, `ShoppingListMultiPurposeLabel`, `ShoppingListRecipeReference`, `ShoppingListItemRecipeReference`.
     - `HouseholdToRecipe` (tracking household `last_made` timestamp).
     - `GroupEventsNotifier`, `GroupEventsNotifierOptions`, `RecipeAction`, `WebhookURL`.
   - **Group models** (`mealie/db/models/group/`):
     - `Group`, `GroupPreferences`, `GroupDataExport`, `GroupReport`, `ReportEntry`, `AiProvider`, `AiProviderSettings`, `AiProviderHeader`, `AiProviderParam`.
   - **User models** (`mealie/db/models/users/`):
     - `User`, `UserToRecipe` (ratings & favorites), `LongLiveToken`, `PasswordResetModel`.
   - **Server models** (`mealie/db/models/server/`):
     - `ServerTask`.

### Phase 3: Database Lifecycle & Configuration (`mealie/db/` and `mealie/core/`)
1. **DB Configuration** (`mealie/core/settings/db_providers.py`, `mealie/db/db_setup.py`):
   - Generate Tortoise DB config dictionary `TORTOISE_ORM`.
   - Functions `init_tortoise()`, `close_tortoise()`.
   - FastAPI lifespan integration in `mealie/app.py`.
2. **DB Initialization & Seeding** (`mealie/db/init_db.py`):
   - `async def init_db()`: Generate schemas, ensure default admin user, default group, and default household exist.
   - Replace Alembic commands with Aerich migration runner / schema generator.

### Phase 4: Repositories & Query Layer (`mealie/repos/`)
1. **Generic Repository** (`mealie/repos/repository_generic.py`):
   - Rewrite `RepositoryGeneric` using Tortoise ORM querysets:
     - `async def get_all(...)`
     - `async def multi_query(...)`
     - `async def get_one(...)`
     - `async def create(...)`
     - `async def create_many(...)`
     - `async def update(...)`
     - `async def update_many(...)`
     - `async def patch(...)`
     - `async def delete(...)`
     - `async def delete_many(...)`
     - `async def count_all(...)`
     - `async def page_all(...)`: Tortoise query builder with pagination, `order_by`, search filtering, and `prefetch_related`.
   - `GroupRepositoryGeneric`, `HouseholdRepositoryGeneric`.
2. **Domain Repositories**:
   - `RepositoryRecipes`: Async CRUD, slug generation, user rating aggregation via `UserToRecipe`, recipe suggestions.
   - `RepositoryUsers`: User CRUD, password management, tokens.
   - `RepositoryUserRatings`: Async favorites & ratings queries.
   - `RepositoryGroup`, `RepositoryHousehold`, `RepositoryCookbooks`, `RepositoryFoods`, `RepositoryUnits`, `RepositoryMealPlans`, `RepositoryMealPlanRules`, `RepositoryAiProvider`.
3. **Repository Factory** (`mealie/repos/repository_factory.py`, `all_repositories.py`):
   - `AllRepositories`: Instantiates all repositories without requiring a synchronous SQLAlchemy Session.

### Phase 5: Query Filter & Search Services (`mealie/services/`)
1. **Query Filter Builder** (`mealie/services/query_filter/builder.py`):
   - Convert parsed filter conditions into Tortoise ORM `Q` objects and `Subquery` expressions for relational operators (`IN`, `CONTAINS ALL`, `IS NULL`, comparisons, etc.).
2. **Search Filter** (`mealie/schema/response/query_search.py`):
   - Implement tokenized and fuzzy recipe search using Tortoise ORM filters.

### Phase 6: Services, Routes & Auth
1. **Services** (`mealie/services/`):
   - `backups_v2`: Rewrite database export/restore to dump/restore Tortoise model rows as JSON.
   - `recipe_service.py`, `shopping_lists.py`, `ingredient_parser.py`, `password_reset_service.py`: Make DB-accessing methods async.
   - `scheduler/tasks/`: Convert task handlers to `async def`.
2. **Routes & Controllers** (`mealie/routes/`):
   - Update `_BaseController` and controller methods to async.
   - Route handlers `await` repository and service methods.
3. **Security & Dependencies** (`mealie/core/`):
   - `dependencies.py`: Update `get_current_user`, `try_get_current_user` to async Tortoise queries.
   - `mealie/core/security/providers/`: Credentials and auth providers use async user queries.

### Phase 7: Schemas Cleanup (`mealie/schema/`)
1. Remove all SQLAlchemy imports across `mealie/schema/`.
2. Replace `loader_options` with relationship lists / no-ops.

### Phase 8: Tests & Verification
1. `tests/conftest.py`:
   - Initialize Tortoise ORM in `scope="session"`.
   - Update `api_client` fixture to run Tortoise lifespan.
2. `tests/fixtures/`:
   - Provide a synchronous proxy on `AllRepositories` (using `api_client.portal`) so sync test functions calling `user.repos.recipes.create(...)` continue working without modification.
3. Run tests:
   - `uv run pytest -n 4 --dist loadfile`.
   - Validate that all backend tests pass.

---

## 4. Verification & Validation Steps
1. **Clean Imports**: Run `python3 -c "import os, sys; ..."` checking that zero files in `mealie/` import `sqlalchemy` or `alembic`.
2. **Test Suite**: Run `uv run pytest -n 4 --dist loadfile` and ensure all tests pass.
3. **PostgreSQL & SQLite Compatibility**: Verify connection handling and schema generation for both SQLite and PostgreSQL.
```

Please let me know if this strategy looks good to you or if you'd like any adjustments before we proceed to implementation.
---
