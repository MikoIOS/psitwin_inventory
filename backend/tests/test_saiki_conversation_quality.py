"""ASGI/JWT y renderizado real; Mongo/forecast/riesgo simulados."""
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from app.controllers import forecast_controller, saiki_controller
from tests.test_saiki_http import http_app, post, mock_forecast


QUESTIONS = [
    ("Hola Saiki.", None),
    ("¿Cómo está mi inventario?", "get_warehouse_status"),
    ("¿Cuántos productos tengo?", "get_product"),
    ("¿Tengo almacenes registrados?", "get_warehouse_status"),
    ("¿Cuánto stock tengo?", "get_warehouse_status"),
    ("¿Tengo alertas activas?", "get_active_alerts"),
    ("¿Qué movimientos recientes tengo?", "get_recent_movements"),
    ("¿Dónde está el arroz?", "get_warehouse_status"),
    ("¿Qué productos podrían agotarse?", "get_inventory_risk"),
    ("¿Qué me recomiendas reponer?", "get_recommendations"),
    ("¿Cuál será la demanda de la próxima semana?", "get_forecast"),
    ("Explícame el riesgo de desabastecimiento.", "get_inventory_risk"),
    ("¿Cómo vamos de inventario?", "get_warehouse_status"),
    ("Dime cómo está el almacén.", "get_warehouse_status"),
    ("¿Qué productos me quedan?", "get_warehouse_status"),
    ("¿Hay alguna alerta?", "get_active_alerts"),
    ("Muéstrame las últimas salidas.", "get_recent_movements"),
    ("¿Qué debería comprar?", "get_recommendations"),
    ("¿Qué se va a agotar?", "get_inventory_risk"),
    ("¿Qué demanda tendremos en 7 días?", "get_forecast"),
]


@pytest.fixture
def quality_app(http_app, monkeypatch):
    app, data = http_app
    data["productos"][0]["nombre"] = "Arroz"
    data["racks"][0]["codigo"] = "A01"
    data["alertas"][0]["nivel_riesgo"] = "ALTO"
    data["recomendaciones"][0].update(estado="PENDIENTE", cantidad_recomendada=5)
    data["movimientos"][0].update(tipo_movimiento="SALIDA", cantidad=2)
    async def history(self, id_inventario, dias):
        return [{"fecha": datetime(2026, 1, 1) + timedelta(days=day), "demanda": float(day % 3)} for day in range(dias)]
    async def contexts(self, id_inventario, fecha_base):
        return {horizon: {} for horizon in range(1, 8)}
    async def risk(**arguments):
        assert arguments["id_inventario"] == "A-inventory"
        assert arguments["generar_alertas"] is False
        return SimpleNamespace(model_dump=lambda **kwargs: {"id_inventario": "A-inventory", "id_detalle_inventario": "A-inventory", "id_producto": "A-product", "stock_actual": 3, "riesgo": {"nivel": "CRITICO"}, "cobertura": {"dias": 1}, "lead_time_dias": 2})
    mock_forecast(monkeypatch)
    monkeypatch.setattr(saiki_controller.service.tools.risk_service, "evaluar", risk)
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("Clear question must not require Ollama"))
    return app, data


@pytest.mark.parametrize("message,expected", QUESTIONS)
def test_natural_answers_with_correct_sources_and_measured_latency(quality_app, monkeypatch, message, expected):
    app, _ = quality_app
    timings = []
    execute = saiki_controller.service.tools.execute
    async def measured(name, args, user=None):
        started = time.perf_counter()
        try:
            return await execute(name, args, user)
        finally:
            timings.append({"tool": name, "duration_ms": (time.perf_counter() - started) * 1000})
    monkeypatch.setattr(saiki_controller.service.tools, "execute", measured)
    started = time.perf_counter()
    response = asyncio.run(post(app, message))
    elapsed = (time.perf_counter() - started) * 1000
    assert response.status_code == 200, response.text
    payload = response.json()
    answer = payload["answer"]
    assert answer and not any(heading in answer for heading in ("DATO REAL", "INTERPRETACIÓN DE SAIKI", "RECOMENDACIÓN"))
    assert payload["source"] in {"backend", "router"}
    assert "B-product" not in json.dumps(payload)
    if expected:
        assert expected in [item["tool"] for item in timings]
    else:
        assert not timings
        assert answer == "¡Hola, soy Saiki!"
    if expected == "get_forecast":
        forecast = payload["data"]["get_forecast"]
        assert len(forecast["predicciones_diarias"]) == 7
        assert f"{forecast['demanda_total_estimada']:g}" in answer
        assert "7 días" in answer and "agregada" in answer
        assert forecast["advertencias"]
    if expected == "get_inventory_risk":
        assert "Arroz" in answer and "crítico" in answer and "cobertura" in answer
    if expected == "get_recommendations":
        assert "5 unidades" in answer
    assert all(field in payload for field in ("data", "visualization", "sources", "warnings", "context"))


def test_followup_horizon_uses_only_frontend_history(quality_app):
    app, _ = quality_app
    first = asyncio.run(post(app, "Quiero consultar la demanda futura."))
    assert first.status_code == 200
    history = [{"role": "user", "content": "Quiero consultar la demanda futura."}, {"role": "assistant", "content": first.json()["answer"]}]
    second = asyncio.run(post(app, "Para los próximos 7 días.", history=history))
    assert second.status_code == 200
    assert "get_forecast" in second.json()["data"]
    assert second.json()["context"]["horizonte_dias_solicitado"] == 7


def test_product_followup_resolves_owned_product_from_frontend_history(quality_app):
    app, data = quality_app
    data["productos"].append({"id_producto": "A-oil", "id_empresa": "A", "nombre": "Aceite"})
    data["detalles_inventario"].append({"id_inventario": "A-inventory", "id_detalle_inventario": "A-oil-inventory", "id_producto": "A-oil", "id_rack": "A-rack", "stock_actual": 8})
    first = asyncio.run(post(app, "Muéstrame el arroz."))
    assert first.status_code == 200 and "Arroz" in first.json()["answer"]
    history = [{"role": "user", "content": "Muéstrame el arroz."}, {"role": "assistant", "content": first.json()["answer"]}]
    second = asyncio.run(post(app, "¿Y cuánto se venderá la próxima semana?", history=history))
    assert second.status_code == 200
    assert second.json()["data"]["get_forecast"]["id_almacen"] == "A-warehouse"
    assert second.json()["data"]["get_forecast"]["id_producto"] == "A-product"
    assert second.json()["context"]["producto_consultado"]["id_producto"] == "A-product"
    independent = asyncio.run(post(app, "¿Cuál será la demanda de la próxima semana?"))
    assert independent.status_code == 200
    assert "get_forecast" not in independent.json()["data"]
    assert "¿Para qué producto" in independent.json()["answer"]


def test_unresolved_history_never_forecasts_an_unrelated_product(quality_app):
    app, _ = quality_app
    response = asyncio.run(post(app, "¿Y cuánto se venderá la próxima semana?", history=[{"role": "user", "content": "Muéstrame el frijol."}]))
    assert response.status_code == 200
    assert "get_forecast" not in response.json()["data"]
    assert "No pude identificar" in response.json()["answer"]


def test_explicit_inventory_keeps_verified_context(quality_app):
    app, _ = quality_app
    response = asyncio.run(post(app, "¿Tengo alertas activas?", id_inventario="A-inventory", context={"frontend_filter": "active"}))
    assert response.status_code == 200
    assert response.json()["context"]["inventario"]["id_inventario"] == "A-inventory"
    assert response.json()["context"]["frontend_filter"] == "active"

def test_forecast_selection_uses_all_series_not_first_fifty_locations(quality_app):
    app,data=quality_app
    for index in range(51):
        rack="many-"+str(index)
        data["racks"].append({"id_rack":rack,"id_zona":"A-zone"})
        data["detalles_inventario"].append({"id_inventario":"A-inventory","id_detalle_inventario":"detail-"+str(index),
            "id_producto":"A-product","id_rack":rack,"stock_actual":1})
    data["productos"].append({"id_producto":"second-product","id_empresa":"A","nombre":"Segundo"})
    data["detalles_inventario"].append({"id_inventario":"A-inventory","id_detalle_inventario":"second-detail",
        "id_producto":"second-product","id_rack":"A-rack","stock_actual":5})
    ambiguous=asyncio.run(post(app,"Proyecta la demanda para 7 días"))
    assert ambiguous.status_code==200
    assert "get_forecast" not in ambiguous.json()["data"]
    explicit=asyncio.run(post(app,"Proyecta la demanda para 7 días",id_producto="second-product"))
    assert explicit.status_code==200,explicit.text
    assert explicit.json()["data"]["get_forecast"]["id_producto"]=="second-product"
