"""Run explicitly from the terminal. Never imported by FastAPI startup."""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', type=Path, default=Path(r'C:\Users\dylan\OneDrive\Escritorio\PsiTwin-Demand\psitwin_dataset_v2\dataset_entrenamiento_forecasting_3_anos_completo.csv'))
    selection = p.add_mutually_exclusive_group()
    selection.add_argument('--porcentaje', type=int, choices=(5, 10, 25, 50, 100))
    selection.add_argument('--productos', type=int, help='Productos distintos con todas sus series; predeterminado: 10')
    p.add_argument('--empresa-id', required=True)
    p.add_argument('--database', default='psitwin_forecasting_test')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--confirmar', action='store_true')
    p.add_argument('--lote', type=int, default=1000)
    p.add_argument('--log', type=Path, default=Path('importar_demanda.log'))
    return p


async def run(args):
    from app.config.settings import settings
    from app.database import mongodb
    from app.services.importar_demanda import read_dataset, import_rows
    # Explicit allowlisted test database, distinct from the normal configured database.
    production = os.environ.get('PSITWIN_PRODUCTION_DATABASE', settings.mongodb_database)
    if args.database == production or not args.database.endswith('_test'):
        raise ValueError('Solo se admite una base independiente con sufijo _test')
    if not args.dry_run and not args.confirmar:
        raise ValueError('Para escribir se requiere --confirmar; para inspeccionar use --dry-run')
    if args.lote < 1: raise ValueError('--lote debe ser positivo')
    rows, summary = read_dataset(args.csv, args.porcentaje, args.productos)
    logging.info('Inspección CSV: %s', json.dumps(summary, ensure_ascii=False))
    settings.mongodb_database = args.database
    # Same Motor connection configuration; no startup schema writes during dry-run.
    if mongodb.AsyncIOMotorClient is None: raise RuntimeError('Instale requirements.txt')
    mongodb.client = mongodb.AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    mongodb.database = mongodb.client[args.database]
    try:
        await mongodb.client.admin.command('ping')
        result = await import_rows(args.empresa_id, rows, args.dry_run, args.lote)
        logging.info('Resumen: %s', json.dumps({**summary, **result, 'database': args.database,
                     'dry_run': args.dry_run}, ensure_ascii=False))
        if result['fallidos']: return 1
        return 0
    finally:
        await mongodb.close_mongo_connection()


if __name__ == '__main__':
    args = parser().parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(args.log, encoding='utf-8')])
    try:
        sys.exit(asyncio.run(run(args)))
    except Exception as error:
        logging.error('Carga detenida: %s', error)
        sys.exit(1)
