"""User-message-only report intent and server-bound confirmation state machine."""
import re
from uuid import uuid4
from app.services.clasificacion_service import normalizar
from app.services.saiki_inventario_detallado import inventario_contextual
from app.services.inventario_reportes_service import InventarioReportesService
from app.dto.inventario_consulta_dto import ReporteSolicitud, InventarioFiltros

service = InventarioReportesService()


def prompt(action):
    state = action['estado']
    if state == 'ELEGIR_FORMATO': return 'Puedo enviarlo al correo registrado de tu empresa. ¿Lo prefieres en Excel o PDF?'
    if state == 'CONFIRMAR': return f"Prepararé {action['formato'].upper()} para {action['destinatario']}. Alcance: {action['alcance']}. Productos: {action['resumen']['productos_distintos']}. ¿Confirmas el envío?"
    if state == 'ACEPTADO_SMTP': return 'El servidor de correo aceptó el reporte para el correo registrado de tu empresa. Esto no confirma que haya llegado a la bandeja de entrada.'
    if state == 'CANCELADO': return 'Envío cancelado. No se envió este reporte.'
    if state in {'GENERANDO','ENVIANDO'}: return 'El reporte ya se está procesando. No iniciaré un segundo envío.'
    if state == 'REVISAR_ENVIO': return 'No se pudo confirmar la respuesta del servidor SMTP. No repetiré el envío automáticamente para evitar duplicados.'
    return 'No pude enviar el reporte. Revisa la configuración del servicio de correo; puedes descargarlo desde Inventario.'


async def report_answer(data, user):
    text = normalizar(data.message or '').strip().strip('¿?¡!. ,')
    identifier = data.context.get('reporte_accion')
    if isinstance(identifier,str) and re.fullmatch(r'(?:si(?:,? envialo)?|confirmo(?: el envio)?|enviar|envialo|pdf|excel|xlsx|no|cancelar|cancela)', text):
        if text in {'no','cancelar','cancela'}: action = await service.cancelar(user,identifier)
        elif text in {'pdf','excel','xlsx'}: action = await service.formato(user,identifier,'pdf' if text=='pdf' else 'xlsx')
        else: action = await service.confirmar(user,identifier)
        return prompt(action), {'reporte_accion':action}
    report = bool(re.search(r'reporte|resumen.*inventario|inventario.*(?:excel|pdf|correo)|(?:excel|pdf).*inventario|envia.*alertas',text))
    if not report: return None
    if re.search(r'que contiene|que incluye',text):
        return 'El reporte contiene existencias por producto y ubicación, unidades, umbrales configurados, alertas, filtros, empresa, usuario y fecha de generación. No incluye valoraciones que no estén registradas.', {}
    if re.search(r'anterior|compar',text):
        result = await inventario_contextual(data,user)
        from app.database.mongodb import get_database
        previous = await get_database()['reportes_inventario'].find_one({'id_empresa':user.id_empresa,'estado':'ACEPTADO_SMTP','filtros':result['filtros'],'instantanea':{'$exists':True}}, {'_id':0}, sort=[('fecha_actualizacion',-1)])
        if not previous: return 'No hay un reporte anterior con instantánea verificable para estos filtros. No puedo inventar una comparación.', {}
        before = {p['id_producto']:p for p in previous['instantanea']['productos']}
        current = {p['id_producto']:p for p in result['productos']}
        changes = []
        for key in sorted(set(before)|set(current)):
            a,b=before.get(key),current.get(key)
            name=(b or a)['producto']
            if not a: changes.append(f'{name}: aparece ahora; antes no tenía registro en el reporte.')
            elif not b: changes.append(f'{name}: no aparece en el inventario actual; no se asume stock cero.')
            elif a['unidad'] == b['unidad'] and a['stock_actual'] != b['stock_actual']: changes.append(f"{name}: {a['stock_actual']:g} → {b['stock_actual']:g} {b['unidad']}.")
        return ('Cambios frente al reporte de ' + str(previous['instantanea']['generado_en']) + ':\n' + ('\n'.join(changes) or 'No hay diferencias de cantidades registradas.')), {'comparacion_reporte':{'id_anterior':previous['id_reporte'],'cambios':changes}}
    if not re.search(r'envia|manda|descarg|genera|prepara|quiero',text): return None
    result = await inventario_contextual(data,user)
    filters = InventarioFiltros(**result['filtros'])
    formato = 'pdf' if 'pdf' in text else 'xlsx' if re.search('excel|xlsx',text) else None
    if re.search(r'envia|manda|correo',text):
        if re.search(r'[\w.+-]+@[\w.-]+', text): return 'Solo puedo enviar al correo registrado y verificado de tu empresa; no utilizo destinatarios escritos en el chat.', {}
        action = await service.solicitar(user,ReporteSolicitud(formato=formato,filtros=filters,clave_idempotencia='saiki-'+uuid4().hex))
        return prompt(action), {'reporte_accion':action}
    if not formato: return '¿Quieres descargar el reporte en Excel o PDF? Puedes elegir el formato desde Exportar inventario.', {'reporte_descarga':{'filtros':result['filtros']}}
    return f"Puedes descargar el reporte {formato.upper()} con {result['resumen']['productos_distintos']} productos distintos del alcance consultado.", {'reporte_descarga':{'formato':formato,'filtros':result['filtros']},'resumen_reporte':result['resumen']}
