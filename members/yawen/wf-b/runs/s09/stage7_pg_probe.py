import asyncio
from uuid import uuid4

import asyncpg
from pydantic import BaseModel, ConfigDict

from mealie.db.tortoise_models import Group, Recipe, Tag
from mealie.db.tortoise_setup import tortoise_config
from mealie.repos.tortoise_repository import AsyncRepository
from mealie.schema.response.pagination import OrderByNullPosition, OrderDirection, PaginationQuery
from mealie.services.query_filter.tortoise import TortoiseFilterCompiler
from mealie.db.tortoise_models import User
from mealie.services.query_filter.builder import NonFilterableValueError
from tortoise import Tortoise

URL = "postgres://stage4:stage4_local_test@127.0.0.1:15432/stage4_test"
SCHEMA = "stage7_probe_" + uuid4().hex

class RecipeResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: object
    name: str

async def main():
    admin = await asyncpg.connect(URL, timeout=8)
    schema_created = False
    tortoise_started = False
    try:
        await admin.execute(f'CREATE SCHEMA "{SCHEMA}"')
        schema_created = True
        config = tortoise_config(URL)
        config["connections"]["default"]["credentials"]["schema"] = SCHEMA
        await Tortoise.init(config=config)
        tortoise_started = True
        await Tortoise.generate_schemas(safe=True)
        current = await Tortoise.get_connection("default").execute_query_dict("SELECT current_schema() AS schema")
        assert current[0]["schema"] == SCHEMA, current

        group = await Group.create(id=uuid4(), name="stage7", slug="stage7")
        excluded = await Tag.create(id=uuid4(), group=group, name="excluded", slug="excluded")
        other = await Tag.create(id=uuid4(), group=group, name="other", slug="other")
        alpha = await Tag.create(id=uuid4(), group=group, name="alpha", slug="alpha")
        beta = await Tag.create(id=uuid4(), group=group, name="beta", slug="beta")

        async def recipe(name, tags=(), rating=1):
            row = await Recipe.create(id=uuid4(), group=group, name=name, name_normalized=name.casefold(), rating=rating)
            if tags:
                await row.tags.add(*tags)
            return row

        matched_excluded = await recipe("excluded-match", [excluded, other])
        only_other = await recipe("only-other", [other])
        empty_relation = await recipe("empty-relation")
        null_rating = await recipe("null-rating", rating=None)
        scalar_match = await recipe("scalar-match", rating=5)
        all_match = await recipe("all-match", [alpha, beta])
        alpha_only = await recipe("alpha-only", [alpha])
        repo = AsyncRepository(Recipe, RecipeResult, group_id=group.id)

        not_in = await repo.page_all(PaginationQuery(per_page=-1, query_filter='tags.name NOT IN ["excluded"]'))
        got = {row.id for row in not_in.items}
        assert matched_excluded.id not in got
        assert {only_other.id, empty_relation.id, null_rating.id, scalar_match.id, all_match.id, alpha_only.id} <= got
        scalar_not_in = await repo.page_all(PaginationQuery(per_page=-1, query_filter="rating NOT IN [5]"))
        assert null_rating.id not in {row.id for row in scalar_not_in.items}
        assert scalar_match.id not in {row.id for row in scalar_not_in.items}

        all_rows = await repo.page_all(PaginationQuery(per_page=-1, query_filter="tags.name CONTAINS ALL [alpha, beta]"))
        assert [row.id for row in all_rows.items] == [all_match.id]
        single = await repo.page_all(PaginationQuery(per_page=-1, query_filter="tags.name CONTAINS ALL [alpha]"))
        assert {row.id for row in single.items} == {all_match.id, alpha_only.id}
        empty = await repo.page_all(PaginationQuery(per_page=-1, query_filter="tags.name CONTAINS ALL []"))
        assert empty.items == []

        sort_group = await Group.create(id=uuid4(), name="sort", slug="sort")
        sort_tags = [await Tag.create(id=uuid4(), group=sort_group, name=n, slug=n) for n in ("a", "b", "c", "d")]
        ac = await Recipe.create(id=uuid4(), group=sort_group, name="ac", name_normalized="ac")
        await ac.tags.add(sort_tags[0], sort_tags[2])
        bd = await Recipe.create(id=uuid4(), group=sort_group, name="bd", name_normalized="bd")
        await bd.tags.add(sort_tags[1], sort_tags[3])
        untagged = await Recipe.create(id=uuid4(), group=sort_group, name="untagged", name_normalized="untagged")
        sort_repo = AsyncRepository(Recipe, RecipeResult, group_id=sort_group.id)
        asc = await sort_repo.page_all(PaginationQuery(per_page=-1, order_by="tags.name", order_direction=OrderDirection.asc, order_by_null_position=OrderByNullPosition.last))
        assert [r.id for r in asc.items] == [ac.id, bd.id, untagged.id]
        desc = await sort_repo.page_all(PaginationQuery(per_page=-1, order_by="tags.name", order_direction=OrderDirection.desc, order_by_null_position=OrderByNullPosition.last))
        assert [r.id for r in desc.items] == [bd.id, ac.id, untagged.id]
        first_null = await sort_repo.page_all(PaginationQuery(per_page=-1, order_by="tags.name", order_direction=OrderDirection.asc, order_by_null_position=OrderByNullPosition.first))
        assert first_null.items[0].id == untagged.id

        page_group = await Group.create(id=uuid4(), name="pages", slug="pages")
        page_tags = [await Tag.create(id=uuid4(), group=page_group, name=f"p{i}", slug=f"p{i}") for i in range(3)]
        page_ids = set()
        for i in range(5):
            row = await Recipe.create(id=uuid4(), group=page_group, name=f"page-{i}", name_normalized=f"page-{i}")
            await row.tags.add(*page_tags)
            page_ids.add(row.id)
        page = await AsyncRepository(Recipe, RecipeResult, group_id=page_group.id).page_all(PaginationQuery(page=1, per_page=5, order_by="tags.name"))
        assert page.total == 5 and len(page.items) == 5 and {r.id for r in page.items} == page_ids

        try:
            TortoiseFilterCompiler.compile('password = "secret"', User)
        except NonFilterableValueError:
            pass
        else:
            raise AssertionError("sensitive field unexpectedly filterable")
        print(f"POSTGRES_STAGE7_OK schema={SCHEMA} current_schema={current[0]['schema']} checks=related_not_in,scalar_null,contains_all,sort_min_max_nulls,pagination,filter_policy")
    finally:
        if tortoise_started:
            await Tortoise.close_connections()
        if schema_created:
            await admin.execute(f'DROP SCHEMA "{SCHEMA}" CASCADE')
            exists = await admin.fetchval("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname=$1)", SCHEMA)
            assert not exists, f"temporary schema {SCHEMA} still exists"
            print(f"POSTGRES_STAGE7_CLEANUP_OK schema={SCHEMA}")
        await admin.close()

asyncio.run(main())
