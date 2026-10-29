import unittest
from unittest.mock import AsyncMock
from app.database.inventario_indexes import ensure_inventory_location_indexes


class InventarioIndexTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_constraint_precedes_removal_of_old_level_blind_index(self):
        collection = AsyncMock()
        collection.index_information.return_value = {"uq_detalle_inventario_ubicacion": {}}
        await ensure_inventory_location_indexes(collection)
        self.assertEqual(collection.create_index.call_args.args[0][-1], ("id_nivel", 1))
        self.assertTrue(collection.create_index.call_args.kwargs["unique"])
        self.assertEqual([call[0] for call in collection.mock_calls], [
            "create_index", "index_information", "drop_index"])

    async def test_index_failure_does_not_remove_previous_constraint(self):
        collection = AsyncMock()
        collection.create_index.side_effect = RuntimeError("build failed")
        with self.assertRaises(RuntimeError):
            await ensure_inventory_location_indexes(collection)
        collection.drop_index.assert_not_awaited()

    async def test_second_start_does_not_drop_unrelated_indexes(self):
        collection = AsyncMock()
        collection.index_information.return_value = {"uq_detalle_inventario_ubicacion_v3": {}}
        await ensure_inventory_location_indexes(collection)
        collection.drop_index.assert_not_awaited()
