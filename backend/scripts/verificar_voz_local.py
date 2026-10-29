"""Download official models, synthesize both Spanish voices, then transcribe a sample.

Run with .voice.local/Scripts/python.exe scripts/verificar_voz_local.py.
This does not access the microphone or send audio/text to remote inference.
"""
import base64
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('HF_HOME', str((ROOT.parent if (ROOT.parent / '.voice.local').exists() else ROOT) / '.voice.local/cache'))
os.environ.setdefault('SAIKI_STT_MODEL', 'base')

from app.services.local_voice_worker import run

(ROOT / 'artifacts').mkdir(exist_ok=True)
report = ROOT / 'artifacts' / 'voz-local-validacion.json'
results = json.loads(report.read_text(encoding='utf-8')) if '--stt-only' in sys.argv and report.is_file() else {}
for voice in (() if '--stt-only' in sys.argv else ('em_santa', 'em_alex')):
    started = time.perf_counter()
    try:
        result = run({'operation': 'synthesize', 'text': 'Hola, soy Saiki, tu asistente de PsiTwin. Puedo ayudarte a revisar tus almacenes y consultar las lecturas de tus sensores.', 'voice': voice, 'speed': 1.0})
        audio = base64.b64decode(result['audio'])
        target = ROOT / 'artifacts' / f'saiki-{voice}.wav'
        target.write_bytes(audio)
        results[voice] = {'ok': True, 'bytes': len(audio), 'seconds': round(time.perf_counter() - started, 3)}
        print(voice, results[voice], flush=True)
    except Exception as exc:
        results[voice] = {'ok': False, 'error': type(exc).__name__, 'detail': str(exc)[:300]}
        print(voice, results[voice], flush=True)
sample = ROOT / 'artifacts' / 'saiki-em_santa.wav'
if sample.is_file():
    started = time.perf_counter()
    try:
        result = run({'operation': 'transcribe', 'audio': base64.b64encode(sample.read_bytes()).decode()})
        results['stt'] = {'ok': bool(result['text']), 'text': result['text'], 'seconds': round(time.perf_counter() - started, 3)}
    except Exception as exc:
        results['stt'] = {'ok': False, 'error': type(exc).__name__, 'detail': str(exc)[:300]}
    print('stt', results['stt'], flush=True)
(ROOT / 'artifacts' / 'voz-local-validacion.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
sys.exit(0 if len(results) == 3 and all(row['ok'] for row in results.values()) else 1)
