"""End-to-end HTTP/ASGI routes, real JWT authorization and disposable MongoDB.

No production lifespan, MQTT broker, SMTP or production records are used.
"""
import asyncio
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI
from app.controllers import (producto_controller, movimiento_controller, dispositivo_controller,
    inventario_controller, detalle_inventario_controller, alerta_controller,
    analisis_controller, monitoreo_ws_controller)
from app.services import dispositivo_service
from app.services.sensores.monitoreo_service import MonitoreoService
from app.utils.security import create_access_token
from tests.test_google_auth import isolated_database


def application():
    app = FastAPI()
    for module in (producto_controller, movimiento_controller, dispositivo_controller,
                   inventario_controller, detalle_inventario_controller, alerta_controller,
                   analisis_controller, monitoreo_ws_controller):
        app.include_router(module.router, prefix='/api/v1')
    return app


def targeted(path):
    return not path.startswith('/api/v1/analisis/') or path.endswith('/historico')


def test_all_requested_http_routes_with_real_jwt_and_temporary_mongo(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            app = application()
            monitor = MonitoreoService()
            monkeypatch.setattr(dispositivo_service, 'monitoreo', monitor)
            monkeypatch.setattr(monitoreo_ws_controller, 'monitoreo', monitor)
            await db.empresas.insert_many([{'id_empresa': 'a'}, {'id_empresa': 'b'}])
            await db.almacenes.insert_many([{'id': 'w', 'id_empresa': 'a', 'nombre': 'Temporal'}, {'id': 'w2', 'id_empresa': 'a'}, {'id': 'foreign-w', 'id_empresa': 'b'}])
            await db.zonas.insert_many([{'id': 'z', 'id_almacen': 'w'}, {'id': 'z2', 'id_almacen': 'w2'}, {'id': 'foreign-z', 'id_almacen': 'foreign-w'}])
            await db.racks.insert_many([{'id_rack': r, 'id_zona': z, 'codigo': r, 'capacidad': 1000, 'estado': 'DISPONIBLE'} for r, z in [('r', 'z'), ('r2', 'z2'), ('foreign-r', 'foreign-z')]])
            await db.operarios.insert_one({'id_operario': 'op', 'id_empresa': 'a', 'id_almacen': 'w', 'estado': 'ACTIVO', 'nombre': 'Operario', 'apellido': 'Prueba'})
            await db.proveedores.insert_one({'id_proveedor': 'supplier', 'id_empresa': 'a', 'estado': 'ACTIVO'})
            tokens = {role: create_access_token(sub=subject, rol=role, id_empresa='a') for role, subject in [('EMPRESA', 'a'), ('OPERARIO', 'op'), ('PROVEEDOR', 'supplier')]}
            foreign_token = create_access_token(sub='b', rol='EMPRESA', id_empresa='b')
            specification = app.openapi()['paths']
            covered = set()
            records = []

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                async def call(method, path, *, role='EMPRESA', status=200, **kwargs):
                    if role is not None:
                        kwargs['headers'] = {'Authorization': 'Bearer ' + (foreign_token if role == 'FOREIGN' else tokens[role])}
                    response = await client.request(method, '/api/v1' + path, **kwargs)
                    records.append({'method': method, 'path': path, 'actor': role or 'anonymous', 'expected': status, 'actual': response.status_code})
                    assert response.status_code == status, f'{method} {path}: {response.status_code}: {response.text}'
                    if response.is_success:
                        for template in specification:
                            if method.lower() in specification[template] and re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', template), '/api/v1' + path):
                                # Static and dynamic paths can both match; select the actual route.
                                candidates = [(p, op) for p, op in specification.items() if method.lower() in op and re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', p), '/api/v1' + path)]
                                actual = min(candidates, key=lambda item: item[0].count('{'))[0]
                                covered.add((method, actual))
                                break
                    return response.json() if response.content else None

                product_body = {'nombre': 'Producto temporal', 'categoria': 'Tropicales', 'familia': 'Frutas', 'peso': 1, 'lead_time_dias': 2, 'vida_util_dias': 30}
                product = await call('POST', '/productos', role='PROVEEDOR', status=201, json={**product_body, 'id_empresa': 'b', 'id_proveedor': 'other'})
                p = product['id_producto']
                assert product['id_empresa'] == 'a' and product['id_proveedor'] == 'supplier'
                await call('POST', '/productos', status=403, json=product_body)
                await call('POST', '/productos', role='PROVEEDOR', status=422, json={**product_body, 'peso': 0})
                await call('PUT', f'/productos/{p}', role='PROVEEDOR', json={'marca': 'Prueba'})
                for invalid in ({'peso': 0}, {'peso': -1}, {'peso': 'Infinity'}, {'volumen': 0}, {'nombre': ''}, {'nombre': '   '}, {'nombre': None}, {'requiere_refrigeracion': None}):
                    await call('PUT', f'/productos/{p}', role='PROVEEDOR', status=422, json=invalid)
                await call('PUT', f'/productos/{p}', role='OPERARIO', json={'id_rack': 'r'})
                await call('PUT', f'/productos/{p}', role='OPERARIO', status=403, json={'nombre': 'No permitido'})
                header = await call('POST', '/inventarios', json={'id_almacen': 'w'})
                inventory = header['id_inventario']
                assert (await call('POST', '/inventarios', json={'id_almacen': 'w'}))['id_inventario'] == inventory
                detail = await call('POST', '/detalles-inventario', status=201, json={'id_inventario': inventory, 'id_producto': p, 'id_rack': 'r', 'stock_actual': 0, 'stock_minimo': 1, 'stock_maximo': 50})
                detail_id = detail['id_detalle_inventario']
                # Seed historical stock for route coverage; receipts are exercised in the procurement HTTP integration.
                await db.detalles_inventario.update_one({'id_detalle_inventario': detail_id}, {'$set': {'stock_actual': 10}})
                detail['stock_actual'] = 10
                # Real records belonging to a second tenant must never leak into lists.
                for collection, original, replacements in [
                    ('productos', product, {'id_producto': 'foreign-p', 'id_empresa': 'b', 'id_rack': 'foreign-r', 'nombre': 'PRIVATE_OTHER_TENANT'}),
                    ('inventarios', header, {'id_inventario': 'foreign-i', 'id_almacen': 'foreign-w'}),
                    ('detalles_inventario', detail, {'id_detalle_inventario': 'foreign-detail', 'id_inventario': 'foreign-i', 'id_producto': 'foreign-p', 'id_rack': 'foreign-r'}),
                ]:
                    record = {**original, **replacements}
                    for key in ('fecha_creacion', 'fecha_actualizacion'):
                        if isinstance(record.get(key), str): record[key] = datetime.fromisoformat(record[key])
                    await db[collection].insert_one(record)
                await call('PUT', f'/detalles-inventario/{detail_id}', role='OPERARIO', status=403, json={'stock_maximo': 40})
                await call('PUT', f'/detalles-inventario/{detail_id}', json={'stock_maximo': 40})
                await call('DELETE', f'/detalles-inventario/{detail_id}', role='OPERARIO', status=400)
                await call('DELETE', f'/productos/{p}', role='PROVEEDOR', status=409)
                body = {'id_inventario': inventory, 'id_detalle_inventario': detail_id, 'tipo_movimiento': 'SALIDA', 'motivo_movimiento': 'VENTA', 'cantidad': 3}
                movement = await call('POST', '/movimientos', role='OPERARIO', status=201, json=body)
                assert movement['stock_anterior'] == 10 and movement['stock_nuevo'] == 7
                assert movement['id_operario'] == 'op'
                await db.movimientos.insert_one({**movement, 'id_movimiento': 'foreign-movement', 'id_almacen': 'foreign-w', 'id_inventario': 'foreign-i', 'id_detalle_inventario': 'foreign-detail', 'id_producto': 'foreign-p', 'id_rack': 'foreign-r', 'fecha_hora': datetime.now(timezone.utc)})
                await call('POST', '/movimientos', role='OPERARIO', status=409, json={**body, 'cantidad': 100})
                await call('POST', '/movimientos', role='OPERARIO', status=422, json={**body, 'tipo_movimiento': 'ENTRADA', 'motivo_movimiento': 'RECEPCION'})
                await call('POST', '/movimientos', status=403, json=body)
                assert (await db.detalles_inventario.find_one({'id_detalle_inventario': detail_id}))['stock_actual'] == 7

                device = await call('POST', '/dispositivos', status=201, json={'id_almacen': 'w', 'id_zona': 'z', 'id_rack': 'r', 'nombre': 'Sensor temporal', 'limites': {'t_int': {'min': 2, 'max': 6, 'duracion_s': 0}}})
                device_id = device['id_dispositivo']
                old_token = device['token']
                assert 'token_hash' not in device
                updated = await call('PUT', f'/dispositivos/{device_id}', json={'nombre': 'Sensor actualizado'})
                assert updated['nombre'] == 'Sensor actualizado'
                new_token = await call('POST', f'/dispositivos/{device_id}/token')
                assert new_token['token'] != old_token
                topic = f'psitwin/dispositivos/{device_id}/lecturas'
                assert not await monitor.procesar_mensaje(topic, json.dumps({'token': old_token, 't_int': 4}))
                assert await monitor.procesar_mensaje(topic, json.dumps({'token': new_token['token'], 't_int': 4, 'hum': 40}))
                foreign_device = {**(await db.dispositivos.find_one({'id_dispositivo': device_id})), 'id_dispositivo': 'foreign-device', 'id_empresa': 'b', 'id_almacen': 'foreign-w', 'id_zona': 'foreign-z', 'id_rack': 'foreign-r'}
                foreign_device.pop('_id', None)
                await db.dispositivos.insert_one(foreign_device)
                assert 'token' not in await call('GET', f'/dispositivos/{device_id}')
                assert (await call('GET', f'/dispositivos/{device_id}'))['estado']['conectado']
                now = datetime.now(timezone.utc)
                await db.dispositivos.update_one({'id_dispositivo': device_id}, {'$set': {'parametros_disponibles': ['t_int', 'hum']}})
                for i in range(3):
                    await db.lecturas.insert_one({'meta': {'id_empresa': 'a', 'id_dispositivo': device_id}, 'ts': now - timedelta(minutes=3-i), 't_int': 3+i, 'hum': 40+i})
                    await db.lecturas_minuto.insert_one({'id_empresa': 'a', 'id_dispositivo': device_id, 'minuto': now - timedelta(minutes=3-i), 't_int': {'min': 3+i, 'max': 3+i, 'suma': 3+i, 'n': 1}})
                page = await call('GET', f'/dispositivos/{device_id}/lecturas', params={'limite': 2, 'tipo': 't_int'})
                assert len(page['puntos']) == 2 and page['hay_mas'] and page['resumen']['t_int']['max'] == 5
                assert 'hum' not in page['puntos'][0]
                last = await call('GET', f'/dispositivos/{device_id}/lecturas', params={'limite': 2, 'pagina': 2})
                assert len(last['puntos']) == 1 and not last['hay_mas']
                for days in (7, 30):
                    history = await call('GET', f'/dispositivos/{device_id}/lecturas', params={'desde': (now-timedelta(days=days)).isoformat(), 'hasta': now.isoformat()})
                    assert history['resolucion'] == 'minuto' and len(history['puntos']) == 3
                for params in ({'pagina': 0}, {'limite': 2001}, {'tipo': 'inventado'}, {'desde': (now+timedelta(days=1)).isoformat(), 'hasta': now.isoformat()}):
                    await call('GET', f'/dispositivos/{device_id}/lecturas', status=422, params=params)
                await call('GET', '/dispositivos', role='OPERARIO')
                for filters in ({'id_almacen': 'w'}, {'id_zona': 'z'}, {'id_rack': 'r'}, {'tipo': 't_int'}, {'id_almacen': 'w', 'id_zona': 'z', 'id_rack': 'r', 'tipo': 'hum'}):
                    selected = await call('GET', '/dispositivos', params=filters)
                    assert len(selected) == 1 and selected[0]['id_dispositivo'] == device_id
                await call('GET', '/dispositivos', role='PROVEEDOR', status=403)
                await call('POST', f'/dispositivos/{device_id}/token', role='OPERARIO', status=403)

                alert = await call('POST', '/alertas', status=201, json={'id_almacen': 'w', 'id_inventario': inventory, 'id_producto': p, 'id_detalle_inventario': detail_id, 'tipo_alerta': 'STOCK_BAJO', 'nivel_riesgo': 'ALTO', 'titulo': 'Alerta temporal', 'mensaje': 'Incidente para prueba aislada', 'stock_actual': 7})
                alert_id = alert['id_alerta']
                await db.alertas.insert_one({**alert, 'id_alerta': 'foreign-alert', 'id_empresa': 'b', 'id_almacen': 'foreign-w', 'id_producto': 'foreign-p', 'id_inventario': 'foreign-i', 'fecha_creacion': now, 'fecha_actualizacion': now})
                await call('PATCH', f'/alertas/{alert_id}/estado', json={'estado': 'VISTA'})
                # Every GET route in scope receives a valid, authenticated request.
                values = {'id_empresa': 'a', 'id_almacen': 'w', 'id_rack': 'r', 'id_inventario': inventory,
                          'id_detalle_inventario': detail_id, 'id_producto': p, 'id_operario': 'op',
                          'id_dispositivo': device_id, 'id_movimiento': movement['id_movimiento'],
                          'id_item': alert_id, 'categoria': 'Tropicales', 'nivel_riesgo': 'ALTO',
                          'tipo_movimiento': 'SALIDA', 'motivo_movimiento': 'VENTA'}
                for template, operations in specification.items():
                    if not targeted(template): continue
                    path = template.removeprefix('/api/v1').format(**values)
                    for method in operations:
                        # Anonymous requests must fail even for destructive methods.
                        await call(method.upper(), path, role=None, status=401, json={} if method not in ('get', 'delete') else None)
                    if 'get' in operations:
                        result = await call('GET', path)
                        assert 'PRIVATE_OTHER_TENANT' not in json.dumps(result)
                        assert 'foreign-movement' not in json.dumps(result)
                        assert 'foreign-device' not in json.dumps(result)
                        assert 'foreign-alert' not in json.dumps(result)
                        if path.endswith('/historial'):
                            assert result and any(row.get('id_operario') == 'op' for row in result)
                            stock_change = next(row for row in result if row.get('id_movimiento') == movement['id_movimiento'])
                            assert stock_change['stock_anterior'] == 10 and stock_change['stock_nuevo'] == 7
                        if path.startswith('/productos') and isinstance(result, list):
                            assert all(row['id_empresa'] == 'a' for row in result)
                # Another company cannot read object or history URLs by guessing IDs.
                for path in (f'/productos/{p}', '/productos/almacen/w', '/productos/rack/r', f'/inventarios/{inventory}',
                             f'/inventarios/{inventory}/historial', f'/detalles-inventario/{detail_id}/historial',
                             f'/movimientos/{movement["id_movimiento"]}', f'/dispositivos/{device_id}',
                             f'/dispositivos/{device_id}/lecturas', f'/alertas/{alert_id}'):
                    await call('GET', path, role='FOREIGN', status=404)
                for path in ('/productos', '/movimientos', '/inventarios', '/dispositivos', '/alertas'):
                    own = await call('GET', path, role='FOREIGN')
                    assert len(own) == 1
                for path in (f'/productos/{p}', f'/movimientos/{movement["id_movimiento"]}', f'/dispositivos/{device_id}', f'/alertas/{alert_id}'):
                    await call('GET', path.replace(p, 'missing') if p in path else path.rsplit('/', 1)[0] + '/missing', status=404)
                await call('GET', '/analisis/historico', status=403, params={'id_empresa': 'b'})
                await call('GET', '/analisis/historico', status=422, params={'fecha_inicio': '2026-10-02', 'fecha_fin': '2026-10-01'})

                await websocket_checks(app, monitor, tokens, device_id, new_token['token'], db, call)
                await call('PATCH', f'/alertas/{alert_id}/estado', json={'estado': 'RESUELTA'})
                await call('POST', '/movimientos', role='OPERARIO', status=201, json={**body, 'cantidad': 7})
                await call('DELETE', f'/detalles-inventario/{detail_id}', role='OPERARIO', status=409)
                disposable = await call('POST', '/productos', role='PROVEEDOR', status=201, json={**product_body, 'nombre': 'Producto sin movimientos'})
                empty = await call('POST', '/detalles-inventario', role='OPERARIO', status=201, json={'id_inventario': inventory, 'id_producto': disposable['id_producto'], 'id_rack': 'r', 'stock_actual': 0, 'stock_minimo': 0, 'stock_maximo': 0})
                await call('DELETE', f'/detalles-inventario/{empty["id_detalle_inventario"]}', role='OPERARIO')
                await call('DELETE', f'/productos/{disposable["id_producto"]}', role='PROVEEDOR')
                await call('DELETE', f'/dispositivos/{device_id}')
                await call('GET', f'/dispositivos/{device_id}', status=404)

                expected = {(method.upper(), path) for path, operations in specification.items() if targeted(path) for method in operations}
                assert expected <= covered, f'Endpoints without successful request: {expected-covered}'
                output = Path(__file__).resolve().parents[2] / 'artifacts/endpoint-review.local'
                output.mkdir(parents=True, exist_ok=True)
                (output / 'requests.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
                (output / 'coverage.json').write_text(json.dumps({'http_routes': len(expected), 'requests': len(records), 'successful_routes': sorted(f'{m} {p}' for m,p in covered), 'websocket': 'authentication, snapshot, tenant and warehouse filters, alert delivery, disconnect cleanup'}, indent=2), encoding='utf-8')
    asyncio.run(run())


async def websocket_checks(app, monitor, tokens, device_id, device_token, db, call):
    async def open_socket(token, zone=None):
        incoming, outgoing = asyncio.Queue(), asyncio.Queue()
        await incoming.put({'type': 'websocket.connect'})
        scope = {'type': 'websocket', 'asgi': {'version': '3.0'}, 'scheme': 'ws', 'path': '/api/v1/ws/monitoreo',
                 'raw_path': b'/api/v1/ws/monitoreo', 'root_path': '', 'query_string': urlencode({'token': token, **({'id_zona': zone} if zone else {})}).encode(),
                 'headers': [], 'client': ('127.0.0.1', 1234), 'server': ('test', 80), 'subprotocols': [], 'state': {}}
        task = asyncio.create_task(app(scope, incoming.get, outgoing.put))
        assert (await asyncio.wait_for(outgoing.get(), 2))['type'] == 'websocket.accept'
        return incoming, outgoing, task

    for token, code in [('', 4401), ('invalid', 4401), (tokens['PROVEEDOR'], 4403)]:
        _, outgoing, task = await open_socket(token)
        assert (await asyncio.wait_for(outgoing.get(), 2))['code'] == code
        await asyncio.wait_for(task, 2)
    for role, zone in (('EMPRESA', None), ('OPERARIO', None), ('EMPRESA', 'z')):
        incoming, outgoing, task = await open_socket(tokens[role], zone)
        try:
            snapshot = json.loads((await asyncio.wait_for(outgoing.get(), 2))['text'])
            assert snapshot['tipo'] == 'snapshot' and snapshot['dispositivos'][0]['id_dispositivo'] == device_id
            monitor._difundir({'id_empresa': 'b', 'id_almacen': 'foreign-w'}, {'tipo': 'alerta', 'private': True})
            if role == 'OPERARIO':
                monitor._difundir({'id_empresa': 'a', 'id_almacen': 'w2'}, {'tipo': 'lectura', 'private': True})
            if zone:
                monitor._difundir({'id_empresa': 'a', 'id_almacen': 'w', 'id_zona': 'other'}, {'tipo': 'lectura', 'private': True})
            monitor._difundir({'id_empresa': 'a', 'id_almacen': 'w', 'id_zona': 'z'}, {'tipo': 'alerta', 'evento': 'NUEVA', 'alerta': {'id_dispositivo': device_id}})
            event = json.loads((await asyncio.wait_for(outgoing.get(), 2))['text'])
            assert event['tipo'] == 'alerta' and not event.get('private')
        finally:
            await incoming.put({'type': 'websocket.disconnect', 'code': 1000})
            await asyncio.wait_for(task, 2)
            assert not monitor.suscriptores
    # Exercise the real detector -> MongoDB incident -> WebSocket -> resolution.
    incoming, outgoing, task = await open_socket(tokens['EMPRESA'])
    try:
        await asyncio.wait_for(outgoing.get(), 2)  # snapshot
        monitor.ultimo_ws[device_id] = time.monotonic()  # isolate alert events from reading throttling
        topic = f'psitwin/dispositivos/{device_id}/lecturas'
        for _ in range(3):
            assert await monitor.procesar_mensaje(topic, json.dumps({'token': device_token, 't_int': 8}))
        opened = json.loads((await asyncio.wait_for(outgoing.get(), 2))['text'])
        assert opened['tipo'] == 'alerta' and opened['evento'] == 'ABIERTA'
        assert opened['alerta']['valor'] == 8 and opened['alerta']['limite'] == 6
        assert opened['alerta']['id_lectura']
        assert await db.alertas.count_documents({'id_dispositivo': device_id}) == 1
        visible = await call('GET', '/alertas', params={'id_dispositivo': device_id, 'estado': 'ACTIVA'})
        assert len(visible) == 1 and visible[0]['id_alerta'] == opened['alerta']['id_alerta']
        assert await monitor.procesar_mensaje(topic, json.dumps({'token': device_token, 't_int': 4}))
        closed = json.loads((await asyncio.wait_for(outgoing.get(), 2))['text'])
        assert closed['evento'] == 'RESUELTA' and closed['alerta']['estado'] == 'RESUELTA'
        assert await db.alertas.count_documents({'id_dispositivo': device_id}) == 1
    finally:
        await incoming.put({'type': 'websocket.disconnect', 'code': 1000})
        await asyncio.wait_for(task, 2)
        assert not monitor.suscriptores
