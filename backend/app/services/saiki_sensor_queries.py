"""Bounded, read-only sensor tools. Tenant identity always comes from authentication."""
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.database.mongodb import get_database
from app.repositories.lectura_repository import LecturaRepository
from app.repositories.rack_repository import RackRepository
from app.services.dispositivo_service import DispositivoService
from app.config.settings import settings

LABELS = {'t_int': ('Temperatura interna', '°C'), 't_amb': ('Temperatura ambiente', '°C'),
          'hum': ('Humedad', '%'), 'corriente': ('Corriente', 'A'), 'puerta': ('Puerta', '')}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def period(text, now=None):
    text = normalize(text)
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo('America/Lima'))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if 'ayer' in text:
        start, end = midnight - timedelta(days=1), midnight
    elif 'este mes' in text:
        start, end = midnight.replace(day=1), local
    elif re.search(r'ultim[oa]s? 7 dias|ultima semana', text):
        start, end = local - timedelta(days=7), local
    elif 'semana' in text:
        start, end = midnight - timedelta(days=local.weekday()), local
    elif '30 dias' in text:
        start, end = local - timedelta(days=30), local
    else:
        start, end = local - timedelta(hours=24), local
    if 'madrugada' in text:
        start = (midnight - timedelta(days=1)) if 'ayer' in text else midnight
        end = min(start + timedelta(hours=6), local)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


async def consultar_sensores(user, question, id_dispositivo=None, id_almacen=None, horas=None):
    from fastapi import HTTPException
    if user is None or not user.es_empresa:
        raise HTTPException(403, 'Se requiere una sesión de empresa para consultar sensores con Saiki.')
    text = normalize(question)
    devices = await DispositivoService.listar(user)
    if id_dispositivo:
        await DispositivoService.obtener_documento(id_dispositivo, user)
        devices = [d for d in devices if d['id_dispositivo'] == id_dispositivo]
    if id_almacen:
        from app.services.acceso_service import AccesoService
        await AccesoService.verificar_almacen(user, id_almacen)
        devices = [d for d in devices if d['id_almacen'] == id_almacen]
    racks = {}
    for rack_id in {d.get('id_rack') for d in devices if d.get('id_rack')}:
        racks[rack_id] = await RackRepository.obtener_por_id(rack_id) or {}
    requested = re.search(r'\brack\s+([a-z0-9]+(?:[-_][a-z0-9]+)*)', text)
    if 'este rack' in text and not id_dispositivo:
        return 'Indica el código del rack o selecciona un dispositivo en Monitoreo para consultar sus sensores.', {}
    if requested and requested[1] not in {'tiene', 'tienen', 'con', 'sin', 'seleccionado'}:
        ids = {key for key, rack in racks.items() if normalize(str(rack.get('codigo', ''))) == requested[1]}
        if not ids:
            return 'No encontré sensores de ese rack en tu empresa. Revisa el código o selecciona un dispositivo en Monitoreo.', {}
        devices = [d for d in devices if d.get('id_rack') in ids]
    if 'desconectad' in text:
        devices = [d for d in devices if not (d.get('estado') or {}).get('conectado')]
    field = 'hum' if 'humedad' in text else 't_amb' if 'ambiente' in text else 't_int' if 'temperatura' in text else 'corriente' if 'corriente' in text else None
    since, until = period(text)
    if id_dispositivo and horas is not None:
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=horas)
    ids = [d['id_dispositivo'] for d in devices]
    lines, evidence = [], {'desde': since.isoformat(), 'hasta': until.isoformat(), 'dispositivos': []}
    temporal = horas is not None or bool(re.search('ayer|semana|mes|madrugada|histor|maxim|minim|promedio|cambio|tendencia|estuvieron|hubo', text))
    if 'alerta' in text or 'incidente' in text or 'fuera de rango' in text or 'madrugada' in text:
        query = {'id_empresa': user.id_empresa, 'id_dispositivo': {'$in': ids}}
        if temporal:
            query['fecha_creacion'] = {'$gte': since, '$lt': until}
        else:
            query['estado'] = {'$in': ['ACTIVA', 'VISTA']}
        alerts = get_database()['alertas']
        count = await alerts.count_documents(query)
        rows = await alerts.find(query, {'_id': 0}).sort('fecha_creacion', -1).limit(50).to_list(length=50)
        lines.append(f"Hay {count} alertas de sensores {'registradas en el periodo' if temporal else 'activas'}. Se muestran hasta 50 incidentes.")
        for a in rows:
            rack = racks.get(a.get('id_rack'), {}).get('codigo', a.get('id_rack') or 'sin rack')
            lines.append(f"Rack {rack}: {a.get('mensaje') or a.get('titulo')} Estado: {a.get('estado')}; fecha {a.get('fecha_creacion')}.")
        evidence.update(total_alertas=count, alertas=rows)
    requested_field = field
    for d in devices[:50]:
        state = d.get('estado') or {}
        latest = state.get('ultima_lectura') or {}
        available = set(d.get('parametros_disponibles', [])) | {p for p in LABELS if latest.get(p) is not None}
        field = requested_field
        if field == 't_int' and 'interna' not in text and 't_int' not in available and 't_amb' in available:
            field = 't_amb'
        if field and field not in available and not temporal:
            continue
        rack = racks.get(d.get('id_rack'), {}).get('codigo') or 'sin rack'
        lines.append(f"{d['nombre']} ({d['id_dispositivo']}) · Rack {rack} · {'conectado' if state.get('conectado') else 'desconectado'}. Tipos: {', '.join(LABELS[p][0] for p in LABELS if p in available) or 'aún sin datos de tipos' }.")
        stats = {}
        for p in LABELS:
            if p == 'puerta' or (field and p != field):
                continue
            limits = (d.get('limites_efectivos') or d.get('limites') or {}).get(p) or {}
            if limits:
                lines.append(f"Umbrales de {LABELS[p][0]}: mínimo {limits.get('min', 'sin configurar')}, máximo {limits.get('max', 'sin configurar')} {LABELS[p][1]}.")
        if temporal:
            stats = await LecturaRepository.resumen(user.id_empresa, d['id_dispositivo'], since, until)
            if field == 't_int' and 'interna' not in text and 't_int' not in stats and 't_amb' in stats:
                field = 't_amb'
            trend = None
            if field and re.search('cambio|evol|tendencia', text):
                midpoint = since + (until - since) / 2
                first = (await LecturaRepository.resumen(user.id_empresa, d['id_dispositivo'], since, midpoint)).get(field)
                second = (await LecturaRepository.resumen(user.id_empresa, d['id_dispositivo'], midpoint, until)).get(field)
                if first and second and first['n'] >= 2 and second['n'] >= 2:
                    trend = second['prom'] - first['prom']
            for p, values in stats.items():
                if field and p != field:
                    continue
                label, unit = LABELS[p]
                lines.append(f"{label}: mínimo {values['min']}, máximo {values['max']}, promedio {values['prom']:.2f} {unit}; {values['n']} mediciones. Estadísticas de minutos del periodo completo.")
            if trend is not None:
                lines.append(f"El promedio de la segunda mitad cambió {trend:+.2f} {LABELS[field][1]} respecto de la primera. Esto describe las lecturas disponibles y no demuestra su causa.")
            elif field and re.search('cambio|evol|tendencia', text):
                lines.append('No hay suficientes mediciones en ambas mitades del periodo para determinar una tendencia.')
            if not stats or (field and field not in stats):
                lines.append('No hay mediciones históricas disponibles en el periodo; no puedo calcular extremos ni tendencias.')
        if field:
            value = latest.get(field)
            timestamp = latest.get('ts')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = None
            if timestamp and timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            fresh = timestamp and 0 <= (datetime.now(timezone.utc) - timestamp).total_seconds() <= settings.sensor_max_reading_age_seconds
            lines.append(f"Último valor registrado: {value} {LABELS[field][1]}, fecha {timestamp}." if value is not None else 'Sin lectura del parámetro solicitado.')
            if not fresh:
                lines.append('La lectura no es reciente; no permite afirmar un estado actual normal.')
        evidence['dispositivos'].append({'id_dispositivo': d['id_dispositivo'], 'rack': rack, 'resumen': stats})
    if not lines:
        lines.append('No hay sensores que coincidan con los filtros en tu empresa.')
    if len(devices) > 50:
        lines.append('Se muestran hasta 50 dispositivos; selecciona un rack para acotar la consulta.')
    if temporal:
        lines.insert(0, f'Periodo: {since.astimezone(ZoneInfo("America/Lima")).isoformat()} a {until.astimezone(ZoneInfo("America/Lima")).isoformat()} (Lima).')
    lines.append('Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica.')
    return '\n\n'.join(lines), evidence
