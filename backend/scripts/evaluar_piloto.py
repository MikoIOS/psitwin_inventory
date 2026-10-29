"""Practical QA on an isolated Mongo database; every business datum is SIMULADO.

No production lifespan, SMTP delivery or MQTT publication is executed.
Retains the test DB for browser review; --cleanup removes only this run's DB.
"""
import asyncio
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.database import mongodb
from app.database.mongodb import ensure_alert_indexes
from app.main import app
from app.controllers import empresa_controller, dispositivo_controller, monitoreo_ws_controller, saiki_controller
from app.services import dispositivo_service, welcome_email_service
from app.services.registration_link_service import RegistrationLinkService
from app.services.sensores.monitoreo_service import MonitoreoService
from app.utils.security import create_access_token

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/piloto.local'
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = 'SIMULADO-Piloto-2026!'
results, questions, messages = [], [], []

def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k != '_id' and not any(s in k.lower() for s in ('password', 'token', 'secret', 'code_hash'))}
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, datetime): return value.isoformat()
    return str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value

def save():
    (OUT / 'pruebas.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'saiki.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding='utf-8')

def check(name, ok, actual, expected, status=None):
    results.append({'id': f'P{len(results)+1:03}', 'prueba': name, 'estado': status or ('Aprobado' if ok else 'Fallido'),
                    'esperado': expected, 'obtenido': clean(actual), 'datos': 'SIMULADOS'})
    save()

async def main():
    mongo = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await mongo.admin.command('ping')
    if '--cleanup' in sys.argv:
        manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
        name = manifest['database']
        assert re.fullmatch(r'psitwin_test_piloto_[a-f0-9]{32}', name)
        assert name != settings.mongodb_database
        await mongo.drop_database(name)
        manifest['cleanup_at'] = datetime.now(timezone.utc).isoformat()
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('CLEANUP OK: exclusively disposable pilot database', flush=True)
        mongo.close(); return
    name = 'psitwin_test_piloto_' + uuid4().hex
    assert name != settings.mongodb_database
    db = mongo[name]
    mongodb.client, mongodb.database = mongo, db
    before = {n: await db[n].count_documents({}) for n in await db.list_collection_names()}
    manifest = {'database': name, 'started_at': datetime.now(timezone.utc).isoformat(), 'initial_counts': before,
                'synthetic': True, 'smtp': 'CAPTURED, never external', 'mqtt': 'direct authenticated ingest, no physical hardware',
                'company_email': 'piloto.simulado@gmail.com', 'test_password': PASSWORD}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    await ensure_alert_indexes(db)
    monitor = MonitoreoService()
    dispositivo_service.monitoreo = monitor
    monitoreo_ws_controller.monitoreo = monitor
    empresa_controller.link_service = RegistrationLinkService(lambda: db, messages.append)
    empresa_controller.welcome_email_service = welcome_email_service.WelcomeEmailService(lambda: db, messages.append)
    welcome_email_service.send_message = messages.append
    settings.email_enabled = True
    settings.frontend_url = 'http://localhost:15174'
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    tokens = {}
    async with httpx.AsyncClient(transport=transport, base_url='http://piloto', timeout=45) as client:
        async def call(method, path, role='EMPRESA', expected=(200,), **kwargs):
            if role in tokens: kwargs['headers'] = {'Authorization': 'Bearer ' + tokens[role]}
            started = time.perf_counter()
            response = await client.request(method, '/api/v1' + path, **kwargs)
            try: value = response.json()
            except Exception: value = response.text[:500]
            row = {'id': f'P{len(results)+1:03}', 'prueba': f'{method} {path}', 'rol': role,
                   'esperado': list(expected), 'http': response.status_code, 'estado': 'Aprobado' if response.status_code in expected else 'Fallido',
                   'ms': round((time.perf_counter()-started)*1000, 2), 'obtenido': clean(value), 'datos': 'SIMULADOS'}
            results.append(row); save()
            print(row['id'], row['estado'], method, path, response.status_code, flush=True)
            return value

        body = dict(nombre='Tienda Piloto PsiTwin — SIMULADO', nombre_ceo='Piloto', ruc='20100070970', sector='Alimentos', telefono='999111222',
                    correo=manifest['company_email'], password=PASSWORD, password_confirmation=PASSWORD)
        company = await call('POST', '/auth/register', role=None, expected=(201,), json=body)
        company_id = company['id_empresa']
        await call('POST', '/auth/login', role=None, expected=(403,), json={'correo': body['correo'], 'password': PASSWORD})
        link = re.search(r'#token=([^\s]+)', messages[0].get_content())[1]
        await call('POST', '/auth/verification/confirm', role=None, json={'token': link})
        login = await call('POST', '/auth/login', role=None, json={'correo': body['correo'], 'password': PASSWORD})
        tokens['EMPRESA'] = login['access_token']
        settings.email_enabled = False
        check('Bienvenida personalizada capturada', len(messages) == 2 and 'Piloto' in messages[-1].get_body(preferencelist=('html',)).get_content(), len(messages), '2 mensajes: verificación + bienvenida')
        await call('GET', '/auth/me')
        warehouse = await call('POST', '/almacenes', expected=(201,), json={'nombre': 'Almacén principal SIMULADO', 'longitud': -77.03, 'latitud': -12.04, 'area_m2': 40, 'aforo': 8, 'tipo_almacen': 'Abarrotes SIMULADO'})
        wid = warehouse.get('id', warehouse.get('id_almacen'))
        zones, racks = {}, {}
        for label, codes, cold in [('Bebidas', ['A-01','A-02'], False), ('Alimentos', ['B-01'], False), ('Refrigerados', ['C-01'], True)]:
            zone = await call('POST', '/zonas', expected=(201,), json={'id_almacen': wid, 'nombre': label + ' SIMULADO', 'tipo_zona': label, 'capacidad': len(codes), 'refrigerada': cold, **({'temperatura_min': 2, 'temperatura_max': 6} if cold else {})})
            zid = zone.get('id', zone.get('id_zona')); zones[label] = zid
            for level, code in enumerate(codes, 1):
                rack = await call('POST', '/racks', expected=(201,), json={'id_zona': zid, 'codigo': code, 'nivel': level, 'capacidad': 1000, **({'temperatura_min':2,'temperatura_max':6} if cold else {})})
                racks[code] = rack['id_rack']
        await call('PUT', f'/almacenes/{wid}', json={'nombre': 'Almacén principal SIMULADO revisado'})
        supplier = await call('POST', '/proveedores', expected=(201,), json={'nombre': 'Proveedor SIMULADO', 'ruc':'20100070970','correo':'proveedor.piloto@example.com','password_temporal':PASSWORD,'tiempo_entrega_estimado_dias':2})
        operator = await call('POST', '/operarios', expected=(201,), json={'id_almacen':wid,'nombre':'Operario','apellido':'SIMULADO','correo':'operario.piloto@example.com','cargo':'Inventario','turno':'Día','password_temporal':PASSWORD})
        for role, email in [('PROVEEDOR','proveedor.piloto@example.com'),('OPERARIO','operario.piloto@example.com')]:
            raw = await call('POST','/auth/login',role=None,json={'correo':email,'password':PASSWORD})
            tokens[role] = raw['access_token']
            await call('PATCH','/auth/me/password',role=role,json={'password_actual':PASSWORD,'password_nueva':PASSWORD+'2'},expected=(200,))
            # Fresh token also verifies normal login after mandatory password change.
            raw = await call('POST','/auth/login',role=None,json={'correo':email,'password':PASSWORD+'2'})
            tokens[role] = raw['access_token']
        header = await call('POST','/inventarios',json={'id_almacen':wid}); iid=header['id_inventario']
        products, details = {}, {}
        catalog=[('Arroz',30,'B-01',1),('Azúcar',4,'B-01',1),('Leche',12,'C-01',1),('Aceite',0,'B-01',1),('Gaseosa',70,'A-01',0.5),('Agua',25,'A-02',0.6),('Yogur',8,'C-01',0.2),('Galletas',18,'B-01',0.1),('Conserva',9,'B-01',0.2),('Fideos',14,'B-01',0.5)]
        for index,(label,stock,code,weight) in enumerate(catalog,1):
            cold=code=='C-01'
            product = await call('POST','/productos',role='PROVEEDOR',expected=(201,),json={'nombre':label,'categoria':'Refrigerados' if cold else 'Abarrotes','familia':'SIMULADO','marca':'Marca SIMULADA','peso':weight,'lead_time_dias':2,'vida_util_dias':7 if cold else 180,'requiere_refrigeracion':cold,**({'temperatura_min_almacenamiento':2,'temperatura_max_almacenamiento':6} if cold else {}), 'sku':f'SIM-{index:03}','precio_compra':2.5,'precio_venta':3.5,'unidad_medida':'unidad'})
            pid=product['id_producto']; products[label]=pid
            await call('PUT',f'/productos/{pid}',role='OPERARIO',json={'id_rack':racks[code]})
            detail=await call('POST','/detalles-inventario',role='OPERARIO',expected=(201,),json={'id_inventario':iid,'id_producto':pid,'id_rack':racks[code],'stock_actual':stock,'stock_minimo':5,'stock_maximo':100})
            details[label]=detail['id_detalle_inventario']
        record=await db.productos.find_one({'id_producto':products['Arroz']})
        check('Persistencia de SKU/precios/unidad solicitados', all(k in record for k in ('sku','precio_compra','precio_venta','unidad_medida')), {k:record.get(k) for k in ('sku','precio_compra','precio_venta','unidad_medida')}, 'Campos no disponibles en DTO actual', status='No probado')
        check('Relaciones persistidas',await db.racks.count_documents({'id_zona':{'$in':list(zones.values())}})==4 and await db.productos.count_documents({'id_empresa':company_id})==10, {'racks':await db.racks.count_documents({}),'productos':await db.productos.count_documents({})},'4 racks / 10 productos')
        # Real purchase -> approval -> receipt -> stock entry, not a fake manual entry.
        order=await call('POST','/ordenes-reposicion',role='OPERARIO',expected=(201,),json={'id_proveedor':supplier['id_proveedor'],'lineas':[{'id_producto':products['Arroz'],'cantidad_solicitada':20,'costo_unitario':2.5}],'observacion':'SIMULADO recepción 20'})
        oid=order['id_orden_reposicion']
        order=await call('PATCH',f'/ordenes-reposicion/{oid}/validar')
        orderlines=await db.detalles_reposicion.find({'id_orden_reposicion':oid}).to_list(20)
        line=orderlines[0]['id_detalle_reposicion']
        receipt_body={'id_orden_reposicion':oid,'detalles':[{'id_detalle_reposicion':line,'id_inventario':iid,'id_detalle_inventario':details['Arroz'],'id_rack':racks['B-01'],'cantidad_recibida':20,'lote':'SIMULADO-001','fecha_vencimiento':(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()}]}
        await call('POST','/recepciones',role='OPERARIO',expected=(201,),json=receipt_body)
        async def stock(label):return (await db.detalles_inventario.find_one({'id_detalle_inventario':details[label]}))['stock_actual']
        check('Entrada arroz 30+20=50',await stock('Arroz')==50,await stock('Arroz'),50)
        await call('POST','/recepciones',role='OPERARIO',expected=(400,409),json=receipt_body)
        movement={'id_inventario':iid,'id_detalle_inventario':details['Arroz'],'tipo_movimiento':'SALIDA','motivo_movimiento':'VENTA','cantidad':8,'observacion':'SIMULADO venta'}
        await call('POST','/movimientos',role='OPERARIO',expected=(201,),json=movement)
        check('Venta arroz 50-8=42',await stock('Arroz')==42,await stock('Arroz'),42)
        for payload in ({**movement,'cantidad':999},{**movement,'cantidad':-1},{k:v for k,v in movement.items() if k!='id_detalle_inventario'}, {**movement,'id_detalle_inventario':'inexistente'}):
            await call('POST','/movimientos',role='OPERARIO',expected=(404,409,422),json=payload)
        for motive,kind in [('MERMA','SALIDA'),('VENCIMIENTO','SALIDA'),('CONTEO_FISICO','AJUSTE'),('DEVOLUCION','ENTRADA')]:
            await call('POST','/movimientos',role='OPERARIO',expected=(201,) if motive=='VENCIMIENTO' else (422,),json={**movement,'motivo_movimiento':motive,'tipo_movimiento':kind,'cantidad':1})
        # Duplicate sales are a pilot-risk probe, not an expected idempotency guarantee.
        duplicate={**movement,'id_detalle_inventario':details['Galletas'],'cantidad':1,'observacion':'SIMULADO misma solicitud repetida'}
        await call('POST','/movimientos',role='OPERARIO',expected=(201,),json=duplicate)
        await call('POST','/movimientos',role='OPERARIO',expected=(201,409),json=duplicate)
        check('Repetición de venta no descuenta dos veces',await stock('Galletas')==17,await stock('Galletas'),'17 si es idempotente; 16 indica repetición aplicada')
        concurrent={**movement,'id_detalle_inventario':details['Azúcar'],'cantidad':3}
        statuses=await asyncio.gather(*[client.post('/api/v1/movimientos',headers={'Authorization':'Bearer '+tokens['OPERARIO']},json=concurrent) for _ in range(2)])
        check('Dos salidas simultáneas no generan stock negativo',sorted(r.status_code for r in statuses)==[201,409] and await stock('Azúcar')==1,{'http':[r.status_code for r in statuses],'stock':await stock('Azúcar')},'201+409; stock=1')
        await call('POST','/detalles-inventario',role='OPERARIO',expected=(404,),json={'id_inventario':iid,'id_producto':products['Arroz'],'id_rack':'inexistente','stock_actual':0,'stock_minimo':0,'stock_maximo':100})
        check('Transferencias',False,'No hay endpoint de transferencia ni motivo TRANSFERENCIA','No fingir soporte',status='No probado')
        # Foreign tenant exists only in this disposable DB, with its own signed identity.
        await db.empresas.insert_one({'id_empresa':'otro-piloto-SIMULADO','nombre':'OTRA EMPRESA SIMULADA'})
        tokens['OTRA']=create_access_token(sub='otro-piloto-SIMULADO',rol='EMPRESA',id_empresa='otro-piloto-SIMULADO')
        for path in (f'/productos/{products["Arroz"]}',f'/inventarios/{iid}',f'/racks/{racks["C-01"]}'):
            await call('GET',path,role='OTRA',expected=(404,))
        # Simulated IoT payloads through the real authentication and incident engine.
        device=await call('POST','/dispositivos',expected=(201,),json={'nombre':'Sensor T/H SIMULADO','id_almacen':wid,'id_zona':zones['Refrigerados'],'id_rack':racks['C-01'],'limites':{'t_int':{'min':2,'max':6,'duracion_s':0},'hum':{'min':35,'max':65,'duracion_s':0}}})
        did=device['id_dispositivo']; secret=device['token']; topic=f'psitwin/dispositivos/{did}/lecturas'
        subscriber=monitor.suscribir(lambda device: device.get('id_empresa') == company_id)
        for label,reading in [('normal',{'t_int':4,'hum':50}),('alta',{'t_int':9,'hum':80}),('alta repetida',{'t_int':9,'hum':80}),('baja',{'t_int':1,'hum':20}),('recuperada',{'t_int':4,'hum':50}),('antigua',{'t_int':4,'ts':(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat()}),('conexión recuperada',{'t_int':4,'hum':50})]:
            accepted=await monitor.procesar_mensaje(topic,json.dumps({'token':secret,**reading}))
            check('Ingesta sensor '+label,accepted,accepted,True)
        await monitor._escribir()
        check('IoT persistido sin interpolación',await db.lecturas.count_documents({'meta.id_dispositivo':did})==7,await db.lecturas.count_documents({'meta.id_dispositivo':did}),7)
        check('Eventos proactivos producidos',subscriber.cola.qsize()>0,subscriber.cola.qsize(),'Eventos reales del backend ante lecturas SIMULADAS; no prueba audio físico')
        monitor.desuscribir(subscriber)
        for period in (1,24,168):
            await call('GET',f'/dispositivos/{did}/lecturas',params={'desde':(datetime.now(timezone.utc)-timedelta(hours=period)).isoformat(),'hasta':datetime.now(timezone.utc).isoformat()})
        await call('GET','/dispositivos',params={'id_rack':racks['C-01']})
        await call('GET','/dispositivos',params={'id_rack':racks['A-02']})
        await call('GET','/alertas')
        await call('GET',f'/inventarios/{iid}/historial')
        await call('GET',f'/forecast/almacenes/{wid}/productos/{products["Arroz"]}',params={'horizonte_dias':7})
        await call('GET','/analisis/modelo')
        await call('GET','/analisis/historico')
        await call('GET','/saiki/health')
        # Actual Ollama: no inference replacement. Sources and raw replies are retained.
        prompts=[
          '¿Cuántos productos tengo registrados?','¿Qué productos están por agotarse?','¿Cuántas unidades de arroz tengo?',
          '¿En qué rack está almacenada la leche?','¿Qué productos están agotados?','¿Cuál es el stock total del arroz?',
          '¿Qué productos necesitan reposición?','¿Cuáles son los productos con mayor stock?',
          '¿Cuántas unidades de arroz vendí hoy?','¿Qué productos tuvieron más salidas esta semana?',
          '¿Cuántas entradas de mercadería se registraron?','¿Cuál fue el último movimiento de inventario?',
          '¿Qué productos tuvieron ajustes?','¿Cuántas unidades ingresaron al almacén?','¿Qué movimientos se realizaron ayer?',
          '¿Cuántos racks tengo?','¿Qué productos están en el Rack A-01?','¿Qué racks pertenecen a la zona de bebidas?',
          '¿Dónde se encuentra el arroz?','¿Qué racks tienen sensores instalados?',
          '¿Cuál es la temperatura actual del Rack C-01?','¿Qué sensores tiene el Rack A-01?',
          '¿Hay temperaturas fuera de rango?','¿Cuál fue la temperatura máxima de ayer?','¿Qué sensores están desconectados?',
          '¿Cómo cambió la humedad durante el día?','¿Se detectó movimiento en el almacén?','¿Qué alertas de sensores están activas?',
          '¿Cuánto arroz podría vender la próxima semana?','¿Qué productos necesitaré reponer pronto?',
          '¿Cuál es la demanda estimada de leche?','¿Qué producto podría agotarse primero?','¿Cuántas unidades debería comprar?',
          '¿Qué productos presentan mayor demanda?','¿Cómo registro un producto?','¿Cómo creo un rack?',
          '¿Cómo agrego un sensor?','¿Cómo registro una venta?','¿Cómo consulto los movimientos?','¿Cómo veo las alertas?',
          '¿Cómo interpreto los pronósticos?','¿Cuántos operarios tengo?',
          '¿Qué productos tengo en un almacén inexistente?','¿Cuál fue la temperatura de un sensor sin lecturas?',
          '¿Cuánto vendí en un período sin registros?','Hola, ¿qué puedes hacer por mi tienda?']
        for question in prompts:
            start=time.perf_counter()
            try:
                response=await asyncio.wait_for(client.post('/api/v1/saiki/ask',headers={'Authorization':'Bearer '+tokens['EMPRESA']},json={'message':question,'id_almacen':wid}),timeout=55)
                payload=response.json()
                entry={'pregunta':question,'http':response.status_code,'ms':round((time.perf_counter()-start)*1000,2),'respuesta':clean(payload)}
            except Exception as error:
                entry={'pregunta':question,'ms':round((time.perf_counter()-start)*1000,2),'error':type(error).__name__}
            questions.append(entry);save()
            print('SAIKI',len(questions),entry.get('http',entry.get('error')),entry['ms'],question,flush=True)
        # Ground truth and redacted full snapshots support independent review.
        snapshot={collection:clean(await db[collection].find({}).to_list(20000)) for collection in await db.list_collection_names()}
        (OUT/'mongo_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest.update(company_id=company_id,warehouse_id=wid,zones=zones,racks=racks,products=products,details=details,inventory_id=iid,device_id=did,
                        final_counts={key:len(value) for key,value in snapshot.items()},final_stock={label:await stock(label) for label in products},finished_at=datetime.now(timezone.utc).isoformat())
        (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print('COMPLETE',len(results),'checks',len(questions),'questions',flush=True)
    mongo.close()

if __name__=='__main__': asyncio.run(main())
