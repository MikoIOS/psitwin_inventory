"""Read-only application queries against a disposable synthetic MongoDB database.
No model calls, production writes, audio recording or credentials in the report.
Run from backend: python scripts/medir_saiki_cantidades.py
"""
import asyncio
import json
import statistics
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.database import mongodb
from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest
from app.services.saiki_service import SaikiService

async def main():
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
    name = 'psitwin_test_saiki_perf_' + uuid4().hex
    db = client[name]
    try:
        await client.admin.command('ping')
        mongodb.database = db
        await db.almacenes.insert_one({'id': 'w', 'id_empresa': 'e', 'nombre': 'Almacén de prueba'})
        await db.zonas.insert_one({'id': 'z', 'id_almacen': 'w', 'nombre': 'Zona de prueba'})
        await db.racks.insert_one({'id_rack': 'r', 'id_zona': 'z', 'codigo': 'R1'})
        await db.productos.insert_one({'id_producto': 'p', 'id_empresa': 'e', 'nombre': 'Mango Kent', 'unidad': 'kg'})
        await db.inventarios.insert_one({'id_inventario': 'i', 'id_almacen': 'w'})
        await db.detalles_inventario.insert_one({'id_detalle_inventario': 'd', 'id_inventario': 'i', 'id_rack': 'r', 'id_producto': 'p', 'stock_actual': 12.375})
        service = SaikiService()
        calls = 0
        def forbidden(*args, **kwargs):
            nonlocal calls
            calls += 1
            raise AssertionError('Una consulta de cantidad no debe usar el modelo')
        service._call_ollama_chat = forbidden
        async def forbidden_async(*args, **kwargs): return forbidden(*args, **kwargs)
        service._ollama_chat = forbidden_async
        user = UsuarioActual(rol='EMPRESA', id_empresa='e')
        questions = [('¿Cuánto stock tengo de Mango Kent?', {}),
                     ('¿Cuántos kilos de mango tengo?', {}), ('Cantidad de Mango Kent', {}),
                     ('Dime el stock de Mango Kent', {}), ('¿Cuántas unidades tengo?', {'id_producto': 'p'})]
        rows = []
        for question, extra in questions:
            times = []
            for _ in range(20):
                start = perf_counter()
                result = await service.ask(SaikiAskRequest(message=question, **extra), user)
                times.append((perf_counter() - start) * 1000)
                assert '12.375 kg' in result['answer'], result['answer']
            rows.append({'pregunta': question, 'respuesta': result['answer'], 'muestras': len(times),
                         'mediana_ms': round(statistics.median(times), 2),
                         'p95_ms': round(sorted(times)[18], 2), 'primera_ms': round(times[0], 2)})
        report = {'entorno': 'MongoDB real, base temporal con datos sintéticos; tiempos del servicio de texto, sin STT/TTS ni transporte HTTP',
                  'llamadas_modelo': calls, 'consultas': rows}
        output = Path(__file__).resolve().parents[2] / 'artifacts/saiki-cantidades.local/medicion.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        assert name.startswith('psitwin_test_saiki_perf_') and len(name.rsplit('_', 1)[-1]) == 32
        await client.drop_database(name)
        client.close()

if __name__ == '__main__': asyncio.run(main())
