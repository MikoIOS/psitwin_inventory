import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import bcrypt
import httpx
import pytest
from fastapi import FastAPI, HTTPException

from app.config.settings import settings
from app.controllers.local_voice_controller import router
from app.dependencies.dependencies import require_empresa_u_operario as require_empresa
from app.dto.auth_dto import UsuarioActual
from app.dto.empresa_dto import EmpresaResponse
from app.repositories.lectura_repository import LecturaRepository
from app.services.dispositivo_service import DispositivoService
from app.services.local_voice_service import LocalVoiceService
from app.services.saiki_sensor_queries import period
from app.utils.security import hash_password, verify_password
from tests.test_google_auth import isolated_database


def test_old_reading_incident_has_its_own_lifecycle_and_keeps_connection_separate(monkeypatch):
    from app.services.sensores.monitoreo_service import MonitoreoService
    service = MonitoreoService()
    device = {'id_dispositivo': 's'}
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(settings, 'sensor_max_reading_age_seconds', 10)
    events = service._eventos_actualidad(device, now - timedelta(seconds=20), now)
    assert len(events) == 1 and events[0].tipo == 'LECTURA_DESACTUALIZADA'
    assert events[0].valor == 20 and events[0].limite == 10
    assert service._eventos_actualidad(device, now - timedelta(seconds=21), now) == []
    resolved = service._eventos_actualidad(device, now, now + timedelta(seconds=1))
    assert len(resolved) == 1 and resolved[0].evento == 'RESUELTA'
    assert service._eventos_actualidad(device, now, now + timedelta(seconds=2)) == []


def test_sensor_alert_index_preserves_inventory_and_separates_devices(monkeypatch):
    from app.database.mongodb import ensure_alert_indexes
    from pymongo.errors import DuplicateKeyError
    async def run():
        async with isolated_database(monkeypatch) as db:
            await db.alertas.create_index([('id_inventario', 1), ('id_producto', 1), ('id_detalle_inventario', 1), ('tipo_alerta', 1)],
                unique=True, partialFilterExpression={'estado': {'$in': ['ACTIVA', 'VISTA']}}, name='uq_alerta_activa_producto_ubicacion')
            await ensure_alert_indexes(db)
            await ensure_alert_indexes(db)
            incident = {'origen': 'SENSOR', 'id_inventario': None, 'id_producto': None, 'tipo_alerta': 'TEMPERATURA_FUERA_RANGO', 'parametro': 't_int', 'estado': 'ACTIVA'}
            await db.alertas.insert_one({**incident, 'id_dispositivo': 'sensor-a'})
            await db.alertas.insert_one({**incident, 'id_dispositivo': 'sensor-b'})
            with pytest.raises(DuplicateKeyError):
                await db.alertas.insert_one({**incident, 'id_dispositivo': 'sensor-a'})
            await db.alertas.update_one({'id_dispositivo': 'sensor-a'}, {'$set': {'estado': 'RESUELTA'}})
            await db.alertas.insert_one({**incident, 'id_dispositivo': 'sensor-a'})
            assert await db.alertas.count_documents({'id_dispositivo': 'sensor-a'}) == 2
    asyncio.run(run())


def test_passwords_support_unicode_over_bcrypt_limit_and_legacy():
    password = 'á' * 100
    hashed = hash_password(password)
    assert hashed.startswith('$argon2') and verify_password(password, hashed)
    assert not verify_password(password + 'x', hashed)
    legacy = bcrypt.hashpw(b'legacy-password', bcrypt.gensalt()).decode()
    assert verify_password('legacy-password', legacy)
    assert not verify_password('wrong', legacy)


def test_generic_active_alert_question_includes_sensors_without_inventory(monkeypatch):
    from app.services.saiki_service import SaikiService
    from app.dto.saiki_dto import SaikiAskRequest
    async def run():
        async with isolated_database(monkeypatch) as db:
            await db.alertas.insert_many([
                {'id_empresa': 'a', 'id_dispositivo': 'sensor-a', 'id_inventario': None, 'estado': 'ACTIVA', 'id_alerta': 'a'},
                {'id_empresa': 'b', 'id_dispositivo': 'sensor-b', 'id_inventario': None, 'estado': 'ACTIVA', 'id_alerta': 'b'},
                {'id_empresa': 'a', 'id_dispositivo': 'sensor-old', 'estado': 'RESUELTA', 'id_alerta': 'old'},
            ])
            response = await SaikiService().ask(SaikiAskRequest(message='¿Hay alertas activas?'), UsuarioActual(rol='EMPRESA', id_empresa='a'))
            assert [a['id_alerta'] for a in response['data']['get_active_alerts']] == ['a']
            assert '1 alerta' in response['answer']
    asyncio.run(run())


def test_company_bson_dates_and_missing_ceo():
    now = datetime.now(timezone.utc)
    company = EmpresaResponse(id_empresa='a', nombre='Antigua', ruc='20123456789', sector='Alimentos',
        correo='ceo@example.org', telefono='123456789', fecha_creacion=now, fecha_actualizacion=now,
        fecha_verificacion_correo=now)
    assert company.nombre_ceo is None
    assert company.fecha_creacion == now.isoformat()


def test_period_yesterday_uses_lima_and_midnight_boundaries():
    since, until = period('temperatura maxima de ayer', datetime(2026, 10, 25, 17, tzinfo=timezone.utc))
    assert since == datetime(2026, 10, 24, 5, tzinfo=timezone.utc)
    assert until == datetime(2026, 10, 25, 5, tzinfo=timezone.utc)


def test_history_is_paginated_scoped_and_stats_use_whole_period(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            start = datetime(2026, 10, 20, tzinfo=timezone.utc)
            for tenant in ('a', 'b'):
                await db.lecturas_minuto.insert_many([{'id_empresa': tenant, 'id_dispositivo': 'device',
                    'minuto': start + timedelta(minutes=i), 't_int': {'min': i, 'max': i + 1, 'suma': i * 2, 'n': 2}}
                    for i in range(5 if tenant == 'a' else 10)])
            rows, more = await LecturaRepository.pagina('a', 'device', start, start + timedelta(days=1), True, 1, 2)
            assert more and len(rows) == 2 and all(r['id_empresa'] == 'a' for r in rows)
            last, more = await LecturaRepository.pagina('a', 'device', start, start + timedelta(days=1), True, 3, 2)
            assert not more and len(last) == 1
            stats = await LecturaRepository.resumen('a', 'device', start, start + timedelta(days=1))
            assert stats['t_int'] == {'min': 0, 'max': 5, 'prom': 2, 'n': 10}
            monkeypatch.setattr(DispositivoService, 'obtener_documento', AsyncMock(side_effect=HTTPException(404, 'no autorizado')))
            with pytest.raises(HTTPException):
                await DispositivoService.lecturas('foreign', UsuarioActual(rol='EMPRESA', id_empresa='a'), start, start + timedelta(days=1))
    asyncio.run(run())


def test_voice_endpoints_require_auth_and_validate_without_inference():
    async def run():
        app = FastAPI()
        app.include_router(router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.get('/saiki/voice/config')).status_code in (401, 403)
            app.dependency_overrides[require_empresa] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='a')
            result = await client.get('/saiki/voice/config')
            assert {v['id'] for v in result.json()['voices']} == {'em_santa', 'em_alex'}
            for payload in ({'text': 'hola', 'voice': '../../x'}, {'text': ' '}, {'text': 'x' * 601}, {'text': 'hola', 'speed': 99}):
                assert (await client.post('/saiki/voice/synthesize', json=payload)).status_code == 422
            assert (await client.post('/saiki/voice/transcribe', content=b'x', headers={'Content-Type': 'audio/webm'})).status_code == 422
            assert (await client.post('/saiki/voice/transcribe', content=b'x', headers={'Content-Type': 'text/plain'})).status_code == 415
    asyncio.run(run())


def test_voice_disconnect_cancels_worker_inference(monkeypatch):
    import threading
    stopped = threading.Event()
    class Pipe:
        def write(self, data): pass
        def flush(self): pass
        def close(self): pass
        def readline(self, limit): stopped.wait(1); return b'{}'
    class Process:
        returncode = None
        stdin = Pipe()
        stdout = Pipe()
        killed = False
        def poll(self): return self.returncode
        def kill(self): self.killed = True; self.returncode = -1; stopped.set()
        def wait(self): return self.returncode
    class Request:
        async def is_disconnected(self): return True
    async def run():
        service = LocalVoiceService()
        process = Process()
        service.process = process
        with pytest.raises(HTTPException) as exc:
            await service.execute({'operation': 'synthesize', 'text': 'test'}, Request())
        assert exc.value.status_code == 408
        assert process.killed and service.process is None and not service.lock.locked()
    asyncio.run(run())


def test_voice_success_does_not_hang_when_disconnect_check_consumes_cancellation(monkeypatch):
    import threading
    entered = threading.Event()

    class Process:
        def poll(self): return None

    class Request:
        async def is_disconnected(self):
            entered.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                # Matches a disconnect check whose inner cancellation scope
                # consumes the watcher's cancellation.
                return False

    async def run():
        service = LocalVoiceService()
        service.process = Process()

        def exchange(*args):
            assert entered.wait(1)
            return {'audio': 'test'}

        monkeypatch.setattr(service, 'exchange', exchange)
        result = await asyncio.wait_for(service.execute({}, Request()), timeout=2)
        assert result == {'audio': 'test'} and not service.lock.locked()

    asyncio.run(run())
