from fastapi import HTTPException, status

from app.dto.movimiento_dto import (
    MovimientoCreate,
    TipoMovimiento,
    MotivoMovimiento
)

from app.repositories.movimiento_repository import (
    MovimientoRepository
)

from app.repositories.detalle_inventario_repository import (
    DetalleInventarioRepository
)

from app.repositories.operario_repository import (
    OperarioRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.repositories.producto_repository import (
    ProductoRepository
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.services.rack_service import (
    RackService
)


class MovimientoService:

    def __init__(self):

        self.repository = MovimientoRepository()

        self.inventario_repository = (
            DetalleInventarioRepository()
        )

        self.operario_repository = (
            OperarioRepository()
        )

    # ========================================================
    # VALIDAR COMBINACION TIPO + MOTIVO
    # ========================================================

    def validar_tipo_motivo(
        self,
        tipo: TipoMovimiento,
        motivo: MotivoMovimiento
    ):

        motivos_entrada = {
            MotivoMovimiento.RECEPCION,
            MotivoMovimiento.REPOSICION,
            MotivoMovimiento.DEVOLUCION,
            MotivoMovimiento.CONTEO_FISICO,
            MotivoMovimiento.OTRO
        }

        motivos_salida = {
            MotivoMovimiento.VENTA,
            MotivoMovimiento.MERMA,
            MotivoMovimiento.VENCIMIENTO,
            MotivoMovimiento.CONTEO_FISICO,
            MotivoMovimiento.OTRO
        }

        motivos_ajuste = {
            MotivoMovimiento.CONTEO_FISICO,
            MotivoMovimiento.OTRO
        }

        if (
            tipo == TipoMovimiento.ENTRADA
            and motivo not in motivos_entrada
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para una ENTRADA"
                )
            )

        if (
            tipo == TipoMovimiento.SALIDA
            and motivo not in motivos_salida
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para una SALIDA"
                )
            )

        if (
            tipo == TipoMovimiento.AJUSTE
            and motivo not in motivos_ajuste
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para un AJUSTE"
                )
            )

    # ========================================================
    # CREAR MOVIMIENTO
    # ========================================================

    async def _crear_movimiento(
        self,
        data: MovimientoCreate,
        user: UsuarioActual | None = None
    ):

        if data.id_detalle_recepcion:
            existente = await (
                self.repository
                .obtener_por_detalle_recepcion(
                    data.id_detalle_recepcion
                )
            )
            if existente:
                if existente["id_inventario"] != data.id_inventario or existente["id_detalle_inventario"] != data.id_detalle_inventario:
                    raise HTTPException(409,"El movimiento de recepción pertenece a otra ubicación")
                return existente

        # ----------------------------------------------------
        # 0. Operario responsable
        #
        # OPERARIO: siempre el del token.
        # ----------------------------------------------------

        if user is not None and user.es_operario:

            data.id_operario = user.id_operario

        if not data.id_operario:

            raise HTTPException(
                status_code=422,
                detail=(
                    "Debe indicar id_operario"
                )
            )

        # ----------------------------------------------------
        # 1. Validar inventario
        # ----------------------------------------------------

        inventario = (
            await self.inventario_repository.obtener_por_id(
                data.id_detalle_inventario
            )
        )

        if not inventario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventario no encontrado"
            )

        # ----------------------------------------------------
        # 2. Validar operario
        # ----------------------------------------------------

        operario = (
            await self.operario_repository.obtener_por_id(
                data.id_operario
            )
        )

        if (
            not operario
            or
            (
                user is not None
                and
                operario.get("id_empresa")
                != user.id_empresa
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operario no encontrado"
            )

        # ----------------------------------------------------
        # 3. Validar operario activo
        # ----------------------------------------------------

        estado_operario = str(
            operario.get(
                "estado",
                ""
            )
        ).upper()

        if estado_operario != "ACTIVO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El operario debe estar ACTIVO "
                    "para registrar movimientos"
                )
            )

        # ----------------------------------------------------
        # 4. Validar tipo + motivo
        # ----------------------------------------------------

        self.validar_tipo_motivo(
            data.tipo_movimiento,
            data.motivo_movimiento
        )

        # ----------------------------------------------------
        # 5. Obtener stock actual
        # ----------------------------------------------------

        from app.repositories.inventario_repository import InventarioRepository
        from app.repositories.almacen_repository import AlmacenRepository
        from app.repositories.zona_repository import ZonaRepository
        if inventario["id_inventario"] != data.id_inventario:
            raise HTTPException(400, "El detalle no pertenece al inventario general indicado")
        header = await InventarioRepository().obtener_por_id(data.id_inventario)
        almacen = await AlmacenRepository.obtener_por_id(header["id_almacen"]) if header else None
        rack_ref = await RackRepository.obtener_por_id(inventario["id_rack"])
        zona = await ZonaRepository.obtener_por_id(rack_ref["id_zona"]) if rack_ref else None
        producto_ref = await ProductoRepository.obtener_por_id(inventario["id_producto"])
        if not almacen or not zona or zona["id_almacen"] != header["id_almacen"] or not producto_ref or producto_ref["id_empresa"] != almacen["id_empresa"]:
            raise HTTPException(409, "Referencias de ubicación/producto incompatibles")
        if operario.get("id_empresa") != almacen["id_empresa"] or operario.get("id_almacen") != header["id_almacen"]:
            raise HTTPException(403, "El operario no pertenece al almacén del detalle")

        stock_anterior = inventario[
            "stock_actual"
        ]

        stock_nuevo = stock_anterior

        # ----------------------------------------------------
        # 6. ENTRADA
        # ----------------------------------------------------

        if (
            data.tipo_movimiento
            == TipoMovimiento.ENTRADA
        ):

            stock_nuevo = (
                stock_anterior
                + data.cantidad
            )

        # ----------------------------------------------------
        # 7. SALIDA
        # ----------------------------------------------------

        elif (
            data.tipo_movimiento
            == TipoMovimiento.SALIDA
        ):

            if data.cantidad > stock_anterior:

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Stock insuficiente. "
                        f"Stock disponible: "
                        f"{stock_anterior}. "
                        f"Cantidad solicitada: "
                        f"{data.cantidad}"
                    )
                )

            stock_nuevo = (
                stock_anterior
                - data.cantidad
            )

        # ----------------------------------------------------
        # 8. AJUSTE
        # ----------------------------------------------------
        #
        # Para AJUSTE, cantidad representa el NUEVO STOCK
        # físico contado.
        #
        # Ejemplo:
        # stock sistema = 100
        # cantidad = 96
        # nuevo stock = 96
        #
        # ----------------------------------------------------

        elif (
            data.tipo_movimiento
            == TipoMovimiento.AJUSTE
        ):

            stock_nuevo = data.cantidad

        # ----------------------------------------------------
        # 9. Validar stock
        # ----------------------------------------------------

        if stock_nuevo < 0:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El movimiento produciría "
                    "stock negativo"
                )
            )

        # ----------------------------------------------------
        # 9.1 Validar capacidad del rack
        #
        # ENTRADA y AJUSTE: la carga resultante (kg) no
        # puede superar la capacidad del rack.
        # ----------------------------------------------------

        incremento = (
            stock_nuevo
            - stock_anterior
        )

        if (
            data.tipo_movimiento
            in (
                TipoMovimiento.ENTRADA,
                TipoMovimiento.AJUSTE
            )
            and
            incremento > 0
        ):

            rack = await (
                RackRepository.obtener_por_id(
                    inventario["id_rack"]
                )
            )

            if not rack:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rack no encontrado"
                )

            producto = await (
                ProductoRepository.obtener_por_id(
                    inventario["id_producto"]
                )
            )

            await RackService.validar_asignacion(
                rack,
                producto or {},
                incremento,
                exigir_disponible=(data.id_detalle_recepcion is not None)
            )

        # ----------------------------------------------------
        # 10. Actualizar inventario
        # ----------------------------------------------------

        actualizado = await (
            self.inventario_repository
            .actualizar_stock_condicional(
                data.id_detalle_inventario,
                stock_anterior,
                stock_nuevo
            )
        )

        if not actualizado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El inventario cambió durante el movimiento; "
                    "intente nuevamente"
                )
            )

        # ----------------------------------------------------
        # 11. Crear historial
        # ----------------------------------------------------

        movimiento_dict = {
            "id_inventario": data.id_inventario,
            "id_detalle_inventario": data.id_detalle_inventario,
            "id_almacen": header["id_almacen"],

            "id_producto":
                inventario["id_producto"],

            "id_rack":
                inventario["id_rack"],

            "id_operario":
                data.id_operario,

            "id_detalle_recepcion":
                data.id_detalle_recepcion,

            "tipo_movimiento":
                data.tipo_movimiento.value,

            "motivo_movimiento":
                data.motivo_movimiento.value,

            "cantidad":
                data.cantidad,

            "stock_anterior":
                stock_anterior,

            "stock_nuevo":
                stock_nuevo,

            "observacion":
                data.observacion
        }

        try:
            movimiento = (
                await self.repository.crear(
                    movimiento_dict
                )
            )
        except Exception:
            await (
                self.inventario_repository
                .actualizar_stock_condicional(
                    data.id_detalle_inventario,
                    stock_nuevo,
                    stock_anterior
                )
            )
            raise

        return movimiento

    # ========================================================
    # ENRIQUECER (HISTORIAL PARA LA EMPRESA)
    #
    # Añade operario_nombre e id_zona a cada movimiento.
    # ========================================================

    async def enriquecer(self, movimientos: list) -> list:

        nombres = await (
            self.operario_repository.nombres_por_ids(
                [
                    movimiento.get("id_operario")
                    for movimiento in movimientos
                ]
            )
        )

        racks = await RackRepository.collection().find(
            {
                "id_rack": {
                    "$in": list(
                        {
                            movimiento.get("id_rack")
                            for movimiento in movimientos
                        }
                    )
                }
            },
            {"_id": 0, "id_rack": 1, "id_zona": 1}
        ).to_list(length=None)

        zonas = {
            rack["id_rack"]: rack.get("id_zona")
            for rack in racks
        }

        for movimiento in movimientos:

            movimiento["operario_nombre"] = nombres.get(
                movimiento.get("id_operario")
            )

            movimiento["id_zona"] = zonas.get(
                movimiento.get("id_rack")
            )

        return movimientos

    # ========================================================
    # OBTENER TODOS
    # ========================================================

    async def obtener_movimientos(self):

        return await self.repository.obtener_todos()

    # ========================================================
    # OBTENER POR ID
    # ========================================================

    async def obtener_movimiento(
        self,
        id_movimiento: str
    ):

        movimiento = (
            await self.repository.obtener_por_id(
                id_movimiento
            )
        )

        if not movimiento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento no encontrado"
            )

        return movimiento

    # ========================================================
    # POR INVENTARIO
    # ========================================================

    async def obtener_por_inventario(
        self,
        id_inventario: str
    ):

        return (
            await self.repository.obtener_por_inventario(
                id_inventario
            )
        )

    # ========================================================
    # POR PRODUCTO
    # ========================================================

    async def obtener_por_producto(
        self,
        id_producto: str
    ):

        return (
            await self.repository.obtener_por_producto(
                id_producto
            )
        )

    # ========================================================
    # POR RACK
    # ========================================================

    async def obtener_por_rack(
        self,
        id_rack: str
    ):

        return (
            await self.repository.obtener_por_rack(
                id_rack
            )
        )

    # ========================================================
    # POR OPERARIO
    # ========================================================

    async def obtener_por_operario(
        self,
        id_operario: str
    ):

        return (
            await self.repository.obtener_por_operario(
                id_operario
            )
        )

    # ========================================================
    # POR TIPO
    # ========================================================

    async def obtener_por_tipo(
        self,
        tipo_movimiento: TipoMovimiento
    ):

        return (
            await self.repository.obtener_por_tipo(
                tipo_movimiento.value
            )
        )

    # ========================================================
    # POR MOTIVO
    # ========================================================

    async def obtener_por_motivo(
        self,
        motivo_movimiento: MotivoMovimiento
    ):

        return (
            await self.repository.obtener_por_motivo(
                motivo_movimiento.value
            )
        )
    async def crear_movimiento(self, data, user=None):
        from app.services.stock_lock import bloqueo_rack
        detalle = await self.inventario_repository.obtener_por_id(data.id_detalle_inventario)
        if not detalle:
            raise HTTPException(404, "Detalle de inventario no encontrado")
        if detalle["id_inventario"] != data.id_inventario:
            raise HTTPException(400, "El detalle no pertenece al inventario indicado")
        async with bloqueo_rack(detalle["id_rack"]):
            return await self._crear_movimiento(data, user)
