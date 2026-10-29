"""Real load + 90-day smoke prediction on one complete series from the supplied ZIP.

Run using the isolated interpreter. No training and no MongoDB connection.
The report gates availability in FastAPI: a failed smoke never becomes a usable forecast.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config.paths import runtime_path


def fingerprint(path):
    digest = hashlib.sha256()
    for file in sorted(path.rglob('*.pkl')):
        if 'utils' in file.parts: continue
        digest.update(str(file.relative_to(path)).encode()); digest.update(file.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, default=runtime_path('artifacts/autogluon.local/psitwin_forecasting'))
    parser.add_argument('--allow-downloads', action='store_true')
    args = parser.parse_args()
    root = args.artifact.resolve()
    os.environ['HF_HOME'] = str(runtime_path('artifacts/huggingface.local'))
    os.environ['HF_HUB_OFFLINE'] = '0' if args.allow_downloads else '1'
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['OPENBLAS_NUM_THREADS'] = '2'
    report = {'success': False, 'validated_at': datetime.now(timezone.utc).isoformat(),
              'model_fingerprint': fingerprint(root / 'modelo_evaluacion'), 'source': 'reference series in supplied artifact; not MongoDB',
              'evaluation_only': True, 'model': 'WeightedEnsemble', 'missing': []}
    try:
        import pandas as pd
        from app.ml.autogluon_worker import load_predictor, predict
        predictor = load_predictor(root / 'modelo_evaluacion')
        report['loaded'] = True
        data = pd.read_pickle(root / 'datos_limpios.pkl')
        identifier = str(data.iloc[0]['item_id'])
        history = data[data.item_id == identifier].sort_values('timestamp')
        rows = [{'fecha': row.timestamp.date().isoformat(), 'cantidad': float(row.cantidad)} for row in history.itertuples()]
        (root / 'smoke_input.json').write_text(json.dumps({'series': [{'series_id': identifier, 'history': rows}]}), encoding='utf-8')
        output = predict(predictor, {'series': [{'series_id': identifier, 'history': rows}]})
        daily = output['predictions'][identifier]
        assert len(daily) == 90
        assert {'q10', 'q50', 'q90'} <= daily[0].keys()
        (root / 'smoke_predictions.json').write_text(json.dumps(output, allow_nan=False), encoding='utf-8')
        report.update(success=True, history_rows=len(rows), forecast_rows=len(daily), first_forecast=daily[0]['fecha'], last_forecast=daily[-1]['fecha'],
                      quantiles=[0.1, 0.5, 0.9], detail='TimeSeriesPredictor.load y predict(model=WeightedEnsemble) completados sin reentrenamiento.')
    except Exception as error:
        import traceback
        traceback.print_exc()
        report['missing'] = [type(error).__name__ + ': ' + str(error)]
        report['detail'] = 'No hay validación funcional del modelo completo. No se publican predicciones simuladas.'
    from importlib.metadata import version, PackageNotFoundError
    report['versions'] = {}
    for package in ['autogluon.timeseries', 'torch', 'pandas', 'numpy', 'scikit-learn', 'transformers', 'chronos-forecasting']:
        try: report['versions'][package] = version(package)
        except PackageNotFoundError: report['versions'][package] = 'MISSING'
    report['foundation_weights'] = {}
    for repository in ['autogluon/chronos-2', 'Datadog/Toto-2.0-22m']:
        cached = ROOT / 'artifacts/huggingface.local/hub' / ('models--' + repository.replace('/', '--'))
        files = [file for file in cached.glob('snapshots/**/*') if file.is_file() and file.suffix in ('.safetensors', '.bin', '.pt')]
        report['foundation_weights'][repository] = {'cached_files': [file.name for file in files], 'cached_bytes': sum(file.stat().st_size for file in files)}
    temporary = root / 'runtime_validation.tmp'
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(root / 'runtime_validation.json')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
