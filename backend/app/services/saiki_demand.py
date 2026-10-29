"""Saiki rendering of real analysis results. Never forecasts inside the LLM."""
from app.services.analisis_service import service


async def historical_answer(user, warehouse=None, product=None, message=''):
    import re
    from datetime import date
    from app.repositories.demanda_historica_repository import DemandaHistoricaRepository
    # Date filters must be explicit; do not silently reinterpret an unsupported time range.
    dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', message)
    normalized = message.casefold()
    if not dates and re.search(r'\b(?:ayer|hoy|semanas?|mes(?:es)?|años?|anos?|desde|hasta|entre|durante|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|20\d{2})\b|\b(?:últim|ultim)\w*', normalized):
        return 'Indica el rango con fechas AAAA-MM-DD (inicio y fin) para consultar la demanda histórica sin suponer un periodo.', {}
    try:
        if len(dates) > 2: raise ValueError('demasiadas fechas')
        start = date.fromisoformat(dates[0]) if dates else None
        end = date.fromisoformat(dates[-1]) if dates else None
        if start and end and start > end: raise ValueError('rango invertido')
    except ValueError:
        return 'El rango de fechas no es válido. Usa inicio y fin en formato AAAA-MM-DD.', {}
    filters = await service.filters(user)
    text = normalized
    for key, current, field in [('almacenes', warehouse, 'almacen'), ('productos', product, 'producto')]:
        if current: continue
        matches = [r['id'] for r in filters[key] if r['id'].casefold() in text or (r.get('nombre') and r['nombre'].casefold() in text)]
        if len(matches) == 1:
            if field == 'almacen': warehouse = matches[0]
            else: product = matches[0]
        elif len(matches) > 1:
            return 'Selecciona un producto y almacén para desambiguar la consulta histórica.', {}
    if re.search(r'\b(?:producto|almac[eé]n)\s+(?!con\b|de\b|y\b)', text) and not warehouse and not product and not re.search(r'mayor|mayores|mas|más|productos', text):
        return 'Selecciona el producto o almacén en los filtros para consultar su demanda histórica.', {}
    report = await DemandaHistoricaRepository().report(user.id_empresa, warehouse, product, start, end, limit=1)
    if not report['documentos']: return 'No hay registros históricos importados para estos filtros.', report
    lines = [f"Demanda histórica del {report['fecha_inicio']} al {report['fecha_fin']}: {report['total']:.2f} unidades; promedio diario {report['promedio_diario']:.2f} en {report['dias_observados']} fechas presentes."]
    names = {r['id']: r['nombre'] for r in filters['productos'] + filters['almacenes']}
    lines.append('Productos con mayor demanda histórica (hasta 20, suma de los almacenes filtrados):')
    for row in report['ranking_productos']:
        lines.append(f"{names.get(row['id_producto'], row['id_producto'])}: {row['cantidad']:.2f} unidades.")
    lines.append('Series con mayor demanda histórica (hasta 20):')
    for row in report['ranking']:
        lines.append(f"{names.get(row['id_producto'], row['id_producto'])} / {names.get(row['id_almacen'], row['id_almacen'])}: {row['cantidad']:.2f} unidades.")
    trend = report['tendencia']
    if trend['promedio_primera_mitad'] is not None:
        lines.append(f"Tendencia observada: promedio de la primera mitad {trend['promedio_primera_mitad']:.2f}, segunda mitad {trend['promedio_segunda_mitad']:.2f} unidades por fecha presente.")
    lines.append('Incluye registros marcados como imputados en el CSV. Es demanda histórica, no stock ni pronóstico. Para demanda futura se requiere un resultado válido de AutoGluon.')
    return '\n\n'.join(lines), report


async def demand_answer(user, horizon=30, warehouse=None, product=None):
    summary = await service.summary(user, horizon, warehouse, product)
    metadata = service.metadata()
    evidence = {**summary, 'evaluacion': {h: metadata['wape_accumulated_pct'][str(h)] for h in (1, 7, 30, 90)},
                'runtime': metadata['runtime'], 'tipo_modelo': 'EVALUACION_NO_REENTRENADO'}
    ready = [row for row in summary['filas'] if row['demanda_acumulada'] is not None]
    lines = []
    if ready:
        lines.append(f'Demanda acumulada proyectada a {horizon} días:')
        for row in ready[:8]:
            lines.append(f"{row['producto']} — {row['almacen']}: {row['demanda_acumulada']:.2f} unidades de demanda; stock actual {row['stock_actual'] if row['stock_actual'] is not None else 'no registrado'}.")
            if row['brecha_stock'] is not None and row['brecha_stock'] > 0:
                lines.append(f"La demanda supera el stock de esa ubicación en {row['brecha_stock']:.2f} unidades. Revisa entradas pendientes, plazos, capacidad y políticas antes de decidir una reposición. No se ejecutó ninguna operación.")
        if not summary['completo']:
            lines.append('El ranking es parcial: todavía no hay pronósticos disponibles para todas las series consultadas.')
    elif summary['calculando']:
        lines.append('PsiTwin está calculando las predicciones reales en segundo plano. La misma consulta reutiliza ese trabajo; puedes ver el progreso en Análisis. Todavía no hay cifras válidas para responder.')
    else:
        lines.append('No hay pronósticos válidos con estos filtros. No sustituiré datos faltantes por estimaciones inventadas.')
        states = sorted({row['estado'] for row in summary['filas']})
        lines.append('Estados de las series: ' + (', '.join(states) if states else 'sin historial ni series operativas disponibles'))
    if not metadata['runtime']['validado']:
        lines.append('El servicio de pronósticos no está disponible en este momento.')
    lines.append('La demanda proyectada es una estimación, no una garantía. El stock proviene del inventario registrado.')
    return '\n\n'.join(lines), evidence
