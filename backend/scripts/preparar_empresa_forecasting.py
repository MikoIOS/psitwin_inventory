"""Create an explicitly configured test account using the existing registration service."""
import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def run(args):
    from app.config.settings import settings
    from app.database import mongodb
    from app.dto.empresa_dto import EmpresaRegisterRequest
    from app.repositories.empresa_repository import EmpresaRepository
    from app.services.empresa_service import register_empresa
    if not args.database.endswith('_test') or args.database == os.environ.get('PSITWIN_PRODUCTION_DATABASE', settings.mongodb_database):
        raise ValueError('Solo se permite una base independiente con sufijo _test')
    if not args.confirmar: raise ValueError('Se requiere --confirmar para crear la cuenta de pruebas')
    settings.mongodb_database = args.database
    mongodb.client = mongodb.AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    mongodb.database = mongodb.client[args.database]
    try:
        company = await EmpresaRepository.obtener_por_correo(args.correo.lower().strip())
        if not company:
            password = os.environ.get('PSITWIN_TEST_PASSWORD') or getpass.getpass('Contraseña para la empresa de prueba: ')
            data = EmpresaRegisterRequest(nombre=args.nombre, nombre_ceo=args.nombre_ceo, correo=args.correo, password=password,
                                          ruc=args.ruc, telefono=args.telefono, sector='Pruebas forecasting')
            company = await register_empresa(data)
        print('Empresa:', company['nombre'])
        print('Usuario (correo):', company['correo'])
        print('ID para --empresa-id:', company['id_empresa'])
        print('Base:', args.database)
        print('Contraseña: la definida al crear esta cuenta; no se cambia una contraseña existente.')
    finally:
        await mongodb.close_mongo_connection()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database', default='psitwin_forecasting_test')
    p.add_argument('--nombre', default='PsiTwin Forecasting Pruebas')
    p.add_argument('--nombre-ceo', default='Demo')
    p.add_argument('--correo', default='forecasting.pruebas@example.com')
    p.add_argument('--ruc', default='00000000000', help='Identificador exclusivo de la cuenta ficticia de pruebas')
    p.add_argument('--telefono', default='000000000')
    p.add_argument('--confirmar', action='store_true')
    try:
        asyncio.run(run(p.parse_args()))
    except Exception as error:
        print(f'Preparación detenida: {error}', file=sys.stderr)
        sys.exit(1)
