import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from tortoise.exceptions import IntegrityError

from mealie.db.tortoise_models import Group, Household, User
from mealie.db.tortoise_setup import tortoise_close, tortoise_init


async def expect_integrity_error(awaitable, label: str) -> None:
    try:
        await awaitable
    except IntegrityError:
        print(f"constraint {label}: PASS (IntegrityError)")
    else:
        raise AssertionError(f"constraint {label}: expected IntegrityError")


async def main() -> None:
    with TemporaryDirectory(prefix="mealie-stage3-") as temp_dir:
        database_url = f"sqlite://{Path(temp_dir) / 'acceptance.sqlite3'}"
        await tortoise_init(database_url, create_schema=True)
        try:
            first_group = await Group.create(name="Stage 3 Group", slug="stage-3-group")
            second_group = await Group.create(name="Second Group", slug="second-group")
            household = await Household.create(name="Home", slug="home", group=first_group)
            same_name_other_group = await Household.create(name="Home", slug="home", group=second_group)
            user = await User.create(
                username="stage3-user", email="stage3@example.invalid", full_name="Stage Three",
                group=first_group, household=household,
            )

            loaded = await User.get(id=user.id).select_related("group", "household")
            assert loaded.group.name == "Stage 3 Group"
            assert loaded.household.name == "Home"
            assert await first_group.households.all().count() == 1
            assert await second_group.households.all().count() == 1
            assert same_name_other_group.group_id == second_group.id
            print("schema creation, CRUD, and group/household/user relations: PASS")

            await expect_integrity_error(
                Group.create(name="Duplicate group name", slug="stage-3-group"), "unique group slug"
            )
            await expect_integrity_error(
                Group.create(name="Stage 3 Group", slug="different-slug"), "unique group name"
            )
            await expect_integrity_error(
                Household.create(name="Home", slug="different", group=first_group),
                "household name unique within group",
            )
            await expect_integrity_error(
                Household.create(name="Different", slug="home", group=first_group),
                "household slug unique within group",
            )
            await expect_integrity_error(
                User.create(username="stage3-user", group=first_group), "unique username"
            )
            await expect_integrity_error(
                User.create(email="stage3@example.invalid", group=first_group), "unique email"
            )

        finally:
            await tortoise_close()


asyncio.run(main())
