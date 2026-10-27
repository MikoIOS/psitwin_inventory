"""Opt-in writes only to a newly named temporary test DB, never production DB."""
import asyncio
import copy
import os
import re
import sys
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient
import pytest

from tests.test_saiki_http import http_app, post


@pytest.mark.skipif(os.environ.get("SAIKI_MONGO_TEST_WRITES_AUTHORIZED") != "1", reason="Explicit authorization for temporary MongoDB test database required")
def test_real_mongodb_concurrent_companies_on_temporary_database(http_app, monkeypatch):
    app, data = http_app
    name = "saiki_test_" + uuid4().hex
    assert re.fullmatch(r"saiki_test_[a-f0-9]{32}", name)
    async def scenario():
        client = AsyncIOMotorClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=2000)
        database = client[name]
        created = False
        try:
            await client.admin.command("ping")
            assert name not in await client.list_database_names(), "Never overwrite an existing database"
            for collection, rows in data.items():
                if rows:
                    await database[collection].insert_many(copy.deepcopy(rows))
                    created = True
            for module_name, module in list(sys.modules.items()):
                if module_name.startswith("app.repositories.") and hasattr(module, "get_database"):
                    monkeypatch.setattr(module, "get_database", lambda: database)
            for message, tool in (("¿Cómo está mi inventario?", "get_warehouse_status"), ("¿Tengo alertas?", "get_active_alerts"), ("¿Qué me recomiendas reponer?", "get_recommendations"), ("¿Qué movimientos recientes tengo?", "get_recent_movements")):
                a, b = await asyncio.gather(post(app, message, "A"), post(app, message, "B"))
                assert a.status_code == b.status_code == 200
                for response, company in ((a, "A"), (b, "B")):
                    result = response.json()["data"][tool]
                    rows = result["inventarios"] if tool == "get_warehouse_status" else result
                    assert {row["id_inventario"] for row in rows} == {company + "-inventory"}
        finally:
            # Only this newly generated, validated name is ever eligible for cleanup.
            assert re.fullmatch(r"saiki_test_[a-f0-9]{32}", name)
            if created:
                await client.drop_database(name)
            client.close()
    asyncio.run(scenario())
