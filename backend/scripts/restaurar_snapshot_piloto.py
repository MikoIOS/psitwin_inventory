"""Restore only the empty, disposable pilot DB for read-only browser review."""
import asyncio,json,re,sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.utils.security import hash_password
OUT=Path(__file__).resolve().parents[2]/'artifacts/piloto.local'
def dates(value):
    if isinstance(value,list):return [dates(v) for v in value]
    if not isinstance(value,dict):return value
    result={}
    for key,item in value.items():
        if isinstance(item,str) and (key.startswith('fecha') or key in ('ts','minuto','inicio','fin','created_at','updated_at')) and 'T' in item:
            try:item=datetime.fromisoformat(item)
            except ValueError:pass
        result[key]=dates(item)
    return result
async def main():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    name=manifest['database'];assert re.fullmatch(r'psitwin_test_piloto_[a-f0-9]{32}',name) and name!=settings.mongodb_database
    c=AsyncIOMotorClient(settings.mongodb_url,serverSelectionTimeoutMS=3000)
    db=c[name];assert not await db.list_collection_names(),'Refusing to overwrite a nonempty database'
    for collection,rows in json.loads((OUT/'mongo_snapshot.json').read_text(encoding='utf-8')).items():
        if rows:await db[collection].insert_many(dates(rows))
    await db.empresas.update_one({'id_empresa':manifest['company_id']},{'$set':{'password':hash_password(manifest['test_password'])}})
    print('Snapshot SIMULADO restaurado exclusivamente para revision visual; no datos reales')
    c.close()
if __name__=='__main__':asyncio.run(main())
