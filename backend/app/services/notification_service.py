from __future__ import annotations

import asyncio
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Callable

from app.config.settings import settings
from app.database.mongodb import get_database


class NotificationService:
    COLLECTION_NAME = "notificaciones_email"

    def __init__(
        self,
        database_provider: Callable[[], Any] | None = None,
        sender: Callable[..., Any] | None = None
    ):
        self.database_provider = database_provider or get_database
        self.sender = sender or self._send_smtp

    def database(self):
        return self.database_provider()

    async def notify_owner(
        self,
        event_id: str,
        id_empresa: str,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        database = self.database()
        collection = database[self.COLLECTION_NAME]
        existing = await collection.find_one(
            {"event_id": event_id},
            {"_id": 0},
        )

        if existing and existing.get("status") in {"ENVIADO", "OMITIDO"}:
            return existing

        empresa = await database["empresas"].find_one(
            {
                "$or": [
                    {"id_empresa": id_empresa},
                    {"id": id_empresa},
                ]
            },
            {"_id": 0, "correo": 1, "correo_verificado": 1},
        )
        recipient = (empresa or {}).get("correo")
        now = datetime.now(timezone.utc)

        if not recipient:
            return await self._record(
                collection,
                event_id,
                id_empresa,
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

        if not settings.email_enabled:
            return await self._record(
                collection,
                event_id,
                id_empresa,
                recipient,
                subject,
                "OMITIDO",
                "EMAIL_ENABLED=false",
                now,
            )

        if not all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_secret,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            return await self._record(
                collection,
                event_id,
                id_empresa,
                recipient,
                subject,
                "ERROR",
                "Configuracion SMTP incompleta",
                now,
            )

        try:
            result = self.sender(
                settings.smtp_host,
                settings.smtp_port,
                settings.smtp_user,
                settings.smtp_secret,
                settings.smtp_from or settings.smtp_user,
                recipient,
                subject,
                body,
            )
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:
            return await self._record(
                collection,
                event_id,
                id_empresa,
                recipient,
                subject,
                "ERROR",
                str(exc),
                now,
            )

        return await self._record(
            collection,
            event_id,
            id_empresa,
            recipient,
            subject,
            "ENVIADO",
            None,
            now,
        )

    async def _entity_email_verified(
        self,
        database,
        collection_name: str,
        id_field: str,
        id_value: str,
    ) -> bool:
        document = await database[collection_name].find_one(
            {
                "$or": [
                    {id_field: id_value},
                    {"id": id_value},
                ]
            },
            {"_id": 0, "correo_verificado": 1},
        )
        if document is None:
            return False
        value = document.get("correo_verificado")
        return bool(value) if value is not None else False

    async def enviar_solicitud_aprobacion(
        self,
        id_recomendacion: str,
        id_operario: str | None = None,
    ) -> dict[str, Any]:
        database = self.database()
        recomendacion = await database["recomendaciones"].find_one(
            {"id_recomendacion": id_recomendacion},
            {"_id": 0},
        )
        if not recomendacion:
            return {"status": "ERROR", "reason": "Recomendacion no encontrada"}

        empresa = await self._find(
            database,
            "empresas",
            recomendacion["id_empresa"],
            "id_empresa",
        )
        almacen = await self._find(
            database,
            "almacenes",
            recomendacion["id_almacen"],
            "id_almacen",
        )
        producto = await self._find(
            database,
            "productos",
            recomendacion["id_producto"],
            "id_producto",
        )
        detalles = await database["detalles_inventario"].find(
            {"id_inventario": recomendacion["id_inventario"], "id_producto": recomendacion["id_producto"]},
            {"_id": 0}).to_list(length=None)
        inventario = {"stock_actual": sum(d["stock_actual"] for d in detalles)}
        operario = (
            await self._find(database, "operarios", id_operario, "id_operario")
            if id_operario
            else None
        )
        nombre_producto = (producto or {}).get("nombre", recomendacion["id_producto"])
        subject = f"[PsiTwin] Reposicion pendiente de aprobacion - {nombre_producto}"
        event_id = f"APROBACION:{id_recomendacion}"
        recipient = (empresa or {}).get("correo")
        now = datetime.now(timezone.utc)
        collection = database[self.COLLECTION_NAME]

        if not recipient:
            return await self._record(
                collection,
                event_id,
                recomendacion["id_empresa"],
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

        if not await self._entity_email_verified(
            database,
            "empresas",
            "id_empresa",
            recomendacion["id_empresa"],
        ):
            return await self._record(
                collection,
                event_id,
                recomendacion["id_empresa"],
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo de la empresa no está verificado",
                now,
            )

        body = "\n".join(
            [
                "PsiTwin detecto una situacion de inventario que requiere revision.",
                f"Empresa: {(empresa or {}).get('nombre', recomendacion['id_empresa'])}",
                f"Almacen: {(almacen or {}).get('nombre', recomendacion['id_almacen'])}",
                f"Producto: {nombre_producto}",
                f"Inventario: {recomendacion['id_inventario']}",
                f"Stock actual: {(inventario or {}).get('stock_actual', 'N/D')}",
                f"Nivel de riesgo: {recomendacion['nivel_riesgo']}",
                f"Forecast 7 dias: {recomendacion.get('forecast_7d', 'N/D')}",
                f"Cantidad minima: {recomendacion.get('cantidad_minima', 'N/D')}",
                f"Cantidad recomendada: {recomendacion.get('cantidad_recomendada', 'N/D')}",
                f"Cantidad segura: {recomendacion.get('cantidad_segura', 'N/D')}",
                f"Explicacion: {recomendacion['explicacion']}",
                f"Validado por: {(operario or {}).get('nombre', id_operario or 'N/D')}",
                f"Recomendacion: {id_recomendacion}",
                "La operacion todavia NO fue aprobada ni comprada.",
                "PENDIENTE DE APROBACION DE EMPRESA.",
            ]
        )
        return await self.notify_owner(
            event_id,
            recomendacion["id_empresa"],
            subject,
            body,
        )

    async def enviar_orden_proveedor(
        self,
        id_orden_reposicion: str,
    ) -> dict[str, Any]:
        database = self.database()
        orden = await database["ordenes_reposicion"].find_one(
            {"id_orden_reposicion": id_orden_reposicion},
            {"_id": 0},
        )
        if not orden:
            return {"status": "ERROR", "reason": "Orden no encontrada"}

        proveedor = await self._find(
            database,
            "proveedores",
            orden["id_proveedor"],
            "id_proveedor",
        )
        empresa = await self._find(
            database,
            "empresas",
            orden["id_empresa"],
            "id_empresa",
        )
        detalles = await database["detalles_reposicion"].find(
            {"id_orden_reposicion": id_orden_reposicion},
            {"_id": 0},
        ).to_list(length=None)
        recipient = (proveedor or {}).get("correo")
        event_id = f"ORDEN_PROVEEDOR:{id_orden_reposicion}"
        subject = f"[PsiTwin] Orden de reposicion - {orden['id_orden_reposicion']}"
        collection = database[self.COLLECTION_NAME]
        now = datetime.now(timezone.utc)

        if not recipient:
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                None,
                subject,
                "ERROR",
                "El proveedor no tiene correo configurado",
                now,
            )

        if not await self._entity_email_verified(
            database,
            "proveedores",
            "id_proveedor",
            orden["id_proveedor"],
        ):
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo del proveedor no está verificado",
                now,
            )

        detalle_lineas = []
        for detalle in detalles:
            detalle_lineas.append(
                (
                    f"- Producto: {detalle.get('id_producto', 'N/D')} | "
                    f"Cantidad: {detalle.get('cantidad_solicitada', 'N/D')} | "
                    f"Costo unitario: {detalle.get('costo_unitario', 'N/D')}"
                )
            )

        detalle_text = detalle_lineas if detalle_lineas else ["- No se registraron líneas de detalle"]
        body = "\n".join(
            [
                "PsiTwin le informa que se ha generado la siguiente orden de reposición.",
                f"Empresa solicitante: {(empresa or {}).get('nombre', orden['id_empresa'])}",
                f"Almacén: {orden.get('id_almacen', 'N/D')}",
                f"Orden: {orden.get('id_orden_reposicion', 'N/D')}",
                f"Fecha: {orden.get('fecha_orden', 'N/D')}",
                "Productos:",
                *detalle_text,
                f"Proveedor: {(proveedor or {}).get('nombre', 'N/D')}",
                f"Observaciones: {orden.get('observacion') or 'Sin observaciones'}",
                "Estado: APROBADA",
                "Esta orden requiere seguimiento de entrega por parte del proveedor.",
            ]
        )

        if not settings.email_enabled:
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "OMITIDO",
                "EMAIL_ENABLED=false",
                now,
            )

        if not all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_secret,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "ERROR",
                "Configuracion SMTP incompleta",
                now,
            )

        try:
            result = self.sender(
                settings.smtp_host,
                settings.smtp_port,
                settings.smtp_user,
                settings.smtp_secret,
                settings.smtp_from or settings.smtp_user,
                recipient,
                subject,
                body,
            )
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "ERROR",
                str(exc),
                now,
            )

        return await self._record(
            collection,
            event_id,
            orden["id_empresa"],
            recipient,
            subject,
            "ENVIADO",
            None,
            now,
        )

    async def enviar_resumen_reposicion(
        self,
        id_detalle_recepcion: str,
        riesgo_antes: str,
        riesgo_despues: str,
    ) -> dict[str, Any]:
        database = self.database()
        detalle = await database["detalles_recepcion"].find_one(
            {"id_detalle_recepcion": id_detalle_recepcion},
            {"_id": 0},
        )
        if not detalle:
            return {"status": "ERROR", "reason": "Detalle no encontrado"}

        recepcion = await database["recepciones_mercaderia"].find_one(
            {"id_recepcion": detalle["id_recepcion"]},
            {"_id": 0},
        )
        orden = await self._find(
            database,
            "ordenes_reposicion",
            (recepcion or {}).get("id_orden_reposicion"),
            "id_orden_reposicion",
        )
        empresa = await self._find(
            database,
            "empresas",
            (orden or {}).get("id_empresa"),
            "id_empresa",
        )
        proveedor = await self._find(
            database,
            "proveedores",
            (orden or {}).get("id_proveedor"),
            "id_proveedor",
        )
        detalle_orden = await database["detalles_reposicion"].find_one(
            {"id_detalle_reposicion": detalle["id_detalle_reposicion"]},
            {"_id": 0},
        )
        inventario = await self._find(database, "detalles_inventario",
            detalle.get("id_detalle_inventario"), "id_detalle_inventario")
        subject = f"[PsiTwin] Reposicion completada - {(empresa or {}).get('nombre', 'Empresa')}"
        recipient = (empresa or {}).get("correo")
        event_id = f"CIERRE:{id_detalle_recepcion}"
        collection = database[self.COLLECTION_NAME]
        now = datetime.now(timezone.utc)

        if not recipient:
            return await self._record(
                collection,
                event_id,
                (orden or {}).get("id_empresa", ""),
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

        if not await self._entity_email_verified(
            database,
            "empresas",
            "id_empresa",
            (orden or {}).get("id_empresa", ""),
        ):
            return await self._record(
                collection,
                event_id,
                (orden or {}).get("id_empresa", ""),
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo de la empresa no está verificado",
                now,
            )

        body = "\n".join([
            "La operacion de reposicion fue completada.",
            f"Empresa: {(empresa or {}).get('nombre', 'N/D')}",
            f"Almacen: {(orden or {}).get('id_almacen', 'N/D')}",
            f"Orden: {(orden or {}).get('id_orden_reposicion', 'N/D')}",
            f"Proveedor: {(proveedor or {}).get('nombre', 'N/D')}",
            f"Producto: {(detalle_orden or {}).get('id_producto', 'N/D')}",
            f"Cantidad solicitada: {(detalle_orden or {}).get('cantidad_solicitada', 'N/D')}",
            f"Cantidad recibida: {detalle.get('cantidad_recibida', 'N/D')}",
            f"Cantidad aceptada: {detalle.get('cantidad_aceptada', 'N/D')}",
            f"Cantidad rechazada: {detalle.get('cantidad_rechazada', 'N/D')}",
            f"Rack destino: {detalle.get('id_rack', 'N/D')}",
            f"Stock final: {(inventario or {}).get('stock_actual', 'N/D')}",
            f"Estado de la orden: {(orden or {}).get('estado', 'N/D')}",
            f"Operario: {recepcion.get('id_operario', 'N/D') if recepcion else 'N/D'}",
            f"Riesgo antes: {riesgo_antes}",
            f"Riesgo despues: {riesgo_despues}",
            f"Observaciones: {detalle.get('comentario_resolucion') or detalle.get('comentario_recepcion') or detalle.get('motivo_rechazo') or 'Sin observaciones'}",
            f"Resultado: {self._risk_message(riesgo_despues)}",
        ])
        return await self.notify_owner(
            event_id,
            (orden or {}).get("id_empresa", ""),
            subject,
            body,
        )

    @staticmethod
    async def _find(database, collection_name, identifier, field):
        if not identifier:
            return None
        return await database[collection_name].find_one(
            {
                "$or": [
                    {field: identifier},
                    {"id": identifier},
                ]
            },
            {"_id": 0},
        )

    @staticmethod
    def _risk_message(level: str) -> str:
        if level == "BAJO":
            return "El inventario se encuentra en un nivel de riesgo bajo/protegido."
        return f"La reposicion fue completada, pero el inventario todavia presenta riesgo {level}."

    @staticmethod
    async def _record(
        collection,
        event_id,
        id_empresa,
        recipient,
        subject,
        status,
        error,
        now,
    ):
        if error:
            for secret in (settings.smtp_app_password, settings.smtp_password):
                if secret: error = error.replace(secret, '[redacted]')
        document = {
            "event_id": event_id,
            "id_empresa": id_empresa,
            "recipient": recipient,
            "subject": subject,
            "status": status,
            "error": error,
            "fecha_actualizacion": now,
        }
        await collection.update_one(
            {"event_id": event_id},
            {
                "$set": document,
                "$setOnInsert": {"fecha_creacion": now},
            },
            upsert=True,
        )
        return await collection.find_one(
            {"event_id": event_id},
            {"_id": 0},
        )

    @staticmethod
    def _send_smtp(
        host,
        port,
        user,
        password,
        sender,
        recipient,
        subject,
        body,
    ):
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        from app.services.smtp_transport import send_message
        send_message(message, host, port, user, password)
