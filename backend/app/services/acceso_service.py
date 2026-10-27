# app/services/acceso_service.py

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set
)

from fastapi import (
    HTTPException,
    status
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.repositories.almacen_repository import (
    AlmacenRepository
)

from app.repositories.zona_repository import (
    ZonaRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.repositories.inventario_repository import (
    InventarioRepository
)

from app.repositories.producto_repository import (
    ProductoRepository
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.repositories.operario_repository import (
    OperarioRepository
)

from app.repositories.orden_reposicion_repository import (
    OrdenReposicionRepository
)

from app.repositories.recepcion_mercaderia_repository import (
    RecepcionMercaderiaRepository
)


# ============================================================
# ACCESO / AISLAMIENTO
#
# Reglas:
#
# - Recurso de otra empresa (o inexistente) -> 404.
# - OPERARIO sobre un recurso de su empresa pero
#   fuera de su almacén -> 403.
# - PROVEEDOR sobre lo que no es suyo -> 403.
#
# Jerarquía usada para resolver la pertenencia:
#
# EMPRESA -> ALMACEN -> ZONA -> RACK -> INVENTARIO
# ============================================================


def _no_encontrado(
    detalle: str
) -> HTTPException:

    return HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
        ),
        detail=detalle
    )


def _prohibido(
    detalle: str = (
        "No tiene acceso a este recurso"
    )
) -> HTTPException:

    return HTTPException(
        status_code=(
            status.HTTP_403_FORBIDDEN
        ),
        detail=detalle
    )


def id_de_zona(
    zona: Dict[str, Any]
) -> Optional[str]:

    return (
        zona.get("id")
        or
        zona.get("id_zona")
    )


def id_de_rack(
    rack: Dict[str, Any]
) -> Optional[str]:

    return (
        rack.get("id_rack")
        or
        rack.get("id")
    )


def id_de_almacen(
    almacen: Dict[str, Any]
) -> Optional[str]:

    return (
        almacen.get("id")
        or
        almacen.get("id_almacen")
    )


class AccesoService:

    # ============================================================
    # ALCANCE (IDS VISIBLES PARA EL USUARIO)
    # ============================================================

    @staticmethod
    async def ids_almacenes(
        user: UsuarioActual
    ) -> Set[str]:

        # PROVEEDOR: no ve almacenes
        if user.es_proveedor:

            return set()

        if user.es_operario:

            return (
                {user.id_almacen}
                if user.id_almacen
                else set()
            )

        almacenes = await (
            AlmacenRepository.obtener_por_empresa(
                user.id_empresa
            )
        )

        return {
            id_de_almacen(almacen)
            for almacen in almacenes
            if id_de_almacen(almacen)
        }


    @staticmethod
    async def zonas_visibles(
        user: UsuarioActual
    ) -> List[Dict[str, Any]]:

        ids_almacen = await (
            AccesoService.ids_almacenes(
                user
            )
        )

        if not ids_almacen:
            return []

        return await (
            ZonaRepository.obtener_por_almacenes(
                list(ids_almacen)
            )
        )


    @staticmethod
    async def ids_zonas(
        user: UsuarioActual
    ) -> Set[str]:

        zonas = await (
            AccesoService.zonas_visibles(
                user
            )
        )

        return {
            id_de_zona(zona)
            for zona in zonas
            if id_de_zona(zona)
        }


    @staticmethod
    async def ids_racks(
        user: UsuarioActual
    ) -> Set[str]:

        ids_zona = await (
            AccesoService.ids_zonas(
                user
            )
        )

        if not ids_zona:
            return set()

        racks = await (
            RackRepository.obtener_por_zonas(
                list(ids_zona)
            )
        )

        return {
            id_de_rack(rack)
            for rack in racks
            if id_de_rack(rack)
        }


    @staticmethod
    async def ids_inventarios(
        user: UsuarioActual
    ) -> Set[str]:

        headers = await InventarioRepository().obtener_por_almacenes(
            await AccesoService.ids_almacenes(user))
        return {row["id_inventario"] for row in headers}

    @staticmethod
    async def ids_detalles_inventario(user):
        from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
        rows = await DetalleInventarioRepository().obtener_por_racks(await AccesoService.ids_racks(user))
        return {row["id_detalle_inventario"] for row in rows}

    # ============================================================
    # FILTROS DE LISTAS
    # ============================================================

    @staticmethod
    def filtrar(
        items: Iterable[Dict[str, Any]],
        campo: str,
        permitidos: Set[str]
    ) -> List[Dict[str, Any]]:

        return [
            item
            for item in items
            if item.get(campo) in permitidos
        ]


    @staticmethod
    def filtrar_empresa(
        user: UsuarioActual,
        items: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        return [
            item
            for item in items
            if item.get("id_empresa")
            == user.id_empresa
        ]


    # ============================================================
    # EMPRESA EN LA RUTA (/.../empresa/{id_empresa})
    # ============================================================

    @staticmethod
    def verificar_empresa(
        user: UsuarioActual,
        id_empresa: str
    ) -> None:

        if id_empresa != user.id_empresa:

            raise _no_encontrado(
                "Empresa no encontrada"
            )


    # ============================================================
    # ALMACEN
    # ============================================================

    @staticmethod
    async def verificar_almacen(
        user: UsuarioActual,
        id_almacen: str
    ) -> Dict[str, Any]:

        if user.es_proveedor:

            raise _prohibido()

        almacen = await (
            AlmacenRepository.obtener_por_id(
                id_almacen
            )
        )

        if (
            not almacen
            or
            almacen.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Almacén no encontrado"
            )

        if (
            user.es_operario
            and
            id_de_almacen(almacen)
            != user.id_almacen
        ):

            raise _prohibido(
                "No tiene acceso a este almacén"
            )

        return almacen


    # ============================================================
    # ZONA
    # ============================================================

    @staticmethod
    async def verificar_zona(
        user: UsuarioActual,
        id_zona: str
    ) -> Dict[str, Any]:

        if user.es_proveedor:

            raise _prohibido()

        zona = await (
            ZonaRepository.obtener_por_id(
                id_zona
            )
        )

        if not zona:

            raise _no_encontrado(
                "Zona no encontrada"
            )

        almacen = await (
            AlmacenRepository.obtener_por_id(
                zona.get("id_almacen")
            )
        )

        if (
            not almacen
            or
            almacen.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Zona no encontrada"
            )

        if (
            user.es_operario
            and
            zona.get("id_almacen")
            != user.id_almacen
        ):

            raise _prohibido(
                "No tiene acceso a esta zona"
            )

        return zona


    # ============================================================
    # RACK
    # ============================================================

    @staticmethod
    async def verificar_rack(
        user: UsuarioActual,
        id_rack: str
    ) -> Dict[str, Any]:

        rack = await (
            RackRepository.obtener_por_id(
                id_rack
            )
        )

        if not rack:

            raise _no_encontrado(
                "Rack no encontrado"
            )

        try:

            await AccesoService.verificar_zona(
                user,
                rack.get("id_zona")
            )

        except HTTPException as exc:

            if exc.status_code == 404:

                raise _no_encontrado(
                    "Rack no encontrado"
                )

            raise _prohibido(
                "No tiene acceso a este rack"
            )

        return rack


    # ============================================================
    # INVENTARIO
    # ============================================================

    @staticmethod
    async def verificar_inventario(
        user: UsuarioActual,
        id_inventario: str
    ) -> Dict[str, Any]:

        inventario = await InventarioRepository().obtener_por_id(id_inventario)
        if not inventario:
            raise _no_encontrado("Inventario general no encontrado")
        await AccesoService.verificar_almacen(user, inventario["id_almacen"])
        return inventario

    @staticmethod
    async def verificar_detalle_inventario(user, id_detalle_inventario):
        from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
        detalle = await DetalleInventarioRepository().obtener_por_id(id_detalle_inventario)
        if not detalle:
            raise _no_encontrado("Detalle de inventario no encontrado")
        await AccesoService.verificar_inventario(user, detalle["id_inventario"])
        await AccesoService.verificar_rack(user, detalle["id_rack"])
        await AccesoService.verificar_producto(user, detalle["id_producto"])
        return detalle

    # ============================================================
    # PRODUCTO
    #
    # EMPRESA / OPERARIO: productos de su empresa.
    # PROVEEDOR: solo los suyos.
    # ============================================================

    @staticmethod
    async def verificar_producto(
        user: UsuarioActual,
        id_producto: str
    ) -> Dict[str, Any]:

        producto = await (
            ProductoRepository.obtener_por_id(
                id_producto
            )
        )

        if (
            not producto
            or
            producto.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Producto no encontrado"
            )

        if (
            user.es_proveedor
            and
            producto.get("id_proveedor")
            != user.id_proveedor
        ):

            raise _prohibido(
                "El producto no es de este proveedor"
            )

        return producto


    # ============================================================
    # PROVEEDOR
    # ============================================================

    @staticmethod
    async def verificar_proveedor(
        user: UsuarioActual,
        id_proveedor: str
    ) -> Dict[str, Any]:

        proveedor = await (
            ProveedorRepository()
            .obtener_por_id(
                id_proveedor
            )
        )

        if (
            not proveedor
            or
            proveedor.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Proveedor no encontrado"
            )

        return proveedor


    # ============================================================
    # OPERARIO
    # ============================================================

    @staticmethod
    async def verificar_operario(
        user: UsuarioActual,
        id_operario: str
    ) -> Dict[str, Any]:

        operario = await (
            OperarioRepository.obtener_por_id(
                id_operario
            )
        )

        if (
            not operario
            or
            operario.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Operario no encontrado"
            )

        return operario


    # ============================================================
    # ORDEN DE REPOSICION
    #
    # OPERARIO: órdenes de su almacén.
    # PROVEEDOR: órdenes enviadas a él
    #            (ENVIADA / PARCIAL / RECIBIDA).
    # ============================================================

    @staticmethod
    async def verificar_orden(
        user: UsuarioActual,
        id_orden: str
    ) -> Dict[str, Any]:

        orden = await (
            OrdenReposicionRepository()
            .obtener_por_id(
                id_orden
            )
        )

        if (
            not orden
            or
            orden.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Orden de reposición no encontrada"
            )

        if (
            user.es_operario
            and
            orden.get("id_almacen")
            != user.id_almacen
        ):

            raise _prohibido(
                "La orden no es de su almacén"
            )

        if (
            user.es_proveedor
            and
            (
                orden.get("id_proveedor")
                != user.id_proveedor
                or
                orden.get("estado") not in (
                    "ENVIADA",
                    "PARCIAL",
                    "RECIBIDA"
                )
            )
        ):

            raise _prohibido(
                "La orden no está enviada "
                "a este proveedor"
            )

        return orden


    # ============================================================
    # RECEPCION
    #
    # OPERARIO: recepciones de órdenes de su almacén.
    # PROVEEDOR: sin acceso.
    # ============================================================

    @staticmethod
    async def verificar_recepcion(
        user: UsuarioActual,
        id_recepcion: str
    ) -> Dict[str, Any]:

        recepcion = await (
            RecepcionMercaderiaRepository()
            .obtener_por_id(
                id_recepcion
            )
        )

        if not recepcion:

            raise _no_encontrado(
                "Recepción no encontrada"
            )

        orden = await (
            OrdenReposicionRepository()
            .obtener_por_id(
                recepcion.get(
                    "id_orden_reposicion"
                )
            )
        )

        if (
            not orden
            or
            orden.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Recepción no encontrada"
            )

        if (
            user.es_proveedor
            or
            (
                user.es_operario
                and
                orden.get("id_almacen")
                != user.id_almacen
            )
        ):

            raise _prohibido(
                "No tiene acceso a esta recepción"
            )

        return recepcion
