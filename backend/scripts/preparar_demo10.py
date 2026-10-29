"""Prepare a separate, repeatable 10-product demo without deleting the previous import."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def run(args):
    from app.database import mongodb
    from app.config.settings import settings
    from app.services.importar_demanda import read_dataset
    from app.services.demo_forecasting import prepare_demo
    from app.repositories.empresa_repository import EmpresaRepository
    if args.source_database != 'psitwin_forecasting_test': raise ValueError('Solo se admite la empresa de la base de pruebas anterior')
    if settings.mongodb_database == 'psitwin_demo10_test': raise ValueError('Ejecute desde la configuración habitual; no use la base demo como producción')
    if not args.dry_run and not args.confirmar: raise ValueError('Use --dry-run o --confirmar')
    rows, summary = read_dataset(args.csv, product_count=10)
    print(json.dumps(summary, ensure_ascii=False))
    client = mongodb.AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    target = client['psitwin_demo10_test']
    try:
        company = await target['empresas'].find_one({'id_empresa': args.empresa_id}, {'_id': 0})
        if not company:
            company = await client[args.source_database]['empresas'].find_one({'id_empresa': args.empresa_id}, {'_id': 0})
        if not company: raise ValueError('Empresa de prueba no encontrada')
        if args.dry_run:
            print('Sin escrituras. Destino: psitwin_demo10_test; 10 productos, stock demo separado, 3 solicitudes pendientes.')
            return
        settings.mongodb_database = target.name
        mongodb.client, mongodb.database = client, target
        await mongodb.connect_to_mongo()
        # Account copy is only from the explicitly selected previous TEST database.
        if not await EmpresaRepository.obtener_por_id(args.empresa_id): await EmpresaRepository.crear(company)
        result = await prepare_demo(args.empresa_id, rows)
        print(json.dumps(result, ensure_ascii=False))
        folder = Path('artifacts/forecasting-access.local')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'demo10-resumen.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        if result['historico']['fallidos']: raise RuntimeError('Hay observaciones fallidas; revisar resumen')
    finally:
        client.close()
        await mongodb.close_mongo_connection()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--empresa-id', default='ba7bfc29-6418-4ee3-a3ea-91affdd150ec')
    parser.add_argument('--source-database', default='psitwin_forecasting_test')
    parser.add_argument('--csv', type=Path, default=Path(r'C:\Users\dylan\OneDrive\Escritorio\PsiTwin-Demand\psitwin_dataset_v2\dataset_entrenamiento_forecasting_3_anos_completo.csv'))
    parser.add_argument('--confirmar', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    try: asyncio.run(run(parser.parse_args()))
    except Exception as error:
        print(f'Demo detenida: {error}', file=sys.stderr)
        sys.exit(1)
