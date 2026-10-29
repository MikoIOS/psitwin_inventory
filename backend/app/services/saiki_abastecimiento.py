"""Deterministic read-only supply evidence; supplier comments are never instructions."""
import re
from decimal import Decimal
from fastapi import HTTPException
from app.services.clasificacion_service import normalizar
from app.services.oferta_service import OfertaService, subtotal, miles
from app.services.abastecimiento_service import AbastecimientoService
from app.services.pedidos_history_service import historial_pedidos
from app.database.mongodb import get_database


async def explicar_abastecimiento(data, user):
    if not user:
        raise HTTPException(403, 'Se requiere una sesión autorizada')
    text = normalizar(data.message or '')
    offers = await OfertaService.listar(user, True)
    products = await get_database()["productos"].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=10000)
    context = data.context.get('grafico', {})
    context = context if isinstance(context, dict) else {}
    selected = data.id_producto or context.get('id_producto')
    named = [p for p in products if normalizar(p['nombre']) in text]
    if not named:
        words = set(re.findall(r'\w+', text))
        named = [p for p in products if any(w in words for w in normalizar(p['nombre']).split() if len(w) >= 4)]
    if not selected and len(named) == 1:
        selected = named[0]['id_producto']
    if selected:
        if not any(p['id_producto'] == selected for p in products):
            raise HTTPException(404, 'Producto no encontrado')
        offers = [o for o in offers if o['id_producto'] == selected]
    provider_names = [o['id_proveedor'] for o in offers if o.get('proveedor') and normalizar(o['proveedor']) in text]
    if provider_names:
        offers = [o for o in offers if o['id_proveedor'] in provider_names]
    rows = await AbastecimientoService.pendientes(user)
    if provider_names:
        rows = [r for r in rows if r['id_proveedor'] in provider_names]
    if selected:
        rows = [r for r in rows if r['id_producto'] == selected]
    if data.id_almacen:
        if user.es_operario and data.id_almacen != user.id_almacen:
            raise HTTPException(403, 'Almacén no autorizado')
        allowed = await get_database()["ordenes_reposicion"].distinct('id_orden_reposicion', {'id_empresa': user.id_empresa, 'id_almacen': data.id_almacen})
        rows = [r for r in rows if r['id_orden'] in allowed]
    evidence = {'ofertas': offers[:50], 'seguimiento': rows[:50]}
    lines = []
    if re.search(r'ofert|disponib|precio|cost|cuest|kg|kilo|proveedor|distribuidor', text):
        amount = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|kilos?|kilogramos?|unidades?)', text)
        for offer in offers[:50]:
            description = f"{offer['producto']} · {offer['proveedor']}: disponibles {offer['cantidad_disponible']:g} {offer['unidad']}; S/ {offer['precio_centimos'] / 100:.2f}/{offer['unidad']}."
            if amount and selected:
                quantity = Decimal(amount[1].replace(',', '.'))
                unit = 'kg' if amount[2] in {'kg', 'kilo', 'kilos', 'kilogramo', 'kilogramos'} else 'unidad'
                if unit != offer['unidad']:
                    description += ' La unidad consultada no coincide con la oferta; no se hace conversión automática.'
                else:
                    miles(quantity, unit)
                    description += f" {quantity} {unit} costarían S/ {subtotal(quantity, offer['precio_centimos']) / 100:.2f} PEN."
                    if quantity > Decimal(str(offer['cantidad_disponible'])):
                        description += ' La cantidad supera la disponibilidad actual.'
            lines.append(description)
        if not offers:
            lines.append('No hay ofertas vigentes disponibles para esta consulta.')
    if re.search(r'pedido|solicitud|despacho|recep|rechaz|falt|pendiente|historial|grafico|frecuencia|reposicion|cada cuantos', text):
        for row in ([] if context.get('tipo') == 'pedidos' else rows[:50]):
            product = next((p['nombre'] for p in products if p['id_producto'] == row['id_producto']), row['id_producto'])
            lines.append(f"Solicitud {row['id_orden']} · {product} · {row['estado']}: solicitados {row['solicitada']:g}, despachados {row['despachada']:g}, recibidos {row['recibida']:g}, aceptados {row['aceptada']:g}, rechazados {row['rechazada']:g}, pendientes {row['faltante']:g} {row.get('unidad', 'unidad')}. Fecha: {row['fecha']}. Motivos registrados: {', '.join(m for m in row['motivos'] if m) or 'sin rechazo documentado' }.")
        if not rows:
            lines.append('No hay solicitudes autorizadas que coincidan con esta consulta.')
        if not user.es_proveedor:
            history = await historial_pedidos(user, selected, context.get('id_proveedor') or (provider_names[0] if len(provider_names) == 1 else None), context.get('desde'), context.get('hasta'), context.get('incluir_canceladas') is True)
            observations = history['registros']
            evidence['historial_pedidos'] = history
            groups = {}
            for row in observations:
                groups.setdefault((row['id_producto'], row['unidad']), []).append(row)
            frequencies = []
            from datetime import date
            for (product_id, unit), records in groups.items():
                name = next((p['nombre'] for p in products if p['id_producto'] == product_id), product_id)
                amounts = [r['cantidad'] for r in records]
                lines.append(f"Historial de solicitudes de {name} (demanda de abastecimiento): " + '; '.join(f"{r['fecha']}: {r['cantidad']:g} {unit}" for r in records[:50]))
                lines.append(f"{name}: mínimo {min(amounts):g}, máximo {max(amounts):g}, promedio {sum(amounts) / len(amounts):.3f} {unit} por línea de solicitud; {len(records)} líneas de solicitud.")
                if len(records) > 1:
                    change = records[-1]['cantidad'] - records[0]['cantidad']
                    lines.append(f"Diferencia entre la primera y última solicitud de {name}: {change:+g} {unit}. Es una comparación histórica, no una predicción.")
                days = sorted({r['dia'] for r in records})
                if len(days) > 1:
                    intervals = [(date.fromisoformat(b) - date.fromisoformat(a)).days for a, b in zip(days, days[1:])]
                    average = sum(intervals) / len(intervals)
                    frequencies.append((average, name))
                    lines.append(f"Intervalos observados de {name}: {', '.join(map(str, intervals))} días; promedio {average:.2f} días entre fechas con pedidos.")
                else:
                    lines.append(f'{name}: solo hay una fecha con pedidos; no permite calcular una frecuencia entre fechas.')
            if frequencies and re.search(r'mayor frecuencia|mas frecuente|frecuencia de reposicion', text):
                average, name = min(frequencies)
                lines.append(f'Entre las series consultadas con al menos dos fechas, {name} tiene el menor intervalo promedio: {average:.2f} días.')
            if not groups:
                lines.append('No hay pedidos históricos que coincidan con los filtros activos.')
    if len(rows) > 50 or len(offers) > 50:
        lines.append('Se muestran hasta 50 registros. Selecciona un producto o proveedor para acotar la consulta.')
    lines.append('No he modificado solicitudes, reservas, recepciones ni inventario.')
    return '\n\n'.join(lines), evidence
