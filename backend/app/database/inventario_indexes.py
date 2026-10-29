"""Allow independent product balances on different levels of the same rack."""


async def ensure_inventory_location_indexes(collection):
    await collection.create_index(
        [("id_inventario", 1), ("id_producto", 1), ("id_rack", 1), ("id_nivel", 1)],
        unique=True, name="uq_detalle_inventario_ubicacion_v3")
    indexes = await collection.index_information()
    if "uq_detalle_inventario_ubicacion" in indexes:
        await collection.drop_index("uq_detalle_inventario_ubicacion")
