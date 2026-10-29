"""Opt-in real artifact test. No doubles, no training, no MongoDB writes."""
import json
import os
from pathlib import Path
import subprocess
import pytest
from app.config.paths import runtime_path


@pytest.mark.skipif(os.environ.get('PSITWIN_AUTOGLUON_INTEGRATION') != '1', reason='Opt-in: real local model and cached foundation weights required')
def test_load_and_predict_real_weighted_ensemble_90_days():
    root = Path(__file__).resolve().parents[1]
    interpreter = runtime_path('.autogluon.local/Scripts/python.exe')
    if os.name != 'nt': interpreter = runtime_path('.autogluon.local/bin/python')
    result = subprocess.run([str(interpreter), str(root / 'scripts/verificar_autogluon.py')], cwd=root,
                            capture_output=True, text=True, encoding='utf-8', timeout=600,
                            env={**os.environ, 'PYTHONUTF8': '1'})
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((runtime_path('artifacts/autogluon.local/psitwin_forecasting/runtime_validation.json')).read_text(encoding='utf-8'))
    assert report['success'] and report['loaded']
    assert report['forecast_rows'] == 90
    assert report['history_rows'] == 1096
    assert report['quantiles'] == [0.1, 0.5, 0.9]
