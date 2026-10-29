"""Google OIDC. Only application JWTs leave the backend; Google tokens are discarded."""
import asyncio
import base64
import hashlib
import secrets
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import httpx
import jwt
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo.errors import DuplicateKeyError
from pymongo.collation import Collation

from app.config.settings import settings
from app.database.mongodb import get_database
from app.dto.empresa_dto import EmpresaRegisterRequest, EmpresaResponse
from app.services.empresa_service import hash_password, verify_password
from app.services.welcome_email_service import WelcomeEmailService
from app.utils.security import create_access_token, ROL_EMPRESA


class CompanyDetails(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=2, max_length=100)
    nombre_ceo: str = Field(min_length=1, max_length=100)
    ruc: str = Field(pattern=r'^\d{11}$')
    sector: str = Field(min_length=2, max_length=100)
    telefono: str = Field(min_length=6, max_length=20)

    @field_validator('nombre', 'nombre_ceo', 'ruc', 'sector', 'telefono', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    def validated(self, email):
        return EmpresaRegisterRequest(**self.model_dump(), correo=email, password=secrets.token_urlsafe(48))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class GoogleAuthService:
    def __init__(self, database_provider=None):
        self.database = database_provider or get_database

    async def indexes(self):
        db = self.database()
        await db['google_oauth_flows'].create_index('expires_at', expireAfterSeconds=0)
        await db['empresas'].create_index('google_sub', unique=True,
            partialFilterExpression={'google_sub': {'$type': 'string'}})
        await db['empresas'].create_index('google_registration_ruc', unique=True,
            partialFilterExpression={'google_registration_ruc': {'$type': 'string'}})
        await db['empresas'].create_index('correo', unique=True,
            partialFilterExpression={'correo': {'$type': 'string'}}, collation=Collation(locale='en', strength=2))
        await db['empresas'].create_index('ruc', unique=True,
            partialFilterExpression={'ruc': {'$type': 'string'}})

    async def start(self, binding, company=None, link_company=None, password_hash=None, purpose='login'):
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(503, {'code': 'GOOGLE_NOT_CONFIGURED', 'detail': 'El acceso con Google aún no está configurado. Contacta al administrador.'})
        await self.indexes()
        state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        await self.database()['google_oauth_flows'].insert_one({
            '_id': digest(state), 'binding': digest(binding), 'nonce': nonce, 'verifier': verifier,
            'company': company.model_dump() if company else None, 'link_company': link_company, 'password_hash': password_hash, 'purpose': purpose,
            'status': 'PENDING', 'expires_at': datetime.now(timezone.utc) + timedelta(seconds=settings.google_oauth_ttl_seconds),
        })
        return {'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
            'client_id': settings.google_client_id, 'redirect_uri': settings.google_redirect_uri,
            'response_type': 'code', 'scope': 'openid email profile', 'state': state, 'nonce': nonce,
            'code_challenge': challenge, 'code_challenge_method': 'S256', 'prompt': 'select_account',
        })}

    async def identity(self, code, flow):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post('https://oauth2.googleapis.com/token', data={
                    'client_id': settings.google_client_id, 'client_secret': settings.google_client_secret,
                    'code': code, 'code_verifier': flow['verifier'], 'grant_type': 'authorization_code',
                    'redirect_uri': settings.google_redirect_uri,
                })
                response.raise_for_status()
                token = response.json()['id_token']
                keys = await client.get('https://www.googleapis.com/oauth2/v3/certs')
                keys.raise_for_status()
                header = jwt.get_unverified_header(token)
                key = next(k for k in keys.json()['keys'] if k['kid'] == header.get('kid'))
                claims = jwt.decode(token, jwt.PyJWK.from_dict(key).key, algorithms=['RS256'],
                    audience=settings.google_client_id, issuer=['https://accounts.google.com', 'accounts.google.com'],
                    options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'nonce', 'email', 'email_verified']})
                if not secrets.compare_digest(str(claims['nonce']), flow['nonce']) or claims['email_verified'] is not True:
                    raise ValueError('Unverified identity')
                if claims.get('azp', settings.google_client_id) != settings.google_client_id:
                    raise ValueError('Invalid authorized party')
                if isinstance(claims['aud'], list) and len(claims['aud']) > 1 and 'azp' not in claims:
                    raise ValueError('Missing authorized party')
                if not str(claims['sub']).strip():
                    raise ValueError('Missing subject')
                return {'sub': claims['sub'], 'email': claims['email'].strip().lower()}
        except (httpx.HTTPError, jwt.PyJWTError, ValueError, KeyError, StopIteration) as exc:
            # Never log the authorization code, OAuth response, Google token or client secret.
            raise HTTPException(401, 'No se pudo validar la identidad de Google. Inicia el proceso nuevamente.') from exc

    async def complete(self, state, code, binding):
        flows = self.database()['google_oauth_flows']
        flow = await flows.find_one_and_update({
            '_id': digest(state), 'binding': digest(binding), 'status': 'PENDING',
            'expires_at': {'$gt': datetime.now(timezone.utc)},
        }, {'$set': {'status': 'CONSUMED'}})
        if not flow:
            raise HTTPException(400, 'La autorización expiró o ya fue utilizada. Inicia nuevamente.')
        identity = await self.identity(code, flow)
        companies = self.database()['empresas']
        linked = await companies.find_one({'google_sub': identity['sub']})
        if flow.get('link_company'):
            if linked and linked['id_empresa'] != flow['link_company']:
                raise HTTPException(409, 'Esta identidad de Google ya está vinculada.')
            company = await companies.find_one({'id_empresa': flow['link_company']})
            if not company:
                raise HTTPException(404, 'Empresa no encontrada')
            if flow.get('password_hash'):
                if company.get('google_sub') != identity['sub']:
                    raise HTTPException(403, 'Debes autorizar la identidad de Google vinculada a esta empresa.')
                await companies.update_one({'id_empresa': company['id_empresa'], 'google_sub': identity['sub']},
                    {'$set': {'password': flow['password_hash'], 'password_local_habilitada': True}})
                company['password_local_habilitada'] = True
                return self.session(company)
            if company.get('google_sub') and company['google_sub'] != identity['sub']:
                raise HTTPException(409, 'La empresa ya tiene otra identidad vinculada.')
            # Linking grants login, without silently changing the company's contact email.
            changes = {'google_sub': identity['sub']}
            if str(company.get('correo', '')).strip().lower() == identity['email']:
                changes.update(correo_verificado=True, fecha_verificacion_correo=datetime.now(timezone.utc).isoformat())
                company.update(changes)
            try:
                result = await companies.update_one({'id_empresa': company['id_empresa'],
                    '$or': [{'google_sub': None}, {'google_sub': identity['sub']}]},
                    {'$set': changes})
                if not result.matched_count:
                    raise HTTPException(409, 'La identidad vinculada cambió. Revisa el perfil.')
            except DuplicateKeyError as exc:
                raise HTTPException(409, 'Esta identidad ya está vinculada.') from exc
            return self.session(company)
        if linked:
            raise HTTPException(409, 'Esta cuenta Google ya está registrada. Inicia sesión con tu correo y contraseña de PsiTwin.')
        if identity['email'].rsplit('@', 1)[-1].lower() != 'gmail.com':
            raise HTTPException(422, 'Registra tu empresa con una cuenta Gmail (@gmail.com).')
        ticket = secrets.token_urlsafe(32)
        await flows.insert_one({'_id': digest(ticket), 'binding': digest(binding), 'identity': identity, 'company': flow.get('company'),
            'status': 'REGISTRATION', 'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10)})
        return {'registration_required': True, 'registration_ticket': ticket, 'verified_email': identity['email'], 'company': flow.get('company')}

    async def finish_registration(self, ticket, binding, company, password_hash=None):
        flow = await self.database()['google_oauth_flows'].find_one_and_update({
            '_id': digest(ticket), 'binding': digest(binding), 'status': 'REGISTRATION',
            'expires_at': {'$gt': datetime.now(timezone.utc)},
        }, {'$set': {'status': 'CONSUMED'}})
        if not flow:
            raise HTTPException(400, 'La autorización expiró o ya fue utilizada.')
        details = CompanyDetails(**flow['company']) if flow.get('company') else company
        if details is None:
            raise HTTPException(422, 'Completa los datos de tu empresa.')
        linked = await self.database()['empresas'].find_one({'google_sub': flow['identity']['sub']})
        if linked:
            raise HTTPException(409, 'Esta cuenta ya está registrada. Inicia sesión con tu correo y contraseña de PsiTwin.')
        return await self.register(flow['identity'], details, password_hash=password_hash)

    async def registration_status(self, ticket, binding):
        flow = await self.database()['google_oauth_flows'].find_one({
            '_id': digest(ticket), 'binding': digest(binding), 'status': 'REGISTRATION',
            'expires_at': {'$gt': datetime.now(timezone.utc)},
        })
        if not flow:
            raise HTTPException(400, 'La verificación de Gmail expiró o ya fue utilizada. Verifica nuevamente tu correo.')
        return {'verified_email': flow['identity']['email'], 'company': flow.get('company')}

    async def register(self, identity, details, password_hash=None):
        if identity['email'].rsplit('@', 1)[-1].lower() != 'gmail.com':
            raise HTTPException(422, 'Registra tu empresa con una cuenta Gmail (@gmail.com).')
        await self.indexes()
        db = self.database()
        payload = details.validated(identity['email'])
        for collection in ('empresas', 'operarios', 'proveedores'):
            if await db[collection].find_one({'correo': {'$regex': '^' + re.escape(str(payload.correo)) + '$', '$options': 'i'}}):
                raise HTTPException(409, 'Ya existe una cuenta con ese correo. Inicia sesión con tu contraseña y vincula Google desde Perfil.')
        if await db['empresas'].find_one({'ruc': payload.ruc}):
            raise HTTPException(409, 'Ya existe una empresa con ese RUC. Inicia sesión en tu cuenta existente.')
        now = datetime.now(timezone.utc).isoformat()
        company = {**details.model_dump(), 'nombre_ceo': payload.nombre_ceo, 'nombre': payload.nombre.strip(),
            'id_empresa': str(uuid4()), 'correo': str(payload.correo), 'google_sub': identity['sub'],
            'google_registration_ruc': payload.ruc, 'password': password_hash or await asyncio.to_thread(hash_password, payload.password), 'password_local_habilitada': bool(password_hash),
            'correo_verificado': True, 'fecha_verificacion_correo': now, 'fecha_creacion': now, 'fecha_actualizacion': now}
        try:
            await db['empresas'].insert_one(company)
        except DuplicateKeyError as exc:
            raise HTTPException(409, 'La empresa ya fue registrada.') from exc
        try:
            await WelcomeEmailService(self.database).enqueue(company)
        except Exception:
            logging.getLogger(__name__).error('welcome_enqueue_failed empresa=%s', company['id_empresa'])
        return self.session(company)

    @staticmethod
    def session(company):
        return {'access_token': create_access_token(sub=company['id_empresa'], rol=ROL_EMPRESA, id_empresa=company['id_empresa']),
            'token_type': 'bearer', 'rol': ROL_EMPRESA, 'empresa': EmpresaResponse(**company).model_dump(mode='json'),
            'debe_cambiar_password': False}
