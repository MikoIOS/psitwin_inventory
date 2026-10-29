"""Isolated browser-test server. Never launch as the production API."""
import os
if os.environ.get('PSITWIN_BROWSER_TEST') != '1':
    raise RuntimeError('This server requires the explicit browser-test environment.')

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
import smtplib
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.database import mongodb
from app.config.settings import settings
from app.services import welcome_email_service
from app.services.google_auth_service import GoogleAuthService
from app.services import registration_link_service

messages = []
smtp_fails = False

def capture_smtp(message):
    if smtp_fails:
        raise smtplib.SMTPException('Controlled SMTP failure')
    messages.append(message)

async def simulated_identity(self, code, flow):
    if code != 'browser-test-code' or not flow.get('nonce') or not flow.get('verifier'):
        raise HTTPException(401, 'Invalid simulated authorization')
    return {'sub': 'browser-test-google-subject', 'email': 'psitwin.browser.test@gmail.com'}

welcome_email_service.send_message = capture_smtp
registration_link_service.send_message = capture_smtp
GoogleAuthService.identity = simulated_identity
from app.main import app

@asynccontextmanager
async def isolated_lifespan(_):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
    await client.admin.command('ping')
    name = 'psitwin_test_browser_' + uuid4().hex
    mongodb.client, mongodb.database = client, client[name]
    try:
        yield
    finally:
        assert name.startswith('psitwin_test_browser_') and len(name.rsplit('_', 1)[-1]) == 32
        await client.drop_database(name)
        client.close()

app.router.lifespan_context = isolated_lifespan

@app.get('/__test/verification-link')
async def verification_link():
    import re
    for message in reversed(messages):
        match = re.search(r'https?://[^\s]+/verificar-correo#token=[^\s]+', message.get_content()) if not message.is_multipart() else None
        if match:
            return {'url': match[0]}
    return {'url': None}

@app.post('/__test/allow-resend')
async def allow_resend():
    await mongodb.database.empresas.update_many({}, {'$unset': {'verificacion_reenvio_despues': ''}})
    return {'ok': True}

@app.post('/__test/reset')
async def reset():
    global smtp_fails
    assert mongodb.database.name.startswith('psitwin_test_browser_')
    await mongodb.client.drop_database(mongodb.database.name)
    messages.clear()
    smtp_fails = False
    return {'ok': True}

@app.post('/__test/smtp-fail')
async def fail_smtp():
    global smtp_fails
    smtp_fails = True
    return {'ok': True}

@app.post('/__test/bson-dates')
async def bson_dates():
    await mongodb.database.empresas.update_many({}, {'$set': {key: datetime.now(timezone.utc) for key in ('fecha_creacion', 'fecha_actualizacion', 'fecha_verificacion_correo')}})
    return {'ok': True}

@app.get('/__test/status')
async def status():
    company = await mongodb.database.empresas.find_one({})
    return {'companies': await mongodb.database.empresas.count_documents({}),
            'outbox': await mongodb.database.bienvenidas_email.count_documents({}),
            'company': {key: company.get(key) for key in ('id_empresa', 'nombre', 'nombre_ceo', 'ruc', 'sector', 'telefono', 'correo')} if company else None,
            'google_linked': bool(company and company.get('google_sub')),
            'argon2id': bool(company and company.get('password', '').startswith('$argon2id$')),
            'sent': len(messages),
            'personalized': bool(messages and messages[-1].get_body(preferencelist=('html',)) and 'Carlos' in messages[-1].get_body(preferencelist=('html',)).get_content() and '{{nombre}}' not in messages[-1].get_body(preferencelist=('html',)).get_content()),
            'sender': str(messages[-1]['From']) if messages else None}
