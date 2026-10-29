# app/database/mongodb.py

from importlib import import_module
from typing import Any
from app.database.alerta_indexes import ensure_alerta_indexes
from app.database.inventario_indexes import ensure_inventory_location_indexes


try:
    _motor = import_module("motor.motor_asyncio")
    AsyncIOMotorClient = _motor.AsyncIOMotorClient
    AsyncIOMotorDatabase = _motor.AsyncIOMotorDatabase
except ImportError as exc:
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = Any
    _motor_import_error = exc

from app.config.settings import (
    settings
)


client: Any = None

database: Any = None


async def ensure_alert_indexes(db):
    # Sensor identity includes device and parameter; inventory IDs may be null.
    await db['alertas'].create_index(
        [('id_dispositivo', 1), ('tipo_alerta', 1), ('parametro', 1)],
        unique=True,
        partialFilterExpression={'estado': {'$in': ['ACTIVA', 'VISTA']},
                                 'origen': 'SENSOR', 'id_dispositivo': {'$type': 'string'}},
        name='uq_alerta_activa_sensor_parametro')
    # Preserve inventory uniqueness and remove the incompatible legacy index last.
    await ensure_alerta_indexes(db['alertas'])
    await db['alertas'].create_index([('id_empresa', 1), ('id_dispositivo', 1), ('fecha_creacion', -1)])
    await db['alertas'].create_index([('id_empresa', 1), ('estado', 1), ('fecha_creacion', -1)])



async def connect_to_mongo():

    global client
    global database

    if AsyncIOMotorClient is None:
        raise RuntimeError(
            "El paquete 'motor' no está instalado. "
            "Instálalo con: pip install motor"
        ) from _motor_import_error

    try:

        client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )

        database = client[
            settings.mongodb_database
        ]

        # Schema indexes only; no data migration is performed at startup.
        if await database["inventarios"].find_one({"id_producto":{"$exists":True}},{"_id":1}):
            raise RuntimeError("MIGRACION_INVENTARIO_REQUERIDA: inventarios legacy; no se instalaron índices nuevos")
        await database["inventarios"].create_index(
            [("id_almacen", 1)], unique=True,
            partialFilterExpression={"id_almacen": {"$type": "string"}},
            name="uq_inventario_almacen")
        await database["inventarios"].create_index(
            [("id_inventario", 1)], unique=True, name="uq_inventario_id")
        await ensure_inventory_location_indexes(database["detalles_inventario"])
        await database["detalles_inventario"].create_index(
            [("id_detalle_inventario", 1)], unique=True, name="uq_detalle_inventario_id")
        await database["movimientos"].create_index(
            [("id_almacen", 1), ("id_producto", 1), ("tipo_movimiento", 1), ("fecha_hora", 1)],
            name="ix_demanda_producto_almacen")
        await database["movimientos"].create_index(
            [("id_detalle_inventario", 1), ("fecha_hora", 1)], name="ix_movimiento_detalle")

        await database["detalles_recepcion"].create_index(
            [("id_detalle_inventario", 1)], name="ix_recepcion_detalle_inventario")
        await database["inventario_historial"].create_index(
            [("id_inventario", 1), ("id_detalle_inventario", 1), ("fecha", -1)], name="ix_historial_inventario_v2")
        await ensure_alert_indexes(database)

        await database["recomendaciones"].create_index(
            [("id_inventario", 1), ("id_producto", 1), ("id_detalle_inventario", 1), ("tipo_recomendacion", 1)],
            unique=True, partialFilterExpression={"estado": {"$in": ["PENDIENTE", "ACEPTADA"]}},
            name="uq_recomendacion_pendiente_producto_ubicacion")

        await database["reportes_inventario"].create_index("id_reporte", unique=True)
        await database["reportes_inventario"].create_index([("id_empresa",1),("actor",1),("fecha_creacion",-1)])
        await database["ofertas_proveedor"].create_index("id_oferta", unique=True)
        await database["ofertas_proveedor"].create_index([("id_empresa", 1), ("id_proveedor", 1), ("id_producto", 1)], unique=True)
        await database["niveles"].create_index([("id_rack", 1), ("numero", 1)], unique=True)
        await database["niveles"].create_index([("id_rack", 1), ("codigo", 1)], unique=True)

        # Verificar conexión real
        await client.admin.command(
            "ping"
        )

        await database["movimientos"].create_index(
            [("id_detalle_recepcion",1)], unique=True,
            partialFilterExpression={"id_detalle_recepcion":{"$type":"string"}},
            name="uq_movimiento_detalle_recepcion")
        await database["movimientos"].create_index(
            [("id_movimiento",1)], unique=True, name="uq_movimiento_id")

        try:
            await database["notificaciones_email"].create_index(
                [("event_id", 1)],
                unique=True,
                name="uq_notificacion_email_evento"
            )
        except Exception as exc:
            print(
                "Advertencia creando índice de notificaciones:"
            )
            print(exc)

        print(
            "MongoDB conectado correctamente"
        )

        print(
            f"Base de datos: "
            f"{settings.mongodb_database}"
        )

    except Exception as e:

        print(
            "Error conectando a MongoDB:"
        )

        print(e)

        raise


async def close_mongo_connection():

    global client
    global database

    if client is not None:

        client.close()

        client = None

        database = None

        print(
            "Conexión MongoDB cerrada"
        )


def get_database() -> Any:

    if database is None:

        raise RuntimeError(
            "MongoDB no está conectado."
        )

    return database
