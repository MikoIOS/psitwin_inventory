import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.config.settings import settings
from app.services.email_verification_service import EmailVerificationService
from app.services.notification_service import NotificationService


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find(self, query, projection=None):
        matches = [dict(row) for row in self.documents if self._matches(row,query)]
        class Cursor:
            async def to_list(self,length=None):
                return matches
        return Cursor()

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if self._matches(document, query):
                return dict(document)
        return None

    async def update_one(self, query, update, upsert=False):
        document = next(
            (item for item in self.documents if self._matches(item, query)),
            None
        )
        if document is None:
            document = dict(query)
            document.pop("$or", None)
            document.update(update.get("$setOnInsert", {}))
            self.documents.append(document)
        document.update(update.get("$set", {}))

    @staticmethod
    def _matches(document, query):
        if "$or" in query:
            return any(
                FakeCollection._matches(document, item)
                for item in query["$or"]
            )
        return all(document.get(key) == value for key, value in query.items())


class FakeDatabase:
    def __init__(self, collections):
        self.collections = {
            name: FakeCollection(documents)
            for name, documents in collections.items()
        }

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())


class NotificationServiceTests(unittest.TestCase):
    def setUp(self):
        self.previous = {
            "email_enabled": settings.email_enabled,
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_user": settings.smtp_user,
            "smtp_password": settings.smtp_password,
            "smtp_from": settings.smtp_from,
        }
        settings.email_enabled = False
        self.database = FakeDatabase({
            "empresas": [{"id_empresa": "empresa-1", "correo": "owner@example.com", "correo_verificado": True}],
            "recomendaciones": [{
                "id_recomendacion": "rec-1",
                "id_empresa": "empresa-1",
                "id_almacen": "almacen-1",
                "id_inventario": "inventario-1",
                "id_producto": "producto-1",
                "nivel_riesgo": "CRITICO",
                "cantidad_minima": 80,
                "cantidad_recomendada": 95,
                "cantidad_segura": 100,
                "forecast_7d": 12.5,
                "explicacion": "Reponer",
            }],
            "almacenes": [{"id": "almacen-1", "nombre": "Principal"}],
            "productos": [{"id_producto": "producto-1", "nombre": "Producto TEST"}],
            "inventarios": [{"id_inventario":"inventario-1","id_almacen":"almacen-1"}],
            "detalles_inventario": [{
                "id_inventario": "inventario-1",
                "id_detalle_inventario": "detalle-1",
                "id_producto": "producto-1",
                "stock_actual": 18,
                "stock_minimo": 10,
                "stock_maximo": 200,
            }],
            "operarios": [{"id_operario": "operario-1", "nombre": "Ana"}],
        })
        self.sent = []

    def tearDown(self):
        for name, value in self.previous.items():
            setattr(settings, name, value)

    def test_disabled_email_is_recorded_and_not_sent_twice(self):
        service = NotificationService(
            lambda: self.database,
            lambda *args: self.sent.append(args)
        )
        first = asyncio.run(service.notify_owner("event-1", "empresa-1", "Subject", "Body"))
        second = asyncio.run(service.notify_owner("event-1", "empresa-1", "Subject", "Body"))
        self.assertEqual(first["status"], "OMITIDO")
        self.assertEqual(second["status"], "OMITIDO")
        self.assertEqual(self.sent, [])

    def test_approval_event_is_sent_once_and_contains_pending_decision(self):
        settings.email_enabled = True
        settings.smtp_host = "smtp.test"
        settings.smtp_user = "user"
        settings.smtp_password = "password"
        settings.smtp_from = "from@example.com"
        service = NotificationService(
            lambda: self.database,
            lambda *args: self.sent.append(args)
        )
        first = asyncio.run(service.enviar_solicitud_aprobacion("rec-1", "operario-1"))
        second = asyncio.run(service.enviar_solicitud_aprobacion("rec-1", "operario-1"))
        self.assertEqual(first["status"], "ENVIADO")
        self.assertEqual(second["status"], "ENVIADO")
        self.assertEqual(len(self.sent), 1)
        self.assertIn("NO fue aprobada", self.sent[0][7])
        self.assertIn("12.5", self.sent[0][7])

    def test_final_email_reports_residual_medium_risk(self):
        settings.email_enabled = True
        settings.smtp_host = "smtp.test"
        settings.smtp_user = "user"
        settings.smtp_password = "password"
        settings.smtp_from = "from@example.com"
        self.database["detalles_recepcion"].documents.append({
            "id_detalle_recepcion": "detail-1",
            "id_recepcion": "reception-1",
            "id_detalle_reposicion": "order-detail-1",
            "id_inventario": "inventario-1",
            "id_rack": "rack-1",
            "cantidad_recibida": 100,
            "cantidad_aceptada": 95,
            "cantidad_rechazada": 5,
            "comentario_recepcion": "Empaque danado",
        })
        self.database["recepciones_mercaderia"].documents.append({
            "id_recepcion": "reception-1",
            "id_orden_reposicion": "order-1",
            "id_operario": "operario-1",
        })
        self.database["ordenes_reposicion"].documents.append({
            "id_orden_reposicion": "order-1",
            "id_empresa": "empresa-1",
            "id_almacen": "almacen-1",
            "id_proveedor": "provider-1",
            "estado": "RECIBIDA",
        })
        self.database["proveedores"].documents.append({
            "id_proveedor": "provider-1",
            "nombre": "Proveedor TEST",
        })
        self.database["detalles_reposicion"].documents.append({
            "id_detalle_reposicion": "order-detail-1",
            "id_producto": "producto-1",
            "cantidad_solicitada": 100,
        })
        service = NotificationService(
            lambda: self.database,
            lambda *args: self.sent.append(args)
        )
        result = asyncio.run(service.enviar_resumen_reposicion("detail-1", "CRITICO", "MEDIO"))
        self.assertEqual(result["status"], "ENVIADO")
        self.assertIn("riesgo MEDIO", self.sent[0][7])
        self.assertIn("Empaque danado", self.sent[0][7])

    def test_smtp_failure_is_recorded_without_retrying_successfully(self):
        settings.email_enabled = True
        settings.smtp_host = "smtp.test"
        settings.smtp_user = "user"
        settings.smtp_password = "password"
        settings.smtp_from = "from@example.com"

        def failing_sender(*args):
            raise OSError("SMTP unavailable")

        service = NotificationService(lambda: self.database, failing_sender)
        result = asyncio.run(
            service.notify_owner(
                "event-failure",
                "empresa-1",
                "Subject",
                "Body"
            )
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("SMTP unavailable", result["error"])
        self.assertEqual(
            self.database["notificaciones_email"].documents[0]["status"],
            "ERROR"
        )

    def test_final_email_marks_low_risk_as_protected(self):
        settings.email_enabled = True
        settings.smtp_host = "smtp.test"
        settings.smtp_user = "user"
        settings.smtp_password = "password"
        settings.smtp_from = "from@example.com"
        self.database["detalles_recepcion"].documents.append({
            "id_detalle_recepcion": "detail-low",
            "id_recepcion": "reception-low",
            "id_detalle_reposicion": "order-detail-low",
            "id_inventario": "inventario-1",
            "id_rack": "rack-1",
            "cantidad_recibida": 10,
            "cantidad_aceptada": 10,
            "cantidad_rechazada": 0,
        })
        self.database["recepciones_mercaderia"].documents.append({
            "id_recepcion": "reception-low",
            "id_orden_reposicion": "order-low",
            "id_operario": "operario-1",
        })
        self.database["ordenes_reposicion"].documents.append({
            "id_orden_reposicion": "order-low",
            "id_empresa": "empresa-1",
            "id_almacen": "almacen-1",
            "id_proveedor": "provider-low",
            "estado": "RECIBIDA",
        })
        self.database["detalles_reposicion"].documents.append({
            "id_detalle_reposicion": "order-detail-low",
            "id_producto": "producto-1",
            "cantidad_solicitada": 10,
        })
        service = NotificationService(
            lambda: self.database,
            lambda *args: self.sent.append(args)
        )
        result = asyncio.run(
            service.enviar_resumen_reposicion(
                "detail-low",
                "CRITICO",
                "BAJO"
            )
        )
        self.assertEqual(result["status"], "ENVIADO")
        self.assertIn("riesgo bajo/protegido", self.sent[0][7])


class EmailVerificationServiceTests(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.database = FakeDatabase({
            "empresas": [{
                "id_empresa": "empresa-1",
                "correo": "dueno@empresa.test",
                "correo_verificado": False,
                "fecha_verificacion_correo": None,
            }],
            "operarios": [{
                "id_operario": "operario-1",
                "id_empresa": "empresa-1",
                "correo": "operario@operario.test",
                "correo_verificado": False,
                "fecha_verificacion_correo": None,
            }],
            "proveedores": [{
                "id_proveedor": "provider-1",
                "id_empresa": "empresa-1",
                "correo": "ventas@proveedor.test",
                "correo_verificado": False,
                "fecha_verificacion_correo": None,
            }],
            "recomendaciones": [{
                "id_recomendacion": "rec-1",
                "id_empresa": "empresa-1",
                "id_almacen": "almacen-1",
                "id_inventario": "inventario-1",
                "id_producto": "producto-1",
                "nivel_riesgo": "CRITICO",
                "cantidad_minima": 80,
                "cantidad_recomendada": 95,
                "cantidad_segura": 100,
                "forecast_7d": 12.5,
                "explicacion": "Reponer",
                "estado": "VALIDADA_OPERARIO",
            }],
            "almacenes": [{"id_almacen": "almacen-1", "id_empresa": "empresa-1", "nombre": "Principal"}],
            "productos": [{"id_producto": "producto-1", "nombre": "Producto TEST"}],
            "inventarios": [{"id_inventario": "inventario-1", "stock_actual": 18, "stock_minimo": 10, "stock_maximo": 200}],
            "notificaciones_email": [],
            "email_verifications": [],
        })

    def test_email_verification_success_and_reuse_block(self):
        service = EmailVerificationService(lambda: self.database, lambda *args, **kwargs: self.sent.append((args, kwargs)))
        code_response = asyncio.run(service.request_verification("empresa", "empresa-1", "dueno@empresa.test"))
        self.assertEqual(code_response["status"], "SENT")
        verification = code_response["verification"]
        self.assertNotIn("code_hash", verification)
        self.assertNotIn("plain_code", verification)
        stored_verification = self.database["email_verifications"].documents[0]
        self.assertTrue(stored_verification["code_hash"])
        code = self.sent[0][0][2].splitlines()[4]
        success = asyncio.run(service.verify_code("empresa", "empresa-1", "dueno@empresa.test", code))
        self.assertTrue(success["verified"])
        second = asyncio.run(service.verify_code("empresa", "empresa-1", "dueno@empresa.test", code))
        self.assertFalse(second["verified"])

    def test_naive_mongo_timestamps_keep_cooldown_working(self):
        service = EmailVerificationService(
            lambda: self.database,
            lambda *args, **kwargs: self.sent.append((args, kwargs)),
        )
        first = asyncio.run(
            service.request_verification(
                "empresa",
                "empresa-1",
                "dueno@empresa.test",
            )
        )
        self.assertEqual(first["status"], "SENT")

        stored = self.database["email_verifications"].documents[0]
        stored["expires_at"] = stored["expires_at"].replace(tzinfo=None)
        stored["cooldown_until"] = stored["cooldown_until"].replace(tzinfo=None)

        second = asyncio.run(
            service.request_verification(
                "empresa",
                "empresa-1",
                "dueno@empresa.test",
            )
        )

        self.assertEqual(second["status"], "COOLDOWN")
        self.assertGreaterEqual(second["remaining_seconds"], 0)
        self.assertEqual(len(self.sent), 1)

    def test_entity_verification_http_contract_is_safe(self):
        service = EmailVerificationService(
            lambda: self.database,
            lambda *args, **kwargs: self.sent.append((args, kwargs)),
        )
        sent = asyncio.run(
            service.request_entity_verification("operario", "operario-1")
        )
        self.assertEqual(sent["status"], "SENT")
        self.assertNotIn("code_hash", sent)
        self.assertNotIn("plain_code", sent)

        code = self.sent[0][0][2].splitlines()[4]
        verified = asyncio.run(
            service.verify_entity_code("operario", "operario-1", code)
        )
        self.assertTrue(verified["verified"])
        self.assertNotIn("entity", verified)
        self.assertNotIn("code_hash", verified)
        self.assertNotIn("plain_code", verified)

    def test_notification_blocks_unverified_empresa_email(self):
        settings.email_enabled = True
        settings.smtp_host = "smtp.test"
        settings.smtp_user = "user"
        settings.smtp_password = "password"
        settings.smtp_from = "from@example.com"
        service = NotificationService(lambda: self.database, lambda *args: self.sent.append(args))
        result = asyncio.run(service.enviar_solicitud_aprobacion("rec-1", "operario-1"))
        self.assertEqual(result["status"], "BLOQUEADA_EMAIL_NO_VERIFICADO")
        self.assertEqual(len(self.sent), 0)

    def test_email_change_invalidates_verification(self):
        service = EmailVerificationService(lambda: self.database, lambda *args, **kwargs: self.sent.append((args, kwargs)))
        first = asyncio.run(service.request_verification("proveedor", "provider-1", "ventas@proveedor.test"))
        code = self.sent[0][0][2].splitlines()[4]
        verify = asyncio.run(service.verify_code("proveedor", "provider-1", "ventas@proveedor.test", code))
        self.assertTrue(verify["verified"])
        update = asyncio.run(service.invalidate_on_email_change("proveedor", "provider-1", "ventas@proveedor.test", "ventas@nuevo-proveedor.test"))
        self.assertTrue(update["correo_verificado"] is False)
        leftover = asyncio.run(service.verify_code("proveedor", "provider-1", "ventas@nuevo-proveedor.test", code))
        self.assertFalse(leftover["verified"])


class OrderNotificationWiringTests(unittest.TestCase):
    # Contrato ROLES.md: validar (alias aprobar / enviar) pasa la
    # solicitud a ENVIADA; el correo es un aviso que nunca bloquea.

    def _service(self, estado, notificacion):
        from app.services.orden_reposicion_service import OrdenReposicionService

        service = OrdenReposicionService()
        service.repository.obtener_por_id = AsyncMock(return_value={
            "id_orden_reposicion": "order-1",
            "estado": estado,
        })
        service.repository.cambiar_estado = AsyncMock(return_value={
            "id_orden_reposicion": "order-1",
            "estado": "ENVIADA",
        })
        service.detalle_repository.obtener_por_orden = AsyncMock(
            return_value=[{"id_detalle_reposicion": "line-1"}]
        )
        service.notification_service.enviar_orden_proveedor = notificacion
        return service

    def test_approval_sends_order_and_notifies_provider_once(self):
        service = self._service(
            "PENDIENTE",
            AsyncMock(return_value={"status": "ENVIADO"}),
        )

        result = asyncio.run(service.aprobar("order-1"))

        self.assertEqual(result["estado"], "ENVIADA")
        service.repository.cambiar_estado.assert_awaited_once_with(
            "order-1",
            "ENVIADA",
        )
        service.notification_service.enviar_orden_proveedor.assert_awaited_once_with(
            "order-1"
        )

    def test_unverified_or_failing_email_never_blocks_sending(self):
        for notificacion in (
            AsyncMock(return_value={"status": "BLOQUEADA_EMAIL_NO_VERIFICADO"}),
            AsyncMock(side_effect=RuntimeError("SMTP caído")),
        ):
            service = self._service("APROBADA", notificacion)

            result = asyncio.run(service.enviar("order-1"))

            self.assertEqual(result["estado"], "ENVIADA")
            service.repository.cambiar_estado.assert_awaited_once()


class RecommendationDecisionTests(unittest.TestCase):
    def test_empresa_change_request_is_audited(self):
        from app.dto.recomendacion_dto import EmpresaCambiosRequest
        from app.services.recomendacion_service import RecomendacionService

        service = RecomendacionService()
        service.repository.obtener_por_id = AsyncMock(return_value={
            "id_recomendacion": "rec-1",
            "id_empresa": "empresa-1",
            "estado": "VALIDADA_OPERARIO",
        })
        service.repository.actualizar = AsyncMock(return_value={
            "id_recomendacion": "rec-1",
            "estado": "CAMBIOS_SOLICITADOS",
        })

        result = asyncio.run(service.solicitar_cambios(
            "rec-1",
            EmpresaCambiosRequest(
                id_empresa="empresa-1",
                comentario="Ajustar cantidad",
            ),
        ))

        self.assertEqual(result["estado"], "CAMBIOS_SOLICITADOS")
        update = service.repository.actualizar.await_args.args[1]
        self.assertEqual(update["solicitud_cambios"]["id_empresa"], "empresa-1")
        self.assertEqual(update["solicitud_cambios"]["estado_anterior"], "VALIDADA_OPERARIO")

    def test_final_approval_creates_and_approves_one_order(self):
        from app.dto.recomendacion_dto import EmpresaAprobacionRequest
        from app.services.recomendacion_service import RecomendacionService

        service = RecomendacionService()
        service.repository.obtener_por_id = AsyncMock(return_value={
            "id_recomendacion": "rec-1",
            "id_empresa": "empresa-1",
            "estado": "VALIDADA_OPERARIO",
        })
        service.repository.actualizar = AsyncMock(return_value={
            "id_recomendacion": "rec-1",
            "estado": "APLICADA",
        })
        service.orden_reposicion_service.repository.obtener_por_recomendacion = AsyncMock(
            return_value=None
        )
        service.crear_orden_desde_recomendacion = AsyncMock(return_value={
            "orden": {"id_orden_reposicion": "order-1"},
            "detalle": {"id_detalle_reposicion": "detail-1"},
        })
        service.orden_reposicion_service.aprobar = AsyncMock(return_value={
            "id_orden_reposicion": "order-1",
            "estado": "APROBADA",
        })

        result = asyncio.run(service.aprobar_por_empresa(
            "rec-1",
            EmpresaAprobacionRequest(
                id_empresa="empresa-1",
                id_proveedor="provider-1",
                costo_unitario=10,
            ),
        ))

        self.assertEqual(result["orden"]["estado"], "APROBADA")
        service.crear_orden_desde_recomendacion.assert_awaited_once()
        service.orden_reposicion_service.aprobar.assert_awaited_once_with("order-1")


if __name__ == "__main__":
    unittest.main()
