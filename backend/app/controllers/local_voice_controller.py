import base64
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

from app.config.settings import settings
from app.dependencies.dependencies import require_empresa_u_operario as require_empresa
from app.services.local_voice_service import VOICES, voice_service

router = APIRouter(prefix='/saiki/voice', tags=['Saiki voz local'], dependencies=[Depends(require_empresa)])


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    voice: Literal['em_santa', 'em_alex'] | None = None
    speed: float | None = Field(default=None, ge=.5, le=2)

    @field_validator('text')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('El texto está vacío')
        return value.strip()


@router.get('/config')
async def config():
    return {'provider': settings.saiki_tts_provider, 'enabled': settings.saiki_tts_enabled,
        'voices': [{'id': key, 'name': name, 'lang': 'es'} for key, name in VOICES.items()] if settings.saiki_tts_provider == 'kokoro' else [{'id': 'em_santa', 'name': 'Piper local configurado', 'lang': 'es'}],
        'default_voice': settings.saiki_tts_voice, 'stt_enabled': settings.saiki_stt_enabled,
        'installed': __import__('pathlib').Path(settings.saiki_voice_python).is_file()}


@router.post('/synthesize')
async def synthesize(data: SpeechRequest, request: Request):
    if not settings.saiki_tts_enabled:
        raise HTTPException(503, 'La síntesis local está desactivada.')
    if settings.saiki_tts_provider not in {'kokoro', 'piper'}:
        raise HTTPException(503, 'Proveedor local no válido.')
    voice = data.voice or settings.saiki_tts_voice
    if voice not in VOICES or settings.saiki_tts_language != 'es':
        raise HTTPException(503, 'Configura una voz española compatible.')
    result = await voice_service.execute({'operation': 'synthesize', 'text': data.text,
        'voice': voice, 'speed': data.speed or settings.saiki_tts_speed}, request)
    return Response(base64.b64decode(result['audio']), media_type='audio/wav', headers={'Cache-Control': 'no-store'})


@router.post('/probe/{voice}')
async def probe(voice: Literal['em_santa', 'em_alex'], request: Request):
    if not settings.saiki_tts_enabled or settings.saiki_tts_provider != 'kokoro':
        raise HTTPException(503, 'Kokoro no está habilitado.')
    return await voice_service.execute({'operation': 'probe', 'voice': voice}, request)


@router.post('/transcribe')
async def transcribe(request: Request):
    if not settings.saiki_stt_enabled:
        raise HTTPException(503, 'La transcripción local está desactivada.')
    content_type = request.headers.get('content-type', '').split(';')[0]
    if content_type not in {'audio/webm', 'audio/ogg', 'audio/wav', 'audio/mp4'}:
        raise HTTPException(415, 'Formato de grabación no admitido.')
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 4 * 1024 * 1024:
            raise HTTPException(413, 'La grabación supera 4 MB. Graba un mensaje de hasta 30 segundos.')
        chunks.append(chunk)
    if size < 100:
        raise HTTPException(422, 'No hay audio suficiente.')
    result = await voice_service.execute({'operation': 'transcribe', 'audio': base64.b64encode(b''.join(chunks)).decode()}, request)
    text = result['text'].strip()
    if not text or not any(c.isalpha() for c in text):
        raise HTTPException(422, 'No se detectó habla inteligible. Intenta nuevamente o escribe tu pregunta.')
    return {'text': text}
