"""Validated complete-series CSV reader and insert-only batch importer."""
import csv
import hashlib
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from app.database.mongodb import get_database
from app.repositories.empresa_repository import EmpresaRepository

PERCENTAGES = (5, 10, 25, 50, 100)
REQUIRED = {'fecha', 'id_almacen', 'id_producto', 'cantidad', 'es_imputado', 'producto_original', 'categoria'}


def read_dataset(path, percentage=None, product_count=None):
    if percentage is not None and product_count is not None:
        raise ValueError('Seleccione porcentaje o número de productos, no ambos')
    if percentage is None and product_count is None: product_count = 10
    if percentage is not None and percentage not in PERCENTAGES:
        raise ValueError('Porcentaje permitido: 5, 10, 25, 50, 100')
    if product_count is not None and product_count < 1: raise ValueError('Número de productos inválido')
    groups = defaultdict(list)
    seen = set()
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing: raise ValueError(f'Columnas faltantes: {sorted(missing)}')
        for line, row in enumerate(reader, 2):
            try:
                day = date.fromisoformat(row['fecha'])
                quantity = float(row['cantidad'])
                if not math.isfinite(quantity) or quantity < 0: raise ValueError('cantidad inválida')
                if row['es_imputado'] not in ('0', '1'): raise ValueError('es_imputado inválido')
                pair = (row['id_almacen'].strip(), row['id_producto'].strip())
                if not all(pair): raise ValueError('identificadores vacíos')
                key = (*pair, day)
                if key in seen: raise ValueError('fecha duplicada en la serie')
                seen.add(key)
                groups[pair].append({'fecha': day.isoformat(), 'id_almacen': pair[0], 'id_producto': pair[1],
                    'cantidad': quantity, 'es_imputado': row['es_imputado'] == '1',
                    'producto_original': row['producto_original'], 'categoria': row['categoria']})
            except ValueError as error:
                raise ValueError(f'Fila {line}: {error}') from error
    if not groups: raise ValueError('CSV vacío')
    for pair, rows in groups.items():
        rows.sort(key=lambda r: r['fecha'])
        if any(date.fromisoformat(b['fecha']) - date.fromisoformat(a['fecha']) != timedelta(days=1)
               for a, b in zip(rows, rows[1:])):
            raise ValueError(f'Serie no continua: {pair}')
    if product_count is not None:
        products = sorted({p for _, p in groups})
        if product_count > len(products): raise ValueError('El CSV no contiene tantos productos distintos')
        selected_products = set(products[:product_count])
        selected = sorted(pair for pair in groups if pair[1] in selected_products)
    else:
        selected = sorted(groups)[:max(1, math.ceil(len(groups) * percentage / 100))]
    return [row for pair in selected for row in groups[pair]], {
        'series_dataset': len(groups), 'series_seleccionadas': len(selected),
        'productos_seleccionados': len({p for _, p in selected}),
        'documentos_seleccionados': sum(len(groups[p]) for p in selected),
        'longitudes_dataset': sorted({len(r) for r in groups.values()}),
        'fecha_inicio': min(r['fecha'] for p in selected for r in groups[p]),
        'fecha_fin': max(r['fecha'] for p in selected for r in groups[p]),
    }


def observation(tenant, row):
    key = '\0'.join((tenant, row['id_almacen'], row['id_producto'], row['fecha']))
    return {**row, '_id': hashlib.sha256(key.encode()).hexdigest(), 'id_empresa': tenant,
            'origen': 'forecasting_csv'}


async def import_rows(tenant, rows, dry_run=True, batch_size=1000):
    if batch_size < 1: raise ValueError('Lote inválido')
    company = await EmpresaRepository.obtener_por_id(tenant)
    if not company: raise ValueError('La empresa debe existir en la base de pruebas')
    collection = get_database()['demanda_historica']
    result = {'insertados': 0, 'omitidos': 0, 'fallidos': 0, 'por_insertar': 0, 'conflictos': 0,
              'empresa': company.get('nombre'), 'correo_acceso': company.get('correo')}
    if not dry_run:
        await collection.create_index([('id_empresa', 1), ('id_almacen', 1), ('id_producto', 1), ('fecha', 1)],
                                      unique=True, name='uq_demanda_historica_serie_fecha')
    for start in range(0, len(rows), batch_size):
        documents = [observation(tenant, r) for r in rows[start:start + batch_size]]
        existing = await collection.find({'_id': {'$in': [d['_id'] for d in documents]}}).to_list(length=None)
        by_id = {d['_id']: d for d in existing}
        result['conflictos'] += sum(any(old.get(k) != v for k, v in d.items())
                                   for d in documents if (old := by_id.get(d['_id'])) is not None)
        if dry_run:
            result['omitidos'] += len(existing)
            result['por_insertar'] += len(documents) - len(existing)
            continue
        operations = [UpdateOne({'_id': d['_id']}, {'$setOnInsert': d}, upsert=True) for d in documents]
        try:
            written = await collection.bulk_write(operations, ordered=False)
            result['insertados'] += written.upserted_count
            result['omitidos'] += written.matched_count
        except BulkWriteError as error:
            details = error.details
            result['insertados'] += details.get('nUpserted', 0)
            result['omitidos'] += details.get('nMatched', 0)
            result['fallidos'] += len(details.get('writeErrors', []))
            if details.get('writeConcernErrors'):
                raise RuntimeError('MongoDB no confirmó la durabilidad del lote; reejecutar es idempotente') from error
    return result
