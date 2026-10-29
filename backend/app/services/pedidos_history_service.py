from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.services.abastecimiento_service import AbastecimientoService


async def historial_pedidos(user, product=None, provider=None, start=None, end=None, cancelled=False):
    try:
        first = date.fromisoformat(start) if start else None
        last = date.fromisoformat(end) if end else None
    except ValueError as exc:
        raise HTTPException(422, 'Use fechas con formato AAAA-MM-DD') from exc
    if first and last and first > last:
        raise HTTPException(422, 'El rango de fechas no es válido')
    rows = await AbastecimientoService.pendientes(user)
    selected = []
    undated = 0
    for row in rows:
        timestamp = row['fecha']
        if not isinstance(timestamp, datetime):
            undated += 1
            continue
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        day = timestamp.astimezone(ZoneInfo('America/Lima')).date()
        if product and row['id_producto'] != product or provider and row['id_proveedor'] != provider:
            continue
        if first and day < first or last and day > last:
            continue
        if not cancelled and row['estado'] == 'CANCELADA':
            continue
        selected.append({**row, 'fecha': timestamp.isoformat(), 'dia': day.isoformat(),
            'cantidad': row['solicitada'], 'unidad': row.get('unidad', 'unidad'),
            'origen': 'SOLICITUD_PSITWIN', 'es_imputado': False,
            'id_origen': row['id_detalle_reposicion']})
    selected.sort(key=lambda row: (row['fecha'], row['id_origen']))
    totals = {}
    for row in selected:
        totals[row['unidad']] = round(totals.get(row['unidad'], 0) + row['cantidad'], 3)
    return {'registros': selected, 'total_registros': len(selected), 'totales_por_unidad': totals,
        'sin_fecha_excluidos': undated, 'tipo_demanda': 'ABASTECIMIENTO', 'fechas_ausentes_imputadas': False}
