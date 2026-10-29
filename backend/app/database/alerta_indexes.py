"""Upgrade the inventory alert index without indexing sensor alerts."""

LEGACY_INDEX = "uq_alerta_activa_producto_ubicacion"
INVENTORY_INDEX = "uq_alerta_activa_producto_ubicacion_v2"


async def ensure_alerta_indexes(collection):
    # Install the replacement before removing the old constraint. A failed
    # creation leaves the existing uniqueness protection in place.
    await collection.create_index(
        [("id_inventario", 1), ("id_producto", 1),
         ("id_detalle_inventario", 1), ("tipo_alerta", 1)],
        unique=True,
        partialFilterExpression={
            "estado": {"$in": ["ACTIVA", "VISTA"]},
            "id_inventario": {"$type": "string"},
        },
        name=INVENTORY_INDEX,
    )
    indexes = await collection.index_information()
    if LEGACY_INDEX in indexes:
        await collection.drop_index(LEGACY_INDEX)
