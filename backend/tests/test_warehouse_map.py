import asyncio
from datetime import datetime, timezone
from io import BytesIO

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from pypdf import PdfReader

from tests.test_google_auth import isolated_database
from tests.test_plano_reportes import sample
from app.dto.inventario_consulta_dto import InventarioFiltros
from app.dto.rack_dto import RackUpdate
from app.services.inventario_consulta_service import consultar_inventario
from app.services.inventario_reportes_service import preparar_datos
from app.services.inventario_reportes_archivos import generar_archivo
from app.services.jerarquia_service import JerarquiaService
from app.services.rack_service import RackService
from app.services.warehouse_map_service import nombres_productos, estado_nivel


def test_product_names_and_sensor_states():
    rows = [dict(id_nivel='n', producto='Papaya', stock_actual=4, ubicacion_valida=True)] * 2
    rows += [dict(id_nivel='n', producto='Rechazado', stock_actual=3, ubicacion_valida=True, rechazado=True),
             dict(id_nivel='n', producto='Agotado', stock_actual=0, ubicacion_valida=True)]
    assert nombres_productos(rows, 'n') == ['Papaya']
    assert nombres_productos(rows, 'empty') == []
    assert estado_nivel([], []) == 'sin_datos'
    assert estado_nivel([{'estado': {'conectado': False}}], []) == 'desconectado'
    assert estado_nivel([], [{'nivel_riesgo': 'ALTO'}]) == 'critico'
    assert estado_nivel([], [{'nivel_riesgo': 'MEDIO'}]) == 'advertencia'
    assert estado_nivel([], [{'nivel_riesgo': 'ALTO', 'estado': 'RESUELTA'}]) == 'sin_datos'
    assert estado_nivel([{'estado': {'conectado': True, 'ultima_lectura': {'ts': datetime.now(timezone.utc), 'hum': 50}}}], []) == 'normal'


def test_live_projection_real_mongodb_and_exports(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            _, operator, company, levels = await sample(db)
            await RackService().actualizar_rack('r', RackUpdate(tipo_rack='Selectivo'))
            await db.detalles_inventario.insert_one(dict(id_detalle_inventario='duplicate', id_inventario='i', id_producto='p', id_rack='r', id_nivel=levels[1]['id_nivel'], stock_actual=2))
            first = await consultar_inventario(company, InventarioFiltros(id_almacen='w'))
            assert first['racks'][0]['tipo_rack'] == 'Selectivo'
            assert next(n for n in first['niveles'] if n['id_nivel'] == levels[1]['id_nivel'])['productos'] == ['Mango Kent']
            assert next(n for n in first['niveles'] if n['id_nivel'] == levels[0]['id_nivel'])['productos'] == []
            # Another session changes stored stock and structure; the next read sees it.
            await db.detalles_inventario.update_many({'id_nivel': levels[1]['id_nivel']}, {'$set': {'id_nivel': levels[3]['id_nivel']}})
            await db.zonas.insert_one(dict(id_zona='new-zone', id_almacen='w', nombre='Zona nueva', capacidad=3))
            await db.racks.insert_one(dict(id_rack='new-rack', id_zona='new-zone', codigo='R02', max_niveles=1))
            await db.niveles.insert_one(dict(id_nivel='new-level', id_rack='new-rack', numero=1, codigo='N-1'))
            updated = await consultar_inventario(operator, InventarioFiltros(id_almacen='w'))
            assert any(z.get('id_zona') == 'new-zone' for z in updated['zonas'])
            assert any(r['id_rack'] == 'new-rack' and r['tipo_rack'] == 'Tipo no definido' for r in updated['racks'])
            assert next(n for n in updated['niveles'] if n['id_nivel'] == levels[1]['id_nivel'])['productos'] == []
            assert next(n for n in updated['niveles'] if n['id_nivel'] == levels[3]['id_nivel'])['productos'] == ['Mango Kent']
            company_read = await consultar_inventario(company, InventarioFiltros(id_almacen='w'))
            assert company_read['niveles'] == updated['niveles']
            with pytest.raises(HTTPException):
                await JerarquiaService.eliminar_nivel(company, levels[3]['id_nivel'])
            from app.dto.dispositivo_dto import DispositivoCreate
            from app.services.dispositivo_service import DispositivoService
            sensor = await DispositivoService.crear(DispositivoCreate(id_almacen='w', id_zona='new-zone', id_rack='new-rack', id_nivel='new-level', nombre='Sensor de prueba'), company)
            assert sensor['id_nivel'] == 'new-level'
            assert (await DispositivoService.regenerar_token(sensor['id_dispositivo'], company))['token']
            await db.alertas.insert_one(dict(id_alerta='critical-test', id_dispositivo=sensor['id_dispositivo'], id_empresa='e', id_almacen='w', id_nivel='new-level', origen='SENSOR', estado='ACTIVA', nivel_riesgo='ALTO', tipo_alerta='TEMPERATURA_FUERA_RANGO', inicio=datetime.now(timezone.utc)))
            alarmed = await consultar_inventario(company, InventarioFiltros(id_almacen='w'))
            assert next(n for n in alarmed['niveles'] if n['id_nivel'] == 'new-level')['monitoreo'] == 'critico'
            assert all(n['monitoreo'] != 'critico' for n in alarmed['niveles'] if n['id_nivel'] != 'new-level')
            with pytest.raises(HTTPException):
                await JerarquiaService.eliminar_nivel(company, 'new-level')
            await db.alertas.update_one({'id_alerta': 'critical-test'}, {'$set': {'estado': 'RESUELTA'}})
            resolved = await consultar_inventario(company, InventarioFiltros(id_almacen='w'))
            assert next(n for n in resolved['niveles'] if n['id_nivel'] == 'new-level')['monitoreo'] != 'critico'
            await db.dispositivos.delete_one({'id_dispositivo': sensor['id_dispositivo']})
            await db.alertas.delete_one({'id_alerta': 'critical-test'})
            await JerarquiaService.eliminar_nivel(company, 'new-level')
            assert not await db.niveles.find_one({'id_nivel': 'new-level'})
            assert await db.detalles_inventario.count_documents({}) == 4
            data = await preparar_datos(company, InventarioFiltros(id_almacen='w'))
            book = load_workbook(BytesIO(generar_archivo(data, 'xlsx')[0]))
            values = list(book['Plano'].values)
            assert any('Selectivo' in row and 'Mango Kent' in row for row in values)
            text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(generar_archivo(data, 'pdf')[0])).pages)
            assert 'Selectivo' in text and 'Mango Kent' in text and 'Zona nueva' in text
            from app.dto.saiki_dto import SaikiAskRequest
            from app.services.saiki_service import SaikiService
            await db.racks.update_one({'id_rack': 'r'}, {'$set': {'codigo': 'R01'}})
            await db.zonas.update_one({'id_zona': 'z'}, {'$set': {'nombre': 'Zona B'}})
            saiki = SaikiService()
            for question, expected in [
                ('¿Qué productos hay en el Nivel 4 del Rack R01?', 'Mango Kent'),
                ('¿Qué tipo de rack es el R01?', 'Selectivo'),
                ('¿Cuántos niveles tiene el Rack R01?', '4 niveles'),
                ('¿Qué niveles están vacíos?', 'Vacío'),
                ('¿Dónde está el Mango Kent?', 'Mango Kent'),
                ('¿Qué productos están en niveles con alertas?', 'No hay niveles'),
                ('¿Se agregó algún rack recientemente?', 'últimos 7 días'),
                ('¿Qué zonas tiene actualmente el almacén?', 'Zona nueva'),
            ]:
                response = await saiki.ask(SaikiAskRequest(message=question), company)
                assert expected in response['answer'], (question, response['answer'])
    asyncio.run(run())
