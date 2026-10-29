from datetime import (
    datetime
)

from typing import (
    Any,
    Dict,
    List
)

from pymongo import (
    UpdateOne
)

from app.database.mongodb import (
    get_database
)


CAMPOS_NUMERICOS = (
    "t_int",
    "t_amb",
    "hum",
    "corriente"
)

TTL_LECTURAS_S = 7 * 24 * 3600


class LecturaRepository:

    # ============================================================
    # COLECCIONES
    #
    # lecturas: time-series (ts + meta.id_dispositivo),
    #           TTL 7 días.
    # lecturas_minuto: min / max / suma / n por minuto y
    #                  campo; sin TTL.
    # ============================================================

    @staticmethod
    async def asegurar_colecciones() -> None:

        database = get_database()

        existentes = await database.list_collection_names()

        if "lecturas" not in existentes:

            await database.create_collection(
                "lecturas",
                timeseries={
                    "timeField": "ts",
                    "metaField": "meta",
                    "granularity": "seconds"
                },
                expireAfterSeconds=TTL_LECTURAS_S
            )

        await database["lecturas_minuto"].create_index(
            [
                ("id_dispositivo", 1),
                ("minuto", 1)
            ],
            unique=True,
            name="uq_dispositivo_minuto"
        )
        await database['lecturas'].create_index([('meta.id_empresa', 1), ('meta.id_dispositivo', 1), ('ts', 1)])
        await database['lecturas_minuto'].create_index([('id_empresa', 1), ('id_dispositivo', 1), ('minuto', 1)])

    @staticmethod
    async def pagina(id_empresa, id_dispositivo, desde, hasta, minuto, pagina, limite, tipo=None):
        collection = get_database()['lecturas_minuto' if minuto else 'lecturas']
        time_field = 'minuto' if minuto else 'ts'
        query = {('id_empresa' if minuto else 'meta.id_empresa'): id_empresa,
                 ('id_dispositivo' if minuto else 'meta.id_dispositivo'): id_dispositivo,
                 time_field: {'$gte': desde, '$lte': hasta}}
        if tipo:
            query[tipo] = {'$ne': None}
        cursor = collection.find(query, {'_id': 0, 'meta': 0}).sort(time_field, 1).skip((pagina - 1) * limite).limit(limite + 1)
        rows = await cursor.to_list(length=limite + 1)
        return rows[:limite], len(rows) > limite

    @staticmethod
    async def resumen(id_empresa, id_dispositivo, desde, hasta):
        # Full period statistics on minute buckets, never calculated from a sampled chart/page.
        group = {'_id': None, 'minutos': {'$sum': 1}}
        for field in CAMPOS_NUMERICOS:
            group[field + '_min'] = {'$min': '$' + field + '.min'}
            group[field + '_max'] = {'$max': '$' + field + '.max'}
            group[field + '_sum'] = {'$sum': '$' + field + '.suma'}
            group[field + '_n'] = {'$sum': '$' + field + '.n'}
        rows = await get_database()['lecturas_minuto'].aggregate([
            {'$match': {'id_empresa': id_empresa, 'id_dispositivo': id_dispositivo,
                        'minuto': {'$gte': desde, '$lt': hasta}}}, {'$group': group}]).to_list(length=1)
        if not rows:
            return {}
        row = rows[0]
        return {field: {'min': row.get(field + '_min'), 'max': row.get(field + '_max'),
                       'prom': row[field + '_sum'] / row[field + '_n'], 'n': row[field + '_n']}
                for field in CAMPOS_NUMERICOS if row.get(field + '_n')}


    # ============================================================
    # ESCRITURA EN BLOQUE
    # ============================================================

    @staticmethod
    async def insertar_lecturas(
        documentos: List[Dict[str, Any]]
    ) -> None:

        if documentos:

            await get_database()["lecturas"].insert_many(
                documentos,
                ordered=False
            )


    @staticmethod
    async def acumular_minutos(
        acumulados: Dict[tuple, Dict[str, Any]]
    ) -> None:

        # acumulados[(id_dispositivo, minuto)] =
        #   {"id_empresa", "campos": {campo: {min, max, suma, n}},
        #    "puerta": {"abiertas", "n"}}

        operaciones = []

        for (id_dispositivo, minuto), acc in acumulados.items():

            minimos = {}
            maximos = {}
            incrementos = {}

            for campo, valores in acc["campos"].items():

                minimos[f"{campo}.min"] = valores["min"]
                maximos[f"{campo}.max"] = valores["max"]
                incrementos[f"{campo}.suma"] = valores["suma"]
                incrementos[f"{campo}.n"] = valores["n"]

            if acc["puerta"]["n"]:

                incrementos["puerta.abiertas"] = acc["puerta"]["abiertas"]
                incrementos["puerta.n"] = acc["puerta"]["n"]

            actualizacion: Dict[str, Any] = {
                "$setOnInsert": {
                    "id_empresa": acc["id_empresa"]
                }
            }

            if minimos:
                actualizacion["$min"] = minimos
                actualizacion["$max"] = maximos

            if incrementos:
                actualizacion["$inc"] = incrementos

            operaciones.append(
                UpdateOne(
                    {
                        "id_dispositivo": id_dispositivo,
                        "minuto": minuto
                    },
                    actualizacion,
                    upsert=True
                )
            )

        if operaciones:

            await get_database()["lecturas_minuto"].bulk_write(
                operaciones,
                ordered=False
            )


    # ============================================================
    # CONSULTAS
    # ============================================================

    @staticmethod
    async def crudas(
        id_dispositivo: str,
        desde: datetime,
        hasta: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            get_database()["lecturas"]
            .find(
                {
                    "meta.id_dispositivo": id_dispositivo,
                    "ts": {
                        "$gte": desde,
                        "$lte": hasta
                    }
                },
                {
                    "_id": 0,
                    "meta": 0
                }
            )
            .sort(
                "ts",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def por_minuto(
        id_dispositivo: str,
        desde: datetime,
        hasta: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            get_database()["lecturas_minuto"]
            .find(
                {
                    "id_dispositivo": id_dispositivo,
                    "minuto": {
                        "$gte": desde,
                        "$lte": hasta
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "minuto",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )
