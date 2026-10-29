"""Isolated, read-only inference worker. Never fits models or connects to MongoDB."""
import argparse
import contextlib
from datetime import timedelta
import json
from pathlib import Path
import sys
import traceback
import pathlib
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.ml.autogluon_calendar import COVARIATES, calendar_values


def load_predictor(path):
    # Python 3.13 moved pathlib classes to pathlib._local. The supplied trainer
    # pickles Linux paths. Map only those serialized path classes to local path
    # classes in this isolated worker; AutoGluon then resets model contexts.
    # No weights/pickle bytes are edited. Prediction validation is still required.
    if sys.version_info < (3, 13) and 'pathlib._local' not in sys.modules:
        compatibility = types.ModuleType('pathlib._local')
        for name in ('Path', 'PosixPath', 'WindowsPath'):
            setattr(compatibility, name, pathlib.Path)
        compatibility.PurePath = pathlib.PurePath
        compatibility.PurePosixPath = pathlib.PurePosixPath
        compatibility.PureWindowsPath = pathlib.PureWindowsPath
        sys.modules['pathlib._local'] = compatibility
    import autogluon.timeseries as ag
    from autogluon.timeseries import TimeSeriesPredictor
    if ag.__version__ != '1.6.1':
        raise RuntimeError(f'AutoGluon 1.6.1 requerido; instalado {ag.__version__}')
    predictor = TimeSeriesPredictor.load(str(path), require_version_match=True)
    if predictor.prediction_length != 90 or predictor.target != 'cantidad' or predictor.freq != 'D':
        raise ValueError('Contrato incompatible: cantidad, D y horizonte 90 requeridos')
    if set(predictor.known_covariates_names) != set(COVARIATES):
        raise ValueError('Covariables del artefacto incompatibles')
    if 'WeightedEnsemble' not in predictor.model_names():
        raise ValueError('WeightedEnsemble no está disponible')
    return predictor


def predict(predictor, payload):
    import numpy as np
    import pandas as pd
    from autogluon.timeseries import TimeSeriesDataFrame
    rows = []
    for item in payload['series']:
        for row in item['history']:
            timestamp = pd.Timestamp(row['fecha'])
            rows.append({'item_id': item['series_id'], 'timestamp': timestamp,
                         'cantidad': row['cantidad'], **calendar_values(timestamp.date())})
    frame = pd.DataFrame(rows)
    if frame.empty or frame.duplicated(['item_id', 'timestamp']).any():
        raise ValueError('Historial vacío o duplicado')
    if not np.isfinite(frame['cantidad']).all() or (frame['cantidad'] < 0).any():
        raise ValueError('Demanda histórica inválida')
    data = TimeSeriesDataFrame.from_data_frame(frame, id_column='item_id', timestamp_column='timestamp')
    future = predictor.make_future_data_frame(data)
    for name in COVARIATES:
        future[name] = [calendar_values(timestamp.date())[name] for timestamp in future['timestamp']]
    covariates = TimeSeriesDataFrame.from_data_frame(future, id_column='item_id', timestamp_column='timestamp')
    # Explicit model: never use a fallback model if a member of the ensemble fails.
    predictions = predictor.predict(data, known_covariates=covariates, model='WeightedEnsemble', use_cache=False)
    if not {'mean', '0.1', '0.5', '0.9'}.issubset(predictions.columns):
        raise ValueError('La salida no incluye mean y los cuantiles 0.1/0.5/0.9 requeridos')
    result = {}
    for item in payload['series']:
        part = predictions.loc[item['series_id']].sort_index()
        if len(part) != 90:
            raise ValueError('El modelo no produjo exactamente 90 días')
        expected = pd.date_range(pd.Timestamp(item['history'][-1]['fecha']) + timedelta(days=1), periods=90, freq='D')
        if not part.index.equals(expected):
            raise ValueError('Fechas de salida incompatibles con el corte')
        values = part[['mean', '0.1', '0.5', '0.9']].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError('El modelo devolvió valores no finitos')
        if ((values[:, 1] > values[:, 2]) | (values[:, 2] > values[:, 3])).any():
            raise ValueError('Cuantiles no ordenados; no se fabrican intervalos')
        result[item['series_id']] = [
            {'fecha': timestamp.date().isoformat(), 'cantidad': float(max(0, row['mean'])),
             'q10': float(max(0, row['0.1'])), 'q50': float(max(0, row['0.5'])), 'q90': float(max(0, row['0.9']))}
            for timestamp, row in part.iterrows()]
    return {'predictions': result, 'negative_values_clipped': bool((predictions[['mean', '0.1', '0.5', '0.9']] < 0).any().any())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = sys.stdout
    try:
        with contextlib.redirect_stdout(sys.stderr):
            predictor = load_predictor(args.model)
        if args.serve:
            for line in sys.stdin:
                try:
                    with contextlib.redirect_stdout(sys.stderr):
                        response = predict(predictor, json.loads(line))
                    output.write(json.dumps(response, allow_nan=False) + '\n'); output.flush()
                except Exception as error:
                    output.write(json.dumps({'error': type(error).__name__ + ': ' + str(error)}) + '\n'); output.flush()
        elif args.input:
            with contextlib.redirect_stdout(sys.stderr):
                response = predict(predictor, json.loads(args.input.read_text(encoding='utf-8')))
            if args.output:
                args.output.write_text(json.dumps(response, allow_nan=False), encoding='utf-8')
            else:
                output.write(json.dumps(response, allow_nan=False) + '\n')
        else:
            output.write(json.dumps({'loaded': True, 'model': 'WeightedEnsemble', 'horizon': predictor.prediction_length, 'models': predictor.model_names()}) + '\n')
    except Exception as error:
        traceback.print_exc(file=sys.stderr)
        output.write(json.dumps({'error': type(error).__name__ + ': ' + str(error)}) + '\n'); output.flush()
        raise SystemExit(1)


if __name__ == '__main__':
    main()
