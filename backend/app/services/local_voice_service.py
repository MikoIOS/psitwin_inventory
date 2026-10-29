"""One bounded inference at a time. Cancellation kills native CPU inference.

Unlike cancelling to_thread(), killing this isolated worker actually releases
the inference. The next request reloads it. Normal requests reuse loaded models.
"""
import asyncio
import json
import os
import logging
import subprocess
from pathlib import Path

from fastapi import HTTPException, Request
from app.config.settings import settings
from app.config.paths import BACKEND_ROOT, runtime_path

VOICES = {'em_santa': 'Kokoro em_santa', 'em_alex': 'Kokoro em_alex'}


class LocalVoiceService:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.process = None

    async def close(self):
        process, self.process = self.process, None
        if process:
            if process.poll() is None:
                process.kill()
            await asyncio.to_thread(process.wait)
            process.stdin.close()
            process.stdout.close()

    @staticmethod
    def exchange(process, payload):
        process.stdin.write((json.dumps(payload) + '\n').encode())
        process.stdin.flush()
        return json.loads(process.stdout.readline(16 * 1024 * 1024))

    async def execute(self, payload, request: Request):
        async def perform():
            # A busy inference returns immediately rather than building an unbounded queue.
            if self.lock.locked():
                raise HTTPException(429, 'La voz local está ocupada. Intenta nuevamente.')
            async with self.lock:
                try:
                    if not self.process or self.process.poll() is not None:
                        executable = Path(settings.saiki_voice_python)
                        if not executable.is_file():
                            raise HTTPException(503, 'Falta instalar el entorno de voz local. El chat escrito sigue disponible.')
                        environment = {**os.environ, 'SAIKI_TTS_PROVIDER': settings.saiki_tts_provider,
                            'SAIKI_TTS_MODEL': settings.saiki_tts_model, 'SAIKI_STT_MODEL': settings.saiki_stt_model,
                            'SAIKI_PIPER_MODEL': settings.saiki_piper_model, 'PYTHONIOENCODING': 'utf-8'}
                        environment['SAIKI_VOICE_SITE_PACKAGES'] = settings.saiki_voice_site_packages
                        environment.setdefault('HF_HOME', str(runtime_path('.voice.local/cache')))
                        self.process = subprocess.Popen([str(executable), '-u', '-m',
                            'app.services.local_voice_worker'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            env=environment, cwd=BACKEND_ROOT,
                            **({'creationflags': 0x08000000} if os.name == 'nt' else {}))
                    # Pipe I/O stays in a thread; CPU inference stays in the killable process.
                    # This also works on Windows SelectorEventLoop, required by aiomqtt.
                    result = await asyncio.to_thread(self.exchange, self.process, payload)
                    if 'error' in result:
                        logging.getLogger(__name__).warning('local_voice_failed type=%s operation=%s dependency=%s',
                            result['error'], result.get('operation'), result.get('dependency'))
                        await self.close()
                        raise HTTPException(503, 'El motor local no pudo procesar el audio. Revisa los modelos y eSpeak NG; puedes seguir por texto.')
                    return result
                except BaseException:
                    await self.close()
                    raise
        task = asyncio.create_task(perform())
        stopping = asyncio.Event()
        async def disconnected():
            # Starlette checks disconnect inside an AnyIO cancellation scope.
            # That scope can consume an external cancellation at just the wrong
            # instant; the explicit stop flag also ends that race on success.
            while not stopping.is_set():
                if await request.is_disconnected():
                    return
                await asyncio.sleep(.15)
        watcher = asyncio.create_task(disconnected())
        try:
            done, _ = await asyncio.wait({task, watcher}, timeout=settings.saiki_voice_timeout_seconds,
                                         return_when=asyncio.FIRST_COMPLETED)
            if task in done:
                return await task
            raise HTTPException(408 if watcher in done else 504, 'Se canceló la operación de voz local.')
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, 'El servicio de voz local no está disponible.') from exc
        finally:
            stopping.set()
            task.cancel()
            watcher.cancel()
            await asyncio.gather(task, watcher, return_exceptions=True)


voice_service = LocalVoiceService()
