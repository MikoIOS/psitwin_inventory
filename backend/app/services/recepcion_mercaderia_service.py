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
            aceptada_por_linea[line] = round(aceptada_por_linea.get(line,0)+accepted, 3)
        for line,accepted in aceptada_por_linea.items():
            previous = await self.detalle_recepcion_repository.obtener_por_detalle_reposicion(line)
            if round(sum(d.get("cantidad_aceptada",0) for d in previous)+accepted, 3) > detalles_orden[line]["cantidad_solicitada"]:
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
        from hashlib import sha256
        await db["recepciones_mercaderia"].update_one({'id_recepcion': recepcion['id_recepcion']},
            {'$set': {'firma': sha256(data.model_dump_json(exclude={'clave_idempotencia', 'id_operario'}).encode()).hexdigest(),
                      'procesamiento': 'EN_PROCESO'}})

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
            from hashlib import sha256
            from app.services.oferta_service import miles
            from app.services.abastecimiento_service import event, AbastecimientoService
            order = await AccesoService.verificar_orden(user, data.id_orden_reposicion)
            signature = sha256(data.model_dump_json(exclude={'clave_idempotencia', 'id_operario'}).encode()).hexdigest()
            key = data.clave_idempotencia or signature
            previous = await get_database()["recepciones_mercaderia"].find_one({'id_orden_reposicion': data.id_orden_reposicion, 'clave_idempotencia': key})
            if previous:
                if previous.get('firma') != signature:
                    raise HTTPException(409, 'La clave de recepción ya corresponde a otro contenido')
                if previous.get('procesamiento') != 'COMPLETA':
                    raise HTTPException(409, 'La recepción requiere reconciliación; no se vuelve a ingresar stock')
                return await self.obtener_por_id(previous['id_recepcion'])
            if (order.get('resolucion_pendiente') or {}).get('decision') == 'CERRAR':
                raise HTTPException(409, 'La empresa cerró el pendiente de esta solicitud')
            dispatched = order.get('despachos') or ([order['despacho']] if order.get('despacho') else [])
            if not dispatched:
                raise HTTPException(409, 'Debe registrarse un despacho antes de recibir mercancía')
            by_line = {}
            for dispatch in dispatched:
                for line in dispatch['lineas']:
                    by_line[line['id_detalle_reposicion']] = round(by_line.get(line['id_detalle_reposicion'], 0) + line['cantidad'], 3)
            grouped = {}
            for detail in data.detalles:
                requested_line = await self.detalle_repository.obtener_por_id(detail.id_detalle_reposicion)
                unit = (requested_line or {}).get('unidad', 'unidad')
                miles(detail.cantidad_recibida, unit)
                miles(detail.cantidad_rechazada, unit)
                grouped[detail.id_detalle_reposicion] = round(grouped.get(detail.id_detalle_reposicion, 0) + detail.cantidad_recibida, 3)
            for identifier, quantity in grouped.items():
                line = await self.detalle_repository.obtener_por_id(identifier)
                miles(quantity, (line or {}).get('unidad', 'unidad'))
                received = sum(r.get('cantidad_recibida', 0) for r in await self.detalle_recepcion_repository.obtener_por_detalle_reposicion(identifier))
                if miles(round(received + quantity, 3)) > miles(by_line.get(identifier, 0)):
                    raise HTTPException(409, 'La cantidad recibida acumulada supera la despachada')
            data.clave_idempotencia = key
            result = await self._crear(data, user)
            await get_database()["recepciones_mercaderia"].update_one({'id_recepcion': result['id_recepcion']},
                {'$set': {'clave_idempotencia': key, 'firma': signature, 'procesamiento': 'COMPLETA'}})
            await get_database()["ordenes_reposicion"].update_one({'id_orden_reposicion': data.id_orden_reposicion},
                {'$push': {'historial_estados': event(order['estado'], (await AbastecimientoService.obtener(data.id_orden_reposicion))['estado'], user,
                    reason='Recepción confirmada', quantities=[d.model_dump() for d in data.detalles])}})
            result['comparacion'] = [r for r in await AbastecimientoService.pendientes(user) if r['id_orden'] == data.id_orden_reposicion]
            return result
