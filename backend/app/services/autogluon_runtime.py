"""One isolated predictor process, serialized inference and content-addressed cache."""
import atexit
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
from uuid import uuid4

from app.config.settings import get_settings
from app.config.paths import runtime_path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / 'app/ml/autogluon_manifest.json').read_text(encoding='utf-8'))


class ModelUnavailable(RuntimeError):
    pass


class AutoGluonRuntime:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.root = (ROOT / self.settings.autogluon_artifact_dir).resolve()
        self.python = (ROOT / self.settings.autogluon_python).resolve()
        self.cache_dir = (ROOT / self.settings.autogluon_cache_dir).resolve()
        self.process = None
        self.responses = queue.Queue()
        self.lock = threading.Lock()
        self.memory = OrderedDict()
        self.log = None
        self._interpreter_check = (0.0, False)
        self._fingerprint_state = None
        self._fingerprint_value = None
        atexit.register(self.close)

    def fingerprint(self):
        path = self.root / 'modelo_evaluacion'
        files = sorted(path.rglob('*.pkl'))
        if not files:
            return None
        state = tuple((str(file), file.stat().st_size, file.stat().st_mtime_ns) for file in files if 'utils' not in file.parts)
        if state == self._fingerprint_state: return self._fingerprint_value
        digest = hashlib.sha256()
        for file in files:
            if 'utils' in file.parts:
                continue
            digest.update(str(file.relative_to(path)).encode())
            digest.update(file.read_bytes())
        self._fingerprint_state = state
        self._fingerprint_value = digest.hexdigest()
        return self._fingerprint_value

    def status(self):
        missing = []
        if not self.python.is_file():
            missing.append('Entorno aislado con autogluon.timeseries==1.6.1, torch y dependencias')
        else:
            checked, usable = self._interpreter_check
            if time.monotonic() - checked > 60:
                try:
                    probe = subprocess.run([str(self.python), '-c', 'import sys; assert sys.version_info >= (3, 10)'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    usable = probe.returncode == 0
                except (OSError, subprocess.TimeoutExpired):
                    usable = False
                self._interpreter_check = (time.monotonic(), usable)
            if not usable:
                missing.append('El intérprete aislado no arranca; revise pyvenv.cfg y la instalación base de Python')
        for name in ['predictor.pkl', 'learner.pkl', 'models/trainer.pkl', 'models/WeightedEnsemble/model.pkl']:
            if not (self.root / 'modelo_evaluacion' / name).is_file(): missing.append('modelo_evaluacion/' + name)
        report_path = self.root / 'runtime_validation.json'
        report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.is_file() else {}
        fingerprint = self.fingerprint()
        verified = bool(not missing and report.get('success') is True and report.get('model_fingerprint') == fingerprint)
        return {'estado': 'DISPONIBLE' if verified else 'MODELO_NO_DISPONIBLE', 'validado': verified,
                'modelo': 'WeightedEnsemble', 'version': '1.6.1', 'tipo': 'EVALUACION_NO_REENTRENADO',
                'faltantes': missing or ([] if verified else report.get('missing', ['Falta ejecutar una predicción real de validación del ensemble con Chronos2 y Toto2.'])),
                'detalle': report.get('detail'), 'model_fingerprint': fingerprint,
                'ultima_validacion': report.get('validated_at')}

    def close(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None
        if self.log is not None:
            self.log.close()
            self.log = None

    def _start(self):
        if self.process and self.process.poll() is None:
            return
        self.close()
        self.responses = queue.Queue()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log = (self.cache_dir / 'worker.log').open('a', encoding='utf-8')
        env = {**os.environ, 'HF_HOME': str(runtime_path('artifacts/huggingface.local')), 'HF_HUB_OFFLINE': '1',
               'PYTHONUTF8': '1', 'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
        self.process = subprocess.Popen([str(self.python), '-u', str(ROOT / 'app/ml/autogluon_worker.py'),
                                         '--model', str(self.root / 'modelo_evaluacion'), '--serve'],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                                        text=True, encoding='utf-8', env=env,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        process, responses = self.process, self.responses
        def reader():
            for line in process.stdout:
                responses.put(line)
            responses.put(None)
        threading.Thread(target=reader, daemon=True).start()

    def predict(self, tenant, identifier, history):
        # The entire history, tenant, model and calendar contract participate in invalidation.
        signature = {'tenant': tenant, 'series_id': identifier, 'history': history,
                     'model': self.fingerprint(), 'calendar': MANIFEST['calendar']}
        key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        with self.lock:
            state = self.status()
            if not state['validado']:
                raise ModelUnavailable('; '.join(state['faltantes']))
            if key in self.memory:
                self.memory.move_to_end(key)
                return self.memory[key], True
            cache = self.cache_dir / (key + '.json')
            if cache.is_file():
                result = json.loads(cache.read_text(encoding='utf-8'))
                self.memory[key] = result
                return result, True
            self._start()
            payload = {'series': [{'series_id': identifier, 'history': history}]}
            try:
                self.process.stdin.write(json.dumps(payload) + '\n'); self.process.stdin.flush()
                line = self.responses.get(timeout=self.settings.autogluon_timeout_seconds)
                if line is None:
                    raise ModelUnavailable('El proceso de AutoGluon terminó; revisa worker.log.')
                result = json.loads(line)
                if result.get('error'):
                    raise ModelUnavailable(result['error'])
                if len(result['predictions'][identifier]) != 90:
                    raise ModelUnavailable('Salida incompleta del predictor')
            except (queue.Empty, BrokenPipeError) as error:
                self.close()
                raise ModelUnavailable('Tiempo de inferencia agotado o proceso no disponible') from error
            temp = cache.with_suffix('.' + uuid4().hex + '.tmp')
            temp.write_text(json.dumps(result, allow_nan=False), encoding='utf-8')
            temp.replace(cache)
            self.memory[key] = result
            while len(self.memory) > 128: self.memory.popitem(last=False)
            return result, False


runtime = AutoGluonRuntime()
