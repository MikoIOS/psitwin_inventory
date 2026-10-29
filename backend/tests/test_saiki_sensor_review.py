"""Conversation checks against isolated MongoDB; live MQTT state is controlled."""
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pymongo.errors import ServerSelectionTimeoutError
from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest
from app.services.dispositivo_service import DispositivoService, monitoreo
from app.services.saiki_sensor_queries import period
from app.services.saiki_service import SaikiService
from tests.test_google_auth import isolated_database


CASES = [
    ('¿Qué sensores tiene el Rack A-01?', ['Temperatura interna', 'Humedad']),
    ('¿Cuál es la temperatura actual del Rack A-01?', ['Último valor registrado: 4', '°C']),
    ('¿Cuál es la temperatura del Rack A-02?', ['21.5', 'Temperatura ambiente']),
    ('¿Qué racks tienen sensores de humedad?', ['A-01', 'A-03']),
    ('¿Hay sensores desconectados?', ['Sensor antiguo', 'desconectado']),
    ('¿Cuál fue la temperatura máxima de ayer en el Rack A-01?', ['máximo 9', 'mínimo 2']),
    ('¿Cómo cambió la humedad en los últimos 7 días en el Rack A-01?', ['máximo 65', '4 mediciones']),
    ('¿Cuántas alertas de sensores hubo este mes?', ['2 alertas de sensores', 'RESUELTA']),
    ('¿Qué incidentes de sensores hubo este mes?', ['2 alertas de sensores', 'RESUELTA']),
    ('¿Qué sensores estuvieron fuera de rango este mes?', ['Temperatura alta', 'Rack A-01']),
    ('¿Cuál es la humedad del Rack A-03?', ['no es reciente', '70']),
    ('¿Qué sensores tiene el Rack VACIO?', ['No encontré sensores']),
]


@pytest.mark.parametrize('question,expected', CASES)
def test_sensor_questions_use_measured_data_and_keep_tenants_isolated(monkeypatch, question, expected):
    async def run():
        async with isolated_database(monkeypatch) as db:
            now = datetime.now(timezone.utc)
            midnight = now.astimezone(ZoneInfo('America/Lima')).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
            await db.almacenes.insert_many([{'id': 'warehouse', 'id_empresa': 'a', 'nombre': 'Almacén de prueba'}, {'id': 'foreign-warehouse', 'id_empresa': 'b'}])
            for rack_id, code in [('r1', 'A-01'), ('r2', 'A-02'), ('r3', 'A-03')]:
                await db.racks.insert_one({'id_rack': rack_id, 'id_zona': 'z', 'codigo': code})
            for device_id, name, rack, fields, tenant in [
                ('d1', 'Sensor frío', 'r1', ['t_int', 'hum'], 'a'),
                ('d2', 'Sensor ambiente', 'r2', ['t_amb'], 'a'),
                ('d3', 'Sensor antiguo', 'r3', ['hum'], 'a'),
                ('foreign', 'SECRETO_EMPRESA_B', 'foreign-rack', ['t_int'], 'b'),
            ]:
                await db.dispositivos.insert_one({'id_dispositivo': device_id, 'id_empresa': tenant,
                    'id_almacen': 'warehouse' if tenant == 'a' else 'foreign-warehouse', 'id_zona': 'z',
                    'id_rack': rack, 'nombre': name, 'parametros_disponibles': fields, 'activo': True})
            states = {
                'd1': {'conectado': True, 'ultima_lectura': {'ts': now, 't_int': 4, 'hum': 45}},
                'd2': {'conectado': True, 'ultima_lectura': {'ts': now, 't_amb': 21.5}},
                'd3': {'conectado': False, 'ultima_lectura': {'ts': now - timedelta(days=1), 'hum': 70}},
            }
            monkeypatch.setattr(monitoreo, 'estado', lambda identifier, *_: states.get(identifier, {}))
            # Minute aggregates: deliberately include an older point that must be excluded.
            for timestamp, low, high in [(midnight - timedelta(hours=12), 2, 9), (now - timedelta(days=2), 3, 6), (now - timedelta(days=8), -999, 999)]:
                await db.lecturas_minuto.insert_one({'id_empresa': 'a', 'id_dispositivo': 'd1', 'minuto': timestamp,
                    't_int': {'min': low, 'max': high, 'suma': low + high, 'n': 2},
                    'hum': {'min': 40, 'max': 65, 'suma': 105, 'n': 2}})
            for tenant, device, status in [('a', 'd1', 'ACTIVA'), ('a', 'd1', 'RESUELTA'), ('b', 'foreign', 'ACTIVA')]:
                await db.alertas.insert_one({'id_empresa': tenant, 'id_dispositivo': device, 'id_rack': 'r1',
                    'fecha_creacion': now - timedelta(minutes=1), 'estado': status, 'mensaje': 'Temperatura alta' if tenant == 'a' else 'SECRETO_EMPRESA_B', 'origen': 'SENSOR'})
            service = SaikiService()
            monkeypatch.setattr(service, '_ollama_chat', AsyncMock(side_effect=AssertionError('Operational sensor answers must use backend evidence')))
            response = await service.ask(SaikiAskRequest(message=question), UsuarioActual(rol='EMPRESA', id_empresa='a'))
            assert response['source'] == 'backend'
            for value in expected:
                assert value in response['answer']
            assert 'SECRETO_EMPRESA_B' not in response['answer']
            if '7 días' in question or 'ayer' in question:
                assert '999' not in response['answer']
    asyncio.run(run())


def test_last_seven_days_has_full_rolling_window():
    now = datetime(2026, 10, 27, 17, tzinfo=timezone.utc)
    start, end = period('humedad en los últimos 7 días', now)
    assert end == now and end - start == timedelta(days=7)


@pytest.mark.parametrize('hours', [1, 6, 24, 168])
def test_explorer_passes_selected_period_to_sensor_query(monkeypatch, hours):
    from app.services import saiki_sensor_queries
    query = AsyncMock(return_value=('Lecturas verificadas', {}))
    monkeypatch.setattr(saiki_sensor_queries, 'consultar_sensores', query)
    response = asyncio.run(SaikiService().ask(
        SaikiAskRequest(message='Explica el gráfico de temperatura: tendencia y umbrales',
                        id_dispositivo='d1', sensor_horas=hours),
        UsuarioActual(rol='EMPRESA', id_empresa='a')))
    assert response['answer'] == 'Lecturas verificadas'
    assert query.await_args.kwargs['horas'] == hours
    assert query.await_args.args[2] == 'd1'


def test_explorer_help_uses_platform_instructions():
    response = asyncio.run(SaikiService().ask(
        SaikiAskRequest(message='Explícame Explora tus sensores')))
    assert response['source'] == 'knowledge'
    assert 'Equipo, Medición y Periodo' in response['answer']


def test_sensor_database_error_is_not_reported_as_empty_inventory(monkeypatch):
    monkeypatch.setattr(DispositivoService, 'listar', AsyncMock(side_effect=ServerSelectionTimeoutError('test unavailable')))
    async def run():
        with pytest.raises(HTTPException) as error:
            await SaikiService().ask(SaikiAskRequest(message='¿Cuál es la temperatura del Rack A-01?'), UsuarioActual(rol='EMPRESA', id_empresa='a'))
        assert error.value.status_code == 503
        assert 'sensores' in error.value.detail and 'inventario' not in error.value.detail
    asyncio.run(run())
