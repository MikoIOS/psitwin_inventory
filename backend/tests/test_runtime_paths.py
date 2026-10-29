from pathlib import Path

from app.config import paths
from app.config.settings import Settings


def test_moved_backend_reuses_legacy_runtime_and_allows_local_override(tmp_path, monkeypatch):
    backend = tmp_path / 'backend'
    backend.mkdir()
    monkeypatch.setattr(paths, 'BACKEND_ROOT', backend)
    monkeypatch.setattr(paths, 'REPOSITORY_ROOT', tmp_path)
    legacy = tmp_path / '.voice.local' / 'Scripts' / 'python.exe'
    legacy.parent.mkdir(parents=True)
    legacy.touch()
    assert paths.runtime_path('.voice.local/Scripts/python.exe') == legacy
    assert paths.runtime_path('.voice.local/cache') == tmp_path / '.voice.local/cache'
    local = backend / '.voice.local' / 'Scripts' / 'python.exe'
    local.parent.mkdir(parents=True)
    local.touch()
    assert paths.runtime_path('.voice.local/Scripts/python.exe') == local
    assert paths.runtime_path(str(legacy)) == legacy
    assert Path(Settings(_env_file=None, saiki_voice_python=str(legacy)).saiki_voice_python) == legacy


def test_forecast_status_rejects_an_existing_but_broken_interpreter(tmp_path, monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from app.services.autogluon_runtime import AutoGluonRuntime
    executable = tmp_path / 'python.exe'
    executable.touch()
    settings = SimpleNamespace(autogluon_artifact_dir=str(tmp_path / 'model'), autogluon_python=str(executable), autogluon_cache_dir=str(tmp_path / 'cache'))
    runtime = AutoGluonRuntime(settings)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=103))
    status = runtime.status()
    assert status['validado'] is False
    assert any('no arranca' in missing for missing in status['faltantes'])
