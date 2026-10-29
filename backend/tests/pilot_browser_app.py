"""Browser QA server restricted to the disposable, simulated pilot database."""
import os
import json
import re
from pathlib import Path
from contextlib import asynccontextmanager
if os.environ.get('PSITWIN_PILOT_BROWSER') != '1':
    raise RuntimeError('Explicit pilot test flag required')
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.database import mongodb
from app.main import app
from app.services import dispositivo_service
from app.controllers import monitoreo_ws_controller
from app.services.sensores.monitoreo_service import MonitoreoService

manifest = json.loads((Path(__file__).resolve().parents[2] / 'artifacts/piloto.local/manifest.json').read_text(encoding='utf-8'))
assert re.fullmatch(r'psitwin_test_piloto_[a-f0-9]{32}', manifest['database'])
assert manifest['database'] != settings.mongodb_database
settings.email_enabled = False

@asynccontextmanager
async def lifespan(_):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
    mongodb.client, mongodb.database = client, client[manifest['database']]
    if os.environ.get('PSITWIN_INVENTORY_WRITE_TESTS') == '1':
        from app.utils.security import hash_password
        # Only synthetic fixtures in the UUID-checked disposable DB.
        await mongodb.database.operarios.update_many({'id_empresa': manifest['company_id']},
            {'$set': {'password_hash': hash_password(manifest['test_password']), 'debe_cambiar_password': False}})
    monitor = MonitoreoService()
    await monitor.cargar_dispositivos()
    dispositivo_service.monitoreo = monitor
    monitoreo_ws_controller.monitoreo = monitor
    try: yield
    finally: client.close()

app.router.lifespan_context = lifespan
