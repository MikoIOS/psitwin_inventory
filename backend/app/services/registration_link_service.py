"""Single-use email links, using the existing verification collection and SMTP."""
import asyncio
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from fastapi import HTTPException
from pymongo import ReturnDocument
from app.config.settings import settings
from app.database.mongodb import get_database
from app.services.smtp_transport import send_message
from app.services.welcome_email_service import WelcomeEmailService, application_url


class RegistrationLinkService:
    def __init__(self, database_provider=None, sender=None):
        self.database = database_provider or get_database
        self.sender = sender or send_message

    async def send(self, email):
        db = self.database()
        company = await db.empresas.find_one({'correo': email, 'requiere_verificacion_registro': True, 'correo_verificado': False})
        if not company:
            return
        now = datetime.now(timezone.utc)
        # Atomic lease survives concurrent resend requests and SMTP failures.
        lease = await db.empresas.find_one_and_update(
            {'id_empresa': company['id_empresa'], 'correo_verificado': False,
             '$or': [{'verificacion_reenvio_despues': {'$lte': now}}, {'verificacion_reenvio_despues': {'$exists': False}}]},
            {'$set': {'verificacion_reenvio_despues': now + timedelta(seconds=settings.email_verification_cooldown_seconds)}},
            return_document=ReturnDocument.AFTER)
        if not lease:
            return
        token = secrets.token_urlsafe(48)
        digest = hashlib.sha256(token.encode()).hexdigest()
        await db.email_verifications.update_one({'_id': 'registro:' + company['id_empresa']}, {'$set': {
            'token_hash': digest, 'entity_id': company['id_empresa'], 'email': email,
            'used': False, 'expires_at': now + timedelta(minutes=settings.email_verification_ttl_minutes),
            'created_at': now}}, upsert=True)
        url = application_url().rstrip('/') + '/verificar-correo#token=' + token
        message = EmailMessage()
        message['From'] = formataddr((settings.smtp_from_name, settings.smtp_from or settings.smtp_user))
        message['To'] = email
        message['Subject'] = 'Verifica tu correo de PsiTwin'
        message.set_content(f'Confirma tu correo para activar tu empresa en PsiTwin:\n\n{url}\n\n'
                            f'Este enlace caduca en {settings.email_verification_ttl_minutes} minutos y solo puede utilizarse una vez. '
                            'Si no solicitaste esta cuenta, ignora este mensaje.')
        try:
            if not settings.email_enabled:
                raise RuntimeError('Email disabled')
            await asyncio.to_thread(self.sender, message)
        except Exception:
            # Never log message content, tokens, SMTP credentials or provider errors.
            logging.getLogger(__name__).error('registration_link_delivery_failed empresa=%s', company['id_empresa'])

    async def confirm(self, token):
        db = self.database()
        digest = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        # Updating the account first makes activation recoverable after a crash;
        # only one request can change its verification state.
        record = await db.email_verifications.find_one({'token_hash': digest, 'used': False, 'expires_at': {'$gt': now}})
        if not record:
            raise HTTPException(400, 'El enlace no es válido, ya fue utilizado o ha caducado. Solicita otro enlace.')
        company = await db.empresas.find_one_and_update(
            {'id_empresa': record['entity_id'], 'correo': record['email'], 'correo_verificado': False,
             'requiere_verificacion_registro': True},
            {'$set': {'correo_verificado': True, 'fecha_verificacion_correo': now}},
            return_document=ReturnDocument.AFTER)
        if not company:
            raise HTTPException(400, 'Este enlace ya fue utilizado o la cuenta no está disponible.')
        await db.email_verifications.update_one({'_id': record['_id']}, {'$set': {'used': True, 'used_at': now}})
        welcome = WelcomeEmailService(self.database)
        await welcome.enqueue(company)
        return company['id_empresa']
