import asyncio
import shutil
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import asyncpg
from aerich import Command
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from mealie.db.tortoise_models import (
    AIProvider,
    AIProviderSettings,
    Category,
    CookBook,
    Group,
    GroupMealPlanRules,
    Household,
    HouseholdToRecipe,
    IngredientFood,
    MultiPurposeLabel,
    Recipe,
    ShoppingList,
    ShoppingListItem,
    ShoppingListItemRecipeReference,
    ShoppingListMultiPurposeLabel,
    ShoppingListRecipeReference,
    Tag,
    Tool,
    User,
    UserToRecipe,
)
from mealie.db.tortoise_setup import tortoise_config

URL = "postgres://stage4:stage4_local_test@127.0.0.1:15432/stage4_test"
SCHEMA = "stage5_acceptance_20261015"
ROOT = Path.cwd()
MIGDIR = ROOT / "mealie/db/aerich_migrations/models"
STAGE4 = MIGDIR / "1_stage4_recipe_constraints.py"
STAGE5 = MIGDIR / "2_stage5_cross_domain_foreign_keys.py"

KEYLESS = {
    "group_to_categories": ("group_id", "category_id"),
    "plan_rules_to_categories": ("group_plan_rule_id", "category_id"),
    "recipes_to_categories": ("recipe_id", "category_id"),
    "cookbooks_to_categories": ("cookbook_id", "category_id"),
    "recipes_to_tags": ("recipe_id", "tag_id"),
    "plan_rules_to_tags": ("plan_rule_id", "tag_id"),
    "cookbooks_to_tags": ("cookbook_id", "tag_id"),
    "households_to_tools": ("household_id", "tool_id"),
    "recipes_to_tools": ("recipe_id", "tool_id"),
    "cookbooks_to_tools": ("cookbook_id", "tool_id"),
    "plan_rules_to_households": ("group_plan_rule_id", "household_id"),
    "households_to_ingredient_foods": ("household_id", "food_id"),
}
KEYLESS_FKS = {
    "group_to_categories": {"group_id": "groups", "category_id": "categories"},
    "plan_rules_to_categories": {"group_plan_rule_id": "group_meal_plan_rules", "category_id": "categories"},
    "recipes_to_categories": {"recipe_id": "recipes", "category_id": "categories"},
    "cookbooks_to_categories": {"cookbook_id": "cookbooks", "category_id": "categories"},
    "recipes_to_tags": {"recipe_id": "recipes", "tag_id": "tags"},
    "plan_rules_to_tags": {"plan_rule_id": "group_meal_plan_rules", "tag_id": "tags"},
    "cookbooks_to_tags": {"cookbook_id": "cookbooks", "tag_id": "tags"},
    "households_to_tools": {"household_id": "households", "tool_id": "tools"},
    "recipes_to_tools": {"recipe_id": "recipes", "tool_id": "tools"},
    "cookbooks_to_tools": {"cookbook_id": "cookbooks", "tool_id": "tools"},
    "plan_rules_to_households": {"group_plan_rule_id": "group_meal_plan_rules", "household_id": "households"},
    "households_to_ingredient_foods": {"household_id": "households", "food_id": "ingredient_foods"},
}
COMPOSITES = {
    "households_to_recipes": ("id", "household_id", "recipe_id"),
    "shopping_list_item_recipe_reference": ("id", "shopping_list_item_id"),
    "shopping_list_recipe_reference": ("id", "shopping_list_id"),
    "shopping_lists_multi_purpose_labels": ("id", "shopping_list_id", "label_id"),
    "users_to_recipes": ("id", "user_id", "recipe_id"),
}
CROSS_FKS = {
    "ai_provider_settings": {
        "default_provider_id": "ai_providers",
        "audio_provider_id": "ai_providers",
        "image_provider_id": "ai_providers",
    },
    "users": {"owned_recipes_id": "recipes"},
}

async def must_fail(awaitable):
    try:
        await awaitable
    except IntegrityError:
        return
    raise AssertionError("expected a database integrity violation")

async def table_rows(db, table):
    key = "id" if table in CROSS_FKS or table == "households_to_ingredient_foods" else "row_id"
    return await db.execute_query_dict(f'SELECT * FROM "{table}" ORDER BY "{key}"')

async def indexes(db, table):
    return await db.execute_query_dict(
        "SELECT indexname, indexdef FROM pg_indexes "
        "WHERE schemaname=current_schema() AND tablename=$1 ORDER BY indexname", [table]
    )

async def unique_tuples(db, table):
    rows = await db.execute_query_dict("""
        SELECT array_agg(a.attname ORDER BY k.ord) AS columns
        FROM pg_index i CROSS JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum
        WHERE i.indrelid=to_regclass($1) AND i.indisunique AND NOT i.indisprimary
          AND k.ord <= i.indnkeyatts GROUP BY i.indexrelid
    """, [table])
    return {tuple(row["columns"]) for row in rows}

async def index_states(db):
    return await db.execute_query_dict("""
        SELECT t.relname AS table_name, i.relname AS index_name, x.indisvalid, x.indisready,
               pg_get_indexdef(x.indexrelid) AS definition
        FROM pg_index x JOIN pg_class t ON t.oid=x.indrelid
        JOIN pg_class i ON i.oid=x.indexrelid JOIN pg_namespace n ON n.oid=t.relnamespace
        WHERE n.nspname=current_schema() ORDER BY t.relname,i.relname
    """)

async def foreign_keys(db, table):
    rows = await db.execute_query_dict("""
        SELECT c.conname, pg_get_constraintdef(c.oid) AS definition, c.confdeltype AS delete_type
        FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
        WHERE c.contype='f' AND t.relname=$1 AND c.connamespace=current_schema()::regnamespace
        ORDER BY c.conname
    """, [table])
    return {row["conname"]: row for row in rows}

async def main():
    # Identity and database contents were checked separately before this script.
    # Use a new schema to ensure this bounded run leaves the database empty.
    admin = await asyncpg.connect(
        host="127.0.0.1", port=15432, user="stage4", password="stage4_local_test", database="stage4_test"
    )
    existing = await admin.fetchval("SELECT 1 FROM pg_namespace WHERE nspname=$1", SCHEMA)
    assert existing is None, f"refusing to reuse existing schema {SCHEMA}"
    await admin.execute(f'CREATE SCHEMA "{SCHEMA}" AUTHORIZATION stage4')
    await admin.close()

    config = tortoise_config(URL)
    config["connections"]["default"]["credentials"]["server_settings"] = {"search_path": f"{SCHEMA},public"}
    with TemporaryDirectory(prefix="mealie-stage5-pg-migrations-") as tmp:
        location = Path(tmp) / "migrations"
        command = Command(tortoise_config=config, app="models", location=str(location))
        try:
            await command.init_db(safe=True)
            await command.init()
            db = Tortoise.get_connection("default")
            assert await db.execute_query_dict("SELECT current_schema() AS schema") == [{"schema": SCHEMA}]

            group = await Group.create(name="Stage 5 PG")
            household = await Household.create(name="home", group=group)
            household2 = await Household.create(name="other home", group=group)
            user = await User.create(group=group, full_name="Owner")
            user2 = await User.create(group=group, full_name="Other")
            recipe = await Recipe.create(group=group, name="recipe", name_normalized="recipe", user=user)
            recipe2 = await Recipe.create(group=group, name="other recipe", name_normalized="other recipe", user=user2)
            settings = await AIProviderSettings.create(group=group)
            provider = await AIProvider.create(settings=settings, name="provider", api_key="key", model="model")
            settings.default_provider = provider
            settings.audio_provider = provider
            settings.image_provider = provider
            await settings.save()
            user.owned_recipes = recipe
            await user.save()
            shopping_list = await ShoppingList.create(group=group, user=user, name="list")
            shopping_list2 = await ShoppingList.create(group=group, user=user2, name="other list")
            item = await ShoppingListItem.create(shopping_list=shopping_list, position=0)
            item2 = await ShoppingListItem.create(shopping_list=shopping_list2, position=0)
            label = await MultiPurposeLabel.create(group=group, name="label")
            category = await Category.create(group=group, name="category", slug="category")
            tag = await Tag.create(group=group, name="tag", slug="tag")
            tool = await Tool.create(group=group, name="tool", slug="tool")
            cookbook = await CookBook.create(group=group, household=household, name="cookbook", slug="cookbook")
            rule = await GroupMealPlanRules.create(group=group, household=household)
            food = await IngredientFood.create(group=group, name="food")

            vals = {
                "group_to_categories": ("group_id", group.id, "category_id", category.id),
                "plan_rules_to_categories": ("group_plan_rule_id", rule.id, "category_id", category.id),
                "recipes_to_categories": ("recipe_id", recipe.id, "category_id", category.id),
                "cookbooks_to_categories": ("cookbook_id", cookbook.id, "category_id", category.id),
                "recipes_to_tags": ("recipe_id", recipe.id, "tag_id", tag.id),
                "plan_rules_to_tags": ("plan_rule_id", rule.id, "tag_id", tag.id),
                "cookbooks_to_tags": ("cookbook_id", cookbook.id, "tag_id", tag.id),
                "households_to_tools": ("household_id", household.id, "tool_id", tool.id),
                "recipes_to_tools": ("recipe_id", recipe.id, "tool_id", tool.id),
                "cookbooks_to_tools": ("cookbook_id", cookbook.id, "tool_id", tool.id),
                "plan_rules_to_households": ("group_plan_rule_id", rule.id, "household_id", household.id),
                "households_to_ingredient_foods": ("household_id", household.id, "food_id", food.id),
            }
            for table, (left, right) in KEYLESS.items():
                await db.execute_query(f'INSERT INTO "{table}" ("{left}", "{right}") VALUES (NULL, NULL)')
                c1, v1, c2, v2 = vals[table]
                await db.execute_query(f'INSERT INTO "{table}" ("{c1}", "{c2}") VALUES ($1, $2)', [v1, v2])
                await db.execute_query(f'INSERT INTO "{table}" ("{left}", "{right}") VALUES (NULL, NULL)')

            sid = uuid.uuid4()
            hr = [
                await HouseholdToRecipe.create(id=sid, household=household, recipe=recipe, last_made=None),
                await HouseholdToRecipe.create(id=sid, household=household2, recipe=recipe2, last_made=None),
            ]
            await must_fail(HouseholdToRecipe.create(id=sid, household=household, recipe=recipe))
            item_refs = [
                await ShoppingListItemRecipeReference.create(id=sid, shopping_list_item=item, recipe=recipe, recipe_quantity=1),
                await ShoppingListItemRecipeReference.create(id=sid, shopping_list_item=item2, recipe=recipe2, recipe_quantity=2),
            ]
            list_refs = [
                await ShoppingListRecipeReference.create(id=sid, shopping_list=shopping_list, recipe=recipe, recipe_quantity=1),
                await ShoppingListRecipeReference.create(id=sid, shopping_list=shopping_list2, recipe=recipe2, recipe_quantity=2),
            ]
            label_links = [
                await ShoppingListMultiPurposeLabel.create(id=sid, shopping_list=shopping_list, label=label),
                await ShoppingListMultiPurposeLabel.create(id=sid, shopping_list=shopping_list2, label=label),
            ]
            ratings = [
                await UserToRecipe.create(id=sid, user=user, recipe=recipe, is_favorite=True),
                await UserToRecipe.create(id=sid, user=user2, recipe=recipe2, is_favorite=False),
            ]
            await must_fail(ShoppingListItemRecipeReference.create(id=sid, shopping_list_item=item, recipe_quantity=3))
            await must_fail(ShoppingListRecipeReference.create(id=sid, shopping_list=shopping_list, recipe_quantity=3))
            await must_fail(ShoppingListMultiPurposeLabel.create(id=uuid.uuid4(), shopping_list=shopping_list, label=label))
            await must_fail(UserToRecipe.create(id=sid, user=user, recipe=recipe, is_favorite=False))
            assert item_refs[0].recipe_scale == 1 and label_links[0].position == 0 and ratings[0].rating is None

            # Run the actual ordered Aerich migrations against a populated schema.
            pre_migration_fks = {t: await foreign_keys(db, t) for t in CROSS_FKS}
            assert not any(k.startswith("fk_ai_provider_settings_") or k == "fk_users_owned_recipes_id_recipes" for constraints in pre_migration_fks.values() for k in constraints)
            index_before = {t: await indexes(db,t) for t in CROSS_FKS}
            watched = [*CROSS_FKS, *COMPOSITES, *KEYLESS]
            data_before = {t: await table_rows(db,t) for t in watched}
            shutil.copy2(STAGE4, location / "models" / STAGE4.name)
            shutil.copy2(STAGE5, location / "models" / STAGE5.name)
            assert await command.upgrade(run_in_transaction=False) == [STAGE4.name, STAGE5.name]
            assert {t: await table_rows(db,t) for t in watched} == data_before
            assert {t: await indexes(db,t) for t in CROSS_FKS} == index_before

            states_after_ordered_upgrade = await index_states(db)
            assert states_after_ordered_upgrade
            assert all(row["indisvalid"] and row["indisready"] for row in states_after_ordered_upgrade)
            trigram = [row for row in states_after_ordered_upgrade if row["index_name"].endswith("_gin")]
            assert len(trigram) == 12, [row["index_name"] for row in trigram]
            stage5_index_state = states_after_ordered_upgrade
            nullable_rows = await db.execute_query_dict("""
                SELECT table_name,column_name,is_nullable FROM information_schema.columns
                WHERE table_schema=current_schema() AND
                  ((table_name='ai_provider_settings' AND column_name IN ('default_provider_id','audio_provider_id','image_provider_id'))
                   OR (table_name='users' AND column_name='owned_recipes_id'))
                ORDER BY table_name,column_name
            """)
            assert len(nullable_rows) == 4 and all(row["is_nullable"] == "YES" for row in nullable_rows)

            fk_expect = {
                "ai_provider_settings": {
                    "fk_ai_provider_settings_default_provider_id_ai_providers": "FOREIGN KEY (default_provider_id) REFERENCES ai_providers(id)",
                    "fk_ai_provider_settings_audio_provider_id_ai_providers": "FOREIGN KEY (audio_provider_id) REFERENCES ai_providers(id)",
                    "fk_ai_provider_settings_image_provider_id_ai_providers": "FOREIGN KEY (image_provider_id) REFERENCES ai_providers(id)",
                },
                "users": {"fk_users_owned_recipes_id_recipes": "FOREIGN KEY (owned_recipes_id) REFERENCES recipes(id)"},
            }
            for table, constraints in fk_expect.items():
                observed = await foreign_keys(db,table)
                for name, ddl in constraints.items():
                    assert ddl in observed[name]["definition"], (name,observed[name])
                    assert observed[name]["delete_type"] in ("a", b"a"), (name,observed[name])
            await settings.fetch_related("default_provider","audio_provider","image_provider")
            await user.fetch_related("owned_recipes")
            assert settings.default_provider.id == provider.id and settings.audio_provider.id == provider.id and settings.image_provider.id == provider.id
            assert user.owned_recipes.id == recipe.id
            for table, columns in CROSS_FKS.items():
                source_id = settings.id if table == "ai_provider_settings" else user.id
                for column in columns:
                    await must_fail(db.execute_query(f'UPDATE "{table}" SET "{column}"=$1 WHERE id=$2',[uuid.uuid4(),source_id]))
            settings.default_provider = settings.audio_provider = settings.image_provider = None
            await settings.save()
            user.owned_recipes = None
            await user.save()
            await settings.fetch_related("default_provider","audio_provider","image_provider")
            await user.fetch_related("owned_recipes")
            assert settings.default_provider is None and settings.audio_provider is None and settings.image_provider is None and user.owned_recipes is None

            for table,pair in KEYLESS.items():
                surrogate = "id" if table == "households_to_ingredient_foods" else "row_id"
                pk = await db.execute_query_dict("""
                    SELECT array_agg(a.attname ORDER BY k.ord) AS cols FROM pg_constraint c
                    CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY k(attnum,ord)
                    JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.attnum
                    JOIN pg_class t ON t.oid=c.conrelid
                    WHERE c.contype='p' AND t.relname=$1 GROUP BY c.oid
                """,[table])
                assert tuple(pk[0]["cols"]) == (surrogate,)
                assert await unique_tuples(db,table) == {pair}
                observed = await foreign_keys(db,table)
                for column,target in KEYLESS_FKS[table].items():
                    assert any(f"FOREIGN KEY ({column}) REFERENCES {target}(id)" in row["definition"] and row["delete_type"] in ("a", b"a") for row in observed.values()),(table,column,observed)
                    await must_fail(db.execute_query(f'INSERT INTO "{table}" ("{column}") VALUES ($1)',[uuid.uuid4()]))
                nulls = await db.execute_query_dict(f'SELECT "{surrogate}" FROM "{table}" WHERE "{pair[0]}" IS NULL AND "{pair[1]}" IS NULL ORDER BY "{surrogate}"')
                assert len(nulls)==2
                k1,k2=nulls[0][surrogate],nulls[1][surrogate]
                moved=max(k1,k2)+1000
                await db.execute_query(f'UPDATE "{table}" SET "{surrogate}"=$1 WHERE "{surrogate}"=$2',[moved,k1])
                assert await db.execute_query_dict(f'SELECT "{surrogate}" FROM "{table}" WHERE "{surrogate}"=$1',[moved])
                assert await db.execute_query_dict(f'SELECT "{surrogate}" FROM "{table}" WHERE "{surrogate}"=$1',[k2])
                await db.execute_query(f'DELETE FROM "{table}" WHERE "{surrogate}"=$1',[moved])
                assert not await db.execute_query_dict(f'SELECT "{surrogate}" FROM "{table}" WHERE "{surrogate}"=$1',[moved])
                assert len(await db.execute_query_dict(f'SELECT 1 FROM "{table}" WHERE "{pair[0]}" IS NULL AND "{pair[1]}" IS NULL'))==1
                c1,v1,c2,v2=vals[table]
                await must_fail(db.execute_query(f'INSERT INTO "{table}" ("{c1}","{c2}") VALUES ($1,$2)',[v1,v2]))

            for table,pair in COMPOSITES.items():
                expected={pair}
                alt={"households_to_recipes":("household_id","recipe_id"),"shopping_lists_multi_purpose_labels":("shopping_list_id","label_id"),"users_to_recipes":("user_id","recipe_id")}.get(table)
                if alt: expected.add(alt)
                assert await unique_tuples(db,table)==expected,(table,await unique_tuples(db,table))
            for pair_rows in (hr,item_refs,list_refs,label_links,ratings):
                assert pair_rows[0].row_id != pair_rows[1].row_id
                pair_rows[0].id=sid
                await pair_rows[0].save()
                await pair_rows[0].delete()
                assert await pair_rows[1].__class__.filter(pk=pair_rows[1].row_id).exists()

            data_before_downgrade={t:await table_rows(db,t) for t in watched}
            assert await command.downgrade(version=-1,delete=False)==[STAGE5.name]
            for table in CROSS_FKS:
                observed=await foreign_keys(db,table)
                assert not any(k.startswith("fk_ai_provider_settings_") or k=="fk_users_owned_recipes_id_recipes" for k in observed)
            assert {t:await indexes(db,t) for t in CROSS_FKS}==index_before
            assert await index_states(db)==stage5_index_state
            assert {t:await table_rows(db,t) for t in watched}==data_before_downgrade
            assert await command.downgrade(version=-1,delete=False)==[STAGE4.name]
            assert {t:await table_rows(db,t) for t in watched}==data_before_downgrade
            remaining_indexes=await index_states(db)
            assert all(row["indisvalid"] and row["indisready"] for row in remaining_indexes)
            assert not any(row["index_name"].endswith("_gin") for row in remaining_indexes)
            print("POSTGRES_STAGE5_ACCEPTANCE=PASS")
            print("ordered_migrations",[STAGE4.name,STAGE5.name])
            print("four_cross_fks_relation_loading nullable/write/rejection PASS")
            print("five_composite_key_tuples PASS")
            print("twelve_keyless_fk_unique_NULL_surrogate_mutations PASS")
            print("populated_upgrade_downgrade_data_indexes PASS")
        finally:
            await command.aclose()
            await Tortoise.close_connections()
            cleanup = await asyncpg.connect(
                host="127.0.0.1", port=15432, user="stage4", password="stage4_local_test", database="stage4_test"
            )
            await cleanup.execute(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE')
            await cleanup.close()

asyncio.run(main())
