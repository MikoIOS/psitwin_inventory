import re
from datetime import datetime, timedelta, timezone
from app.services.saiki_inventario_detallado import inventario_contextual
from app.services.clasificacion_service import normalizar


async def respuesta_plano(data, user):
    text = normalizar(data.message or '')
    if not re.search(r'tipo.*rack|cuantos niveles|niveles.*vaci|donde.*(?:esta|hay|encuentr)|productos.*nivel|rack.*recient|agrego.*rack|zonas.*almacen', text):
        return None
    result = await inventario_contextual(data, user)
    f = result['filtros']
    zones = [z for z in result['zonas'] if not f['id_zona'] or f['id_zona'] == z.get('id_zona', z.get('id'))]
    racks = [r for r in result['racks'] if (not f['id_rack'] or f['id_rack'] == r['id_rack']) and (not f['id_zona'] or f['id_zona'] == r['id_zona'])]
    levels = [n for n in result['niveles'] if n['id_rack'] in {r['id_rack'] for r in racks} and (not f['id_nivel'] or n['id_nivel'] == f['id_nivel']) and n.get('estado', 'ACTIVO') == 'ACTIVO']
    if 'recient' in text or 'agrego' in text:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        racks = [r for r in racks if isinstance(r.get('fecha_creacion'), datetime) and r['fecha_creacion'].replace(tzinfo=timezone.utc) >= cutoff]
        answer = 'Racks agregados en los últimos 7 días: ' + (', '.join(r.get('codigo', r['id_rack']) for r in racks) or 'ninguno registrado')
    elif 'tipo' in text:
        answer = '\n'.join(f"Rack {r.get('codigo', r['id_rack'])}: {r['tipo_rack']}" for r in racks)
    elif 'cuantos niveles' in text:
        answer = '\n'.join(f"Rack {r.get('codigo', r['id_rack'])}: {sum(n['id_rack'] == r['id_rack'] for n in levels)} niveles" for r in racks)
    elif 'zonas' in text:
        answer = 'Zonas actuales: ' + ', '.join(z.get('nombre', z.get('codigo', 'Sin nombre')) for z in zones if z.get('estado', 'ACTIVO') == 'ACTIVO')
    elif 'donde' in text:
        rows = [r for r in result['ubicaciones'] if r['stock_actual'] > 0 and not r.get('rechazado')]
        answer = '\n'.join(sorted({f"{r['producto']}: {r['almacen']} / {r['zona']} / Rack {r['rack']} / Nivel {r['nivel']}" for r in rows})) or 'No hay existencias disponibles para ese producto.'
    else:
        if 'vaci' in text:
            levels = [n for n in levels if not n['productos']]
        if 'alerta' in text:
            levels = [n for n in levels if n['monitoreo'] in {'critico', 'advertencia'}]
        codes = {r['id_rack']: r.get('codigo', r['id_rack']) for r in racks}
        answer = '\n'.join(f"Rack {codes[n['id_rack']]} / Nivel {n['numero']}: {', '.join(n['productos']) or 'Vacío'}" for n in levels) or 'No hay niveles que coincidan.'
    return answer, {'plano': {'racks': racks, 'niveles': levels}, 'generado_en': result['generado_en']}
