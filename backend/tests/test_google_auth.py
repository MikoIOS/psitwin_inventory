"""Real MongoDB isolated database + FastAPI/JWT; Google's external exchange is controlled.
These tests do NOT claim an interactive Google consent has occurred.
"""
import asyncio
import json
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import jwt
import pytest
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.hazmat.primitives.asymmetric import rsa
from app.config.settings import settings
from app.controllers import google_auth_controller as controller, empresa_controller
from app.database import mongodb
from app.services.google_auth_service import GoogleAuthService, CompanyDetails, digest
from app.services.empresa_service import hash_password

DETAILS = dict(nombre='Empresa de prueba', nombre_ceo='Carlos', ruc='20123456789', sector='Alimentos', telefono='987654321')
BINDING = 'b' * 64

@asynccontextmanager
async def isolated_database(monkeypatch):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    name = 'psitwin_test_google_' + uuid4().hex
    connected = False
    try:
        try: await client.admin.command('ping')
        except Exception: pytest.skip('MongoDB no disponible para prueba de integración')
        connected = True
        db = client[name]
        monkeypatch.setattr(mongodb, 'database', db)
        monkeypatch.setattr(controller, 'service', GoogleAuthService(lambda: db))
        monkeypatch.setattr(settings, 'google_client_id', 'synthetic-client')
        monkeypatch.setattr(settings, 'google_client_secret', 'synthetic-secret')
        monkeypatch.setattr(settings, 'email_enabled', False)
        yield db
    finally:
        if not name.startswith('psitwin_test_google_') or len(name) != len('psitwin_test_google_') + 32:
            raise AssertionError('Refusing to clean a non-test database')
        if connected:
            await client.drop_database(name)
        client.close()

def app():
    instance = FastAPI()
    instance.include_router(controller.router)
    instance.include_router(empresa_controller.router)
    return instance

def state(url): return parse_qs(urlsplit(url).query)['state'][0]


def test_registration_status_cannot_be_forged_or_reused(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            monkeypatch.setattr(controller.service, 'identity', AsyncMock(return_value={'sub': 'status-sub', 'email': 'carlos@gmail.com'}))
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                for initial in ({'binding': BINDING}, {'binding': BINDING, 'company': DETAILS, 'purpose': 'login'}):
                    assert (await client.post('/auth/google/start', json=initial)).status_code == 422
                initial = await client.post('/auth/google/start', json={'binding': BINDING, 'company': DETAILS})
                complete = await client.post('/auth/google/complete', json={'binding': BINDING, 'state': state(initial.json()['authorization_url']), 'code': 'controlled-code'})
                ticket = complete.json()['registration_ticket']
                body = {'binding': BINDING, 'registration_ticket': ticket}
                valid = await client.post('/auth/google/registration/status', json=body)
                assert valid.json() == {'verified_email': 'carlos@gmail.com', 'company': DETAILS}
                assert (await client.post('/auth/google/registration/status', json={**body, 'binding': 'x'*64})).status_code == 400
                assert (await client.post('/auth/google/registration/status', json={**body, 'registration_ticket': 'forged-ticket-not-issued-by-server'})).status_code == 400
                await db.google_oauth_flows.update_one({'_id': digest(ticket)}, {'$set': {'expires_at': datetime.now(timezone.utc)-timedelta(seconds=1)}})
                assert (await client.post('/auth/google/registration/status', json=body)).status_code == 400
                assert (await client.post('/auth/google/register', json={**body, 'company': DETAILS, 'registration_password': 'secure-password-2026', 'registration_password_confirmation': 'different-password'})).status_code == 422
                assert await db.empresas.count_documents({}) == 0
    asyncio.run(run())


def test_auth_validation_errors_do_not_echo_passwords():
    from app.main import app as full_app
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=full_app), base_url='http://test') as client:
            result = await client.post('/api/v1/auth/register', json={'password': 'sensitive-password-2026', 'password_confirmation': 'different-sensitive-password'})
            assert result.status_code == 422
            assert 'sensitive-password' not in result.text and 'input' not in result.text
    asyncio.run(run())


@pytest.mark.parametrize('role,email', [('OPERARIO', 'operario@example.com'), ('PROVEEDOR', 'proveedor@example.org')])
def test_legacy_operator_and_supplier_password_login_preserves_roles(monkeypatch, role, email):
    async def run():
        async with isolated_database(monkeypatch) as db:
            now = datetime.now(timezone.utc)
            await db.empresas.insert_one({**DETAILS, 'id_empresa': 'legacy', 'correo': 'legacy@example.com', 'fecha_creacion': now, 'fecha_actualizacion': now})
            common = {'id_empresa': 'legacy', 'correo': email, 'nombre': 'Cuenta', 'estado': 'ACTIVO', 'tiene_cuenta': True, 'debe_cambiar_password': False, 'password_hash': hash_password('legacy-password'), 'fecha_creacion': now, 'fecha_actualizacion': now}
            if role == 'OPERARIO':
                await db.operarios.insert_one({**common, 'id_operario': 'operator', 'apellido': 'Prueba', 'cargo': 'Operario', 'turno': 'Dia', 'id_almacen': 'warehouse'})
            else:
                await db.proveedores.insert_one({**common, 'id_proveedor': 'supplier', 'ruc': '20123456789', 'tiempo_entrega_estimado_dias': 2})
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                login = await client.post('/auth/login', json={'correo': email, 'password': 'legacy-password'})
                assert login.status_code == 200, login.text
                assert login.json()['rol'] == role and login.json()['empresa']['id_empresa'] == 'legacy'
                headers = {'Authorization': 'Bearer '+login.json()['access_token']}
                me = await client.get('/auth/me', headers=headers)
                assert me.status_code == 200 and me.json()['rol'] == role
                assert (await client.get('/empresas/me', headers=headers)).status_code == 403
    asyncio.run(run())


def test_registration_requires_password_and_uses_server_business_snapshot(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            monkeypatch.setattr(controller.service, 'identity', AsyncMock(return_value={'sub': 'snapshot-sub', 'email': 'carlos@gmail.com'}))
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                start = await client.post('/auth/google/start', json={'binding': BINDING, 'company': DETAILS, 'purpose': 'register'})
                complete = await client.post('/auth/google/complete', json={'binding': BINDING, 'state': state(start.json()['authorization_url']), 'code': 'test-code'})
                data = complete.json()
                assert 'access_token' not in data and data['company'] == DETAILS
                assert await db.empresas.count_documents({}) == 0
                finish = {'binding': BINDING, 'registration_ticket': data['registration_ticket'], 'company': {**DETAILS, 'nombre': 'Alterado'}}
                for invalid in ({}, {'registration_password': 'short'}):
                    assert (await client.post('/auth/google/register', json={**finish, **invalid})).status_code == 422
                result = await client.post('/auth/google/register', json={**finish, 'registration_password': 'secure-password-2026', 'registration_password_confirmation': 'secure-password-2026'})
                assert result.status_code == 200 and result.json()['empresa']['nombre'] == DETAILS['nombre']
                stored = await db.empresas.find_one({})
                assert stored['password'].startswith('$argon2id$')
                assert (await client.post('/auth/google/register', json={**finish, 'registration_password': 'secure-password-2026', 'registration_password_confirmation': 'secure-password-2026'})).status_code == 400
                assert await db.empresas.count_documents({}) == 1
    asyncio.run(run())


def test_auth_query_strings_are_redacted_in_server_logs():
    import logging
    from app.utils.log_redaction import AuthQueryFilter
    record = logging.LogRecord('uvicorn.error', logging.INFO, '', 1, 'WebSocket %s', ('/ws/monitoreo?token=private-jwt&other=ok',), None)
    assert AuthQueryFilter().filter(record)
    assert 'private-jwt' not in record.getMessage() and 'other=ok' in record.getMessage()
    from uvicorn.logging import AccessFormatter
    access = logging.LogRecord('uvicorn.access', logging.INFO, '', 1, '%s - "%s %s HTTP/%s" %d', ('127.0.0.1', 'GET', '/ws?token=private-jwt', '1.1', 200), None)
    AuthQueryFilter().filter(access)
    assert 'private-jwt' not in AccessFormatter().format(access)


def test_login_preserves_legacy_email_accounts():
    from app.dto.auth_dto import LoginRequest
    from pydantic import ValidationError
    for email in ('ceo@gmail.com', 'CEO@GMAIL.COM', 'operario@psitwin.com', 'proveedor@example.com'):
        assert LoginRequest(correo=email, password='registered-password')
    for email in ('not-an-email', 'ceo@', ''):
        with pytest.raises(ValidationError):
            LoginRequest(correo=email, password='registered-password')


def test_google_registration_rejects_non_gmail_before_creating_company():
    service = GoogleAuthService(lambda: pytest.fail('Must reject before database access'))
    async def run():
        with pytest.raises(HTTPException) as error:
            await service.register({'sub': 'workspace', 'email': 'ceo@example.com'}, CompanyDetails(**DETAILS))
        assert error.value.status_code == 422
    asyncio.run(run())


@pytest.mark.parametrize('explicit_purpose', [False, True])
def test_google_registration_enables_chosen_password_after_verified_identity(monkeypatch, explicit_purpose):
    async def run():
        async with isolated_database(monkeypatch) as db:
            monkeypatch.setattr(controller.service, 'identity', AsyncMock(return_value={'sub': 'password-google-sub', 'email': 'carlos@gmail.com'}))
            password = 'chosen-registration-password'
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                initial = {'binding': BINDING, 'company': DETAILS, **({'purpose': 'register'} if explicit_purpose else {})}
                start = await client.post('/auth/google/start', json=initial)
                assert start.status_code == 200
                flow = await db.google_oauth_flows.find_one({'_id': digest(state(start.json()['authorization_url']))})
                assert password not in json.dumps(flow, default=str)
                assert await db.empresas.count_documents({}) == 0
                result = await client.post('/auth/google/complete', json={'binding': BINDING, 'state': state(start.json()['authorization_url']), 'code': 'controlled-code'})
                assert result.json()['registration_required']
                assert result.json()['verified_email'] == 'carlos@gmail.com'
                assert await db.empresas.count_documents({}) == 0
                result = await client.post('/auth/google/register', json={'binding': BINDING, 'company': DETAILS, 'registration_password': password, 'registration_password_confirmation': password, 'registration_ticket': result.json()['registration_ticket']})
                assert result.status_code == 200
                assert result.json()['empresa']['password_local_habilitada'] is True
                assert password not in result.text
                company = await db.empresas.find_one({'google_sub': 'password-google-sub'})
                assert company['correo_verificado'] and company['password'] != password
                assert controller.verify_password(password, company['password'])
                login = await client.post('/auth/login', json={'correo': 'carlos@gmail.com', 'password': password})
                assert login.status_code == 200
                assert (await client.post('/auth/login', json={'correo': 'carlos@gmail.com', 'password': 'incorrect-password'})).status_code == 401
                # Registering again must never replace the existing account's password.
                again = await client.post('/auth/google/start', json={'binding': BINDING})
                assert again.status_code == 422
                assert controller.verify_password(password, (await db.empresas.find_one({'google_sub': 'password-google-sub'}))['password'])
    asyncio.run(run())


def test_missing_google_configuration_has_explicit_safe_error(monkeypatch):
    monkeypatch.setattr(settings, 'google_client_id', '')
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
            result = await client.post('/auth/google/start', json={'binding': BINDING, 'company': DETAILS})
            assert result.status_code == 503
            assert result.json()['detail']['code'] == 'GOOGLE_NOT_CONFIGURED'
    asyncio.run(run())

def test_google_registration_login_replay_and_legacy_password_session(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            service = controller.service
            identity = AsyncMock(return_value={'sub': 'stable-google-sub', 'email': 'carlos@gmail.com'})
            monkeypatch.setattr(service, 'identity', identity)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                start = await client.post('/auth/google/start', json={'binding': BINDING, 'company': DETAILS})
                assert start.status_code == 200
                query = parse_qs(urlsplit(start.json()['authorization_url']).query)
                assert query['code_challenge_method'] == ['S256'] and query['nonce'] and query['scope'] == ['openid email profile']
                payload = {'binding': BINDING, 'state': query['state'][0], 'code': 'controlled-code'}
                wrong = await client.post('/auth/google/complete', json={**payload, 'binding': 'x' * 64})
                assert wrong.status_code == 400
                result = await client.post('/auth/google/complete', json=payload)
                assert result.status_code == 200
                assert result.json()['registration_required']
                assert await db.empresas.count_documents({}) == 0
                result = await client.post('/auth/google/register', json={'binding': BINDING, 'registration_ticket': result.json()['registration_ticket'], 'registration_password': 'legacy-test-password', 'registration_password_confirmation': 'legacy-test-password'})
                session = result.json(); token = session['access_token']
                assert session['empresa']['nombre_ceo'] == 'Carlos' and session['empresa']['correo_verificado']
                assert 'google_sub' not in session['empresa'] and 'password' not in session['empresa']
                headers = {'Authorization': 'Bearer ' + token}
                for endpoint in ('/auth/me', '/empresas/me'):
                    assert (await client.get(endpoint, headers=headers)).status_code == 200
                assert (await client.get('/auth/me')).status_code in (401, 403)
                assert (await client.post('/auth/google/complete', json=payload)).status_code == 400
                assert await db.empresas.count_documents({}) == 1
                assert await db.bienvenidas_email.count_documents({}) == 1
                # Google is verification only; it cannot open an existing account.
                start2 = await client.post('/auth/google/start', json={'binding': BINDING, 'company': DETAILS})
                repeated = await client.post('/auth/google/complete', json={**payload, 'state': state(start2.json()['authorization_url'])})
                assert repeated.status_code == 409 and 'access_token' not in repeated.json()
                assert await db.empresas.count_documents({}) == 1
                # Legacy credentials remain valid after the Mongo datetime update.
                await db.empresas.update_one({'id_empresa': session['empresa']['id_empresa']}, {'$set': {
                    'password': hash_password('legacy-test-password'), 'fecha_verificacion_correo': datetime.now(timezone.utc)}})
                legacy = await client.post('/auth/login', json={'correo': 'carlos@gmail.com', 'password': 'legacy-test-password'})
                assert legacy.status_code == 200
                assert (await client.get('/auth/me', headers={'Authorization': 'Bearer ' + legacy.json()['access_token']})).status_code == 200
                # Sensitive setup requires Google proof from the already linked subject.
                setup = await client.post('/auth/google/password/start', json={'binding': BINDING, 'new_password': 'configured-local-password'}, headers=headers)
                assert setup.status_code == 200
                confirmed = await client.post('/auth/google/complete', json={**payload, 'state': state(setup.json()['authorization_url'])})
                assert confirmed.status_code == 200 and confirmed.json()['empresa']['password_local_habilitada'] is True
                enabled = await client.post('/auth/login', json={'correo': 'carlos@gmail.com', 'password': 'configured-local-password'})
                assert enabled.status_code == 200
    asyncio.run(run())

def test_google_unlinked_registration_and_secure_link_no_email_takeover(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            service = controller.service
            monkeypatch.setattr(service, 'identity', AsyncMock(return_value={'sub': 'new-sub', 'email': 'new@gmail.com'}))
            start = await service.start(BINDING)
            required = await service.complete(state(start['authorization_url']), 'code', BINDING)
            assert required['registration_required']
            result = await service.finish_registration(required['registration_ticket'], BINDING, CompanyDetails(**DETAILS))
            assert result['empresa']['correo'] == 'new@gmail.com'
            with pytest.raises(HTTPException):
                await service.finish_registration(required['registration_ticket'], BINDING, CompanyDetails(**DETAILS))
            await db.empresas.update_one({'id_empresa': result['empresa']['id_empresa']}, {'$unset': {'google_sub': ''}, '$set': {'password': hash_password('old-account-pass')}})
            start = await service.start(BINDING, CompanyDetails(**DETAILS))
            duplicate = await service.complete(state(start['authorization_url']), 'code', BINDING)
            with pytest.raises(HTTPException) as error:
                await service.finish_registration(duplicate['registration_ticket'], BINDING, CompanyDetails(**DETAILS))
            assert error.value.status_code == 409
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url='http://test') as client:
                headers = {'Authorization': 'Bearer ' + result['access_token']}
                assert (await client.post('/auth/google/link', json={'binding': BINDING, 'password': 'wrong'}, headers=headers)).status_code == 400
                link = await client.post('/auth/google/link', json={'binding': BINDING, 'password': 'old-account-pass'}, headers=headers)
                assert link.status_code == 200
                linked = await client.post('/auth/google/complete', json={'binding': BINDING, 'state': state(link.json()['authorization_url']), 'code': 'code'})
                assert linked.status_code == 200
                assert await db.empresas.count_documents({}) == 1
    asyncio.run(run())

def test_expired_and_concurrent_callbacks_never_create_duplicates(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            service = controller.service
            monkeypatch.setattr(service, 'identity', AsyncMock(return_value={'sub': 'race-sub', 'email': 'race@gmail.com'}))
            start = await service.start(BINDING, CompanyDetails(**DETAILS))
            current = state(start['authorization_url'])
            await db.google_oauth_flows.update_one({'_id': digest(current)}, {'$set': {'expires_at': datetime.now(timezone.utc) - timedelta(minutes=1)}})
            with pytest.raises(HTTPException): await service.complete(current, 'code', BINDING)
            assert await db.empresas.count_documents({}) == 0
            start = await service.start(BINDING, CompanyDetails(**DETAILS))
            current = state(start['authorization_url'])
            results = await asyncio.gather(service.complete(current, 'code', BINDING), service.complete(current, 'code', BINDING), return_exceptions=True)
            assert sum(isinstance(result, dict) and result.get('registration_required') is True for result in results) == 1
            assert await db.empresas.count_documents({}) == 0
            ticket = next(result['registration_ticket'] for result in results if isinstance(result, dict))
            finished = await asyncio.gather(service.finish_registration(ticket, BINDING, CompanyDetails(**DETAILS)), service.finish_registration(ticket, BINDING, CompanyDetails(**DETAILS)), return_exceptions=True)
            assert sum(isinstance(result, dict) and 'access_token' in result for result in finished) == 1
            assert await db.empresas.count_documents({}) == 1
            assert await db.bienvenidas_email.count_documents({}) == 1
    asyncio.run(run())

@pytest.mark.parametrize('invalid', [None, 'signature', 'audience', 'issuer', 'expired', 'nonce', 'unverified', 'azp'])
def test_real_signature_and_oidc_claim_validation(monkeypatch, invalid):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key())); public['kid'] = 'test-key'
    now = datetime.now(timezone.utc)
    claims = {'iss': 'https://accounts.google.com', 'aud': 'client', 'sub': 'subject', 'email': 'carlos@gmail.com',
        'email_verified': True, 'iat': now, 'exp': now + timedelta(minutes=5), 'nonce': 'nonce'}
    if invalid == 'audience': claims['aud'] = 'attacker'
    if invalid == 'issuer': claims['iss'] = 'https://attacker.example'
    if invalid == 'expired': claims['exp'] = now - timedelta(minutes=1)
    if invalid == 'nonce': claims['nonce'] = 'wrong'
    if invalid == 'unverified': claims['email_verified'] = False
    if invalid == 'azp': claims['azp'] = 'attacker'
    token = jwt.encode(claims, other if invalid == 'signature' else private, algorithm='RS256', headers={'kid': 'test-key'})
    original = httpx.AsyncClient
    def handler(request):
        return httpx.Response(200, json={'id_token': token} if request.url.path == '/token' else {'keys': [public]})
    monkeypatch.setattr('app.services.google_auth_service.httpx.AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(settings, 'google_client_id', 'client')
    call = GoogleAuthService().identity('code', {'nonce': 'nonce', 'verifier': 'v' * 43})
    if invalid:
        with pytest.raises(HTTPException) as error: asyncio.run(call)
        assert error.value.status_code == 401
    else:
        assert asyncio.run(call) == {'sub': 'subject', 'email': 'carlos@gmail.com'}
