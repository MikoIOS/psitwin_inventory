"""Authorized exports and a durable, explicit-confirmation mail outbox."""
import asyncio
import hashlib
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from uuid import uuid4
from fastapi import HTTPException
from pymongo import ReturnDocument
from app.database.mongodb import get_database
from app.config.settings import settings
from app.dto.inventario_consulta_dto import InventarioFiltros
from app.services.inventario_consulta_service import consultar_inventario
from app.services.inventario_reportes_archivos import generar_archivo, label
from app.services.smtp_transport import send_message, DeliveryUncertain

SENDER = 'psitwin2026@gmail.com'
ACTOR = lambda user: user.id_operario or user.id_empresa

async def preparar_datos(user, filtros):
    data = await consultar_inventario(user, filtros)
    db = get_database()
    company = await db['empresas'].find_one({'id_empresa': user.id_empresa}, {'_id': 0})
    if not company: raise HTTPException(404, 'Empresa no encontrada')
    actor = company if user.es_empresa else await db['operarios'].find_one({'id_operario': user.id_operario, 'id_empresa': user.id_empresa}, {'_id': 0}) or {}
    data.update(empresa=company.get('nombre') or 'Empresa', solicitante=actor.get('nombre_ceo') if user.es_empresa else actor.get('nombre'))
    data['solicitante'] = data['solicitante'] or ACTOR(user)
    f = data['filtros']
    parts = [w.get('nombre') or 'Almacén' for w in data['almacenes']] if f['id_almacen'] else ['Empresa completa']
    for key, collection, id_key, name in [('id_zona','zonas','id_zona','nombre'), ('id_rack','racks','id_rack','codigo'), ('id_nivel','niveles','id_nivel','codigo')]:
        if f[key]: parts.append(next((r.get(name) or f[key] for r in data[collection] if (r.get(id_key) or r.get('id')) == f[key]), f[key]))
    if f['busqueda']: parts.append('Búsqueda: ' + f['busqueda'])
    if f['estado'] != 'todos': parts.append('Estado: ' + f['estado'])
    data['alcance'] = ' / '.join(parts)
    return data

async def destinatario(user):
    if not user.es_empresa: raise HTTPException(403, 'Solo la empresa puede confirmar envíos por correo')
    company = await get_database()['empresas'].find_one({'id_empresa': user.id_empresa}, {'_id': 0})
    if not company or company.get('correo_verificado') is not True or not company.get('correo'):
        raise HTTPException(409, 'Verifica primero el correo registrado de la empresa')
    return company['correo']


def publico(row):
    return {k: row.get(k) for k in ('id_reporte','estado','formato','destinatario','alcance','filtros','resumen','expira_en','codigo_error','fecha_actualizacion')}

class InventarioReportesService:
    def __init__(self, sender=None): self.sender = sender or send_message
    async def obtener(self, user, identifier):
        if not user.es_empresa: raise HTTPException(403, 'No tiene permiso para los envíos')
        row = await get_database()['reportes_inventario'].find_one({'id_reporte': identifier, 'id_empresa': user.id_empresa, 'actor': ACTOR(user)}, {'_id': 0})
        if not row: raise HTTPException(404, 'Reporte no encontrado')
        return row

    async def _solicitar(self, user, request):
        recipient = await destinatario(user)
        data = await preparar_datos(user, request.filtros)
        signature = hashlib.sha256((user.id_empresa + ':' + ACTOR(user) + ':' + request.clave_idempotencia).encode()).hexdigest()
        collection = get_database()['reportes_inventario']
        previous = await collection.find_one({'_id': signature})
        if previous:
            if previous['formato'] != request.formato or previous['filtros'] != data['filtros'] or previous['destinatario'] != recipient:
                raise HTTPException(409, 'La clave ya corresponde a otra solicitud de reporte')
            return publico(previous)
        now = datetime.now(timezone.utc)
        if await collection.count_documents({'id_empresa': user.id_empresa, 'actor': ACTOR(user), 'fecha_creacion': {'$gt': now - timedelta(minutes=10)}}) >= 5:
            raise HTTPException(429, 'Espera unos minutos antes de solicitar otro reporte')
        row = {'_id': signature, 'id_reporte': str(uuid4()), 'id_empresa': user.id_empresa, 'actor': ACTOR(user),
            'estado': 'CONFIRMAR' if request.formato else 'ELEGIR_FORMATO', 'formato': request.formato,
            'destinatario': recipient, 'filtros': data['filtros'], 'alcance': data['alcance'], 'resumen': data['resumen'],
            'fecha_creacion': now, 'fecha_actualizacion': now, 'expira_en': now + timedelta(minutes=10)}
        await collection.update_one({'_id': signature}, {'$setOnInsert': row}, upsert=True)
        return publico(await collection.find_one({'_id': signature}))

    async def formato(self, user, identifier, formato):
        row = await self.obtener(user, identifier)
        if row['estado'] != 'ELEGIR_FORMATO': return publico(row)
        if row['expira_en'].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc): raise HTTPException(410, 'La confirmación expiró; solicita un reporte nuevo')
        await get_database()['reportes_inventario'].update_one({'id_reporte': identifier, 'estado': 'ELEGIR_FORMATO'}, {'$set': {'formato': formato, 'estado':'CONFIRMAR','fecha_actualizacion':datetime.now(timezone.utc)}})
        return publico(await self.obtener(user, identifier))

    async def cancelar(self, user, identifier):
        await self.obtener(user, identifier)
        await get_database()['reportes_inventario'].update_one({'id_reporte': identifier, 'estado': {'$in':['CONFIRMAR','ELEGIR_FORMATO']}}, {'$set':{'estado':'CANCELADO','fecha_actualizacion':datetime.now(timezone.utc)}})
        return publico(await self.obtener(user, identifier))

    async def confirmar(self, user, identifier):
        row = await self.obtener(user, identifier)
        if row['estado'] != 'CONFIRMAR': return publico(row)
        now = datetime.now(timezone.utc)
        if row['expira_en'].replace(tzinfo=timezone.utc) < now: raise HTTPException(410, 'La confirmación expiró; solicita un reporte nuevo')
        if await destinatario(user) != row['destinatario']: raise HTTPException(409, 'Cambió el correo registrado; solicita una confirmación nueva')
        collection = get_database()['reportes_inventario']
        claimed = await collection.find_one_and_update({'id_reporte':identifier,'estado':'CONFIRMAR','id_empresa':user.id_empresa,'actor':ACTOR(user)}, {'$set':{'estado':'GENERANDO','fecha_actualizacion':now}}, return_document=ReturnDocument.AFTER)
        if not claimed: return publico(await self.obtener(user, identifier))
        state, code, snapshot = 'ERROR', None, None
        try:
            if not settings.email_enabled or not settings.smtp_secret or (settings.smtp_user or '').lower() != SENDER or settings.smtp_host.lower() != 'smtp.gmail.com' or (settings.smtp_port != 465 and not settings.smtp_use_tls):
                raise ValueError('SMTP_NO_CONFIGURADO')
            data = await preparar_datos(user, InventarioFiltros(**row['filtros']))
            blob, mime, filename = await asyncio.to_thread(generar_archivo, data, row['formato'])
            if not blob: raise RuntimeError('ARCHIVO_VACIO')
            if len(blob) > 10 * 1024 * 1024: raise ValueError('ARCHIVO_DEMASIADO_GRANDE')
            message = EmailMessage()
            message['From'], message['To'] = SENDER, row['destinatario']
            message['Subject'] = 'PsiTwin Inventory — Resumen de inventario'
            message['Message-ID'] = f"<inventario.{identifier}@psitwin.inventory>"
            message.set_content('Hola,\n\nAdjuntamos el resumen actualizado del inventario de tu empresa, generado desde PsiTwin Inventory.\n\n'
                f"Fecha de generación: {label(data['generado_en'])}\nEmpresa: {data['empresa']}\nFormato: {row['formato'].upper()}\nAlcance: {data['alcance']}\n\n"
                'Este reporte contiene las existencias y alertas registradas al momento de su generación.\n\nSaludos,\nPsiTwin Inventory')
            maintype, subtype = mime.split('/',1)
            message.add_attachment(blob, maintype=maintype, subtype=subtype, filename=filename)
            await collection.update_one({'id_reporte':identifier}, {'$set':{'estado':'ENVIANDO','fecha_actualizacion':datetime.now(timezone.utc)}})
            await asyncio.to_thread(self.sender, message)
            state = 'ACEPTADO_SMTP'
            snapshot = {'resumen':data['resumen'],'productos':data['productos'],'generado_en':data['generado_en']}
        except DeliveryUncertain: state, code = 'REVISAR_ENVIO', 'CONFIRMACION_SMTP_DESCONOCIDA'
        except smtplib.SMTPAuthenticationError: code = 'SMTP_AUTENTICACION'
        except (OSError, smtplib.SMTPConnectError): code = 'SMTP_CONEXION'
        except ValueError: code = 'CONFIGURACION_O_LIMITE'
        except Exception: code = 'GENERACION_O_ENVIO'
        update = {'estado':state,'codigo_error':code,'fecha_actualizacion':datetime.now(timezone.utc)}
        if snapshot: update['instantanea'] = snapshot
        await collection.update_one({'id_reporte':identifier,'estado':{'$in':['GENERANDO','ENVIANDO']}}, {'$set':update})
        return publico(await self.obtener(user, identifier))

    async def solicitar(self, user, request):
        from app.services.stock_lock import bloqueo_recurso
        async with bloqueo_recurso('reporte-solicitud:' + user.id_empresa + ':' + ACTOR(user)):
            return await self._solicitar(user, request)
