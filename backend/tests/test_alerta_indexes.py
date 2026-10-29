import unittest
from unittest.mock import AsyncMock

from app.database.alerta_indexes import (
    ensure_alerta_indexes, INVENTORY_INDEX, LEGACY_INDEX,
)


class AlertaIndexTests(unittest.IsolatedAsyncioTestCase):
    async def test_upgrade_preserves_keys_and_excludes_sensor_null_inventory(self):
        collection = AsyncMock()
        collection.index_information.return_value = {LEGACY_INDEX: {}}
        await ensure_alerta_indexes(collection)
        keys = collection.create_index.call_args.args[0]
        options = collection.create_index.call_args.kwargs
        self.assertEqual([key for key, _ in keys], [
            "id_inventario", "id_producto", "id_detalle_inventario", "tipo_alerta"])
        self.assertTrue(options["unique"])
        self.assertEqual(options["name"], INVENTORY_INDEX)
        self.assertEqual(options["partialFilterExpression"], {
            "estado": {"$in": ["ACTIVA", "VISTA"]},
            "id_inventario": {"$type": "string"},
        })
        collection.drop_index.assert_awaited_once_with(LEGACY_INDEX)
        self.assertEqual([call[0] for call in collection.mock_calls], [
            "create_index", "index_information", "drop_index"])

    async def test_already_upgraded_does_not_drop_indexes(self):
        collection = AsyncMock()
        collection.index_information.return_value = {INVENTORY_INDEX: {}}
        await ensure_alerta_indexes(collection)
        collection.drop_index.assert_not_awaited()

    async def test_creation_failure_keeps_legacy_constraint(self):
        collection = AsyncMock()
        collection.create_index.side_effect = RuntimeError("index build failed")
        with self.assertRaises(RuntimeError):
            await ensure_alerta_indexes(collection)
        collection.drop_index.assert_not_awaited()
