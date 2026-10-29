"""Read-only sensor evidence, scoped through the existing device service."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from math import isfinite
from app.config.settings import settings

from app.services.dispositivo_service import DispositivoService
from app.repositories.alerta_repository import AlertaRepository
from app.repositories.almacen_repository import AlmacenRepository
from app.repositories.zona_repository import ZonaRepository
from app.repositories.rack_repository import RackRepository


async def sensor_report(user, id_dispositivo=None, horas=24):
    if user is None:
        raise ValueError("Se requiere una sesión para consultar sensores")
    devices = await DispositivoService.listar(user)
    if id_dispositivo:
        await DispositivoService.obtener_documento(id_dispositivo, user)
        devices = [device for device in devices if device['id_dispositivo'] == id_dispositivo]
    ids = {d["id_dispositivo"] for d in devices}
    history = [a for a in await AlertaRepository().listar_por_empresa(user.id_empresa)
               if a.get("id_dispositivo") in ids]
    history.sort(key=lambda a: str(a.get("fecha_creacion", "")), reverse=True)
    counts = Counter((a.get("id_dispositivo"), a.get("parametro")) for a in history)
    lines = []
    readings_evidence = None
    connected = False
    for device in devices:
        state = device.get("estado") or {}
        latest = state.get('ultima_lectura') or {}
        timestamp = latest.get('ts')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                timestamp = None
        if isinstance(timestamp, datetime) and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        fresh = isinstance(timestamp, datetime) and 0 <= (datetime.now(timezone.utc) - timestamp).total_seconds() <= settings.sensor_max_reading_age_seconds
        connected |= bool(state.get('conectado') and latest and fresh)
        warehouse = await AlmacenRepository.obtener_por_id(device["id_almacen"])
        zone = await ZonaRepository.obtener_por_id(device["id_zona"])
        rack = await RackRepository.obtener_por_id(device["id_rack"]) if device.get("id_rack") else None
        location = " / ".join(str(x) for x in [(warehouse or {}).get("nombre"), (zone or {}).get("nombre"), (rack or {}).get("codigo")] if x)
        lines.append(f"{device['nombre']} — {location or 'Ubicación sin nombre registrado'}: "
                     + (f"última lectura {state['ultima_lectura']}" if state.get("conectado") and state.get("ultima_lectura") else "Sin datos disponibles"))
        if latest and not fresh:
            lines.append('Lectura desactualizada o sin fecha válida; no confirma el estado actual de la medición.')
        if id_dispositivo:
            until = datetime.now(timezone.utc)
            since = until - timedelta(hours=horas)
            readings_evidence = await DispositivoService.lecturas(id_dispositivo, user, since, until)
            points = readings_evidence.get('puntos', [])
            lines.append(f"Historial de lecturas de {device['nombre']}: {len(points)} puntos devueltos para las últimas {horas} horas; resolución {readings_evidence.get('resolucion')}. Son datos históricos, no prueba de una conexión actual.")
            for parameter, unit in [('t_int', '°C'), ('t_amb', '°C'), ('hum', '%'), ('corriente', 'A')]:
                summary = readings_evidence.get('resumen', {}).get(parameter)
                if summary:
                    lines.append(f"{parameter}: mínimo {summary['min']} {unit}, máximo {summary['max']} {unit}, promedio {summary['prom']:.2f} {unit}; {summary['n']} mediciones del periodo completo por minutos.")
                    continue
                lows, highs = [], []
                for point in points:
                    value = point.get(parameter)
                    low, high = (value.get('min'), value.get('max')) if isinstance(value, dict) else (value, value)
                    if type(low) in (int, float) and isfinite(low): lows.append(low)
                    if type(high) in (int, float) and isfinite(high): highs.append(high)
                if lows and highs:
                    lines.append(f"{parameter}: mínimo {min(lows)} {unit}, máximo {max(highs)} {unit} entre los puntos devueltos; no se infiere una causa ni se completan lecturas ausentes.")
    priority = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}
    active = sorted([a for a in history if a.get("estado") in {"ACTIVA", "VISTA"}], key=lambda a: priority.get(a.get("nivel_riesgo"), 4))
    names = {d['id_dispositivo']: d['nombre'] for d in devices}
    for alert in active:
        lines.append(f"{alert.get('nivel_riesgo', '')}: {names[alert['id_dispositivo']]} — {alert.get('mensaje') or alert.get('titulo')}. "
                     f"Parámetro: {alert.get('parametro')}; valor observado: {alert.get('valor')}; límite: {alert.get('limite')}; extremo: {alert.get('valor_extremo')}; inicio: {alert.get('inicio') or alert.get('fecha_creacion')}.")
        if counts[(alert.get('id_dispositivo'), alert.get('parametro'))] > 1:
            lines.append("Hay episodios registrados del mismo parámetro en este equipo. Conviene inspeccionar y calibrar el sensor, contrastar con una medición independiente y programar mantenimiento preventivo. Evaluar reemplazo solo si una revisión técnica confirma fallas persistentes.")
    for device in devices:
        alerts = [a for a in active if a.get('id_dispositivo') == device['id_dispositivo']]
        parameters = {a.get('parametro') for a in alerts}
        if any(a.get('tipo_alerta') == 'SENSOR_SIN_DATOS' for a in alerts):
            lines.append(f"{device['nombre']}: la falta de datos puede deberse a conexión, alimentación o sensor; no permite concluir que falló la refrigeración. Revisa la comunicación y contrasta la temperatura con un instrumento independiente.")
        if 't_int' in parameters and 'corriente' in parameters:
            lines.append(f"{device['nombre']}: hay alertas abiertas de temperatura interna y corriente. Revisa alimentación y refrigeración con personal técnico; las alertas abiertas no prueban simultaneidad de las mediciones ni una causa concreta.")
        if 't_int' in parameters and 'puerta' in parameters:
            lines.append(f"{device['nombre']}: también existe una alerta de puerta. Comprueba su cierre antes de atribuir la temperatura al compresor o al sensor.")
    if active:
        lines.append("Una lectura anormal no confirma una avería. Contrasta el sensor con un instrumento independiente; revisa puerta, alimentación y refrigeración. Temperatura y corriente anormales simultáneas justifican revisar el sistema de frío, pero no prueban su causa.")
    elif devices:
        lines.append("No hay alertas abiertas registradas en los equipos visibles. Esto no confirma que todos los equipos funcionen correctamente.")
    if history:
        lines.append(f"Historial disponible: {len(history)} incidentes registrados; se muestran los 20 más recientes. No se infiere frecuencia sin un periodo de observación completo.")
        for alert in history[:20]:
            lines.append(f"{names[alert['id_dispositivo']]}: {alert.get('estado')} — {alert.get('mensaje') or alert.get('titulo')}; fecha {alert.get('fecha_creacion')}; parámetro {alert.get('parametro')}; valor {alert.get('valor')}; límite {alert.get('limite')}.")
        for (device_id, parameter), count in counts.items():
            if count > 1:
                lines.append(f"{names[device_id]}: {count} episodios registrados para {parameter}. Recomiendo inspección, contraste y posible calibración del sensor, y mantenimiento preventivo del sistema de frío. El historial por sí solo no justifica reemplazar el equipo; hace falta confirmación técnica de fallas persistentes.")
    answer = ("Sin datos disponibles. No hay lecturas actuales de sensores conectados.\n\n" if not connected else "") + "\n\n".join(lines)
    return answer, {"dispositivos": devices, "incidentes": history[:100], "historial_total": len(history), "historial_limite": 100, "lecturas": readings_evidence}
