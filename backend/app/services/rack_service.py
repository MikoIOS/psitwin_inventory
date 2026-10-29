from datetime import (
    datetime,
    timezone
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set
)

from uuid import uuid4

from fastapi import HTTPException

from app.database.mongodb import (
    get_database
)

from app.dto.rack_dto import (
    RackCreate,
    RackUpdate
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.repositories.zona_repository import (
    ZonaRepository
)

from app.repositories.detalle_inventario_repository import (
    DetalleInventarioRepository
)


def _id_rack(
    rack: Dict[str, Any]
) -> Optional[str]:

    return (
        rack.get("id_rack")
        or
        rack.get("id")
    )


def _kg(
    valor: float
) -> str:

    return f"{round(float(valor), 2):g}"


class RackService:

    def __init__(self):
        self.repository = RackRepository()
        self.zona_repository = ZonaRepository()


    # ============================================================
    # CARGA / LIBRE (KG)
    #
    # carga_kg = Σ stock_actual × peso del producto
    # libre_kg = capacidad - carga_kg
    #
    # Productos sin peso (antiguos) cuentan 0 kg.
    # ============================================================

    @staticmethod
    async def enriquecer(
        racks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        if not racks:
            return []

        ids = [
            _id_rack(rack)
            for rack in racks
            if _id_rack(rack)
        ]

        inventarios = await (
            DetalleInventarioRepository()
            .obtener_por_racks(
                ids
            )
        )

        productos = await (
            get_database()["productos"]
            .find(
                {
                    "id_producto": {
                        "$in": list(
                            {
                                inventario["id_producto"]
                                for inventario in inventarios
                            }
                        )
                    }
                },
                {
                    "_id": 0,
                    "id_producto": 1,
                    "peso": 1
                }
            )
            .to_list(
                length=None
            )
        )

        pesos = {
            producto["id_producto"]:
                float(producto.get("peso") or 0)
            for producto in productos
        }

        cargas: Dict[str, float] = {}

        for inventario in inventarios:

            cargas[inventario["id_rack"]] = (
                cargas.get(
                    inventario["id_rack"],
                    0.0
                )
                + float(
                    inventario.get("stock_actual") or 0
                )
                * pesos.get(
                    inventario["id_producto"],
                    0.0
                )
            )

        resultado = []

        for rack in racks:

            item = dict(rack)

            if "id_rack" not in item:
                item["id_rack"] = _id_rack(rack)

            carga = round(
                cargas.get(
                    item["id_rack"],
                    0.0
                ),
                3
            )

            item["carga_kg"] = carga

            item["libre_kg"] = round(
                float(
                    item.get(
                        "capacidad",
                        0
                    )
                )
                - carga,
                3
            )

            resultado.append(item)

        return resultado


    @staticmethod
    async def enriquecer_uno(
        rack: Dict[str, Any]
    ) -> Dict[str, Any]:

        return (
            await RackService.enriquecer(
                [rack]
            )
        )[0]


    # ============================================================
    # MOTIVO POR EL QUE UN PRODUCTO NO CABE EN UN RACK
    #
    # rack: ya enriquecido (carga_kg / libre_kg).
    # Devuelve None si cabe.
    #
    # 1. rack DISPONIBLE (si exigir_disponible)
    # 2. cantidad × peso <= libre_kg
    # 3. producto refrigerado: el rango del rack debe
    #    caber dentro del rango del producto
    # ============================================================

    @staticmethod
    def motivo_no_cabe(
        rack: Dict[str, Any],
        producto: Dict[str, Any],
        cantidad: float,
        exigir_disponible: bool = True
    ) -> Optional[str]:

        codigo = rack.get(
            "codigo",
            rack["id_rack"]
        )

        if (
            exigir_disponible
            and
            rack.get("estado") != "DISPONIBLE"
        ):

            return (
                f"El rack {codigo} no está "
                "DISPONIBLE (estado: "
                f"{rack.get('estado')})"
            )

        carga = (
            float(cantidad)
            * float(producto.get("peso") or 0)
        )

        if carga > 0 and carga > rack["libre_kg"] + 1e-9:

            return (
                f"Capacidad insuficiente en el rack "
                f"{codigo}. Libre: "
                f"{_kg(max(rack['libre_kg'], 0))} kg. "
                f"Carga a ingresar: {_kg(carga)} kg"
            )

        if producto.get("requiere_refrigeracion"):

            r_min = rack.get("temperatura_min")
            r_max = rack.get("temperatura_max")
            p_min = producto.get(
                "temperatura_min_almacenamiento"
            )
            p_max = producto.get(
                "temperatura_max_almacenamiento"
            )

            if r_min is None or r_max is None:

                return (
                    f"El producto requiere refrigeración "
                    f"y el rack {codigo} no tiene "
                    "temperatura definida"
                )

            if (
                (p_min is not None and r_min < p_min)
                or
                (p_max is not None and r_max > p_max)
            ):

                return (
                    f"La temperatura del rack {codigo} "
                    f"({_kg(r_min)} a {_kg(r_max)} °C) no cabe "
                    "en el rango del producto "
                    f"({_kg(p_min)} a {_kg(p_max)} °C)"
                )

        return None


    # ============================================================
    # VALIDAR ASIGNACION (409)
    #
    # Usado por: crear inventario, ingreso de recepción,
    # resolver evaluación y entradas de stock.
    # ============================================================

    @staticmethod
    async def validar_asignacion(
        rack: Dict[str, Any],
        producto: Dict[str, Any],
        cantidad: float,
        exigir_disponible: bool = True
    ) -> Dict[str, Any]:

        rack = await (
            RackService.enriquecer_uno(
                rack
            )
        )

        motivo = RackService.motivo_no_cabe(
            rack,
            producto,
            cantidad,
            exigir_disponible
        )

        if motivo:

            raise HTTPException(
                status_code=409,
                detail=motivo
            )

        return rack


    # ============================================================
    # CREAR
    # ============================================================

    async def _crear_rack(
        self,
        data: RackCreate
    ):
        zona = (
            await self.zona_repository.obtener_por_id(
                data.id_zona
            )
        )

        if not zona:
            raise HTTPException(
                status_code=404,
                detail="Zona no encontrada"
            )

        # --------------------------------------------------------
        # NIVEL DENTRO DE LOS NIVELES DE LA ZONA
        # --------------------------------------------------------

        racks_zona = await self.repository.obtener_por_zona(data.id_zona)

        codigo = data.codigo.strip().upper()

        if any(
            rack.get("codigo") == codigo
            for rack in racks_zona
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe un rack con ese "
                    "código en la zona"
                )
            )

        # --------------------------------------------------------
        # TEMPERATURA: SOLO ZONAS REFRIGERADAS
        # --------------------------------------------------------

        tiene_temperatura = (
            data.temperatura_min is not None
            or data.temperatura_max is not None
        )

        if zona.get("refrigerada"):

            if (
                data.temperatura_min is None
                or data.temperatura_max is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La zona es refrigerada: indique "
                        "temperatura_min y temperatura_max "
                        "del rack"
                    )
                )

        elif tiene_temperatura:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo los racks de zonas refrigeradas "
                    "tienen temperatura"
                )
            )

        ahora = datetime.now(
            timezone.utc
        )

        rack = {
            "id_rack":
                str(uuid4()),

            "id_zona":
                data.id_zona,

            "max_niveles": data.max_niveles,
            "tipo_rack": data.tipo_rack.strip() if data.tipo_rack else None,
            "codigo":
                codigo,

            "nivel":
                data.nivel,

            "capacidad":
                data.capacidad,

            "temperatura_min":
                data.temperatura_min,

            "temperatura_max":
                data.temperatura_max,

            "estado":
                data.estado.value,

            "fecha_creacion":
                ahora,

            "fecha_actualizacion":
                ahora
        }

        return await self.enriquecer_uno(
            await self.repository.crear(
                rack
            )
        )


    # ============================================================
    # OBTENER RACKS
    #
    # ids_zona: alcance del usuario (None = sin filtro).
    # ============================================================

    async def obtener_racks(
        self,
        ids_zona: Optional[Set[str]] = None
    ):

        if ids_zona is None:

            racks = await (
                self.repository.obtener_todos()
            )

        elif not ids_zona:

            return []

        else:

            racks = await (
                self.repository.obtener_por_zonas(
                    list(ids_zona)
                )
            )

        return await self.enriquecer(
            racks
        )


    async def obtener_rack(
        self,
        id_rack: str
    ):
        rack = (
            await self.repository.obtener_por_id(
                id_rack
            )
        )

        if not rack:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

        return await self.enriquecer_uno(
            rack
        )


    async def obtener_racks_zona(
        self,
        id_zona: str
    ):
        zona = (
            await self.zona_repository.obtener_por_id(
                id_zona
            )
        )

        if not zona:
            raise HTTPException(
                status_code=404,
                detail="Zona no encontrada"
            )

        return await self.enriquecer(
            await self.repository.obtener_por_zona(
                id_zona
            )
        )


    # ============================================================
    # RACKS DISPONIBLES PARA UN PRODUCTO
    #
    # Racks del almacén donde caben `cantidad` unidades
    # del producto (estado, kg y temperatura).
    # Sin producto: solo racks DISPONIBLES.
    # ============================================================

    async def obtener_disponibles(
        self,
        id_almacen: str,
        producto: Optional[Dict[str, Any]] = None,
        cantidad: float = 0
    ):

        zonas = await (
            self.zona_repository
            .obtener_por_almacenes(
                [id_almacen]
            )
        )

        nombres_zona = {
            (zona.get("id") or zona.get("id_zona")):
                zona.get("nombre")
            for zona in zonas
        }

        if not nombres_zona:
            return []

        racks = await self.enriquecer(
            await self.repository.obtener_por_zonas(
                list(nombres_zona.keys())
            )
        )

        disponibles = []

        for rack in racks:

            if self.motivo_no_cabe(
                rack,
                producto or {},
                cantidad
            ):
                continue

            rack["id_almacen"] = id_almacen

            rack["nombre_zona"] = nombres_zona.get(
                rack.get("id_zona")
            )

            disponibles.append(rack)

        disponibles.sort(
            key=lambda r: (
                r.get("nombre_zona") or "",
                r.get("nivel") or 0
            )
        )

        return disponibles


    # ============================================================
    # ACTUALIZAR (OPERARIO): estado y temperatura
    # ============================================================

    async def _actualizar_rack(
        self,
        id_rack: str,
        data: RackUpdate
    ):
        rack_actual = (
            await self.repository.obtener_por_id(
                id_rack
            )
        )

        if not rack_actual:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

        datos = data.model_dump(
            exclude_unset=True
        )
        if datos.get('max_niveles') is not None:
            levels = await get_database()["niveles"].find({'id_rack': id_rack}, {'_id': 0}).to_list(length=1000)
            if datos['max_niveles'] < max([len(levels)] + [level['numero'] for level in levels]):
                raise HTTPException(409, 'El máximo de niveles no puede ser menor que los niveles existentes')

        if "estado" in datos:

            if datos["estado"] is None:
                datos.pop("estado")
            else:
                datos["estado"] = datos["estado"].value

        if (
            "temperatura_min" in datos
            or "temperatura_max" in datos
        ):

            zona = (
                await self.zona_repository.obtener_por_id(
                    rack_actual["id_zona"]
                )
            )

            if not (zona or {}).get("refrigerada"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Solo los racks de zonas refrigeradas "
                        "tienen temperatura"
                    )
                )

            t_min = datos.get(
                "temperatura_min",
                rack_actual.get("temperatura_min")
            )

            t_max = datos.get(
                "temperatura_max",
                rack_actual.get("temperatura_max")
            )

            if t_min is None or t_max is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Indique temperatura_min "
                        "y temperatura_max"
                    )
                )

            if t_min > t_max:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La temperatura mínima no puede "
                        "ser mayor que la máxima"
                    )
                )

        if not datos:
            return await self.enriquecer_uno(
                rack_actual
            )

        return await self.enriquecer_uno(
            await self.repository.actualizar(
                id_rack,
                datos
            )
        )


    async def _eliminar_rack(
        self,
        id_rack: str
    ):
        rack = (
            await self.repository.obtener_por_id(
                id_rack
            )
        )

        if not rack:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

        # --------------------------------------------------------
        # NO BORRAR RACKS CON INVENTARIO
        # --------------------------------------------------------

        inventarios = await (
            DetalleInventarioRepository()
            .obtener_por_rack(
                id_rack
            )
        )

        if inventarios:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El rack tiene inventarios; "
                    "no puede eliminarse"
                )
            )

        eliminado = (
            await self.repository.eliminar(
                id_rack
            )
        )

        return {
            "mensaje":
                "Rack eliminado correctamente",

            "eliminado":
                eliminado
        }

    async def crear_rack(self, data):
        from app.services.jerarquia_service import JerarquiaService
        return await JerarquiaService.crear_rack(self, data)

    async def actualizar_rack(self, identifier, data):
        from app.services.stock_lock import bloqueo_rack
        async with bloqueo_rack(identifier):
            result = await self._actualizar_rack(identifier, data)
            if data.max_niveles is not None:
                from app.services.jerarquia_service import JerarquiaService
                await JerarquiaService.asegurar_niveles(result)
            return result

    async def eliminar_rack(self, identifier):
        from app.services.stock_lock import bloqueo_rack
        async with bloqueo_rack(identifier):
            if await get_database()["niveles"].find_one({'id_rack': identifier}):
                raise HTTPException(409, 'El rack contiene niveles; elimine o reubique sus referencias primero')
            for collection in ('dispositivos', 'movimientos', 'detalles_recepcion', 'alertas', 'lecturas'):
                if await get_database()[collection].find_one({'id_rack': identifier}):
                    raise HTTPException(409, 'El rack tiene referencias; desactive o archive la ubicacion')
            return await self._eliminar_rack(identifier)
