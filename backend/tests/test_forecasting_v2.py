import asyncio
from datetime import date, datetime, timedelta, timezone
from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.services.forecast_service import ForecastService
from app.repositories.serie_demanda_repository import SerieDemandaRepository
from app.services.inventory_risk_service import InventoryRiskService
from app.services.saiki_tools import ForecastArgs, SaikiToolRegistry
from app.services.saiki_responses import forecast_answer, risk_answer
from app.dto.forecast_dto import ForecastResponse, PrediccionDiaria
from test_inventario_v2 import db, run, detail, Collection, Cursor

class SeriesRepository:
    def __init__(self,first_days=400):
        self.corte=date(2026,10,12)
        self.first_days=first_days
        self.calls=[]
    async def primera_salida(self,warehouse,product,corte):
        if self.first_days is None: return None
        return {"fecha_hora":datetime.combine(corte-timedelta(days=self.first_days),datetime.min.time(),timezone.utc)}
    async def diarios(self,warehouse,start,end,products=None):
        self.calls.append((warehouse,start,end,products))
        assert end<=self.corte
        return [{"fecha":(start+timedelta(days=i)).isoformat(),"demanda":float((i%7)+1)}
                for i in range((end-start).days+1)]
    async def productos_almacen(self,warehouse):
        return [{"id_producto":"p","categoria":"C"},{"id_producto":"q","categoria":"C"}]

class Builder:
    def __init__(self,corte): self.corte=corte; self.calls=[]
    def build_demand_features(self,history,horizon,context):
        assert history["fecha"].max()==self.corte
        assert all(day<=self.corte for day in history["fecha"])
        self.calls.append((horizon,deepcopy(context)))
        return {"target_weekday":(self.corte+timedelta(days=horizon)).weekday(),"history_last":history["demanda"].iloc[-1]}

class Predictor:
    def __init__(self): self.calls=[]
    def predict_horizon(self,features,horizon):
        self.calls.append(horizon)
        return features["target_weekday"]+features["history_last"]

@pytest.mark.parametrize("horizon",[1,7])
def test_direct_forecasts_consecutive_sum_and_no_future_leak(horizon):
    repo=SeriesRepository(); builder=Builder(repo.corte); predictor=Predictor()
    service=ForecastService(repo,predictor,builder)
    result=run(service.predecir("a","p",horizon,repo.corte))
    assert result.estado=="DISPONIBLE"
    assert len(result.predicciones_diarias)==horizon
    assert [p.fecha for p in result.predicciones_diarias]==[repo.corte+timedelta(days=i) for i in range(1,horizon+1)]
    assert result.demanda_total_estimada==sum(p.demanda_estimada for p in result.predicciones_diarias)
    assert predictor.calls==list(range(1,horizon+1))
    assert all(call[2]<=repo.corte for call in repo.calls)

def test_shared_prefix_identical_between_1_and_7():
    repo=SeriesRepository()
    service=ForecastService(repo,Predictor(),Builder(repo.corte))
    one=run(service.predecir("a","p",1,repo.corte))
    seven=run(service.predecir("a","p",7,repo.corte))
    assert one.predicciones_diarias==seven.predicciones_diarias[:1]

@pytest.mark.parametrize("horizon",[30,90])
def test_long_horizons_explicit_unavailable_without_extrapolation(horizon):
    repo=SeriesRepository(); predictor=Predictor()
    result=run(ForecastService(repo,predictor,Builder(repo.corte)).predecir("a","p",horizon,repo.corte))
    assert result.estado=="MODELO_NO_DISPONIBLE"
    assert result.predicciones_diarias==[] and result.demanda_total_estimada is None
    assert result.fecha_fin==repo.corte+timedelta(days=horizon)
    assert not predictor.calls
    assert str(horizon) in forecast_answer(result.model_dump())

@pytest.mark.parametrize("age",[None,30,365])
def test_insufficient_history_does_not_load_or_run_model(age):
    repo=SeriesRepository(age); predictor=Predictor()
    result=run(ForecastService(repo,predictor,Builder(repo.corte)).predecir("a","p",7,repo.corte))
    assert result.estado=="HISTORIAL_INSUFICIENTE"
    assert not result.historial_suficiente and not predictor.calls

def test_missing_artifact_returns_explicit_status(monkeypatch):
    repo=SeriesRepository()
    service=ForecastService(repo)
    def unavailable(): raise FileNotFoundError("artefacto faltante")
    monkeypatch.setattr(service,"_cargar_modelo",unavailable)
    result=run(service.predecir("a","p",1,repo.corte))
    assert result.estado=="MODELO_NO_DISPONIBLE"
    assert result.modelo is None and result.version_modelo is None

def test_completed_cutoff_and_unsupported_horizon():
    service=ForecastService(SeriesRepository())
    with pytest.raises(HTTPException): run(service.predecir("a","p",7,datetime.now(timezone.utc).date()+timedelta(days=1)))
    with pytest.raises(HTTPException): run(service.predecir("a","p",14))

def test_real_repository_query_aggregates_racks_and_isolates_warehouse(db,monkeypatch):
    def aggregate(collection,pipeline):
        query=pipeline[0]["$match"]
        assert query["id_almacen"]=="a"
        assert query["id_producto"]=={"$in":["p"]}
        assert query["tipo_movimiento"]=="SALIDA" and "motivo_movimiento" not in query
        from test_inventario_v2 import matches
        rows=[r for r in collection.rows if matches(r,query)]
        totals={}
        for row in rows:
            key=row["fecha_hora"].date().isoformat()
            totals[key]=totals.get(key,0)+row["cantidad"]
        return Cursor([{"fecha":k,"demanda":v} for k,v in sorted(totals.items())])
    monkeypatch.setattr(Collection,"aggregate",aggregate,raising=False)
    def movement(warehouse,product,rack,quantity,kind="SALIDA",day=12):
        return {"id_almacen":warehouse,"id_producto":product,"id_rack":rack,"tipo_movimiento":kind,
                "fecha_hora":datetime(2026,10,day,tzinfo=timezone.utc),"cantidad":quantity,"motivo_movimiento":"VENCIMIENTO"}
    db["movimientos"].rows=[
        movement("a","p","r1",3),movement("a","p","r2",5),
        movement("b","p","rb",50),movement("a","q","r1",20),
        movement("a","p","r1",100,"ENTRADA"),movement("a","p","r1",90,day=13)]
    rows=run(SerieDemandaRepository().diarios("a",date(2026,10,1),date(2026,10,12),["p"]))
    assert rows==[{"fecha":"2026-10-12","demanda":8}]

def test_risk_aggregated_and_long_horizons_remain_absent(db,monkeypatch):
    async def scenario():
        from app.repositories.inventario_repository import InventarioRepository
        header=await InventarioRepository().garantizar("a")
        await detail(header,stock=10)
        await detail(header,rack="r2",stock=5)
        repo=SeriesRepository()
        service=InventoryRiskService(ForecastService(repo,Predictor(),Builder(repo.corte)))
        async def fixed(warehouse,product,horizon=7,fecha_corte=None,dias=400):
            return await ForecastService(repo,Predictor(),Builder(repo.corte)).predecir(warehouse,product,horizon,repo.corte,dias)
        monkeypatch.setattr(service.forecast_service,"predecir",fixed)
        calls=[]
        async def process(result): calls.append(result)
        monkeypatch.setattr(service,"_procesar_alerta",process)
        result=await service.evaluar(header["id_inventario"],True,"p")
        assert result.stock_actual==15
        assert result.riesgo and len(calls)==1
        assert result.pronosticos[30]["estado"]=="MODELO_NO_DISPONIBLE"
        assert result.pronosticos[90]["demanda_total_estimada"] is None
    run(scenario())

def test_unavailable_risk_never_creates_alert_or_exhaustion(db,monkeypatch):
    async def scenario():
        from app.repositories.inventario_repository import InventarioRepository
        header=await InventarioRepository().garantizar("a")
        await detail(header)
        repo=SeriesRepository(30)
        forecasts=ForecastService(repo)
        async def fixed(warehouse,product,horizon=7,fecha_corte=None,dias=400):
            return await ForecastService(repo).predecir(warehouse,product,horizon,repo.corte,dias)
        monkeypatch.setattr(forecasts,"predecir",fixed)
        service=InventoryRiskService(forecasts)
        async def forbidden(*args): pytest.fail("No debe generar alertas")
        monkeypatch.setattr(service,"_procesar_alerta",forbidden)
        result=await service.evaluar(header["id_inventario"],True,"p")
        assert result.riesgo is None and result.reposicion is None and result.seguridad is None
        assert result.forecast.fecha_quiebre_estimada is None
        assert "No pude" in risk_answer([result.model_dump()])
    run(scenario())

def test_llm_contract_requires_product_and_supports_explicit_long_status():
    from pydantic import ValidationError
    with pytest.raises(ValidationError): ForecastArgs(id_inventario="header")
    assert ForecastArgs(id_inventario="header",id_producto="p",horizonte_dias=90).horizonte_dias==90

def test_existing_lightgbm_full_pipeline_shared_day_without_training():
    repo=SeriesRepository()
    service=ForecastService(repository=repo)  # builder/predictor/artefactos reales; solo historial en memoria
    weekly=run(service.predecir("a","p",7,repo.corte))
    assert weekly.estado=="DISPONIBLE",weekly.advertencias
    assert len(weekly.predicciones_diarias)==7
    assert weekly.version_modelo=="psitwin_v3_6"
    tomorrow=run(service.predecir("a","p",1,repo.corte))
    assert tomorrow.predicciones_diarias==weekly.predicciones_diarias[:1]
    assert weekly.demanda_total_estimada==round(sum(p.demanda_estimada for p in weekly.predicciones_diarias),4)

def test_metadata_updated_after_cut_is_not_used_for_department_features():
    import math
    class Repository(SeriesRepository):
        async def productos_almacen(self,warehouse):
            return [{"id_producto":"p","categoria":"Futura",
                "fecha_actualizacion":datetime(2026,10,13,tzinfo=timezone.utc)}]
    repo=Repository()
    context=run(ForecastService(repository=repo).contexto("a","p",repo.corte,1))
    assert math.isnan(context["dept_sales_mean_7"])
    assert math.isnan(context["future_dept_lag_7"])
    assert not math.isnan(context["store_sales_mean_7"])
    assert all(call[2]<=repo.corte for call in repo.calls)
