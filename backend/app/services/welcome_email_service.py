"""Durable welcome outbox. SMTP failures never roll back a registered company."""
import asyncio
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

from pymongo import ReturnDocument
from app.config.settings import settings
from app.database.mongodb import get_database
from app.services.smtp_transport import send_message, DeliveryUncertain

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
SUBJECT = '¡Bienvenido a PsiTwin! 🚀'


def application_url():
    url = (settings.frontend_url or '').strip()
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('FRONTEND_URL debe ser una URL HTTP(S) válida')
    return url


def build_welcome_message(company):
    name = str(company.get('nombre_ceo') or '').strip()
    if not name: raise ValueError('La empresa debe registrar el nombre del CEO')
    url = application_url()
    message = EmailMessage()
    message['From'] = formataddr((settings.smtp_from_name, settings.smtp_user))
    message['To'] = company['correo']
    message['Subject'] = SUBJECT
    message['Message-ID'] = f"<bienvenida.{company['id_empresa']}@psitwin.inventory>"
    message.set_content(f'¡Hola, {name}! 👋\n\n¡Bienvenido a PsiTwin Ψ!\n\n'
        'Nos alegra que formes parte de nuestra comunidad.\n\n'
        'En PsiTwin creemos que una gestión inteligente hace la diferencia. Por eso, nuestro compromiso es acompañarte '
        'con herramientas que te ayuden a controlar tu inventario, anticiparte a posibles problemas y tomar mejores decisiones.\n\n'
        'Tú haces crecer tu negocio. Nosotros te ayudamos a estar un paso adelante.\n\n'
        'Estamos felices de comenzar este camino contigo.\n\n'
        '¡Bienvenido a una forma más inteligente de gestionar tu almacén!\n\n'
        f'Ir a PsiTwin: {url}\n\nGrupo 404: Opportunity Found')
    html = Template((ROOT / 'templates/welcome.html').read_text(encoding='utf-8')).substitute(
        nombre=escape(name), frontend_url=escape(url, quote=True))
    if len(html.encode('utf-8')) > 20000 or any(marker in html for marker in ('{{nombre}}', '[Nombre]', '$nombre', 'data:image/')):
        raise ValueError('La bienvenida contiene marcadores o excede el tama?o permitido')
    message.add_alternative(html, subtype='html')
    for filename, cid in (('welcome-header.jpg', 'psitwin-welcome-art'), ('welcome-logo.jpg', 'psitwin-logo')):
        message.get_payload()[-1].add_related((ROOT / 'assets/email' / filename).read_bytes(),
            maintype='image', subtype='jpeg', cid=f'<{cid}>', disposition='inline', filename='Bienvenida-' + filename)
    return message


class WelcomeEmailService:
    def __init__(self, database_provider=None, sender=None):
        self.database = database_provider or get_database
        self.sender = sender or send_message

    def collection(self): return self.database()['bienvenidas_email']

    async def enqueue(self, company):
        now = datetime.now(timezone.utc)
        await self.collection().update_one({'_id': f"bienvenida:{company['id_empresa']}"}, {'$setOnInsert': {
            'id_empresa': company['id_empresa'], 'status': 'PENDIENTE', 'intentos': 0,
            'fecha_creacion': now, 'fecha_actualizacion': now}}, upsert=True)

    async def status(self, tenant):
        row = await self.collection().find_one({'_id': f'bienvenida:{tenant}'}, {'_id': 0})
        return {k: row[k] for k in ('status', 'intentos', 'fecha_envio', 'error_code') if k in row} if row else {'status': 'NO_SOLICITADO', 'intentos': 0}

    async def deliver(self, tenant):
        collection = self.collection()
        key = f'bienvenida:{tenant}'
        row = await collection.find_one_and_update({'_id': key, 'status': {'$in': ['PENDIENTE', 'ERROR', 'CONFIGURACION_PENDIENTE', 'CONFIRMACION_PENDIENTE']}},
            {'$set': {'status': 'ENVIANDO', 'fecha_actualizacion': datetime.now(timezone.utc)}, '$inc': {'intentos': 1}},
            return_document=ReturnDocument.AFTER)
        if not row: return await self.status(tenant)
        status, error_code = 'ERROR', None
        try:
            company = await self.database()['empresas'].find_one({'id_empresa': tenant}, {'_id': 0})
            if not company: raise ValueError('Empresa no encontrada')
            if company.get('correo_verificado') is not True:
                status, error_code = 'CONFIRMACION_PENDIENTE', 'CORREO_NO_VERIFICADO'
            elif not settings.email_enabled or not settings.smtp_secret or not settings.smtp_user:
                status, error_code = 'CONFIGURACION_PENDIENTE', 'SMTP_NO_CONFIGURADO'
            else:
                message = build_welcome_message(company)
                await asyncio.to_thread(self.sender, message)
                status = 'ENVIADO'
        except DeliveryUncertain:
            status, error_code = 'REVISAR_ENVIO', 'SMTP_CONFIRMACION_DESCONOCIDA'
        except Exception as error:
            error_code = type(error).__name__  # Never persist SMTP responses or credentials.
        update = {'status': status, 'error_code': error_code, 'fecha_actualizacion': datetime.now(timezone.utc)}
        if status == 'ENVIADO': update['fecha_envio'] = datetime.now(timezone.utc)
        await collection.update_one({'_id': key, 'status': 'ENVIANDO'}, {'$set': update})
        logger.info('welcome_delivery empresa=%s status=%s code=%s', tenant, status, error_code)
        return await self.status(tenant)

    async def deliver_safely(self, tenant):
        try: return await self.deliver(tenant)
        except Exception:
            # A crash after SMTP acceptance leaves ENVIANDO for manual review, never an automatic duplicate.
            logger.error('welcome_dispatch_failed empresa=%s', tenant)
            return {'status': 'ERROR', 'error_code': 'OUTBOX_NO_DISPONIBLE'}
