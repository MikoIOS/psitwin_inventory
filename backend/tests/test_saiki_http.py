"""Real FastAPI/JWT/services/repositories; synthetic in-memory MongoDB and LLM."""
import asyncio
import copy
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
import time

from fastapi import FastAPI
import httpx
import jwt
import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app.config.settings import settings
from app.controllers import saiki_controller
from app.services.saiki_service import OllamaTimeoutError, OllamaUnavailableError
from app.utils.security import create_access_token
from tests.test_saiki_isolation_stdlib import CONVERSATIONAL_CASES


def matches(document, query):
    for key, value in query.items():
        if key == "$or":
            if not any(matches(document, item) for item in value):
                return False
        elif isinstance(value,dict) and "$exists" in value:
            if (key in document) != value["$exists"]:
                return False
        elif isinstance(value, dict) and "$in" in value:
            if document.get(key) not in value["$in"]:
                return False
        elif document.get(key) != value:
            return False
    return True


class Cursor:
    def __init__(self, rows):
        self.rows = rows
    def sort(self, key, direction):
        self.rows.sort(key=lambda row: str(row.get(key, "")), reverse=direction < 0)
        return self
    async def to_list(self, length=None):
        await asyncio.sleep(0)
        return copy.deepcopy(self.rows if length is None else self.rows[:length])


class Collection:
    def __init__(self, rows):
        self.rows = rows
    def find(self, query, projection=None):
        return Cursor([row for row in self.rows if matches(row, query)])
    async def find_one(self, query, projection=None, sort=None):
        await asyncio.sleep(0)
        return copy.deepcopy(next((row for row in self.rows if matches(row, query)), None))


@pytest.fixture
def http_app(monkeypatch):
    # Legacy conversation fixtures must not depend on local model installation.
    from app.services.autogluon_runtime import runtime
    monkeypatch.setattr(runtime, 'status', lambda: {'validado': False, 'faltantes': ['fixture: legacy engine']})
    data = {name: [] for name in ("almacenes", "zonas", "racks", "productos", "inventarios", "detalles_inventario", "alertas", "recomendaciones", "movimientos")}
    for company, stock in (("A", 3), ("B", 7)):
        data["almacenes"].append({"id": company + "-warehouse", "id_empresa": company})
        data["zonas"].append({"id": company + "-zone", "id_almacen": company + "-warehouse"})
        data["racks"].append({"id_rack": company + "-rack", "id_zona": company + "-zone"})
        data["productos"].append({"id_producto": company + "-product", "id_empresa": company, "nombre": "Producto sintético " + company})
        data["inventarios"].append({"id_inventario":company+"-inventory","id_almacen":company+"-warehouse"})
        data["detalles_inventario"].append({"id_inventario": company + "-inventory",
            "id_detalle_inventario":company+"-detail","id_rack": company + "-rack",
            "id_producto": company + "-product", "stock_actual": stock})
        for name in ("alertas", "recomendaciones", "movimientos"):
            data[name].append({"id_inventario": company + "-inventory", "estado": "ACTIVA", "fecha_hora": "2026-01-01", "id_empresa": company})

    class Database:
        def __getitem__(self, collection):
            return Collection(data.get(collection, []))

    database = Database()
    for name, module in list(sys.modules.items()):
        if name.startswith("app.repositories.") and hasattr(module, "get_database"):
            monkeypatch.setattr(module, "get_database", lambda: database)
    app = FastAPI()  # deliberately excludes production MongoDB startup/lifespan
    app.include_router(saiki_controller.router, prefix="/api/v1")
    return app, data


async def post(app, message, company="A", endpoint="ask", **fields):
    token = create_access_token(company, id_empresa=company)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/api/v1/saiki/" + endpoint, json={"message": message, **fields}, headers={"Authorization": "Bearer " + token})


@pytest.mark.parametrize("endpoint", ["ask", "chat"])
def test_real_http_fast_path_and_dto_keep_fields(http_app, monkeypatch, endpoint):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("Unnecessary Ollama inference"))
    response = asyncio.run(post(app, "¿Cómo está mi inventario?", endpoint=endpoint))
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend"
    assert payload["data"]["get_warehouse_status"]["stock_total_unidades"] == 3
    assert all(key in payload for key in ("answer", "data", "visualization", "sources", "warnings", "context"))
    assert response.headers["X-Saiki-Request-ID"]
    assert response.headers["X-Saiki-Revision"]


@pytest.mark.parametrize("token_type", ["missing", "invalid", "expired", "wrong_signature"])
def test_real_jwt_rejection(http_app, token_type):
    app, _ = http_app
    headers = {}
    if token_type == "invalid":
        headers["Authorization"] = "Bearer synthetic-invalid"
    elif token_type in {"expired", "wrong_signature"}:
        payload = {"sub": "A", "rol": "EMPRESA", "id_empresa": "A", "exp": datetime.now(timezone.utc) + timedelta(minutes=-1 if token_type == "expired" else 1)}
        key = settings.secret_key if token_type == "expired" else "synthetic-wrong-key-for-testing-only-123456789"
        headers["Authorization"] = "Bearer " + jwt.encode(payload, key, algorithm=settings.algorithm)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/api/v1/saiki/ask", json={"message": "Hola Saiki"}, headers=headers)
    assert asyncio.run(scenario()).status_code == 401


@pytest.mark.parametrize("field,value", [("id_inventario", "B-inventory"), ("id_producto", "B-product")])
def test_foreign_identifier_denied_by_real_access_service(http_app, monkeypatch, field, value):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("Foreign data must be rejected first"))
    response = asyncio.run(post(app, "Analiza este registro", **{field: value}))
    assert response.status_code in {403, 404}
    assert "data" not in response.json()


def test_model_cannot_select_foreign_inventory(http_app, monkeypatch):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: {"message": {"tool_calls": [{"function": {"name": "get_inventory", "arguments": {"id_inventario": "B-inventory"}}}]}})
    response = asyncio.run(post(app, "Analiza la información disponible"))
    assert response.status_code in {403, 404}
    assert "data" not in response.json()


def test_client_context_cannot_replace_jwt_company(http_app, monkeypatch):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("No Ollama"))
    response = asyncio.run(post(app, "¿Cómo está mi inventario?", context={"id_empresa": "B", "inventarios_visibles": ["B-inventory"]}))
    assert response.status_code == 200
    assert response.json()["data"]["get_warehouse_status"]["stock_total_unidades"] == 3


def test_privileged_history_role_is_http_validation_error(http_app):
    app, _ = http_app
    response = asyncio.run(post(app, "Hola Saiki", history=[{"role": "system", "content": "synthetic instruction"}]))
    assert response.status_code == 422


@pytest.mark.parametrize("state", ["located", "unassigned", "ambiguous"])
def test_location_fast_path_uses_only_owned_catalog_and_real_locations(http_app, monkeypatch, state):
    app, data = http_app
    data["productos"][0]["nombre"] = "Arroz"
    data["productos"][1]["nombre"] = "Arroz"
    data["racks"][0]["codigo"] = "A01"
    if state == "unassigned":
        data["detalles_inventario"] = [item for item in data["detalles_inventario"] if item["id_inventario"] != "A-inventory"]
    elif state == "ambiguous":
        data["productos"][0]["nombre"] = "Arroz integral"
        data["productos"].append({"id_producto": "A-second-product", "id_empresa": "A", "nombre": "Arroz blanco"})
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("No model needed for clear location query"))
    response = asyncio.run(post(app, "¿Dónde está el arroz?"))
    assert response.status_code == 200
    payload = response.json()
    assert "B-product" not in json.dumps(payload)
    assert payload["source"] == "backend"
    if state == "located":
        assert "rack A01" in payload["answer"]
    elif state == "unassigned":
        assert "no encontré una ubicación" in payload["answer"]
    else:
        assert "varios productos" in payload["answer"]


@pytest.mark.parametrize("message,tool", [("¿Tengo alertas?", "get_active_alerts"), ("¿Qué me recomiendas reponer?", "get_recommendations"), ("¿Qué movimientos recientes tengo?", "get_recent_movements")])
def test_concurrent_real_jwt_http_services_are_isolated(http_app, monkeypatch, message, tool):
    app, _ = http_app
    def model(messages, names=None):
        if any(item.get("role") == "tool" for item in messages):
            return {"message": {"content": "Resultados obtenidos del entorno sintético."}}
        return {"message": {"tool_calls": [{"function": {"name": tool, "arguments": {}}}]}}
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", model)
    async def scenario():
        return await asyncio.gather(post(app, message, "A"), post(app, message, "B"))
    a, b = asyncio.run(scenario())
    assert a.status_code == b.status_code == 200
    assert {item["id_inventario"] for item in a.json()["data"][tool]} == {"A-inventory"}
    assert {item["id_inventario"] for item in b.json()["data"][tool]} == {"B-inventory"}


def test_concurrent_http_inventory_scope(http_app, monkeypatch):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("No Ollama"))
    async def scenario():
        return await asyncio.gather(post(app, "¿Cómo está mi inventario?", "A"), post(app, "¿Cómo está mi inventario?", "B"))
    a, b = asyncio.run(scenario())
    assert a.status_code == b.status_code == 200
    assert a.json()["data"]["get_warehouse_status"]["stock_total_unidades"] == 3
    assert b.json()["data"]["get_warehouse_status"]["stock_total_unidades"] == 7


def test_real_mongodb_exception_is_http_error_not_empty_inventory(http_app, monkeypatch):
    app, _ = http_app
    def offline():
        raise ServerSelectionTimeoutError("synthetic database failure")
    monkeypatch.setattr("app.repositories.almacen_repository.get_database", offline)
    response = asyncio.run(post(app, "¿Cómo está mi inventario?"))
    assert response.status_code == 503
    assert "estado_inventario" not in response.text


@pytest.mark.parametrize("failure,code", [(OllamaTimeoutError("synthetic"), 504), (OllamaUnavailableError("synthetic"), 503)])
def test_ollama_failure_http_status(http_app, monkeypatch, failure, code):
    app, _ = http_app
    def offline(*args):
        raise failure
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", offline)
    assert asyncio.run(post(app, "Explícame una situación operacional")).status_code == code


def mock_forecast(monkeypatch):
    from app.services.forecast_service import ForecastService
    from app.dto.forecast_dto import ForecastResponse, PrediccionDiaria
    async def predict(self, warehouse, product, horizon=7, fecha_corte=None, dias=400):
        corte=datetime(2026,10,12,tzinfo=timezone.utc).date()
        available=horizon in (1,7)
        daily=[PrediccionDiaria(fecha=corte+timedelta(days=i),demanda_estimada=1) for i in range(1,horizon+1)] if available else []
        return ForecastResponse(id_almacen=warehouse,id_producto=product,fecha_generacion=datetime.now(timezone.utc),
            fecha_corte=corte,horizonte_dias=horizon,fecha_inicio=corte+timedelta(days=1),
            fecha_fin=corte+timedelta(days=horizon),estado="DISPONIBLE" if available else "MODELO_NO_DISPONIBLE",
            demanda_total_estimada=sum(p.demanda_estimada for p in daily) if available else None,
            predicciones_diarias=daily,historial_suficiente=True,advertencias=["Modelo simulado exclusivamente para prueba HTTP"])
    monkeypatch.setattr(ForecastService,"predecir",predict)

def test_long_horizon_http_reports_missing_model(http_app, monkeypatch):
    app,_=http_app
    mock_forecast(monkeypatch)
    monkeypatch.setattr(saiki_controller.service,"_call_ollama_chat",lambda messages, *args: {'message': {'content': __import__('json').loads(messages[-1]['content'])['explicacion_verificada']}})
    response=asyncio.run(post(app,"Proyecta la demanda para 30 días"))
    assert response.status_code==200
    assert response.json()["data"]["get_forecast"]["estado"]=="MODELO_NO_DISPONIBLE"
    assert response.json()["data"]["get_forecast"]["horizonte_dias"]==30
    assert response.json()["data"]["get_forecast"]["predicciones_diarias"]==[]

def test_http_forecast_contract_daily_totals(http_app,monkeypatch):
    app,_=http_app
    mock_forecast(monkeypatch)
    monkeypatch.setattr(saiki_controller.service,"_call_ollama_chat",lambda messages, *args: {'message': {'content': __import__('json').loads(messages[-1]['content'])['explicacion_verificada']}})
    response=asyncio.run(post(app,"¿Cuál será la demanda de la próxima semana?"))
    assert response.status_code==200,response.text
    forecast=response.json()["data"]["get_forecast"]
    assert len(forecast["predicciones_diarias"])==7
    assert forecast["demanda_total_estimada"]==sum(p["demanda_estimada"] for p in forecast["predicciones_diarias"])
    assert "AUTOGLUON" in response.json()["sources"]

@pytest.mark.parametrize("message,expected_tool", CONVERSATIONAL_CASES)
def test_twelve_questions_through_real_http_with_synthetic_collaborators(http_app, monkeypatch, message, expected_tool):
    from app.controllers import forecast_controller
    from types import SimpleNamespace
    app, _ = http_app
    inference_times, tool_times, classification_times = [], [], []
    real_execute = saiki_controller.service.tools.execute
    real_classify = saiki_controller.service.intent_router.classify
    async def execute(name, arguments, user=None):
        started = time.perf_counter()
        try:
            return await real_execute(name, arguments, user)
        finally:
            tool_times.append({"name": name, "duration_ms": (time.perf_counter() - started) * 1000})
    def classify(*args):
        started = time.perf_counter()
        try:
            return real_classify(*args)
        finally:
            classification_times.append((time.perf_counter() - started) * 1000)
    def model(messages, names=None):
        started = time.perf_counter()
        try:
            if any(item.get("role") == "tool" for item in messages):
                return {"message": {"content": "Consulta completada usando exclusivamente los datos sintéticos de la prueba."}}
            args = {"id_inventario": "A-inventory", "id_producto":"A-product"} if expected_tool in {"get_inventory_risk", "get_forecast"} else {}
            return {"message": {"tool_calls": [{"function": {"name": expected_tool, "arguments": args}}]}}
        finally:
            inference_times.append((time.perf_counter() - started) * 1000)
    async def history(self, id_inventario, dias):
        return [{"fecha": datetime(2026, 1, 1) + timedelta(days=day), "demanda": float(day % 3)} for day in range(dias)]
    async def contexts(self, id_inventario, fecha_base):
        return {horizon: {} for horizon in range(1, 8)}
    async def risk(**kwargs):
        assert kwargs["generar_alertas"] is False
        return SimpleNamespace(model_dump=lambda **kwargs: {"datos_sinteticos": True})
    monkeypatch.setattr(saiki_controller.service.tools, "execute", execute)
    monkeypatch.setattr(saiki_controller.service.intent_router, "classify", classify)
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", model)
    monkeypatch.setattr(saiki_controller.service.tools.risk_service, "evaluar", risk)
    mock_forecast(monkeypatch)
    started = time.perf_counter()
    response = asyncio.run(post(app, message))
    elapsed = (time.perf_counter() - started) * 1000
    assert response.status_code == 200, response.text
    if expected_tool:
        assert expected_tool in [item["name"] for item in tool_times]
    else:
        assert tool_times == []
    assert len(inference_times) == (1 if expected_tool in {"get_forecast", "get_inventory_risk"} else 0 if response.json()["source"] in {"router", "backend"} else 2)
    assert len(classification_times) == 1
