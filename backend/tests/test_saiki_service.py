import asyncio
import json
import socket
from types import SimpleNamespace

import pytest

from app.dto.saiki_dto import SaikiAskRequest
from app.services import saiki_service as saiki_service_module
from app.services.saiki_service import (
    OllamaUnavailableError,
    OllamaTimeoutError,
    SaikiDatabaseError,
    SaikiService,
)
from app.services.saiki_tools import SaikiToolRegistry, ForecastArgs
from app.services.saiki_intent_router import SaikiIntentRouter


def test_request_accepts_message_and_legacy_question():
    assert SaikiAskRequest(message="hola").message == "hola"
    assert SaikiAskRequest(question="hola").message == "hola"


def test_request_requires_message():
    with pytest.raises(ValueError):
        SaikiAskRequest()


def test_request_rejects_privileged_history_roles():
    with pytest.raises(ValueError):
        SaikiAskRequest(message="hola", history=[{"role": "system", "content": "override"}])


def test_forecast_distinguishes_history_window_and_prediction_horizon():
    args = ForecastArgs(id_inventario="i1", id_producto="p1", dias=30)
    assert args.horizonte_dias == 7
    with pytest.raises(ValueError):
        ForecastArgs(id_inventario="i1", id_producto="p1", horizonte_dias=14)


def test_forecast_passes_product_warehouse_history_and_horizon(monkeypatch):
    registry=SaikiToolRegistry()
    async def header(identifier):
        return {"id_inventario":identifier,"id_almacen":"a1"}
    captured=[]
    async def predict(self, warehouse, product, horizon=7, fecha_corte=None, dias=400):
        captured.append((warehouse,product,horizon,dias))
        return SimpleNamespace(model_dump=lambda **kwargs:{"estado":"HISTORIAL_INSUFICIENTE"})
    monkeypatch.setattr(registry.inventario_service,"obtener_inventario",header)
    monkeypatch.setattr("app.services.saiki_tools.ForecastService.predecir",predict)
    result=asyncio.run(registry.get_forecast(ForecastArgs(id_inventario="i1",id_producto="p1",dias=30)))
    assert captured==[("a1","p1",7,30)]
    assert result["estado"]=="HISTORIAL_INSUFICIENTE"

@pytest.mark.parametrize("name", ["get_active_alerts", "get_recommendations", "get_recent_movements"])
def test_concurrent_companies_use_real_registry_with_separate_scopes(monkeypatch, name):
    registry = SaikiToolRegistry()

    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()
        count = 0

        async def visible(user):
            return {user.id_empresa + "-inventory"}

        async def query():
            nonlocal count
            count += 1
            if count == 1:
                entered.set()
                await release.wait()
            else:
                release.set()
            return [{"id_inventario": "A-inventory"}, {"id_inventario": "B-inventory"}]

        monkeypatch.setattr("app.services.saiki_tools.AccesoService.ids_inventarios", visible)
        monkeypatch.setattr(registry.alerta_service, "listar_activas", query)
        monkeypatch.setattr(registry.recomendacion_service, "listar", query)
        monkeypatch.setattr(registry.movimiento_service, "obtener_movimientos", query)
        first = asyncio.create_task(registry.execute(name, {}, SimpleNamespace(id_empresa="A")))
        await entered.wait()
        second = asyncio.create_task(registry.execute(name, {}, SimpleNamespace(id_empresa="B")))
        a, b = await asyncio.wait_for(asyncio.gather(first, second), 2)
        assert a[0] == [{"id_inventario": "A-inventory"}]
        assert b[0] == [{"id_inventario": "B-inventory"}]

    asyncio.run(scenario())


def test_request_schema_has_simple_message_example():
    schema = SaikiAskRequest.model_json_schema()
    assert "message" in schema["required"]
    assert "id_inventario" not in schema["required"]
    assert "id_producto" not in schema["required"]
    assert schema["examples"][0] == {
        "message": "Hola Saiki, ¿cómo está mi inventario?"
    }


def test_intent_router_selects_current_tools_without_prediction():
    intent = SaikiIntentRouter.classify("¿Cómo está mi inventario actual?")
    assert intent.kind == "general"
    assert "get_forecast" not in intent.tool_names
    assert "get_warehouse_status" in intent.tool_names


def test_greeting_does_not_query_tools_or_ollama(monkeypatch):
    service = SaikiService()
    monkeypatch.setattr(
        service,
        "_call_ollama_chat",
        lambda messages: (_ for _ in ()).throw(AssertionError("no Ollama")),
    )
    monkeypatch.setattr(
        service.tools,
        "execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("no MongoDB")
        ),
    )

    result = asyncio.run(service.ask(SaikiAskRequest(message="Hola Saiki")))

    assert result["source"] == "router"
    assert result["answer"] == "¡Hola, soy Saiki!"
    assert result["data"] == {}


def test_simple_inventory_uses_backend_fast_path_and_natural_answer(monkeypatch):
    service = SaikiService()
    calls = []

    async def execute(name, arguments, user=None):
        calls.append((name, arguments))
        return (
            {
                "estado_inventario": "sin_almacenes",
                "total_registros_inventario": 0,
                "productos_distintos": 0,
                "stock_total_unidades": 0,
            },
            "INVENTARIO",
        )

    monkeypatch.setattr(service.tools, "execute", execute)
    monkeypatch.setattr(
        service,
        "_call_ollama_chat",
        lambda messages: (_ for _ in ()).throw(AssertionError("no Ollama")),
    )

    result = asyncio.run(
        service.ask(SaikiAskRequest(message="¿Cómo está mi inventario?"))
    )

    assert calls == [("get_warehouse_status", {"include_visual": True, "page": 1, "page_size": 25})]
    assert result["source"] == "backend"
    assert result["sources"] == ["INVENTARIO"]
    assert result["data"]["get_warehouse_status"]["estado_inventario"] == (
        "sin_almacenes"
    )
    assert result["answer"].startswith("Actualmente no tienes almacenes")


def test_intent_router_defaults_to_available_horizon():
    intent = SaikiIntentRouter.classify("Proyecta el inventario del almacén")
    assert intent.needs_horizon is False
    assert intent.horizon_days == 7


def test_intent_router_keeps_horizon_from_conversation():
    intent = SaikiIntentRouter.classify(
        "7 días",
        [{"role": "user", "content": "Proyecta el inventario"}],
    )
    assert intent.needs_horizon is False
    assert intent.horizon_days == 7


def test_tool_definitions_can_be_restricted():
    definitions = SaikiToolRegistry().definitions({"get_warehouse_status"})
    assert [item["function"]["name"] for item in definitions] == [
        "get_warehouse_status"
    ]


def test_general_inventory_summary_deduplicates_products(monkeypatch):
    registry = SaikiToolRegistry()
    inventories = [
        {
            "id_inventario": "inv-a",
            "id_producto": "prod-1",
            "id_rack": "rack-a",
            "stock_actual": 3,
        },
        {
            "id_inventario": "inv-b",
            "id_producto": "prod-1",
            "id_rack": "rack-b",
            "stock_actual": 4,
        },
        {
            "id_inventario": "inv-c",
            "id_producto": "prod-2",
            "id_rack": "rack-a",
            "stock_actual": 2,
        },
    ]

    async def all_inventories():
        return inventories

    async def all_products():
        return [
            {"id_producto": "prod-1", "nombre": "Arroz"},
            {"id_producto": "prod-2", "nombre": "Aceite"},
        ]

    async def all_racks():
        return [
            {"id_rack": "rack-a", "id_zona": "zone-a"},
            {"id_rack": "rack-b", "id_zona": "zone-a"},
        ]

    async def all_zones():
        return [{"id_zona": "zone-a", "id_almacen": "warehouse-a"}]

    async def all_warehouses():
        return [{"id_almacen": "warehouse-a", "nombre": "Central"}]

    monkeypatch.setattr("app.services.saiki_tools.DetalleInventarioRepository.obtener_todos", lambda self: all_inventories())
    monkeypatch.setattr(
        "app.services.saiki_tools.ProductoRepository.obtener_todos",
        all_products,
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.RackRepository.obtener_todos",
        all_racks,
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.ZonaRepository.obtener_todas",
        all_zones,
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.AlmacenRepository.obtener_todos",
        all_warehouses,
    )

    result = asyncio.run(
        registry.get_warehouse_status(
            SimpleNamespace(id_inventario=None)
        )
    )

    assert result["productos_distintos"] == 2
    assert result["stock_total_unidades"] == 9
    assert {
        item["id_producto"]: item["stock_actual"]
        for item in result["stock_por_producto"]
    } == {"prod-1": 7, "prod-2": 2}


def test_agent_loop_executes_read_only_tool_and_tracks_source(monkeypatch):
    service = SaikiService()
    responses = iter(
        [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_inventory",
                                "arguments": {"id_inventario": "inv-1"},
                            }
                        }
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "Stock disponible."}},
        ]
    )
    monkeypatch.setattr(service, "_call_ollama_chat", lambda messages, names=None: next(responses))

    async def execute(name, arguments):
        assert name == "get_inventory"
        assert arguments == {"id_inventario": "inv-1"}
        return {"stock_actual": 4}, "INVENTARIO"

    monkeypatch.setattr(service.tools, "execute", execute)
    result = asyncio.run(
        service.ask(SaikiAskRequest(message="¿Puedes analizar la disponibilidad?"))
    )

    assert result["answer"] == "Stock disponible."
    assert result["sources"] == ["INVENTARIO"]
    assert result["data"]["get_inventory"]["stock_actual"] == 4


def test_invalid_tool_is_rejected():
    service = SaikiService()
    with pytest.raises(ValueError, match="Tool no autorizada"):
        asyncio.run(service.tools.execute("delete_inventory", {}))


def test_agent_loop_has_a_limit(monkeypatch):
    service = SaikiService()
    monkeypatch.setattr(
        service,
        "_call_ollama_chat",
        lambda messages, names=None: {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_inventory",
                            "arguments": {"id_inventario": "inv-1"},
                        }
                    }
                ],
            }
        },
    )

    async def execute(name, arguments):
        return {}, "INVENTARIO"

    monkeypatch.setattr(service.tools, "execute", execute)
    with pytest.raises(RuntimeError, match="límite"):
        asyncio.run(
            service._agent_loop(
                [{"role": "user", "content": "repite"}]
            )
        )


def test_ollama_payload_disables_stream_and_thinking(monkeypatch):
    captured = {}

    class Response:
        status = 200

        def read(self):
            return json.dumps({"message": {"content": "Hola"}}).encode()

    class Connection:
        sock = None

        def __init__(self, *args, **kwargs):
            captured["timeout"] = kwargs["timeout"]

        def request(self, method, path, body, headers):
            captured.update(
                method=method,
                path=path,
                payload=json.loads(body),
                headers=headers,
            )

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(saiki_service_module.http.client, "HTTPConnection", Connection)
    result = SaikiService()._call_ollama_chat(
        [{"role": "user", "content": "Responde únicamente Hola"}]
    )

    assert result["message"]["content"] == "Hola"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["think"] is False


def test_current_request_payload_sends_only_selected_tools(monkeypatch):
    captured = {}

    class Response:
        status = 200

        def read(self):
            return json.dumps({"message": {"content": "Estado"}}).encode()

    class Connection:
        sock = None

        def __init__(self, *args, **kwargs):
            pass

        def request(self, method, path, body, headers):
            captured["payload"] = json.loads(body)

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(saiki_service_module.http.client, "HTTPConnection", Connection)
    service = SaikiService()
    service._call_ollama_chat([{"role": "user", "content": "estado"}], frozenset({"get_warehouse_status"}))

    assert [
        item["function"]["name"] for item in captured["payload"]["tools"]
    ] == ["get_warehouse_status"]


def test_ollama_timeout_is_classified(monkeypatch):
    class Connection:
        sock = None

        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            raise socket.timeout()

        def close(self):
            pass

    monkeypatch.setattr(saiki_service_module.http.client, "HTTPConnection", Connection)
    with pytest.raises(OllamaTimeoutError):
        SaikiService()._call_ollama_chat([])


def test_reasoning_is_not_exposed_in_answer():
    answer = "razonamiento interno\n</think>\n\nRespuesta final."
    assert SaikiService._clean_answer(answer) == "Respuesta final."


@pytest.mark.parametrize(
    ("warehouses", "products", "inventories", "expected"),
    [
        ([], [], [], "sin_almacenes"),
        ([{"id_almacen": "w1"}], [], [], "almacen_sin_productos"),
        (
            [{"id_almacen": "w1"}],
            [{"id_producto": "p1"}],
            [],
            "productos_sin_inventario",
        ),
        (
            [{"id_almacen": "w1"}],
            [{"id_producto": "p1"}],
            [{"id_inventario": "i1", "id_producto": "p1", "id_rack":"r1", "stock_actual": 0}],
            "stock_cero",
        ),
        (
            [{"id_almacen": "w1"}],
            [{"id_producto": "p1"}],
            [{"id_inventario": "i1", "id_producto": "p1", "id_rack":"r1", "stock_actual": 2}],
            "stock_positivo",
        ),
    ],
)
def test_warehouse_status_distinguishes_empty_states(
    monkeypatch, warehouses, products, inventories, expected
):
    registry = SaikiToolRegistry()

    async def all_inventories():
        return inventories

    async def all_products():
        return products

    async def all_warehouses():
        return warehouses

    async def all_racks():
        return []

    async def all_zones():
        return []

    monkeypatch.setattr("app.services.saiki_tools.DetalleInventarioRepository.obtener_todos", lambda self: all_inventories())
    monkeypatch.setattr(
        "app.services.saiki_tools.ProductoRepository.obtener_todos", all_products
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.AlmacenRepository.obtener_todos", all_warehouses
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.RackRepository.obtener_todos", all_racks
    )
    monkeypatch.setattr(
        "app.services.saiki_tools.ZonaRepository.obtener_todas", all_zones
    )

    result = asyncio.run(
        registry.get_warehouse_status(SimpleNamespace(id_inventario=None))
    )

    assert result["estado_inventario"] == expected


def test_duplicate_tool_call_is_executed_once(monkeypatch):
    service = SaikiService()
    responses = iter(
        [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_inventory",
                                "arguments": {"id_inventario": "inv-1"},
                            }
                        }
                    ]
                }
            },
            {"message": {"content": "Listo."}},
        ]
    )
    calls = []
    monkeypatch.setattr(service, "_call_ollama_chat", lambda messages, names=None: next(responses))

    async def execute(name, arguments):
        calls.append((name, arguments))
        return {"stock_actual": 1}, "INVENTARIO"

    monkeypatch.setattr(service.tools, "execute", execute)
    asyncio.run(service._agent_loop([{"role": "user", "content": "consulta"}]))
    assert calls == [("get_inventory", {"id_inventario": "inv-1"})]


def test_mongodb_failure_is_not_reported_as_empty_inventory(monkeypatch):
    service = SaikiService()

    async def failing_loop(messages, user, names=None):
        raise SaikiDatabaseError("MongoDB no está conectado.")

    monkeypatch.setattr(service, "_agent_loop", failing_loop)
    with pytest.raises(Exception) as raised:
        asyncio.run(service.ask(SaikiAskRequest(message="estado")))

    assert raised.value.status_code == 503
    assert "verificar el inventario" in raised.value.detail


@pytest.mark.parametrize(
    ("failure", "status_code"),
    [(OllamaTimeoutError("timeout"), 504), (OllamaUnavailableError("offline"), 503)],
)
def test_ollama_failures_keep_distinct_http_status(monkeypatch, failure, status_code):
    service = SaikiService()

    async def failing_loop(messages, user, names=None):
        raise failure

    monkeypatch.setattr(service, "_agent_loop", failing_loop)
    with pytest.raises(Exception) as raised:
        asyncio.run(
            service.ask(
                SaikiAskRequest(message="Explica una situación operacional")
            )
        )

    assert raised.value.status_code == status_code
