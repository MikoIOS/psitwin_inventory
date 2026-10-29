"""Read-only diagnostic and bounded regression against the retained pilot database."""
import asyncio, json, re, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.database import mongodb
from app.main import app
from app.utils.security import create_access_token

OUT=Path(__file__).resolve().parents[2]/'artifacts/piloto.local'
async def main():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    assert re.fullmatch(r'psitwin_test_piloto_[a-f0-9]{32}',manifest['database'])
    assert manifest['database']!=settings.mongodb_database
    mongo=AsyncIOMotorClient(settings.mongodb_url,serverSelectionTimeoutMS=3000)
    mongodb.client,mongodb.database=mongo,mongo[manifest['database']]
    settings.email_enabled=False
    token=create_access_token(sub=manifest['company_id'],rol='EMPRESA',id_empresa=manifest['company_id'])
    headers={'Authorization':'Bearer '+token}
    results=[]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://pilot',headers=headers) as client:
        for question in ['¿Qué productos están agotados?','¿Qué productos están por agotarse?','¿Cómo registro un producto?','¿Cómo creo un rack?','¿Cómo agrego un sensor?','¿Cómo registro una venta?','¿Cómo consulto los movimientos?','¿Cómo veo las alertas?','¿Cómo interpreto los pronósticos?','¿Cuántos productos tengo registrados?']:
            start=time.perf_counter()
            try:
                r=await asyncio.wait_for(client.post('/api/v1/saiki/ask',json={'message':question,'id_almacen':manifest['warehouse_id']}),timeout=8)
                result={'pregunta':question,'http':r.status_code,'respuesta':r.json()}
            except Exception as e:
                result={'pregunta':question,'error':type(e).__name__,'trace':traceback.format_exc()[-6000:]}
            result['ms']=round((time.perf_counter()-start)*1000,2);results.append(result)
            (OUT/'saiki_regresion.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            print(question.encode('ascii','backslashreplace').decode(),result.get('http',result.get('error')),flush=True)
    async with httpx.AsyncClient(timeout=httpx.Timeout(15,connect=3)) as client:
        started=time.perf_counter()
        try:
            r=await client.post(settings.ollama_base_url+'/api/chat',json={'model':settings.ollama_model,'messages':[{'role':'user','content':'Responde solo: Hola, soy Saiki.'}],'think':False,'stream':False,'options':{'num_predict':32,'num_thread':2}})
            probe={'http':r.status_code,'respuesta':r.json(),'ms':round((time.perf_counter()-started)*1000,2),'modelo':settings.ollama_model}
        except Exception as e:probe={'error':type(e).__name__,'ms':round((time.perf_counter()-started)*1000,2),'modelo':settings.ollama_model}
        (OUT/'ollama_directo.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2),encoding='utf-8')
    mongo.close()
if __name__=='__main__':asyncio.run(main())
