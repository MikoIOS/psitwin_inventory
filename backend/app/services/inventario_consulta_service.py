"""One authorized source for maps, inventory supervision and exports."""
import asyncio
import math
from datetime import datetime, timezone
from fastapi import HTTPException
from app.database.mongodb import get_database
from app.dto.inventario_consulta_dto import InventarioFiltros
from app.services.acceso_service import AccesoService
from app.services.clasificacion_service import normalizar


def ident(row, key): return row.get(key) or row.get('id')
def number(value): return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
def status(stock, minimum, maximum):
    if stock == 0: return 'AGOTADO'
    if number(minimum) and minimum > 0:
        if stock < minimum: return 'BAJO_MINIMO'
        if stock == minimum: return 'EN_MINIMO'
    if number(maximum) and maximum > 0 and stock > maximum: return 'SOBRE_MAXIMO'
    return 'NORMAL' if (number(minimum) and minimum > 0) or (number(maximum) and maximum > 0) else 'SIN_UMBRALES'


async def _consultar_inventario(user, filtros=None):
    if not user or user.es_proveedor: raise HTTPException(403, 'No tiene acceso al inventario')
    f = (filtros or InventarioFiltros()).model_copy(deep=True)
    if user.es_operario:
        if not user.id_almacen: raise HTTPException(403, 'No tiene un almacén asignado')
        if f.id_almacen and f.id_almacen != user.id_almacen: raise HTTPException(403, 'Almacén no autorizado')
        f.id_almacen = user.id_almacen
    for key, verify in [('id_almacen', AccesoService.verificar_almacen), ('id_zona', AccesoService.verificar_zona), ('id_rack', AccesoService.verificar_rack), ('id_producto', AccesoService.verificar_producto)]:
        if getattr(f, key): await verify(user, getattr(f, key))
    db = get_database()
    if f.id_nivel:
        level = await db['niveles'].find_one({'id_nivel': f.id_nivel}, {'_id': 0})
        if not level: raise HTTPException(404, 'Nivel no encontrado')
        await AccesoService.verificar_rack(user, level['id_rack'])
        if f.id_rack and f.id_rack != level['id_rack']: raise HTTPException(422, 'Nivel y rack no coinciden')
        f.id_rack = level['id_rack']
    if f.id_inventario:
        header = await AccesoService.verificar_inventario(user, f.id_inventario)
        if f.id_almacen and f.id_almacen != header['id_almacen']: raise HTTPException(422, 'Inventario y almacén no coinciden')
        f.id_almacen = header['id_almacen']
    if f.id_rack:
        rack = await AccesoService.verificar_rack(user, f.id_rack)
        if f.id_zona and f.id_zona != rack['id_zona']: raise HTTPException(422, 'Rack y zona no coinciden')
        f.id_zona = rack['id_zona']
    if f.id_zona:
        zone = await AccesoService.verificar_zona(user, f.id_zona)
        if f.id_almacen and f.id_almacen != zone['id_almacen']: raise HTTPException(422, 'Zona y almacén no coinciden')
        f.id_almacen = zone['id_almacen']
    warehouses, products = await asyncio.gather(
        db['almacenes'].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=None),
        db['productos'].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=None))
    warehouses = [w for w in warehouses if not f.id_almacen or ident(w, 'id_almacen') == f.id_almacen]
    wm = {ident(w, 'id_almacen'): w for w in warehouses}
    zones = await db['zonas'].find({'id_almacen': {'$in': list(wm)}}, {'_id': 0}).to_list(length=None)
    zm = {ident(z, 'id_zona'): z for z in zones}
    if f.id_zona and f.id_zona not in zm: raise HTTPException(422, 'La zona no pertenece al almacén seleccionado')
    racks = await db['racks'].find({'id_zona': {'$in': list(zm)}}, {'_id': 0}).to_list(length=None)
    rm = {ident(r, 'id_rack'): r for r in racks}
    if f.id_rack and (f.id_rack not in rm or f.id_zona and rm[f.id_rack]['id_zona'] != f.id_zona): raise HTTPException(422, 'El rack no pertenece a la zona seleccionada')
    levels, headers = await asyncio.gather(
        db['niveles'].find({'id_rack': {'$in': list(rm)}}, {'_id': 0}).to_list(length=None),
        db['inventarios'].find({'id_almacen': {'$in': list(wm)}}, {'_id': 0}).to_list(length=None))
    lm = {l['id_nivel']: l for l in levels}
    hm = {h['id_inventario']: h for h in headers if not f.id_inventario or h['id_inventario'] == f.id_inventario}
    pm = {p['id_producto']: p for p in products}
    query = {'id_inventario': {'$in': list(hm)}, 'id_producto': {'$in': list(pm)}}
    for key in ('id_producto', 'id_rack', 'id_nivel'):
        if getattr(f, key): query[key] = getattr(f, key)
    details = await db['detalles_inventario'].find(query, {'_id': 0}).to_list(length=None)
    rows, alerts = [], []
    allowed_status = {'stock-bajo': {'BAJO_MINIMO', 'EN_MINIMO'}, 'sin-stock': {'AGOTADO'}, 'sobre-stock': {'SOBRE_MAXIMO'}, 'normal': {'NORMAL'}}
    for d in details:
        p, h = pm[d['id_producto']], hm[d['id_inventario']]
        r = rm.get(d.get('id_rack'), {})
        z = zm.get(r.get('id_zona'), {})
        level = lm.get(d.get('id_nivel'), {})
        valid = bool(r and z and z['id_almacen'] == h['id_almacen'] and (not d.get('id_nivel') or level.get('id_rack') == d.get('id_rack')))
        if f.id_zona and ident(z, 'id_zona') != f.id_zona: continue
        if f.busqueda and normalizar(f.busqueda) not in normalizar(' '.join(str(p.get(k) or '') for k in ('nombre', 'codigo', 'familia', 'categoria', 'marca'))): continue
        stock = d.get('stock_actual')
        if not number(stock) or stock < 0: raise HTTPException(503, 'Existen cantidades de inventario que no pudieron verificarse')
        minimum, maximum = d.get('stock_minimo'), d.get('stock_maximo')
        state = status(stock, minimum, maximum)
        if f.estado != 'todos' and state not in allowed_status[f.estado]: continue
        row = {'id_detalle_inventario': d['id_detalle_inventario'], 'id_inventario': d['id_inventario'],
            'id_producto': p['id_producto'], 'codigo': p.get('codigo') or p['id_producto'], 'producto': p.get('nombre') or 'Sin nombre',
            'familia': p.get('familia'), 'categoria': p.get('categoria'), 'unidad': p.get('unidad', 'unidad'),
            'stock_actual': stock, 'stock_minimo': minimum if number(minimum) and minimum > 0 else None,
            'stock_maximo': maximum if number(maximum) and maximum > 0 else None, 'estado': state,
            'cantidad_reservada': None, 'cantidad_disponible': stock,
            'id_almacen': h['id_almacen'], 'almacen': wm[h['id_almacen']].get('nombre'),
            'id_zona': ident(z, 'id_zona'), 'zona': z.get('nombre'), 'id_rack': d.get('id_rack'), 'rack': r.get('codigo'),
            'id_nivel': d.get('id_nivel'), 'nivel': level.get('numero'), 'codigo_nivel': level.get('codigo'),
            'ubicacion_valida': valid, 'ultima_actualizacion': d.get('fecha_actualizacion') or d.get('fecha_creacion')}
        rows.append(row)
        if state in {'AGOTADO', 'BAJO_MINIMO', 'EN_MINIMO', 'SOBRE_MAXIMO'}:
            alerts.append({'id_producto': p['id_producto'], 'producto': row['producto'], 'tipo': state, 'cantidad': stock,
                'umbral': row['stock_maximo'] if state == 'SOBRE_MAXIMO' else row['stock_minimo'], 'unidad': row['unidad'],
                'ubicacion': ' / '.join(str(row[k]) for k in ('almacen', 'zona', 'rack', 'nivel') if row[k] is not None),
                'id_detalle_inventario': row['id_detalle_inventario'], 'observacion': 'Estado calculado con existencias y umbrales registrados'})
        if not valid:
            alerts.append({'id_producto': p['id_producto'], 'producto': row['producto'], 'tipo': 'UBICACION_INVALIDA', 'cantidad': stock,
                'unidad': row['unidad'], 'observacion': 'Revisar las referencias de almacén, zona, rack y nivel'})
    detail_by_id = {d['id_detalle_inventario']: d for d in details}
    for row in rows:
        source = detail_by_id[row['id_detalle_inventario']]
        row['rechazado'] = str(source.get('estado', '')).upper() in {'RECHAZADO', 'RECHAZADA'}
    selected_products = {r['id_producto'] for r in rows}
    raw_alerts = await db['alertas'].find({'id_empresa': user.id_empresa, 'id_almacen': {'$in': list(wm)}, 'estado': {'$in': ['ACTIVA', 'VISTA']}}, {'_id': 0}).to_list(length=None)
    row_ids = {r['id_detalle_inventario'] for r in rows}
    for a in raw_alerts:
        if f.id_zona and a.get('id_zona') != f.id_zona and a.get('id_detalle_inventario') not in row_ids: continue
        if f.id_rack and a.get('id_rack') != f.id_rack and a.get('id_detalle_inventario') not in row_ids: continue
        if f.id_nivel and a.get('id_detalle_inventario') not in row_ids: continue
        if f.id_producto and a.get('id_producto') != f.id_producto: continue
        alerts.append({'id_producto': a.get('id_producto'), 'producto': pm.get(a.get('id_producto'), {}).get('nombre'), 'tipo': a.get('tipo_alerta'),
            'cantidad': a.get('stock_actual'), 'umbral': a.get('limite'), 'unidad': pm.get(a.get('id_producto'), {}).get('unidad'),
            'ubicacion': ' / '.join(str(a.get(k)) for k in ('id_almacen','id_zona','codigo_rack') if a.get(k)),
            'observacion': a.get('mensaje') or a.get('titulo'), 'origen': a.get('origen', 'INVENTARIO'), 'id_alerta': a.get('id_alerta'), **{k:a.get(k) for k in ('id_almacen','id_zona','id_rack','id_nivel','id_detalle_inventario')}})
    consolidated = []
    for product_id in sorted(selected_products, key=lambda x: pm[x].get('nombre', '')):
        items = [r for r in rows if r['id_producto'] == product_id]
        p = pm[product_id]
        states = sorted({r['estado'] for r in items})
        consolidated.append({'id_producto': product_id, 'codigo': p.get('codigo') or product_id, 'producto': p.get('nombre'),
            'familia': p.get('familia'), 'categoria': p.get('categoria'), 'unidad': p.get('unidad', 'unidad'),
            'stock_actual': round(sum(r['stock_actual'] for r in items), 3), 'ubicaciones': len(items), 'estados': states,
            'stock_minimo': items[0]['stock_minimo'] if all(r['stock_minimo'] == items[0]['stock_minimo'] for r in items) else None,
            'stock_maximo': items[0]['stock_maximo'] if all(r['stock_maximo'] == items[0]['stock_maximo'] for r in items) else None})
    totals = {}
    for p in consolidated: totals[p['unidad']] = round(totals.get(p['unidad'], 0) + p['stock_actual'], 3)
    summary = {'productos_distintos': len(consolidated), 'productos_con_stock': sum(p['stock_actual'] > 0 for p in consolidated),
        'productos_agotados': sum(p['stock_actual'] == 0 for p in consolidated),
        'productos_stock_bajo': len({r['id_producto'] for r in rows if r['estado'] in {'BAJO_MINIMO','EN_MINIMO'}}),
        'productos_con_alertas': len({a['id_producto'] for a in alerts if a.get('id_producto') in selected_products}),
        'ubicaciones_utilizadas': sum(r['stock_actual'] > 0 for r in rows), 'totales_por_unidad': totals}
    from app.services.warehouse_map_service import enriquecer_plano
    await enriquecer_plano(db, user, racks, levels, rows, raw_alerts)
    return {'generado_en': datetime.now(timezone.utc), 'id_empresa': user.id_empresa, 'filtros': f.model_dump(),
            'resumen': summary, 'productos': consolidated, 'ubicaciones': rows, 'alertas': alerts,
            'almacenes': warehouses, 'zonas': zones, 'racks': racks, 'niveles': levels,
            'nota_reservas': 'El stock físico no incluye disponibilidad externa; no hay reserva física configurada.'}


async def consultar_inventario(user, filtros=None):
    from pymongo.errors import PyMongoError
    try: return await _consultar_inventario(user, filtros)
    except PyMongoError as error:
        import logging
        logging.getLogger(__name__).error('inventory_query_failed type=%s', type(error).__name__)
        raise HTTPException(503, 'No se pudo consultar el inventario y sus alertas; no se puede confirmar su estado') from error
