import asyncio
import copy
import smtplib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from app.config.settings import settings
from app.dto.empresa_dto import EmpresaRegisterRequest, EmpresaResponse
from app.services import welcome_email_service as welcome
from app.services import smtp_transport

COMPANY = {'id_empresa': 'e', 'nombre': 'Empresa', 'nombre_ceo': 'Carlos', 'correo': 'carlos@example.com',
           'correo_verificado': True,
           'ruc': '20123456789', 'sector': 'Alimentos', 'telefono': '987654321',
           'fecha_creacion': '2026-10-24T10:00:00Z', 'fecha_actualizacion': '2026-10-24T10:00:00Z'}


class Collection:
    def __init__(self, rows=None): self.rows = copy.deepcopy(rows or [])
    @staticmethod
    def matches(row, query):
        return all(row.get(k) in v['$in'] if isinstance(v, dict) and '$in' in v else row.get(k) == v for k, v in query.items())
    async def find_one(self, query, projection=None):
        return copy.deepcopy(next((r for r in self.rows if self.matches(r, query)), None))
    async def update_one(self, query, update, upsert=False):
        row = next((r for r in self.rows if self.matches(r, query)), None)
        if row is None and upsert:
            row = {**query, **copy.deepcopy(update.get('$setOnInsert', {}))}; self.rows.append(row)
        if row is not None:
            row.update(copy.deepcopy(update.get('$set', {})))
            for k, v in update.get('$inc', {}).items(): row[k] = row.get(k, 0) + v
        return SimpleNamespace(matched_count=int(row is not None))
    async def find_one_and_update(self, query, update, **kwargs):
        row = next((r for r in self.rows if self.matches(r, query)), None)
        if row is None: return None
        await self.update_one(query, update)
        return copy.deepcopy(row)


@pytest.fixture
def configured(monkeypatch):
    for key, value in {'email_enabled': True, 'smtp_app_password': 'test-only-secret',
                       'smtp_user': 'psitwin2026@gmail.com', 'frontend_url': 'https://inventory.example.com',
                       'smtp_port': 465}.items(): monkeypatch.setattr(settings, key, value)
    return {'empresas': Collection([COMPANY]), 'bienvenidas_email': Collection()}


def test_ceo_required_single_name_trimmed_and_old_company_compatible():
    body = dict(nombre='Empresa', nombre_ceo=' Carlos ', ruc='20123456789', sector='Alimentos',
                correo='carlos@example.com', telefono='987654321', password='secure-test')
    assert EmpresaRegisterRequest(**body).nombre_ceo == 'Carlos'
    for value in ('', '  '):
        with pytest.raises(ValidationError): EmpresaRegisterRequest(**dict(body, nombre_ceo=value))
    body.pop('nombre_ceo')
    with pytest.raises(ValidationError): EmpresaRegisterRequest(**body)
    legacy = dict(COMPANY); legacy.pop('nombre_ceo')
    assert EmpresaResponse(**legacy).nombre_ceo is None


def test_template_personalization_image_cta_and_escaping(configured):
    message = welcome.build_welcome_message(dict(COMPANY, nombre_ceo='<Carlos & Ana>'))
    html = message.get_body(preferencelist=('html',)).get_content()
    plain = message.get_body(preferencelist=('plain',)).get_content()
    assert '&lt;Carlos &amp; Ana&gt;' in html and '<Carlos & Ana>' in plain
    assert '{{nombre}}' not in html and '[Nombre]' not in html
    assert 'https://inventory.example.com' in html and 'Ir a PsiTwin' in html
    assert 'psitwin2026@gmail.com' in message['From'] and message['Subject'] == welcome.SUBJECT
    assert any(part['Content-ID'] == '<psitwin-welcome-art>' for part in message.walk())
    assert '<img src="cid:psitwin-welcome-art"' in html
    image = next(part for part in message.walk() if part['Content-ID'] == '<psitwin-welcome-art>')
    assert image.get_payload(decode=True).startswith(b'\xff\xd8')
    assert image.get_filename().startswith('Bienvenida-')
    assert html.count('<img ') == 2 and '<h1' in html and '<h2' in html
    assert len(html.encode('utf-8')) < 20000
    assert len(message.as_bytes()) < 100000
    assert 'data:image/' not in html and '$nombre' not in html
    for section in ('Pronostica tu demanda', 'Controla tu inventario', 'Recibe alertas', 'Consulta a Saiki', 'Grupo 404'):
        assert section in html


def test_verified_company_profile_accepts_mongo_datetime():
    from datetime import datetime, timezone
    verified_at = datetime.now(timezone.utc)
    result = EmpresaResponse(**dict(COMPANY, correo_verificado=True, fecha_verificacion_correo=verified_at))
    assert result.correo_verificado is True
    assert result.fecha_verificacion_correo == verified_at.isoformat()


def test_invalid_frontend_url_never_creates_an_unsafe_cta(configured, monkeypatch):
    monkeypatch.setattr(settings, 'frontend_url', 'javascript:alert(1)')
    with pytest.raises(ValueError): welcome.build_welcome_message(COMPANY)


def test_welcome_uses_the_same_legacy_credentials_as_transport(configured, monkeypatch):
    monkeypatch.setattr(settings, 'smtp_app_password', '')
    monkeypatch.setattr(settings, 'smtp_password', 'legacy-secret')
    sender = Mock()
    service = welcome.WelcomeEmailService(lambda: configured, sender)
    async def run():
        await service.enqueue(COMPANY)
        assert (await service.deliver('e'))['status'] == 'ENVIADO'
        sender.assert_called_once()
    asyncio.run(run())


def test_outbox_concurrency_and_success_are_idempotent(configured):
    sender = Mock()
    service = welcome.WelcomeEmailService(lambda: configured, sender)
    async def run():
        await service.enqueue(COMPANY); await service.enqueue(COMPANY)
        await asyncio.gather(service.deliver('e'), service.deliver('e'))
        await service.deliver('e')
        state = await service.status('e')
        assert state['status'] == 'ENVIADO' and state['intentos'] == 1
        assert sender.call_count == 1 and len(configured['bienvenidas_email'].rows) == 1
    asyncio.run(run())


def test_failed_delivery_preserves_company_and_can_retry_without_leaking_secrets(configured):
    sender = Mock(side_effect=[smtplib.SMTPAuthenticationError(535, b'test-only-secret'), None])
    service = welcome.WelcomeEmailService(lambda: configured, sender)
    async def run():
        await service.enqueue(COMPANY)
        assert (await service.deliver('e'))['status'] == 'ERROR'
        assert len(configured['empresas'].rows) == 1
        assert 'test-only-secret' not in str(configured['bienvenidas_email'].rows)
        assert (await service.deliver('e'))['status'] == 'ENVIADO'
        assert sender.call_count == 2
    asyncio.run(run())


def test_missing_smtp_is_truthfully_pending_and_uncertain_send_is_never_repeated(configured, monkeypatch):
    sender = Mock(side_effect=smtp_transport.DeliveryUncertain())
    service = welcome.WelcomeEmailService(lambda: configured, sender)
    async def run():
        await service.enqueue(COMPANY)
        monkeypatch.setattr(settings, 'email_enabled', False)
        assert (await service.deliver('e'))['status'] == 'CONFIGURACION_PENDIENTE'
        sender.assert_not_called()
        monkeypatch.setattr(settings, 'email_enabled', True)
        assert (await service.deliver('e'))['status'] == 'REVISAR_ENVIO'
        await service.deliver('e')
        assert sender.call_count == 1
    asyncio.run(run())


@pytest.mark.parametrize('port', [465, 587])
def test_transport_uses_ssl_or_starttls_and_real_acknowledgment(configured, monkeypatch, port):
    server = Mock(); server.send_message.return_value = {}
    ssl = Mock(return_value=server); tls = Mock(return_value=server)
    monkeypatch.setattr(smtp_transport.smtplib, 'SMTP_SSL', ssl)
    monkeypatch.setattr(smtp_transport.smtplib, 'SMTP', tls)
    monkeypatch.setattr(settings, 'smtp_use_tls', True)
    smtp_transport.send_message(welcome.build_welcome_message(COMPANY), port=port)
    assert ssl.call_count == (port == 465) and tls.call_count == (port != 465)
    assert server.starttls.call_count == (port != 465)
    server.login.assert_called_once_with('psitwin2026@gmail.com', 'test-only-secret')
    server.send_message.assert_called_once(); server.close.assert_called_once()


def test_gmail_app_password_pasted_with_unicode_spaces(configured, monkeypatch):
    server = Mock(); server.send_message.return_value = {}
    monkeypatch.setattr(smtp_transport.smtplib, 'SMTP_SSL', Mock(return_value=server))
    monkeypatch.setattr(settings, 'smtp_host', 'smtp.gmail.com')
    smtp_transport.send_message(welcome.build_welcome_message(COMPANY), password='abcd\u00a0efgh ijkl\nmnop')
    server.login.assert_called_once_with('psitwin2026@gmail.com', 'abcdefghijklmnop')


def test_registration_and_retry_routes_keep_tenant_and_existing_company(configured, monkeypatch):
    from app.controllers import empresa_controller as controller
    from app.services import empresa_service
    from app.dependencies.dependencies import get_usuario_activo
    from app.dto.auth_dto import UsuarioActual
    service = welcome.WelcomeEmailService(lambda: configured, Mock(side_effect=smtplib.SMTPAuthenticationError(535, b'bad')))
    monkeypatch.setattr(controller, 'welcome_email_service', service)
    verification = AsyncMock(return_value={'status': 'SENT'})
    monkeypatch.setattr(controller.link_service, 'send', verification)
    from types import SimpleNamespace
    monkeypatch.setattr(controller, 'get_database', lambda: SimpleNamespace(empresas=SimpleNamespace(create_index=AsyncMock()), email_verifications=SimpleNamespace(create_index=AsyncMock())))
    monkeypatch.setattr(empresa_service.empresa_repository, 'find_by_email', AsyncMock(return_value=None))
    monkeypatch.setattr(empresa_service.empresa_repository, 'find_by_ruc', AsyncMock(return_value=None))
    monkeypatch.setattr(empresa_service, 'validar_correo_disponible', AsyncMock())
    create = AsyncMock(return_value=COMPANY)
    monkeypatch.setattr(empresa_service.empresa_repository, 'create_empresa', create)
    monkeypatch.setattr(empresa_service.empresa_repository, 'find_by_id', AsyncMock(return_value=COMPANY))
    monkeypatch.setattr(welcome.WelcomeEmailService, 'enqueue', service.enqueue)
    app = FastAPI(); app.include_router(controller.router)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/auth/register', json={k: COMPANY[k] for k in ('nombre', 'nombre_ceo', 'correo', 'sector', 'telefono', 'ruc')} | {'password': 'secure-test', 'password_confirmation': 'secure-test', 'correo': 'carlos@gmail.com', 'ruc': '20100070970'})
            assert response.status_code == 201 and response.json()['nombre_ceo'] == 'Carlos'
            verification.assert_awaited_once_with(COMPANY['correo'])
            assert create.call_args.args[0]['nombre_ceo'] == 'Carlos'
            assert (await service.status('e'))['status'] == 'PENDIENTE'
            assert (await client.post('/empresas/me/bienvenida/reintentar')).status_code in (401, 403)
            app.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='e')
            assert (await client.post('/empresas/me/bienvenida/reintentar')).status_code == 202
            create.assert_awaited_once()
            app.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='foreign')
            assert (await client.get('/empresas/me/bienvenida')).json()['status'] == 'NO_SOLICITADO'
    asyncio.run(run())


def test_company_survives_an_outbox_failure_and_duplicate_registration_does_not_enqueue(configured, monkeypatch):
    from app.services import empresa_service
    from fastapi import HTTPException
    payload = EmpresaRegisterRequest(**{k: COMPANY[k] for k in ('nombre', 'nombre_ceo', 'correo', 'sector', 'telefono', 'ruc')}, password='secure-test')
    find = AsyncMock(return_value=None)
    monkeypatch.setattr(empresa_service.empresa_repository, 'find_by_email', find)
    monkeypatch.setattr(empresa_service.empresa_repository, 'find_by_ruc', AsyncMock(return_value=None))
    monkeypatch.setattr(empresa_service, 'validar_correo_disponible', AsyncMock())
    create = AsyncMock(return_value=COMPANY)
    monkeypatch.setattr(empresa_service.empresa_repository, 'create_empresa', create)
    enqueue = AsyncMock(side_effect=RuntimeError('outbox unavailable'))
    monkeypatch.setattr(welcome.WelcomeEmailService, 'enqueue', enqueue)
    async def run():
        assert (await empresa_service.register_empresa(payload))['nombre_ceo'] == 'Carlos'
        create.assert_awaited_once()
        find.return_value = COMPANY
        with pytest.raises(HTTPException) as error: await empresa_service.register_empresa(payload)
        assert error.value.status_code == 409
        enqueue.assert_awaited_once()
    asyncio.run(run())


def test_smtp_lost_ack_is_uncertain_but_close_failure_after_ack_is_not_a_failed_send(configured, monkeypatch):
    server = Mock(); server.send_message.return_value = {}
    monkeypatch.setattr(smtp_transport.smtplib, 'SMTP_SSL', Mock(return_value=server))
    server.close.side_effect = RuntimeError('failed close')
    smtp_transport.send_message(welcome.build_welcome_message(COMPANY))
    server.send_message.side_effect = smtplib.SMTPServerDisconnected('lost DATA acknowledgement')
    with pytest.raises(smtp_transport.DeliveryUncertain): smtp_transport.send_message(welcome.build_welcome_message(COMPANY))


def test_unverified_registration_waits_then_verification_sends_once(configured, monkeypatch):
    from app.controllers import empresa_controller as controller
    from app.dependencies.dependencies import get_usuario_activo
    from app.dto.auth_dto import UsuarioActual
    configured['empresas'].rows[0]['correo_verificado'] = False
    sender = Mock()
    service = welcome.WelcomeEmailService(lambda: configured, sender)
    monkeypatch.setattr(controller, 'welcome_email_service', service)
    monkeypatch.setattr(controller.empresa_service, 'get_empresa_profile',
                        AsyncMock(side_effect=lambda _: copy.deepcopy(configured['empresas'].rows[0])))

    async def verify(*args):
        configured['empresas'].rows[0]['correo_verificado'] = True
        return {'verified': True, 'status': 'VERIFIED', 'email': COMPANY['correo']}

    monkeypatch.setattr(controller.email_verification_service, 'verify_entity_code', verify)
    instance = FastAPI()
    instance.include_router(controller.router)
    instance.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='e')

    async def run():
        await service.enqueue(COMPANY)
        assert (await service.deliver('e'))['status'] == 'CONFIRMACION_PENDIENTE'
        sender.assert_not_called()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=instance), base_url='http://test') as client:
            assert (await client.post('/empresas/me/bienvenida/reintentar')).status_code == 409
            for _ in range(2):
                result = await client.post('/empresas/e/correo/verificar', json={'codigo': '123456'})
                assert result.status_code == 200 and result.json()['verified']
        assert (await service.status('e'))['status'] == 'ENVIADO'
        sender.assert_called_once()

    asyncio.run(run())
