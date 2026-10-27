import asyncio
import json

import pytest

from app.controllers import saiki_controller
from app.dto.saiki_dto import SaikiAskResponse
from tests.test_saiki_http import http_app, post


def request(http_app, monkeypatch, **fields):
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("No Ollama for inventory summary"))
    return asyncio.run(post(http_app[0], "Saiki, ¿cómo está mi inventario?", **fields))


def test_multiple_products_racks_and_catalog(http_app, monkeypatch):
    _, data = http_app
    data["almacenes"][0]["nombre"] = "Principal"
    data["zonas"][0]["nombre"] = "A"
    data["racks"][0]["codigo"] = "A01"
    data["racks"].append({"id_rack": "A-rack2", "id_zona": "A-zone", "codigo": "A02"})
    data["productos"].extend([
        {"id_producto": "oil", "id_empresa": "A", "nombre": "Aceite"},
        {"id_producto": "catalog-only", "id_empresa": "A", "nombre": "Sin existencias"}])
    data["detalles_inventario"][0]["stock_minimo"] = 5
    data["detalles_inventario"].extend([
        {"id_inventario": "A-inventory", "id_detalle_inventario": "second", "id_producto": "A-product", "id_rack": "A-rack2", "stock_actual": 4},
        {"id_inventario": "A-inventory", "id_detalle_inventario": "oil-inv", "id_producto": "oil", "id_rack": "A-rack", "stock_actual": 2, "stock_minimo": 1}])
    response = request(http_app, monkeypatch)
    assert response.status_code == 200
    payload = response.json()
    SaikiAskResponse.model_validate(payload)
    summary = payload["data"]["inventory_summary"]
    assert (summary["distinct_products"], summary["total_units"], summary["warehouse_count"], summary["catalog_products"]) == (2, 9, 1, 3)
    assert len(summary["rows"]) == 3
    assert {row["rack_name"] for row in summary["rows"] if row["id_producto"] == "A-product"} == {"A01", "A02"}
    assert {row["status_label"] for row in summary["rows"]} == {"Bajo stock", "Disponible", "Sin determinar"}
    assert payload["visualization"]["title"] == "Resumen de inventario"
    assert "9 unidades distribuidas en 1 almacén" in payload["answer"]
    assert "B-product" not in json.dumps(payload)


def test_pagination_keeps_company_totals(http_app, monkeypatch):
    _, data = http_app
    data["racks"].append({"id_rack": "extra", "id_zona": "A-zone"})
    data["detalles_inventario"].append({"id_inventario": "A-inventory", "id_detalle_inventario": "extra-inv", "id_producto": "A-product", "id_rack": "extra", "stock_actual": 4})
    pages = [request(http_app, monkeypatch, page=page, page_size=1).json()["data"]["inventory_summary"] for page in (1, 2, 3)]
    assert all(row["total_units"] == 7 and row["distinct_products"] == 1 for row in pages)
    assert pages[0]["pagination"]["total_rows"] == pages[1]["pagination"]["total_pages"] == 2
    assert len(pages[0]["rows"]) == len(pages[1]["rows"]) == 1
    assert pages[2]["rows"] == []


@pytest.mark.parametrize("state", ["sin_almacenes", "almacen_sin_productos", "productos_sin_inventario", "stock_cero"])
def test_empty_states_do_not_count_catalog_as_stock(http_app, monkeypatch, state):
    _, data = http_app
    if state == "stock_cero":
        data["detalles_inventario"][0]["stock_actual"] = 0
    else:
        data["detalles_inventario"] = data["detalles_inventario"][1:]
        if state == "sin_almacenes":
            data["almacenes"] = data["almacenes"][1:]
        elif state == "almacen_sin_productos":
            data["productos"] = data["productos"][1:]
    payload = request(http_app, monkeypatch).json()
    summary = payload["data"]["inventory_summary"]
    assert summary["inventory_state"] == state
    assert summary["distinct_products"] == summary["total_units"] == 0
    assert payload["visualization"]["type"] == "inventory_summary"
    if state == "sin_almacenes":
        assert summary["catalog_products"] == 1
        assert "no tienes productos" not in payload["answer"]


def test_cross_company_product_reference_is_not_exposed(http_app, monkeypatch):
    _, data = http_app
    data["detalles_inventario"].append({"id_inventario": "A-inventory", "id_detalle_inventario": "corrupt", "id_producto": "B-product", "id_rack": "A-rack", "stock_actual": 900})
    response = request(http_app, monkeypatch, context={"id_empresa": "B"})
    assert response.status_code == 200
    assert response.json()["data"]["inventory_summary"]["total_units"] == 3
    assert "B-product" not in response.text


@pytest.mark.parametrize("stock", [None, -1, "3"])
def test_missing_or_invalid_stock_is_error_not_zero(http_app, monkeypatch, stock):
    http_app[1]["detalles_inventario"][0]["stock_actual"] = stock
    response = request(http_app, monkeypatch)
    assert response.status_code == 503
    assert "inventory_summary" not in response.json()


@pytest.mark.parametrize("fields", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_invalid_pagination(http_app, fields):
    assert asyncio.run(post(http_app[0], "¿Cómo está mi inventario?", **fields)).status_code == 422


def test_same_location_records_group_without_stock_duplication(http_app, monkeypatch):
    http_app[1]["detalles_inventario"].append({"id_inventario": "A-inventory", "id_detalle_inventario": "second-record", "id_producto": "A-product", "id_rack": "A-rack", "stock_actual": 4})
    summary = request(http_app, monkeypatch).json()["data"]["inventory_summary"]
    assert summary["total_units"] == 7
    assert len(summary["rows"]) == 1
    assert summary["rows"][0]["stock"] == 7
    assert summary["rows"][0]["status_label"] == "Sin determinar"


def test_missing_names_are_null_not_invented(http_app, monkeypatch):
    row = request(http_app, monkeypatch).json()["data"]["inventory_summary"]["rows"][0]
    assert row["warehouse_name"] is None
    assert row["zone_name"] is None
    assert row["rack_name"] is None
    assert row["status_label"] == "Sin determinar"


def test_visual_summary_concurrent_company_totals_and_rows(http_app, monkeypatch):
    app, _ = http_app
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", lambda *args: pytest.fail("No Ollama"))
    async def scenario():
        return await asyncio.gather(post(app, "¿Cómo está mi inventario?", "A"), post(app, "¿Cómo está mi inventario?", "B"))
    a, b = asyncio.run(scenario())
    for response, company, units in ((a, "A", 3), (b, "B", 7)):
        assert response.status_code == 200
        summary = response.json()["data"]["inventory_summary"]
        assert summary["total_units"] == units
        assert {row["id_producto"] for row in summary["rows"]} == {company + "-product"}
