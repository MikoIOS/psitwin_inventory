# app/services/dispositivo_service.py

import secrets

from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Any,
    Dict,
    List,
    Optional
)
from uuid import uuid4

from fastapi import (
    HTTPException,
    status
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.dispositivo_dto import (
    DispositivoCreate,
    DispositivoUpdate
)

from app.repositories.alerta_repository import (
    AlertaRepository
)

from app.repositories.dispositivo_repository import (
    DispositivoRepository
)

from app.repositories.lectura_repository import (
    CAMPOS_NUMERICOS,
    LecturaRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.repositories.zona_repository import (
    ZonaRepository
)

from app.services.sensores.limites import (
    limites_efectivos
)

from app.services.sensores.monitoreo_service import (
    hash_token,
    monitoreo
)


MAX_PUNTOS_CRUDOS = 2000

VENTANA_CRUDA = timedelta(hours=24)


def _aware(
    valor: Optional[datetime]
) -> Optional[datetime]:

    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)

    return valor


class DispositivoService:

    # ============================================================
    # RESPUESTA
    #
    # Sin token_hash; con limites_efectivos y estado en vivo.
    # ============================================================

    @staticmethod
    async def respuestas(
        documentos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        if not documentos:
            return []

        abiertas = await AlertaRepository().listar_abiertas_sensores(
            [
                documento["id_dispositivo"]
                for documento in documentos
            ]
        )

        por_dispositivo: Dict[str, list] = {}

        for alerta in abiertas:
            por_dispositivo.setdefault(
                alerta["id_dispositivo"],
                []
            ).append(alerta)

        resultado = []

        for documento in documentos:

            rack = (
                await RackRepository.obtener_por_id(
                    documento["id_rack"]
                )
                if documento.get("id_rack")
                else None
            )

            item = {
                clave: valor
                for clave, valor in documento.items()
                if clave != "token_hash"
            }

            item["limites_efectivos"] = limites_efectivos(
                documento.get("limites"),
                rack
            )

            item["estado"] = monitoreo.estado(
                documento["id_dispositivo"],
                por_dispositivo.get(
                    documento["id_dispositivo"],
                    []
                )
            )

            resultado.append(item)

        return resultado


    @staticmethod
    async def respuesta(
        documento: Dict[str, Any]
    ) -> Dict[str, Any]:

        return (
            await DispositivoService.respuestas(
                [documento]
            )
        )[0]


    # ============================================================
    # VALIDACIONES DE UBICACION
    #
    # El almacén ya fue verificado (AccesoService).
    # La zona debe ser de ese almacén y el rack de esa zona.
    # ============================================================

    @staticmethod
    async def _validar_zona_y_rack(
        id_almacen: str,
        id_zona: str,
        id_rack: Optional[str]
    ) -> None:

        zona = await ZonaRepository.obtener_por_id(
            id_zona
        )

        if (
            not zona
            or zona.get("id_almacen") != id_almacen
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zona no encontrada en el almacén"
            )

        if id_rack is None:
            return

        rack = await RackRepository.obtener_por_id(
            id_rack
        )

        if (
            not rack
            or rack.get("id_zona") != id_zona
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rack no encontrado en la zona"
            )


    # ============================================================
    # CREAR (EMPRESA) -> token en claro una sola vez
    # ============================================================

    @staticmethod
    async def crear(
        data: DispositivoCreate,
        user: UsuarioActual
    ) -> Dict[str, Any]:

        await DispositivoService._validar_zona_y_rack(
            data.id_almacen,
            data.id_zona,
            data.id_rack
        )

        token = secrets.token_urlsafe(24)

        ahora = datetime.now(
            timezone.utc
        )

        documento = {
            "id_dispositivo": str(uuid4()),
            "id_empresa": user.id_empresa,
            "id_almacen": data.id_almacen,
            "id_zona": data.id_zona,
            "id_rack": data.id_rack,
            "nombre": data.nombre.strip(),
            "activo": True,
            "token_hash": hash_token(token),
            "limites": data.limites.model_dump(
                exclude_none=True
            ),
            "ultima_lectura_ts": None,
            "fecha_creacion": ahora,
            "fecha_actualizacion": ahora
        }

        creado = await DispositivoRepository.crear(
            documento
        )

        await monitoreo.recargar(
            creado["id_dispositivo"]
        )

        return {
            **await DispositivoService.respuesta(creado),
            "token": token
        }


    # ============================================================
    # LISTAR
    #
    # EMPRESA: los suyos. OPERARIO: los de su almacén.
    # ============================================================

    @staticmethod
    async def listar_documentos(
        user: UsuarioActual,
        id_zona: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        filtro: Dict[str, Any] = {
            "id_empresa": user.id_empresa
        }

        if user.es_operario:
            filtro["id_almacen"] = user.id_almacen

        if id_zona:
            filtro["id_zona"] = id_zona

        return await DispositivoRepository.listar(
            filtro
        )


    @staticmethod
    async def listar(
        user: UsuarioActual,
        id_zona: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        return await DispositivoService.respuestas(
            await DispositivoService.listar_documentos(
                user,
                id_zona
            )
        )


    # ============================================================
    # OBTENER (con aislamiento)
    # ============================================================

    @staticmethod
    async def obtener_documento(
        id_dispositivo: str,
        user: UsuarioActual
    ) -> Dict[str, Any]:

        documento = await DispositivoRepository.obtener_por_id(
            id_dispositivo
        )

        if (
            not documento
            or documento.get("id_empresa") != user.id_empresa
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispositivo no encontrado"
            )

        if (
            user.es_operario
            and documento.get("id_almacen") != user.id_almacen
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a este dispositivo"
            )

        return documento


    # ============================================================
    # ACTUALIZAR (EMPRESA)
    # ============================================================

    @staticmethod
    async def actualizar(
        id_dispositivo: str,
        data: DispositivoUpdate,
        user: UsuarioActual
    ) -> Dict[str, Any]:

        actual = await DispositivoService.obtener_documento(
            id_dispositivo,
            user
        )

        cambios: Dict[str, Any] = {}

        enviados = data.model_fields_set

        if data.nombre is not None:
            cambios["nombre"] = data.nombre.strip()

        if data.activo is not None:
            cambios["activo"] = data.activo

        if "id_rack" in enviados:

            await DispositivoService._validar_zona_y_rack(
                actual["id_almacen"],
                actual["id_zona"],
                data.id_rack
            )

            cambios["id_rack"] = data.id_rack

        if data.limites is not None:
            cambios["limites"] = data.limites.model_dump(
                exclude_none=True
            )

        if not cambios:
            return await DispositivoService.respuesta(actual)

        actualizado = await DispositivoRepository.actualizar(
            id_dispositivo,
            cambios
        )

        await monitoreo.recargar(
            id_dispositivo
        )

        return await DispositivoService.respuesta(
            actualizado
        )


    # ============================================================
    # REGENERAR TOKEN (EMPRESA)
    # ============================================================

    @staticmethod
    async def regenerar_token(
        id_dispositivo: str,
        user: UsuarioActual
    ) -> Dict[str, str]:

        await DispositivoService.obtener_documento(
            id_dispositivo,
            user
        )

        token = secrets.token_urlsafe(24)

        await DispositivoRepository.actualizar(
            id_dispositivo,
            {
                "token_hash": hash_token(token)
            }
        )

        await monitoreo.recargar(
            id_dispositivo
        )

        return {
            "token": token
        }


    # ============================================================
    # ELIMINAR (EMPRESA)
    #
    # Las lecturas y alertas históricas se conservan.
    # ============================================================

    @staticmethod
    async def eliminar(
        id_dispositivo: str,
        user: UsuarioActual
    ) -> Dict[str, str]:

        await DispositivoService.obtener_documento(
            id_dispositivo,
            user
        )

        monitoreo.quitar(
            id_dispositivo
        )

        await DispositivoRepository.eliminar(
            id_dispositivo
        )

        return {
            "mensaje":
                "Dispositivo eliminado correctamente"
        }


    # ============================================================
    # LECTURAS
    #
    # <= 24 h -> crudas (submuestreadas a <= 2000 puntos)
    # >  24 h -> por minuto (min / max / promedio)
    # Por defecto: la última hora.
    # ============================================================

    @staticmethod
    async def lecturas(
        id_dispositivo: str,
        user: UsuarioActual,
        desde: Optional[datetime],
        hasta: Optional[datetime]
    ) -> Dict[str, Any]:

        await DispositivoService.obtener_documento(
            id_dispositivo,
            user
        )

        hasta = _aware(hasta) or datetime.now(timezone.utc)

        desde = _aware(desde) or (hasta - timedelta(hours=1))

        if desde > hasta:
            raise HTTPException(
                status_code=422,
                detail="desde no puede ser posterior a hasta"
            )

        if hasta - desde <= VENTANA_CRUDA:

            puntos = await LecturaRepository.crudas(
                id_dispositivo,
                desde,
                hasta
            )

            paso = max(
                1,
                -(-len(puntos) // MAX_PUNTOS_CRUDOS)
            )

            return {
                "id_dispositivo": id_dispositivo,
                "desde": desde,
                "hasta": hasta,
                "resolucion": "cruda",
                "puntos": puntos[::paso]
            }

        puntos = []

        for fila in await LecturaRepository.por_minuto(
            id_dispositivo,
            desde,
            hasta
        ):

            punto: Dict[str, Any] = {
                "ts": fila["minuto"]
            }

            for campo in CAMPOS_NUMERICOS:

                valores = fila.get(campo)

                punto[campo] = (
                    {
                        "min": valores["min"],
                        "max": valores["max"],
                        "prom": round(
                            valores["suma"] / valores["n"],
                            3
                        )
                    }
                    if valores and valores.get("n")
                    else None
                )

            puerta = fila.get("puerta")

            punto["puerta"] = (
                {
                    "fraccion_abierta": round(
                        puerta["abiertas"] / puerta["n"],
                        3
                    )
                }
                if puerta and puerta.get("n")
                else None
            )

            puntos.append(punto)

        return {
            "id_dispositivo": id_dispositivo,
            "desde": desde,
            "hasta": hasta,
            "resolucion": "minuto",
            "puntos": puntos
        }
