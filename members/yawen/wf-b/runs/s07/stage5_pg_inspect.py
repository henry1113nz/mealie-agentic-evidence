import asyncio
from tortoise import Tortoise
from mealie.db.tortoise_setup import tortoise_config

URL = "postgres://stage4:stage4_local_test@127.0.0.1:15432/stage4_test"

async def main():
    await Tortoise.init(config=tortoise_config(URL))
    db = Tortoise.get_connection("default")
    identity = await db.execute_query_dict(
        "SELECT current_database() AS database, current_user AS role, "
        "inet_server_addr() AS server_addr, inet_server_port() AS server_port"
    )
    tables = await db.execute_query_dict(
        "SELECT schemaname, tablename FROM pg_tables "
        "WHERE schemaname NOT IN ('pg_catalog', 'information_schema') "
        "ORDER BY schemaname, tablename"
    )
    counts = await db.execute_query_dict(
        "SELECT schemaname, relname AS table_name, n_live_tup AS estimated_rows "
        "FROM pg_stat_user_tables ORDER BY schemaname, relname"
    )
    print("IDENTITY", identity)
    print("TABLES", tables)
    print("ROW_ESTIMATES", counts)
    await Tortoise.close_connections()

asyncio.run(main())
