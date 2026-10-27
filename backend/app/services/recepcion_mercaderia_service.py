from fastapi import HTTPException

from app.database.mongodb import get_database

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.recepcion_mercaderia_dto import (
    RecepcionMercaderiaCreate
)

from app.repositories.recepcion_mercaderia_repository import (
    RecepcionMercaderiaRepository
)

from app.repositories.orden_reposicion_repository import (
    OrdenReposicionRepository
)

from app.repositories.detalle_reposicion_repository import (
    DetalleReposicionRepository
)

from app.repositories.detalle_recepcion_repository import (
    DetalleRecepcionRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.detalle_recepcion_service import (
    DetalleRecepcionService
)

from app.services.rack_service import (
    RackService
)


class RecepcionMercaderiaService:

    def __init__(self):
        self.repository = RecepcionMercaderiaRepository()
        self.orden_repository = OrdenReposicionRepository()
        self.detalle_repository = DetalleReposicionRepository()
        self.detalle_recepcion_repository = (
            DetalleRecepcionRepository()
        )
        self.detalle_recepcion_service = (
            DetalleRecepcionService()
        )

    async def _crear(
        self,
        data: RecepcionMercaderiaCreate,
        user: UsuarioActual
    ):

        orden = await self.orden_repository.obtener_por_id(
            data.id_orden_reposicion
        )

        if (
            not orden
            or orden.get("id_empresa") != user.id_empresa
        ):
            raise HTTPException(
                status_code=404,
                detail="Orden no encontrada"
            )

        # ----------------------------------------------------
        # Solo OPERARIO, sobre órdenes de su almacén.
        # id_operario se fuerza al del token.
        # ----------------------------------------------------

        if orden.get("id_almacen") != user.id_almacen:

            raise HTTPException(
                status_code=403,
                detail="La orden no es de su almacén"
            )

        data.id_operario = user.id_operario

        if orden["estado"] not in [
            "ENVIADA",
            "PARCIAL"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden debe estar ENVIADA "
                    "o PARCIAL para recibir mercancía"
                )
            )

        detalles = (
            await self.detalle_repository.obtener_por_orden(
                data.id_orden_reposicion
            )
        )

        if not detalles:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden no contiene productos"
                )
            )

        # Cada detalle debe pertenecer a la orden
        ids_detalle_orden = {
            detalle["id_detalle_reposicion"]
            for detalle in detalles
        }

        for detalle in data.detalles:

            if (
                detalle.id_detalle_reposicion
                not in ids_detalle_orden
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El detalle de reposición "
                        f"{detalle.id_detalle_reposicion} "
                        "no pertenece a la orden"
                    )
                )

        db = get_database()

        operario = await db["operarios"].find_one(
            {"id_operario": data.id_operario},
            {"_id": 0}
        )

        if (
            not operario
            or operario.get("id_empresa") != user.id_empresa
        ):
            raise HTTPException(
                status_code=404,
                detail="Operario no encontrado"
            )

        if operario.get("estado") != "ACTIVO":
            raise HTTPException(
                status_code=409,
                detail="El operario está inactivo"
            )

        if (
            operario.get("id_almacen")
            != orden["id_almacen"]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El operario no pertenece "
                    "al almacén de la orden"
                )
            )

        # ----------------------------------------------------
        # PRE-VALIDACION (antes de crear nada)
        #
        # - inventario del producto de la línea, dentro
        #   del almacén del operario
        # - temperatura obligatoria si el producto es
        #   refrigerado (422)
        # - rack DISPONIBLE, con kg libres para todo lo
        #   aceptado en esta recepción y temperatura
        #   compatible (409)
        # ----------------------------------------------------

        detalles_orden = {
            detalle["id_detalle_reposicion"]: detalle
            for detalle in detalles
        }

        aceptada_por_linea = {}
        for detalle in data.detalles:
            accepted = 0 if detalle.estado_recepcion.value == "EN_EVALUACION" else detalle.cantidad_recibida-detalle.cantidad_rechazada
            line = detalle.id_detalle_reposicion
            aceptada_por_linea[line] = aceptada_por_linea.get(line,0)+accepted
        for line,accepted in aceptada_por_linea.items():
            previous = await self.detalle_recepcion_repository.obtener_por_detalle_reposicion(line)
            if sum(d.get("cantidad_aceptada",0) for d in previous)+accepted > detalles_orden[line]["cantidad_solicitada"]:
                raise HTTPException(409,"La cantidad aceptada supera la pendiente de la orden")

        racks: dict = {}

        for detalle in data.detalles:

            inventario = await self.detalle_recepcion_service.resolver_ubicacion(
                detalle, detalles_orden[detalle.id_detalle_reposicion]["id_producto"], user,
                crear=False)

            producto = await db["productos"].find_one(
                {
                    "id_producto":
                        detalles_orden[
                            detalle.id_detalle_reposicion
                        ]["id_producto"]
                },
                {"_id": 0}
            ) or {}

            if (
                inventario["id_producto"]
                != producto.get("id_producto")
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El inventario seleccionado "
                        "no corresponde al producto "
                        "de la orden"
                    )
                )

            if (
                producto.get("requiere_refrigeracion")
                and detalle.temperatura_recepcion is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Indique la temperatura de recepción: "
                        f"{producto.get('nombre')} es refrigerado"
                    )
                )

            if detalle.estado_recepcion.value == "EN_EVALUACION":
                continue

            aceptada = (
                detalle.cantidad_recibida
                - detalle.cantidad_rechazada
            )

            if aceptada <= 0:
                continue

            id_rack = inventario["id_rack"]

            if id_rack not in racks:

                racks[id_rack] = await (
                    RackService.enriquecer_uno(
                        await RackRepository.obtener_por_id(
                            id_rack
                        )
                    )
                )

            motivo = RackService.motivo_no_cabe(
                racks[id_rack],
                producto,
                aceptada
            )

            if motivo:
                raise HTTPException(
                    status_code=409,
                    detail=motivo
                )

            # Descontar para las siguientes líneas del mismo rack
            racks[id_rack]["libre_kg"] -= (
                aceptada
                * float(producto.get("peso") or 0)
            )

        recepcion = await self.repository.crear(
            data.model_dump()
        )

        for detalle in data.detalles:
            await self.detalle_recepcion_service.crear(
                recepcion["id_recepcion"],
                detalle,
                user
            )

        recepcion["detalles"] = await (
            self.detalle_recepcion_repository
            .obtener_por_recepcion(
                recepcion["id_recepcion"]
            )
        )

        return recepcion

    async def obtener_todos(self):
        recepciones = await self.repository.obtener_todos()
        return await self._incluir_detalles(recepciones)

    async def obtener_por_id(self, id_recepcion):

        recepcion = await self.repository.obtener_por_id(
            id_recepcion
        )

        if not recepcion:
            raise HTTPException(
                status_code=404,
                detail="Recepción no encontrada"
            )

        recepcion["detalles"] = await (
            self.detalle_recepcion_repository
            .obtener_por_recepcion(id_recepcion)
        )
        return recepcion

    async def obtener_por_orden(self, id_orden):
        recepciones = await self.repository.obtener_por_orden(
            id_orden
        )
        return await self._incluir_detalles(recepciones)

    async def obtener_por_operario(self, id_operario):
        recepciones = await self.repository.obtener_por_operario(
            id_operario
        )
        return await self._incluir_detalles(recepciones)

    async def obtener_por_ordenes(self, ids_orden):
        recepciones = await self.repository.obtener_por_ordenes(
            ids_orden
        )
        return await self._incluir_detalles(recepciones)

    async def _incluir_detalles(self, recepciones):
        for recepcion in recepciones:
            recepcion["detalles"] = await (
                self.detalle_recepcion_repository
                .obtener_por_recepcion(
                    recepcion["id_recepcion"]
                )
            )
        return recepciones
    async def crear(self, data, user):
        from app.services.stock_lock import bloqueo_orden
        async with bloqueo_orden(data.id_orden_reposicion):
            return await self._crear(data,user)
