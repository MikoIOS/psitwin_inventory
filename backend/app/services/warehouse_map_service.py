"""Map projection shared by authorized inventory, exports and Saiki. No writes."""
from datetime import datetime, timezone


def nombres_productos(rows, identifier):
    return sorted({r['producto'] for r in rows if r.get('id_nivel') == identifier
                   and r.get('ubicacion_valida') and not r.get('rechazado')
                   and r.get('cantidad_disponible', r.get('stock_actual', 0)) > 0}, key=str.casefold)


def estado_nivel(devices, alerts, now=None):
    now = now or datetime.now(timezone.utc)
    active = [a for a in alerts if a.get('estado', 'ACTIVA') in {'ACTIVA', 'VISTA'}]
    if any(str(a.get('nivel_riesgo', '')).upper() in {'CRITICO', 'CRITICA', 'ALTO', 'ALTA'} for a in active):
        return 'critico'
    if active:
        return 'advertencia'
    if not devices:
        return 'sin_datos'
    if any(not d.get('estado', {}).get('conectado') for d in devices):
        return 'desconectado'
    for d in devices:
        state = d.get('estado', {})
        reading = state.get('ultima_lectura') or {}
        ts = reading.get('ts')
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        if not ts or abs((now - ts.replace(tzinfo=ts.tzinfo or timezone.utc)).total_seconds()) > state.get('max_edad_lectura_s', 5):
            return 'sin_datos'
        if not any(reading.get(p) is not None for p in ('t_int', 't_amb', 'hum', 'corriente', 'puerta')):
            return 'sin_datos'
    for d in devices:
        state = d.get('estado', {})
        reading = state.get('ultima_lectura') or {}
        opened = state.get('puerta_abierta_desde')
        if isinstance(opened, str):
            opened = datetime.fromisoformat(opened.replace('Z', '+00:00'))
        if reading.get('puerta') and opened:
            maximum = (d.get('limites_efectivos', {}).get('puerta') or {}).get('max_abierta_s', 60)
            if (now - opened.replace(tzinfo=opened.tzinfo or timezone.utc)).total_seconds() > maximum:
                return 'advertencia'
        for parameter in ('t_int', 't_amb', 'hum', 'corriente'):
            value = reading.get(parameter)
            limits = d.get('limites_efectivos', {}).get(parameter) or {}
            if value is not None and ((limits.get('min') is not None and value < limits['min']) or (limits.get('max') is not None and value > limits['max'])):
                return 'advertencia'
    return 'normal'


async def enriquecer_plano(db, user, racks, levels, rows, alerts):
    from app.services.dispositivo_service import DispositivoService
    documents = await db['dispositivos'].find({'id_empresa': user.id_empresa,
        'id_rack': {'$in': [r.get('id_rack', r.get('id')) for r in racks]}, 'activo': True}, {'_id': 0}).to_list(length=None)
    devices = await DispositivoService.respuestas(documents)
    for rack in racks:
        rack['tipo_rack'] = rack.get('tipo_rack') or 'Tipo no definido'
        rack['numero_niveles'] = sum(l['id_rack'] == rack.get('id_rack', rack.get('id')) and l.get('estado', 'ACTIVO') == 'ACTIVO' for l in levels)
    for level in levels:
        identifier = level['id_nivel']
        assigned = [d for d in devices if d.get('id_nivel') == identifier]
        level_alerts = [a for d in assigned for a in d.get('estado', {}).get('alertas_abiertas', [])]
        level_alerts += [a for a in alerts if a.get('id_nivel') == identifier and a.get('origen') == 'SENSOR']
        level['productos'] = nombres_productos(rows, identifier)
        level['monitoreo'] = estado_nivel(assigned, level_alerts)
        level['sensores'] = assigned


def estructura_reporte(data):
    """Include empty locations and preserve the selected report scope."""
    records = []
    f = data['filtros']
    for warehouse in data['almacenes']:
        wid = warehouse.get('id_almacen', warehouse.get('id'))
        for zone in data['zonas']:
            zid = zone.get('id_zona', zone.get('id'))
            if zone['id_almacen'] != wid or f.get('id_zona') and f['id_zona'] != zid:
                continue
            racks = [r for r in data['racks'] if r['id_zona'] == zid and (not f.get('id_rack') or f['id_rack'] == r['id_rack'])]
            if not racks:
                records.append(dict(almacen=warehouse.get('nombre', wid), zona=zone.get('nombre', zid), rack='', tipo_rack='', nivel='', productos='', monitoreo='', niveles=0, estado=zone.get('estado', 'ACTIVO')))
            for rack in racks:
                levels = [n for n in data['niveles'] if n['id_rack'] == rack['id_rack'] and (not f.get('id_nivel') or f['id_nivel'] == n['id_nivel'])]
                for level in sorted(levels, key=lambda n: -n['numero']) or [None]:
                    records.append(dict(almacen=warehouse.get('nombre', wid), zona=zone.get('nombre', zid), rack=rack.get('codigo', rack['id_rack']),
                        tipo_rack=rack.get('tipo_rack') or 'Tipo no definido', niveles=rack.get('numero_niveles', len(levels)),
                        nivel=level['numero'] if level else '', productos=', '.join(level.get('productos', [])) or 'Vacío' if level else 'Sin niveles',
                        monitoreo=level.get('monitoreo', 'sin_datos') if level else 'sin_datos',
                        estado=' / '.join([zone.get('estado', 'ACTIVO'), rack.get('estado', 'DISPONIBLE'), level.get('estado', 'ACTIVO') if level else 'Sin niveles'])))
    return records
