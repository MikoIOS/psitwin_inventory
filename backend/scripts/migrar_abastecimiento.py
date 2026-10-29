"""Idempotent additive migration. Default is a read-only plan; stop writers before --apply.

python scripts/migrar_abastecimiento.py
python scripts/migrar_abastecimiento.py --apply --backup <new-directory>
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config.settings import settings


async def plan(db):
    operations = []
    zones = await db.zonas.find({}).to_list(length=None)
    racks = await db.racks.find({}).to_list(length=None)
    for row in zones:
        changes = {}
        if row.get('max_racks') is None:
            changes['max_racks'] = max(row.get('capacidad', 0), sum(r['id_zona'] == row.get('id', row.get('id_zona')) for r in racks))
        if not row.get('codigo'):
            changes['codigo'] = 'Z-' + str(row.get('id', row.get('id_zona')))[:12].upper()
        if changes:
            operations.append(('zonas', {'_id': row['_id']}, changes))
    levels = []
    for rack in racks:
        identifier = str(uuid5(NAMESPACE_URL, 'psitwin-nivel-heredado:' + rack['id_rack']))
        if not await db.niveles.find_one({'id_rack': rack['id_rack']}):
            levels.append({'id_nivel': identifier, 'id_rack': rack['id_rack'], 'codigo': 'HEREDADO', 'numero': 1,
                'origen': 'MIGRACION_ABASTECIMIENTO', 'fecha_creacion': datetime.now(timezone.utc)})
        if 'max_niveles' not in rack:
            operations.append(('racks', {'_id': rack['_id']}, {'max_niveles': 1}))
        for detail in await db.detalles_inventario.find({'id_rack': rack['id_rack'], 'id_nivel': {'$exists': False}}).to_list(length=None):
            existing = await db.niveles.find_one({'id_rack': rack['id_rack']}, sort=[('numero', 1)])
            operations.append(('detalles_inventario', {'_id': detail['_id']}, {'id_nivel': (existing or {'id_nivel': identifier})['id_nivel']}))
    for product in await db.productos.find({}).to_list(length=None):
        changes = {k: v for k, v in {'unidad': 'unidad', 'activo': True}.items() if k not in product}
        if changes:
            operations.append(('productos', {'_id': product['_id']}, changes))
    return operations, levels


async def apply(db, backup):
    operations, levels = await plan(db)
    directory = Path(backup).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    # Capture the originals and index definitions before any change. No prices,
    # availability, accepted receipts, or classification names are fabricated.
    for name in ('zonas', 'racks', 'niveles', 'productos', 'detalles_inventario'):
        (directory / (name + '.json')).write_text(json_util.dumps(await db[name].find({}).to_list(length=None)), encoding='utf-8')
    (directory / 'indices.json').write_text(json_util.dumps(await db.detalles_inventario.index_information()), encoding='utf-8')
    for level in levels:
        await db.niveles.update_one({'id_nivel': level['id_nivel']}, {'$setOnInsert': level}, upsert=True)
    for collection, query, changes in operations:
        await db[collection].update_one(query, {'$set': changes})
    await db.detalles_inventario.create_index([('id_inventario', 1), ('id_producto', 1), ('id_rack', 1), ('id_nivel', 1)], unique=True, name='uq_detalle_inventario_ubicacion_v3')
    for name, index in (await db.detalles_inventario.index_information()).items():
        if index.get('unique') and index['key'] == [('id_inventario', 1), ('id_producto', 1), ('id_rack', 1)]:
            await db.detalles_inventario.drop_index(name)
    await db.ofertas_proveedor.create_index('id_oferta', unique=True)
    await db.ofertas_proveedor.create_index([('id_empresa', 1), ('id_proveedor', 1), ('id_producto', 1)], unique=True)
    await db.niveles.create_index([('id_rack', 1), ('numero', 1)], unique=True)
    await db.niveles.create_index([('id_rack', 1), ('codigo', 1)], unique=True)
    return {'actualizaciones': len(operations), 'niveles_heredados': len(levels)}


async def main(args):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
    try:
        await client.admin.command('ping')
        db = client[settings.mongodb_database]
        if args.apply:
            if not args.backup:
                raise SystemExit('--apply requiere --backup en un directorio nuevo y escritores detenidos')
            result = await apply(db, args.backup)
        else:
            operations, levels = await plan(db)
            result = {'modo': 'SOLO_LECTURA', 'actualizaciones': len(operations), 'niveles_heredados': len(levels),
                'ofertas_inventadas': 0, 'pedidos_alterados': 0, 'stock_alterado': 0}
        print(json.dumps(result))
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup')
    asyncio.run(main(parser.parse_args()))
