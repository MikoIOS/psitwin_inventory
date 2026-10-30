"""Read-only ranking of authorized rack load; never asks an LLM for inventory values."""
import re

from fastapi import HTTPException
from app.database.mongodb import get_database
from app.services.inventario_consulta_service import number
from app.services.saiki_inventario_detallado import inventario_contextual


async def product_weights(user, identifiers):
    if not identifiers:
        return {}
    documents = await get_database()['productos'].find({
        'id_empresa': user.id_empresa, 'id_producto': {'$in': sorted(identifiers)}
    }, {'_id': 0, 'id_producto': 1, 'peso': 1}).to_list(length=None)
    return {row['id_producto']: row.get('peso') for row in documents}


async def rack_occupancy(data, user):
    if user is None:
        raise HTTPException(401, 'Se requiere una sesión autenticada')
    if user.es_proveedor:
        raise HTTPException(403, 'No tiene acceso al inventario')
    # This source enforces tenant/operator warehouse scope and selected location filters.
    result = await inventario_contextual(data, user)
    filters = result['filtros']
    racks = [r for r in result['racks']
             if (not filters.get('id_rack') or filters['id_rack'] == r['id_rack'])
             and (not filters.get('id_zona') or filters['id_zona'] == r['id_zona'])]
    ids = {r['id_rack'] for r in racks}
    details = [row for row in result['ubicaciones'] if row.get('id_rack') in ids]
    weights = await product_weights(user, {row['id_producto'] for row in details if row['stock_actual'] > 0})
    ranked, unknown = [], []
    for rack in racks:
        levels = [n for n in result['niveles'] if n['id_rack'] == rack['id_rack'] and n.get('estado', 'ACTIVO') == 'ACTIVO']
        capacities = [n.get('capacidad_kg') for n in levels]
        # Newer data uses level capacities; legacy data stores the rack capacity.
        capacity = (sum(capacities) if capacities and all(number(c) and c > 0 for c in capacities)
                    else rack.get('capacidad'))
        load, missing = 0.0, []
        for row in details:
            if row['id_rack'] != rack['id_rack'] or row['stock_actual'] <= 0:
                continue
            weight = weights.get(row['id_producto'])
            if row.get('ubicacion_valida') is False or not number(weight) or weight <= 0:
                missing.append(row['id_producto'])
            else:
                load += row['stock_actual'] * weight
        verified = not missing and number(load) and number(capacity) and capacity > 0
        record = {'id_rack': rack['id_rack'], 'codigo': rack.get('codigo') or rack['id_rack'],
                  'carga_kg': round(load, 3) if not missing and number(load) else None,
                  'capacidad_kg': capacity if number(capacity) and capacity > 0 else None,
                  'ocupacion_pct': round(100 * load / capacity, 2) if verified else None,
                  'productos_sin_peso_o_ubicacion_valida': sorted(set(missing))}
        (ranked if verified else unknown).append(record)
    normalized = data.message.casefold()
    ascending = bool(re.search(r'menos\s+(?:lleno|ocupad)|mas\s+vaci|más\s+vací', normalized))
    empty_only = bool(re.search(r'\bvaci[oa]s?\b|\bvací[oa]s?\b', normalized)) and not re.search(r'm[aá]s\s+vac', normalized)
    if empty_only:
        ranked = [row for row in ranked if row['ocupacion_pct'] == 0]
    ranked.sort(key=lambda row: ((row['ocupacion_pct'] if ascending else -row['ocupacion_pct']), row['codigo']))
    partial = bool(filters.get('id_producto') or filters.get('id_inventario') or filters.get('id_nivel')
                   or filters.get('busqueda') or filters.get('estado', 'todos') != 'todos')
    if not racks:
        answer = 'No hay racks registrados dentro del alcance consultado.'
    elif not ranked and empty_only:
        answer = 'No hay racks vacíos verificables dentro del alcance consultado.'
    elif not ranked:
        answer = 'No puedo comparar la ocupación: faltan capacidades, pesos o ubicaciones válidas para los racks consultados.'
    else:
        answer = ('Racks con menor ocupación' if ascending else 'Racks con mayor ocupación') + ' según carga registrada / capacidad en kg:\n'
        answer += '\n'.join(f"{i}. Rack {row['codigo']}: {row['ocupacion_pct']:g}% · {row['carga_kg']:g} de {row['capacidad_kg']:g} kg."
                            for i, row in enumerate(ranked[:5], 1))
        if len(ranked) > 5:
            answer += f'\nSe muestran 5 de {len(ranked)} racks comparables.'
    if unknown:
        answer += '\nSin porcentaje verificable: ' + ', '.join(row['codigo'] for row in unknown) + '. Faltan pesos, capacidades o referencias válidas; no se consideran vacíos.'
    if partial:
        answer += '\nLa carga corresponde solo a las existencias filtradas; no representa la ocupación total del rack.'
    return answer, {'ocupacion_racks': ranked, 'racks_sin_ocupacion_verificada': unknown,
                    'alcance_filtrado': partial, 'filtros': filters, 'generado_en': result['generado_en']}
