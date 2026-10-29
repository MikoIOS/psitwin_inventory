import re
from fastapi import HTTPException
from app.dto.inventario_consulta_dto import InventarioFiltros
from app.services.clasificacion_service import normalizar
from app.services.inventario_consulta_service import consultar_inventario, ident
from app.services.abastecimiento_service import AbastecimientoService

KEYS = ('id_almacen','id_zona','id_rack','id_nivel','id_producto','id_inventario')
ESTADOS = {'AGOTADO':'agotado', 'BAJO_MINIMO':'por debajo del mínimo', 'EN_MINIMO':'en el mínimo', 'SOBRE_MAXIMO':'por encima del máximo', 'NORMAL':'dentro de los umbrales configurados', 'SIN_UMBRALES':'sin umbrales configurados'}

async def inventario_contextual(data, user):
    context = data.context.get('ubicacion', {})
    context = context if isinstance(context, dict) else {}
    values = {key: getattr(data, key, None) or (context.get(key) if isinstance(context.get(key), str) else None) for key in KEYS}
    values['busqueda'] = context.get('busqueda') if isinstance(context.get('busqueda'),str) else ''
    values['estado'] = context.get('estado') if context.get('estado') in {'todos','stock-bajo','sin-stock','sobre-stock','normal'} else 'todos'
    text = normalizar(data.message or '')
    if 'agotad' in text: values['estado'] = 'sin-stock'
    elif re.search(r'stock bajo|debajo.*minim|en el minimo|reposicion', text): values['estado'] = 'stock-bajo'
    elif re.search(r'encima.*maxim|superior.*maxim|sobrestock', text): values['estado'] = 'sobre-stock'
    filters = InventarioFiltros(**values)
    result = await consultar_inventario(user, filters)
    for key, collection, noun, name in [('id_almacen','almacenes','almacen','nombre'),('id_zona','zonas','zona','nombre'),('id_rack','racks','rack','codigo')]:
        if getattr(filters, key) or not re.search(r'\b' + noun + r'\b', text): continue
        candidates = []
        for row in result[collection]:
            label = normalizar(str(row.get(name) or ''))
            code = normalizar(str(row.get('codigo') or ''))
            variants = [v for v in (label, noun + ' ' + code if code else '') if v]
            if any(re.search(r'\b' + re.escape(v) + r'\b', text) for v in variants): candidates.append(row)
        if len(candidates) > 1: raise HTTPException(409, f'Hay varios {noun}s que coinciden; selecciona la ubicación exacta')
        explicit = re.search(r'\b' + noun + r'\s+([a-z0-9-]+)',text)
        if not candidates and explicit and explicit[1] not in {'seleccionado','seleccionada','actual','de','del','en','que','es','recientemente','reciente'}:
            raise HTTPException(404, f'No se identificó ese {noun} dentro del alcance autorizado; selecciónalo para consultar')
        if candidates:
            setattr(filters,key,ident(candidates[0],key))
            result = await consultar_inventario(user, filters)
    level_match = re.search(r'\bnivel\s+(\d+)\b', text)
    if level_match and not filters.id_nivel:
        candidates = [l for l in result['niveles'] if l['numero'] == int(level_match[1]) and (not filters.id_rack or l['id_rack'] == filters.id_rack)]
        if len(candidates) != 1:
            raise HTTPException(409, 'Selecciona el rack para identificar ese nivel sin ambigüedad')
        filters.id_nivel = candidates[0]['id_nivel']
        result = await consultar_inventario(user, filters)
    if re.search(r'\bdonde\b', text) and not filters.id_producto:
        candidates = [p for p in result['productos'] if any(re.search(r'\b'+re.escape(v)+r'\b',text) for v in (normalizar(p['producto']),normalizar(p['producto']).split(' ')[0]) if len(v)>=4)]
        if not candidates: raise HTTPException(404, 'No se identifico el producto dentro del inventario autorizado')
        if len(candidates)>1: raise HTTPException(409, 'Coinciden varios productos; indica su nombre completo o selecciónalo')
        if candidates:
            filters.id_producto = candidates[0]['id_producto']
            result = await consultar_inventario(user, filters)
    return result


async def respuesta_inventario(data, user, problemas=False):
    result = await inventario_contextual(data, user)
    if problemas:
        issues = [f"{a.get('producto') or 'Ubicación/equipo'}: {ESTADOS.get(a['tipo'],a['tipo'])} · {a.get('ubicacion') or ''}. " + (f"Cantidad registrada: {a['cantidad']:g} {a.get('unidad') or ''}. " if isinstance(a.get('cantidad'),(float,int)) else '') + (f"Umbral: {a['umbral']:g}. " if isinstance(a.get('umbral'),(float,int)) else '') + (a.get('observacion') or '') for a in result['alertas']]
        try:
            supply = await AbastecimientoService.pendientes(user)
            f = result['filtros']
            supply = [s for s in supply if (not f['id_almacen'] or s['id_almacen'] == f['id_almacen']) and (not f['id_producto'] or s['id_producto'] == f['id_producto'])]
            for row in supply:
                label = f"Solicitud {row['id_orden']} ({row['proveedor']})"
                if row['estado'] in {'PENDIENTE','OBSERVADA'}: issues.append(label + ': pendiente de aprobación/corrección.')
                elif row['estado'] in {'ENVIADA','PARCIAL'} and (row.get('resolucion') or {}).get('decision') != 'CERRAR':
                    if row['despachada'] == 0: issues.append(label + ': aprobada, sin despacho registrado.')
                    if row['diferencia_despacho'] > 0: issues.append(f"{label}: {row['diferencia_despacho']:g} {row['unidad']} despachados pendientes de recepción.")
                    if row['recibida'] and row['faltante']: issues.append(f"{label}: faltan {row['faltante']:g} {row['unidad']} por aceptar.")
                if row['rechazada']: issues.append(f"{label}: {row['rechazada']:g} {row['unidad']} rechazados. Motivos: {', '.join(m for m in row['motivos'] if m) or 'sin motivo documentado'}.")
        except HTTPException: raise
        except Exception:
            issues.append('No se pudieron verificar las solicitudes y recepciones; ese estado no está disponible.')
            supply = None
        answer = ('Situaciones registradas para revisar:\n' + '\n'.join(f'{i+1}. {s}' for i,s in enumerate(issues[:30]))) if issues else 'No encontré alertas de stock ni pendientes de abastecimiento en el alcance consultado.'
        if len(issues)>30: answer += f'\nSe muestran 30 de {len(issues)} situaciones; selecciona un almacén o producto para acotar.'
        answer += '\nLas incidencias registradas no confirman por sí solas una avería. No se han verificado lecturas nuevas fuera de las alertas registradas.'
        return answer, {'alertas_inventario':result['alertas'], 'pendientes_abastecimiento':supply, 'filtros':result['filtros']}
    products = result['productos']
    offset = (data.page-1)*data.page_size
    selected = products[offset:offset+data.page_size]
    lines = []
    for p in selected:
        unit = 'unidades' if p['unidad']=='unidad' else p['unidad']
        locations = [r for r in result['ubicaciones'] if r['id_producto']==p['id_producto']]
        location_text = '; '.join(' / '.join(str(r.get(k) or 'Sin asignar') for k in ('almacen','zona','rack')) + f" / Nivel {r['nivel'] if r['nivel'] is not None else 'sin asignar'}" for r in locations[:3])
        warning = ', '.join(ESTADOS.get(s,s) for s in p['estados'])
        lines.append(f"{p['producto']}: {p['stock_actual']:g} {unit}. {location_text}. Estado: {warning}.")
    if not products: answer = 'No hay existencias registradas para estos filtros; los productos solo ofertados no se cuentan como inventario.'
    else:
        answer = f"Hay {len(products)} productos distintos en el inventario consultado:\n" + '\n'.join(f'{offset+i+1}. {line}' for i,line in enumerate(lines))
        if offset+len(selected)<len(products): answer += f'\nPágina {data.page}. Solicita la página {data.page+1} para continuar; hay {len(products)} productos en total.'
    return answer, {'inventario_detallado':selected, 'ubicaciones': [r for r in result['ubicaciones'] if r['id_producto'] in {p['id_producto'] for p in selected}],
        'alertas_inventario':result['alertas'], 'filtros':result['filtros'], 'paginacion':{'pagina':data.page,'limite':data.page_size,'total':len(products)}}


async def respuesta_movimientos(data, user):
    from app.database.mongodb import get_database
    result = await inventario_contextual(data,user)
    query = {'id_almacen': {'$in': [ident(w,'id_almacen') for w in result['almacenes']]}}
    f = result['filtros']
    if f['id_producto']: query['id_producto'] = f['id_producto']
    if f['id_rack']: query['id_rack'] = f['id_rack']
    elif f['id_zona']: query['id_rack'] = {'$in':[r['id_rack'] for r in result['racks'] if r['id_zona']==f['id_zona']]}
    if f['id_nivel']: query['id_detalle_inventario'] = {'$in':[r['id_detalle_inventario'] for r in result['ubicaciones']]}
    text = normalizar(data.message or '')
    if re.search(r'ingres|entrad',text): query['tipo_movimiento']='ENTRADA'
    elif re.search(r'salid',text): query['tipo_movimiento']='SALIDA'
    rows = await get_database()['movimientos'].find(query, {'_id':0}).sort('fecha_hora',-1).to_list(length=25)
    names = {p['id_producto']:p for p in result['productos']}
    lines=[]
    for r in rows:
        p=names.get(r.get('id_producto'))
        if not p: continue
        lines.append(f"{r.get('fecha_hora')}: {p['producto']} · {r['tipo_movimiento']} · {r['cantidad']:g} {p['unidad']} · {r.get('motivo_movimiento') or ''}.")
    return ('Últimos movimientos registrados (máximo 25):\n'+'\n'.join(lines) if lines else 'No hay movimientos verificables para este alcance.'), {'movimientos_registrados':rows,'filtros':f}
