import asyncio
import csv
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import importar_demanda as loader


def make_csv(path, pairs=20, days=4):
    rows = [dict(fecha=(date(2025, 1, 1) + timedelta(days=d)).isoformat(),
                 id_almacen=f'a{i:03}', id_producto=f'p{i:03}', cantidad=str(d + 1),
                 es_imputado=str(d % 2), producto_original=str(i), categoria='FOODS')
            for i in range(pairs) for d in range(days)]
    write_csv(path, list(reversed(rows)))
    return rows


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_percentage_selects_complete_sorted_nested_series(tmp_path):
    path = tmp_path / 'data.csv'
    make_csv(path, pairs=200)
    previous = set()
    for percentage, expected in [(5, 10), (10, 20), (25, 50), (50, 100), (100, 200)]:
        rows, summary = loader.read_dataset(path, percentage)
        pairs = {(r['id_almacen'], r['id_producto']) for r in rows}
        assert len(pairs) == expected and len(rows) == expected * 4
        assert previous <= pairs
        for pair in pairs:
            assert [r['fecha'] for r in rows if (r['id_almacen'], r['id_producto']) == pair] == [
                '2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04']
        assert summary['series_dataset'] == 200
        previous = pairs
    assert loader.read_dataset(path)[1]['productos_seleccionados'] == 10


def test_ten_products_include_every_warehouse_series(tmp_path):
    path = tmp_path / 'data.csv'
    rows = make_csv(path, pairs=12)
    rows.extend([dict(row, id_almacen='another') for row in rows[:4]])
    write_csv(path, rows)
    selected, summary = loader.read_dataset(path)
    assert len({r['id_producto'] for r in selected}) == 10
    assert summary['series_seleccionadas'] == 11 and len(selected) == 44
    assert len([r for r in selected if r['id_producto'] == 'p000']) == 8
    with pytest.raises(ValueError): loader.read_dataset(path, product_count=13)
    with pytest.raises(ValueError): loader.read_dataset(path, product_count=0)
    with pytest.raises(ValueError): loader.read_dataset(path, percentage=10, product_count=10)


@pytest.mark.parametrize('corruption', ['duplicate', 'gap', 'negative', 'nan', 'missing_column', 'imputed'])
def test_invalid_dataset_stops_before_database_access(tmp_path, corruption):
    path = tmp_path / 'data.csv'
    rows = make_csv(path, pairs=1)
    if corruption == 'duplicate': rows.append(rows[0])
    if corruption == 'gap': rows.pop(1)
    if corruption == 'negative': rows[0]['cantidad'] = '-1'
    if corruption == 'nan': rows[0]['cantidad'] = 'nan'
    if corruption == 'imputed': rows[0]['es_imputado'] = '2'
    if corruption == 'missing_column':
        for row in rows: row.pop('id_producto')
    write_csv(path, rows)
    with pytest.raises(ValueError): loader.read_dataset(path)


class MemoryCollection:
    def __init__(self): self.documents = {}; self.index_calls = 0; self.batches = []
    async def create_index(self, *args, **kwargs): self.index_calls += 1
    def find(self, query):
        return SimpleNamespace(to_list=AsyncMock(return_value=[d for k, d in self.documents.items() if k in query['_id']['$in']]))
    async def bulk_write(self, operations, ordered):
        assert not ordered
        self.batches.append(len(operations))
        inserted = matched = 0
        for op in operations:
            assert set(op._doc) == {'$setOnInsert'}
            doc = op._doc['$setOnInsert']
            if doc['_id'] in self.documents: matched += 1
            else: self.documents[doc['_id']] = dict(doc); inserted += 1
        return SimpleNamespace(upserted_count=inserted, matched_count=matched)


def test_batches_dry_run_duplicates_conflicts_and_tenant_isolation(tmp_path, monkeypatch):
    path = tmp_path / 'data.csv'
    make_csv(path, pairs=1)
    rows, _ = loader.read_dataset(path, 100)
    collection = MemoryCollection()
    monkeypatch.setattr(loader, 'get_database', lambda: {'demanda_historica': collection})
    monkeypatch.setattr(loader.EmpresaRepository, 'obtener_por_id', AsyncMock(return_value={'nombre': 'Test', 'correo': 'test@example.com'}))
    async def run():
        preview = await loader.import_rows('e', rows)
        assert preview['por_insertar'] == 4 and not collection.documents and collection.index_calls == 0
        first = await loader.import_rows('e', rows, dry_run=False, batch_size=3)
        assert first['insertados'] == 4 and collection.batches == [3, 1]
        second = await loader.import_rows('e', rows, dry_run=False)
        assert second['insertados'] == 0 and second['omitidos'] == 4
        modified = [dict(r, cantidad=999) for r in rows]
        conflict = await loader.import_rows('e', modified, dry_run=False)
        assert conflict['conflictos'] == 4 and conflict['omitidos'] == 4
        assert all(d['cantidad'] != 999 for d in collection.documents.values())
        other = await loader.import_rows('other', rows, dry_run=False)
        assert other['insertados'] == 4 and len(collection.documents) == 8
    asyncio.run(run())


def test_missing_company_never_creates_entities(tmp_path, monkeypatch):
    monkeypatch.setattr(loader.EmpresaRepository, 'obtener_por_id', AsyncMock(return_value=None))
    with pytest.raises(ValueError, match='empresa'):
        asyncio.run(loader.import_rows('absent', [], False))


def test_bulk_failures_are_counted_without_overwrites(monkeypatch):
    from pymongo.errors import BulkWriteError
    collection = MemoryCollection()
    collection.bulk_write = AsyncMock(side_effect=BulkWriteError({
        'nUpserted': 1, 'nMatched': 0, 'writeErrors': [{'index': 1, 'code': 121}], 'writeConcernErrors': []}))
    monkeypatch.setattr(loader, 'get_database', lambda: {'demanda_historica': collection})
    monkeypatch.setattr(loader.EmpresaRepository, 'obtener_por_id', AsyncMock(return_value={'nombre': 'Test'}))
    rows = [{'id_almacen': 'a', 'id_producto': 'p', 'fecha': f'2025-01-0{i}', 'cantidad': 1} for i in (1, 2)]
    result = asyncio.run(loader.import_rows('e', rows, dry_run=False))
    assert result['insertados'] == 1 and result['fallidos'] == 1
