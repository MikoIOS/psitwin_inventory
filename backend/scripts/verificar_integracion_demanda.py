"""Read-only smoke check of tenant-scoped MongoDB -> shared runtime -> Saiki.

Does not seed records, install indexes, train models or create alerts.
Prints counts and availability only; no tenant identifiers or credentials.
"""
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.database import mongodb
from app.dto.auth_dto import UsuarioActual
from app.services.analisis_service import service
from app.services.saiki_service import SaikiService


async def main():
    report = {'runtime_validated': service.model.status()['validado']}
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    mongodb.client = client
    mongodb.database = client[settings.mongodb_database]
    try:
        await client.admin.command('ping')
        report['mongodb'] = True
        report['warehouse_count'] = await mongodb.database['almacenes'].count_documents({})
        report['movement_count'] = await mongodb.database['movimientos'].count_documents({})
        saiki = SaikiService()
        report['llm_ready'] = (await saiki.health()).get('ready', False)
        warehouses = await mongodb.database['almacenes'].find(
            {'id_empresa': {'$type': 'string'}}, {'_id': 0}).to_list(length=None)
        checked = 0
        for warehouse in warehouses:
            user = UsuarioActual(rol='EMPRESA', id_empresa=warehouse['id_empresa'])
            pairs = await service.repository.pairs(user.id_empresa, warehouse.get('id', warehouse.get('id_almacen')))
            for w, p in pairs:
                checked += 1
                result = await service.series(user, w, p, wait=True)
                if result.estado != 'DISPONIBLE':
                    continue
                report.update(series_checked=checked, forecast_rows=len(result.predicciones),
                              history_rows=len(result.historico), stock_registered=result.stock_actual is not None)
                # Uses exactly the same tool evidence and interpreter as the HTTP route.
                from app.services.saiki_demand import demand_answer
                verified, evidence = await demand_answer(user, 7, w, p)
                saiki = SaikiService()
                health = await saiki.health()
                report['llm_ready'] = health.get('ready', False)
                if report['llm_ready']:
                    response = await saiki._interpret_demand('Explica la demanda de la próxima semana.',
                        verified, {}, {'get_demand_analysis': evidence}, {'AUTOGLUON'})
                    report['interpretation_source'] = response['source']
                    report['answer_present'] = bool(response['answer'])
                print(json.dumps(report, ensure_ascii=False))
                return
        report.update(series_checked=checked, forecast_rows=0, detail='No eligible operational series')
        if report['llm_ready']:
            response = await saiki._interpret_demand('Explica la disponibilidad de los pronósticos.',
                'No hay pronósticos válidos con los datos disponibles.', {}, {}, {'AUTOGLUON'})
            report['interpretation_source'] = response['source']
    except Exception as error:
        report.update(error=type(error).__name__)
    finally:
        service.model.close()
        client.close()
        mongodb.client = mongodb.database = None
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
