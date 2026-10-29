"""Current stock answers from authorized inventory only; no language-model inference."""
import re
from datetime import datetime, timezone
from fastapi import HTTPException
from app.services.acceso_service import AccesoService
from app.services.saiki_inventory_summary import inventory_summary
from app.services.clasificacion_service import normalizar


async def quantity_answer(data, user):
    if user.es_proveedor:
        raise HTTPException(403, 'No tiene acceso al inventario')
    if data.id_almacen:
        await AccesoService.verificar_almacen(user, data.id_almacen)
    if data.id_inventario:
        await AccesoService.verificar_inventario(user, data.id_inventario)
    if data.id_producto:
        await AccesoService.verificar_producto(user, data.id_producto)
    summary = await inventory_summary(user, warehouse=data.id_almacen, inventory=data.id_inventario)
    catalog = summary['catalogo_productos']
    text = normalizar(data.message or '')
    exact = [p for p in catalog if p.get('nombre') and re.search(r'\b' + re.escape(normalizar(p['nombre'])) + r'\b', text)]
    if exact:
        longest = max(len(normalizar(p['nombre'])) for p in exact)
        matches = [p for p in exact if len(normalizar(p['nombre'])) == longest]
    else:
        words = set(re.findall(r'\w+', text)) - {'producto', 'productos', 'stock', 'cantidad', 'disponible', 'inventario', 'unidad', 'unidades'}
        matches = [p for p in catalog if any(word in words for word in normalizar(p.get('nombre') or '').split() if len(word) >= 3)]
    if data.id_producto:
        selected = next((p for p in catalog if p['id_producto'] == data.id_producto), None)
        if matches and selected and any(p['id_producto'] != data.id_producto for p in matches):
            return 'El producto mencionado y el producto seleccionado no coinciden. Confirma cuál quieres consultar.', {}
        matches = [selected] if selected else []
    if len(matches) > 1:
        return 'Hay varios productos que coinciden: ' + ', '.join(p['nombre'] for p in matches[:10]) + '. Indica el nombre completo.', {'coincidencias': matches[:10]}
    if not matches:
        return 'No identifiqué un producto único en tu catálogo autorizado. Indica su nombre completo o selecciónalo; no puedo confirmar una cantidad.', {}
    product = matches[0]
    amount = next((row['stock_actual'] for row in summary['stock_por_producto'] if row['id_producto'] == product['id_producto']), None)
    if amount is not None:
        amount = round(amount, 3)
    unit = product.get('unidad') or 'unidad'
    record = {'id_producto': product['id_producto'], 'producto': product['nombre'], 'cantidad': amount,
              'unidad': unit, 'estado': 'SIN_INVENTARIO' if amount is None else 'REGISTRADO',
              'id_almacen': data.id_almacen or (user.id_almacen if user.es_operario else None),
              'consultado_en': datetime.now(timezone.utc).isoformat()}
    if amount is None:
        answer = f"{product['nombre']}: no hay inventario registrado en el ámbito consultado. Eso no confirma stock cero."
    else:
        label = 'unidades' if unit == 'unidad' else unit
        answer = f"Tienes {format(amount, '.3f').rstrip('0').rstrip('.')} {label} de {product['nombre']} en el inventario consultado."
    return answer, {'cantidades_verificadas': [record]}
