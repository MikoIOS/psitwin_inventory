import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.dto.auth_dto import UsuarioActual
from app.dto.abastecimiento_dto import OfertaRequest, NivelRequest, DecisionPendiente
from app.dto.orden_reposicion_dto import OrdenReposicionCreate, DespachoRequest
from app.dto.recepcion_mercaderia_dto import RecepcionMercaderiaCreate
from app.services.oferta_service import OfertaService
from app.services.abastecimiento_service import AbastecimientoService
from app.services.recepcion_mercaderia_service import RecepcionMercaderiaService
from app.services.analisis_service import AnalisisService
from app.services.jerarquia_service import JerarquiaService
from tests.test_google_auth import isolated_database


async def seed(db):
    now = datetime.now(timezone.utc)
    await db.empresas.insert_one({'id_empresa': 'e', 'nombre': 'Prueba'})
    await db.almacenes.insert_one({'id': 'w', 'id_empresa': 'e', 'nombre': 'Almacén'})
    await db.zonas.insert_one({'id': 'z', 'id_empresa': 'e', 'id_almacen': 'w', 'capacidad': 3, 'max_racks': 3})
    await db.racks.insert_one({'id_rack': 'r', 'id_zona': 'z', 'codigo': 'R1', 'nivel': 1, 'max_niveles': 4,
        'capacidad': 1000, 'estado': 'DISPONIBLE', 'fecha_creacion': now, 'fecha_actualizacion': now})
    await db.proveedores.insert_one({'id_proveedor': 'v', 'id_empresa': 'e', 'nombre': 'Proveedor de prueba', 'estado': 'ACTIVO', 'telefono': '987654321'})
    await db.operarios.insert_one({'id_operario': 'o', 'id_empresa': 'e', 'id_almacen': 'w', 'estado': 'ACTIVO', 'nombre': 'Operario'})
    await db.productos.insert_one({'id_producto': 'p', 'id_empresa': 'e', 'id_proveedor': 'v', 'nombre': 'Mango Kent',
        'familia': 'Frutas', 'categoria': 'Tropicales', 'unidad': 'kg', 'activo': True, 'peso': 1,
        'requiere_refrigeracion': False, 'lead_time_dias': 1, 'vida_util_dias': 10})
    await db.inventarios.insert_one({'id_inventario': 'i', 'id_almacen': 'w'})
    await db.detalles_inventario.insert_one({'id_detalle_inventario': 'di', 'id_inventario': 'i', 'id_producto': 'p', 'id_rack': 'r',
        'stock_actual': 0, 'stock_minimo': 0, 'stock_maximo': 100, 'fecha_creacion': now, 'fecha_actualizacion': now})
    return (UsuarioActual(rol='PROVEEDOR', id_empresa='e', id_proveedor='v'),
            UsuarioActual(rol='OPERARIO', id_empresa='e', id_almacen='w', id_operario='o'),
            UsuarioActual(rol='EMPRESA', id_empresa='e'))


def order(quantity=20, key='order-test-001'):
    return OrdenReposicionCreate(id_empresa='e', id_almacen='w', id_proveedor='v', clave_idempotencia=key,
        lineas=[{'id_producto': 'p', 'cantidad_solicitada': quantity}])


def test_offer_reservation_price_snapshot_cancellation_and_concurrency(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='4.50', cantidad_total=100), supplier)
            created = await AbastecimientoService.crear(order(20.5), 'o')
            assert created['total_centimos'] == 9225
            assert (await OfertaService.listar(operator, True))[0]['cantidad_disponible'] == 79.5
            again = await AbastecimientoService.crear(order(20.5), 'o')
            assert again['id_orden_reposicion'] == created['id_orden_reposicion']
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='6.00', cantidad_total=100), supplier)
            line = await db.detalles_reposicion.find_one({'id_orden_reposicion': created['id_orden_reposicion']})
            assert line['precio_centimos'] == 450
            attempts = await asyncio.gather(*(AbastecimientoService.crear(order(60, f'parallel-{i}'), 'o') for i in range(2)), return_exceptions=True)
            assert sum(isinstance(r, dict) for r in attempts) == 1
            await AbastecimientoService.transicion(created['id_orden_reposicion'], {'PENDIENTE'}, 'CANCELADA', company, 'Rechazada')
            assert (await OfertaService.listar(operator))[0]['cantidad_reservada'] == 60
            assert await db.ordenes_reposicion.count_documents({}) == 2
    asyncio.run(run())


@pytest.mark.parametrize('received,rejected,accepted', [(20, 0, 20), (15, 0, 15), (20, 5, 15), (20, 20, 0), (.3, .2, .1)])
def test_dispatch_receipt_updates_only_accepted_stock_and_analytics(monkeypatch, received, rejected, accepted):
    async def run():
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            monkeypatch.setattr('app.services.detalle_recepcion_service.DetalleRecepcionService._obtener_riesgo', AsyncMock(return_value=None))
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='4.50', cantidad_total=100), supplier)
            created = await AbastecimientoService.crear(order(), 'o')
            identifier = created['id_orden_reposicion']
            assert not (await AnalisisService().filters(company))['productos']
            await AbastecimientoService.transicion(identifier, {'PENDIENTE'}, 'ENVIADA', company)
            line = await db.detalles_reposicion.find_one({'id_orden_reposicion': identifier})
            dispatch = DespachoRequest(clave_idempotencia='dispatch-test-01', lineas=[{'id_detalle_reposicion': line['id_detalle_reposicion'], 'cantidad': 20}])
            await AbastecimientoService.despacho(identifier, dispatch, supplier)
            await AbastecimientoService.despacho(identifier, dispatch, supplier)
            assert len((await AbastecimientoService.obtener(identifier))['despachos']) == 1
            data = RecepcionMercaderiaCreate(id_orden_reposicion=identifier, clave_idempotencia='receipt-test-001', detalles=[{
                'id_detalle_reposicion': line['id_detalle_reposicion'], 'id_inventario': 'i', 'id_detalle_inventario': 'di',
                'cantidad_recibida': received, 'cantidad_rechazada': rejected,
                'estado_recepcion': 'RECHAZADO' if rejected == received else 'CONFORME',
                'motivo_rechazo': 'Producto deteriorado' if rejected else None}])
            result = await RecepcionMercaderiaService().crear(data, operator)
            assert (await db.detalles_inventario.find_one({'id_detalle_inventario': 'di'}))['stock_actual'] == accepted
            # Fresh request objects reproduce a network retry, not mutated DTO state.
            data.detalles[0].id_detalle_inventario = 'di'
            duplicate = await RecepcionMercaderiaService().crear(data, operator)
            assert duplicate['id_recepcion'] == result['id_recepcion']
            assert await db.movimientos.count_documents({}) == (1 if accepted else 0)
            assert bool((await AnalisisService().filters(company))['productos']) == bool(accepted)
            rows = await AbastecimientoService.pendientes(company)
            assert rows[0]['faltante'] == 20 - accepted
    asyncio.run(run())


def test_levels_have_real_parent_limits_and_cannot_be_deleted_with_inventory(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            _, _, company = await seed(db)
            levels = [await JerarquiaService.crear_nivel(company, 'r', NivelRequest(codigo=f'N{i}', numero=i)) for i in range(1, 5)]
            with pytest.raises(HTTPException):
                await JerarquiaService.crear_nivel(company, 'r', NivelRequest(codigo='N5', numero=5))
            await db.detalles_inventario.update_one({'id_detalle_inventario': 'di'}, {'$set': {'id_nivel': levels[0]['id_nivel']}})
            with pytest.raises(HTTPException):
                await JerarquiaService.eliminar_nivel(company, levels[0]['id_nivel'])
    asyncio.run(run())


@pytest.mark.parametrize('body', [dict(unidad='unidad', precio='4.50', cantidad_total=1.5), dict(unidad='kg', precio='0', cantidad_total=10), dict(unidad='kg', precio='-1', cantidad_total=10), dict(unidad='kg', precio='2', cantidad_total=-1)])
def test_invalid_offers_rejected(body):
    with pytest.raises(ValidationError):
        OfertaRequest(id_producto='p', **body)


def test_history_filters_real_dates_cancellations_and_saiki_cost(monkeypatch):
    async def run():
        from app.services.pedidos_history_service import historial_pedidos
        from app.services.saiki_abastecimiento import explicar_abastecimiento
        from app.dto.saiki_dto import SaikiAskRequest
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='4.50', cantidad_total=100), supplier)
            first = await AbastecimientoService.crear(order(10, 'history-first'), 'o')
            second = await AbastecimientoService.crear(order(5, 'history-second'), 'o')
            await db.ordenes_reposicion.update_one({'id_orden_reposicion': first['id_orden_reposicion']}, {'$set': {'fecha_orden': datetime(2026, 1, 2, 17, tzinfo=timezone.utc)}})
            await db.ordenes_reposicion.update_one({'id_orden_reposicion': second['id_orden_reposicion']}, {'$set': {'fecha_orden': datetime(2026, 1, 12, 17, tzinfo=timezone.utc)}})
            result = await historial_pedidos(operator, 'p', 'v', '2026-01-01', '2026-01-31')
            assert [r['dia'] for r in result['registros']] == ['2026-01-02', '2026-01-12']
            assert result['totales_por_unidad'] == {'kg': 15}
            assert not (await historial_pedidos(operator, provider='other'))['registros']
            answer, evidence = await explicar_abastecimiento(SaikiAskRequest(message='Cuánto cuestan 20 kg de Mango Kent', id_producto='p'), operator)
            assert '90.00 PEN' in answer
            assert evidence['ofertas'][0]['cantidad_disponible'] == 85
            answer, _ = await explicar_abastecimiento(SaikiAskRequest(message='Explícame el historial de pedidos', id_producto='p'), operator)
            assert '10 días' in answer
            await AbastecimientoService.transicion(first['id_orden_reposicion'], {'PENDIENTE'}, 'CANCELADA', company, 'No requerido')
            assert len((await historial_pedidos(operator))['registros']) == 1
            assert len((await historial_pedidos(operator, cancelled=True))['registros']) == 2
            foreign = UsuarioActual(rol='OPERARIO', id_empresa='e', id_operario='o2', id_almacen='other')
            assert not (await historial_pedidos(foreign))['registros']
    asyncio.run(run())


def test_partial_dispatch_over_receipt_and_company_closure(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='4.50', cantidad_total=100), supplier)
            created = await AbastecimientoService.crear(order(), 'o')
            identifier = created['id_orden_reposicion']
            line = await db.detalles_reposicion.find_one({'id_orden_reposicion': identifier})
            dispatch = DespachoRequest(clave_idempotencia='partial-dispatch', lineas=[{'id_detalle_reposicion': line['id_detalle_reposicion'], 'cantidad': 10}])
            with pytest.raises(HTTPException):
                await AbastecimientoService.despacho(identifier, dispatch, supplier)
            await AbastecimientoService.transicion(identifier, {'PENDIENTE'}, 'ENVIADA', company)
            await AbastecimientoService.despacho(identifier, dispatch, supplier)
            receipt = RecepcionMercaderiaCreate(id_orden_reposicion=identifier, detalles=[{'id_detalle_reposicion': line['id_detalle_reposicion'], 'id_inventario': 'i', 'id_detalle_inventario': 'di', 'cantidad_recibida': 11, 'estado_recepcion': 'CONFORME'}])
            with pytest.raises(HTTPException):
                await RecepcionMercaderiaService().crear(receipt, operator)
            assert (await db.detalles_inventario.find_one({'id_detalle_inventario': 'di'}))['stock_actual'] == 0
            await AbastecimientoService.resolver(identifier, DecisionPendiente(decision='MANTENER', motivo='Esperar siguiente entrega'), company)
            assert (await OfertaService.listar(operator))[0]['cantidad_reservada'] == 10
            await AbastecimientoService.resolver(identifier, DecisionPendiente(decision='CERRAR', motivo='Cancelar saldo'), company)
            assert (await OfertaService.listar(operator))[0]['cantidad_reservada'] == 0
            with pytest.raises(HTTPException):
                await AbastecimientoService.despacho(identifier, dispatch.model_copy(update={'clave_idempotencia': 'another-dispatch'}), supplier)
    asyncio.run(run())


def test_migration_is_readonly_then_backed_up_idempotent_and_preserves_stock(monkeypatch, tmp_path):
    async def run():
        from scripts.migrar_abastecimiento import plan, apply
        async with isolated_database(monkeypatch) as db:
            await seed(db)
            await db.detalles_inventario.update_one({'id_detalle_inventario': 'di'}, {'$set': {'stock_actual': 12.5}})
            operations, levels = await plan(db)
            assert levels and operations
            assert not await db.niveles.count_documents({})
            await apply(db, tmp_path / 'before')
            detail = await db.detalles_inventario.find_one({'id_detalle_inventario': 'di'})
            assert detail['stock_actual'] == 12.5 and detail['id_nivel']
            assert (tmp_path / 'before' / 'detalles_inventario.json').exists()
            assert await plan(db) == ([], [])
            await apply(db, tmp_path / 'second')
            assert await db.niveles.count_documents({}) == 1
            assert await db.ofertas_proveedor.count_documents({}) == 0
    asyncio.run(run())


def test_purchase_forecast_keeps_gaps_and_requires_accepted_entry(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            await OfertaService.guardar(OfertaRequest(id_producto='p', unidad='kg', precio='4.50', cantidad_total=100), supplier)
            for day in (2, 12):
                created = await AbastecimientoService.crear(order(10, f'forecast-{day}'), 'o')
                await db.ordenes_reposicion.update_one({'id_orden_reposicion': created['id_orden_reposicion']}, {'$set': {'fecha_orden': datetime(2026, 1, day, 17, tzinfo=timezone.utc)}})
            analysis = AnalisisService()
            before = await analysis.series(company, 'w', 'p', source='solicitudes')
            assert before.estado == 'SIN_HISTORIAL' and before.historico == []
            await db.movimientos.insert_one({'id_almacen': 'w', 'id_producto': 'p', 'tipo_movimiento': 'ENTRADA', 'motivo_movimiento': 'RECEPCION', 'cantidad': 1})
            result = await analysis.series(company, 'w', 'p', source='solicitudes')
            assert result.estado == 'HISTORIAL_INSUFICIENTE'
            assert len(result.historico) == 2 and not result.predicciones
            assert result.unidad == 'kg' and result.fuente_demanda == 'SOLICITUDES_ABASTECIMIENTO'
            assert [r.cantidad for r in result.historico] == [10, 10]
    asyncio.run(run())


def test_http_complete_flow_and_role_boundaries(monkeypatch):
    async def run():
        import httpx
        from fastapi import FastAPI, Request
        from app.dependencies.dependencies import get_usuario_activo
        from app.controllers import abastecimiento_controller, orden_reposicion_controller, recepcion_mercaderia_controller, detalle_inventario_controller
        from app.services.notification_service import NotificationService
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            monkeypatch.setattr(NotificationService, 'enviar_orden_proveedor', AsyncMock())
            monkeypatch.setattr('app.services.detalle_recepcion_service.DetalleRecepcionService._obtener_riesgo', AsyncMock(return_value=None))
            app = FastAPI()
            for controller in (abastecimiento_controller, orden_reposicion_controller, recepcion_mercaderia_controller, detalle_inventario_controller):
                app.include_router(controller.router)
            users = {'PROVEEDOR': supplier, 'OPERARIO': operator, 'EMPRESA': company}
            async def identity(request: Request):
                return users[request.headers['x-test-role']]
            app.dependency_overrides[get_usuario_activo] = identity
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                async def call(method, path, role, body=None):
                    return await client.request(method, path, headers={'x-test-role': role}, json=body)
                offer = {'id_producto': 'p', 'unidad': 'kg', 'precio': '4.50', 'cantidad_total': 100}
                assert (await call('PUT', '/abastecimiento/ofertas', 'OPERARIO', offer)).status_code == 403
                assert (await call('PUT', '/abastecimiento/ofertas', 'PROVEEDOR', offer)).status_code == 200
                body = {'id_proveedor': 'v', 'clave_idempotencia': 'http-order-key', 'lineas': [{'id_producto': 'p', 'cantidad_solicitada': 20, 'costo_unitario': .01}]}
                response = await call('POST', '/ordenes-reposicion', 'OPERARIO', body)
                assert response.status_code == 201, response.text
                identifier = response.json()['id_orden_reposicion']
                assert response.json()['total_centimos'] == 9000
                assert (await call('PATCH', f'/ordenes-reposicion/{identifier}/validar', 'OPERARIO')).status_code == 403
                assert (await call('PATCH', f'/ordenes-reposicion/{identifier}/validar', 'EMPRESA')).status_code == 200
                line = await db.detalles_reposicion.find_one({'id_orden_reposicion': identifier})
                dispatch = {'clave_idempotencia': 'http-dispatch-key', 'lineas': [{'id_detalle_reposicion': line['id_detalle_reposicion'], 'cantidad': 20}]}
                assert (await call('POST', f'/ordenes-reposicion/{identifier}/despacho', 'EMPRESA', dispatch)).status_code == 403
                response = await call('POST', f'/ordenes-reposicion/{identifier}/despacho', 'PROVEEDOR', dispatch)
                assert response.status_code == 200, response.text
                receipt = {'id_orden_reposicion': identifier, 'clave_idempotencia': 'http-receipt-key', 'detalles': [{'id_detalle_reposicion': line['id_detalle_reposicion'], 'id_inventario': 'i', 'id_detalle_inventario': 'di', 'cantidad_recibida': 20, 'cantidad_rechazada': 5, 'estado_recepcion': 'CONFORME', 'motivo_rechazo': 'Deterioro'}]}
                response = await call('POST', '/recepciones', 'OPERARIO', receipt)
                assert response.status_code == 201, response.text
                assert response.json()['comparacion'][0]['aceptada'] == 15
                assert (await db.detalles_inventario.find_one({'id_detalle_inventario': 'di'}))['stock_actual'] == 15
                assert (await call('PUT', '/detalles-inventario/di', 'OPERARIO', {'stock_minimo': 50})).status_code == 403
                assert (await call('PATCH', f'/abastecimiento/solicitudes/{identifier}/pendiente', 'OPERARIO', {'decision': 'CERRAR', 'motivo': 'No autorizado'})).status_code == 403
                response = await call('GET', '/abastecimiento/historial-pedidos', 'EMPRESA')
                assert response.status_code == 200 and len(response.json()['registros']) == 1
                users['EMPRESA'] = UsuarioActual(rol='EMPRESA', id_empresa='foreign')
                assert (await call('GET', f'/ordenes-reposicion/{identifier}', 'EMPRESA')).status_code in (403, 404)
                assert (await call('GET', '/abastecimiento/seguimiento', 'EMPRESA')).json() == []
    asyncio.run(run())


def test_zone_three_racks_limit_duplicate_code_and_reducing_capacity(monkeypatch):
    async def run():
        from app.services.rack_service import RackService
        from app.dto.rack_dto import RackCreate
        from app.dto.zona_dto import ZonaUpdate
        async with isolated_database(monkeypatch) as db:
            await seed(db)
            service = RackService()
            for i in (2, 3):
                await service.crear_rack(RackCreate(id_zona='z', codigo=f'R{i}', capacidad=100, max_niveles=4))
            with pytest.raises(HTTPException):
                await service.crear_rack(RackCreate(id_zona='z', codigo='R4', capacidad=100))
            with pytest.raises(HTTPException):
                await JerarquiaService.actualizar_zona('z', ZonaUpdate(max_racks=2))
            assert await db.racks.count_documents({'id_zona': 'z'}) == 3
    asyncio.run(run())


def test_classification_and_canonical_catalog_keep_history_when_deactivated(monkeypatch):
    async def run():
        from app.services.clasificacion_service import validar_clasificacion
        from app.services.producto_service import ProductoService
        from app.dto.producto_dto import ProductoCreate, ProductoUpdate
        async with isolated_database(monkeypatch) as db:
            supplier, operator, company = await seed(db)
            assert await validar_clasificacion('e', 'frutas', 'tropicales') == ('Frutas', 'Tropicales')
            with pytest.raises(HTTPException):
                await validar_clasificacion('e', 'Frutas', 'Lácteos')
            data = ProductoCreate(id_empresa='e', id_proveedor='v', nombre='mango kent', familia='Frutas', categoria='Tropicales', unidad='kg', peso=5, lead_time_dias=1, vida_util_dias=10)
            assert (await ProductoService.crear(data))['id_producto'] == 'p'
            assert await db.productos.count_documents({}) == 1
            await db.productos.insert_one({'id_producto': 'p2', 'id_empresa': 'e', 'nombre': 'Papaya', 'familia': 'Frutas', 'categoria': 'Tropicales', 'unidad': 'kg'})
            with pytest.raises(HTTPException):
                await ProductoService.actualizar('p2', ProductoUpdate(nombre='Mango Kent'))
            await db.movimientos.insert_one({'id_producto': 'p', 'id_almacen': 'w', 'tipo_movimiento': 'ENTRADA', 'motivo_movimiento': 'RECEPCION', 'cantidad': 5})
            await ProductoService.eliminar('p')
            assert (await db.productos.find_one({'id_producto': 'p'}))['activo'] is False
            assert [p['id'] for p in (await AnalisisService().filters(company))['productos']] == ['p']
    asyncio.run(run())
