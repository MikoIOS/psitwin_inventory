import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.saiki_intent_router import SaikiIntentRouter
from app.services.saiki_sensors import sensor_report


class SensorReportTests(unittest.IsolatedAsyncioTestCase):
    async def report(self, devices, incidents):
        with patch('app.services.saiki_sensors.DispositivoService.listar', new=AsyncMock(return_value=devices)) as listing, \
             patch('app.services.saiki_sensors.AlertaRepository.listar_por_empresa', new=AsyncMock(return_value=incidents)) as history, \
             patch('app.services.saiki_sensors.AlmacenRepository.obtener_por_id', new=AsyncMock(return_value={'nombre': 'Almacén Norte'})), \
             patch('app.services.saiki_sensors.ZonaRepository.obtener_por_id', new=AsyncMock(return_value={'nombre': 'Frío'})):
            user = SimpleNamespace(id_empresa='tenant')
            result = await sensor_report(user)
            listing.assert_awaited_once_with(user)
            history.assert_awaited_once_with('tenant')
            return result

    async def test_no_connection_does_not_claim_health(self):
        answer, data = await self.report([], [])
        self.assertIn('Sin datos disponibles', answer)
        self.assertEqual(data['incidentes'], [])

    async def test_scope_priority_recurrence_and_evidence(self):
        device = {'id_dispositivo': 'visible', 'nombre': 'Cámara 1', 'id_almacen': 'a', 'id_zona': 'z', 'estado': {'conectado': True, 'ultima_lectura': {'t_int': 12}}}
        base = {'id_dispositivo': 'visible', 'parametro': 't_int', 'valor': 12, 'limite': 5, 'fecha_creacion': '2026-10-20', 'mensaje': 'Temperatura alta'}
        incidents = [dict(base, id_alerta='1', estado='RESUELTA', nivel_riesgo='MEDIO'), dict(base, id_alerta='2', estado='ACTIVA', nivel_riesgo='CRITICO'), dict(base, id_dispositivo='other', mensaje='PRIVATE')]
        answer, data = await self.report([device], incidents)
        self.assertNotIn('PRIVATE', answer)
        self.assertEqual(data['historial_total'], 2)
        self.assertIn('Almacén Norte / Frío', answer)
        self.assertIn('valor observado: 12', answer)
        self.assertIn('calibrar', answer)
        self.assertIn('no confirma una avería', answer)

    async def test_anonymous_access_rejected(self):
        with self.assertRaises(ValueError):
            await sensor_report(None)

    def test_sensor_intent_precedes_inventory_history(self):
        for question in ['Historial de sensores', 'Recomienda mantenimiento de refrigeración', 'Humedad fuera de rango']:
            self.assertEqual(SaikiIntentRouter.classify(question).kind, 'sensors')
