import asyncio
import re
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from fastapi import FastAPI
from app.controllers import empresa_controller as controller
from app.services.registration_link_service import RegistrationLinkService
from app.services import welcome_email_service
from tests.test_google_auth import isolated_database

BODY = dict(nombre='Empresa enlaces', nombre_ceo='Jinwoo', ruc='20100070970', sector='Alimentos',
            telefono='999111222', correo='enlaces@gmail.com', password='password-segura-2026', password_confirmation='password-segura-2026')

def test_public_oauth_routes_are_retired():
    from app.main import app
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            for path in ('start', 'complete', 'register', 'link', 'registration/status'):
                assert (await client.post('/api/v1/auth/google/' + path, json={})).status_code == 404
    asyncio.run(run())

def test_registration_activation_resend_expiry_and_legacy(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            sent = []
            monkeypatch.setattr(controller, 'link_service', RegistrationLinkService(lambda: db, sent.append))
            monkeypatch.setattr(controller, 'welcome_email_service', welcome_email_service.WelcomeEmailService(lambda: db, sent.append))
            monkeypatch.setattr(controller.link_service, 'sender', sent.append)
            from app.config.settings import settings
            monkeypatch.setattr(settings, 'email_enabled', True)
            app = FastAPI(); app.include_router(controller.router)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.post('/auth/register', json={**BODY, 'password_confirmation': 'different-password'})).status_code == 422
                assert (await client.post('/auth/register', json={**BODY, 'correo': 'bad@example.com'})).status_code == 422
                assert (await client.post('/auth/register', json={**BODY, 'ruc': '20100070971'})).status_code == 422
                response = await client.post('/auth/register', json={**BODY, 'correo': ' ENLACES@gmail.com '})
                assert response.status_code == 201, response.text
                company = await db.empresas.find_one({})
                assert company['nombre_ceo'] == 'Jinwoo' and not company['correo_verificado']
                assert company['password'].startswith('$argon2id$')
                credentials = {'correo': BODY['correo'], 'password': BODY['password']}
                assert (await client.post('/auth/login', json=credentials)).status_code == 403
                assert len(sent) == 1
                token = re.search(r'#token=([^\s]+)', sent[0].get_content())[1]
                record = await db.email_verifications.find_one({})
                assert token not in str(record) and record['token_hash']
                assert (await client.post('/auth/verification/confirm', json={'token': 'f' * 64})).status_code == 400
                # Resend cooldown avoids a second delivery; expiry is checked by the API, not only TTL cleanup.
                assert (await client.post('/auth/verification/resend', json={'correo': BODY['correo']})).status_code == 202
                assert len(sent) == 1
                await db.email_verifications.update_many({}, {'$set': {'expires_at': datetime.now(timezone.utc) - timedelta(seconds=1)}})
                assert (await client.post('/auth/verification/confirm', json={'token': token})).status_code == 400
                await db.empresas.update_many({}, {'$unset': {'verificacion_reenvio_despues': ''}})
                await client.post('/auth/verification/resend', json={'correo': BODY['correo']})
                assert len(sent) == 2
                new_token = re.search(r'#token=([^\s]+)', sent[-1].get_content())[1]
                assert new_token != token
                assert (await client.post('/auth/verification/confirm', json={'token': token})).status_code == 400
                confirmed = await client.post('/auth/verification/confirm', json={'token': new_token})
                assert confirmed.status_code == 200, confirmed.text
                assert len(sent) == 3
                html = sent[-1].get_body(preferencelist=('html',)).get_content()
                assert 'Jinwoo' in html and '{{nombre}}' not in html
                assert (await client.post('/auth/verification/confirm', json={'token': new_token})).status_code == 400
                assert len(sent) == 3
                logged = await client.post('/auth/login', json=credentials)
                assert logged.status_code == 200, logged.text
                headers = {'Authorization': 'Bearer ' + logged.json()['access_token']}
                assert (await client.get('/auth/me', headers=headers)).status_code == 200
                assert (await client.get('/empresas/me', headers=headers)).status_code == 200
                assert (await client.post('/auth/register', json=BODY)).status_code == 409
                assert await db.empresas.count_documents({}) == 1
                # Existing accounts are not retroactively locked when the new marker is absent.
                await db.empresas.update_many({}, {'$unset': {'requiere_verificacion_registro': ''}, '$set': {'correo_verificado': False}})
                assert (await client.post('/auth/login', json=credentials)).status_code == 200
    asyncio.run(run())

def test_smtp_failure_keeps_pending_company(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            def fail(_): raise RuntimeError('smtp unavailable')
            monkeypatch.setattr(controller, 'link_service', RegistrationLinkService(lambda: db, fail))
            app = FastAPI(); app.include_router(controller.router)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.post('/auth/register', json=BODY)).status_code == 201
                assert await db.empresas.count_documents({}) == 1
                assert (await client.post('/auth/login', json={'correo': BODY['correo'], 'password': BODY['password']})).status_code == 403
                assert (await client.post('/auth/register', json=BODY)).status_code == 409
    asyncio.run(run())
