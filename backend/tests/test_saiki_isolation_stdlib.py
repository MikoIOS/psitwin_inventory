"""Dependency-free tests of routing and actual request-scope methods.

The registry methods are compiled from their source without importing the ML
stack. This verifies async isolation, not FastAPI/Pydantic integration.
"""
import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
import time
import hashlib
import json
import re
from uuid import uuid4
import unittest

from app.services.saiki_intent_router import SaikiIntentRouter
from app.services.saiki_grounding import public_evidence
from app.services.saiki_responses import operational_answer, forecast_answer, risk_answer


ROOT = Path(__file__).resolve().parents[1]


class HttpError(Exception):
    def __init__(self, status_code, detail, headers=None):
        self.status_code, self.detail = status_code, detail


class DatabaseError(Exception):
    pass


def isolated_service():
    tree = ast.parse((ROOT / "app/services/saiki_service.py").read_text(encoding="utf-8-sig"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *classes], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "__file__": str(ROOT / "app/services/saiki_service.py"),
        "public_evidence": public_evidence, "asyncio": asyncio, "time": time, "hashlib": hashlib, "json": json, "re": re,
        "uuid4": uuid4, "logger": logging.getLogger(__name__),
        "SaikiIntentRouter": SaikiIntentRouter, "SaikiToolRegistry": SimpleNamespace,
        "get_settings": lambda: SimpleNamespace(ollama_model="test", ollama_base_url="test", saiki_request_timeout_seconds=2, saiki_database_timeout_seconds=1, saiki_idle_timeout_seconds=1, saiki_model_start_timeout_seconds=1, ollama_connect_timeout_seconds=1),
        "HTTPException": HttpError, "PyMongoError": DatabaseError,
        "status": SimpleNamespace(HTTP_503_SERVICE_UNAVAILABLE=503, HTTP_500_INTERNAL_SERVER_ERROR=500, HTTP_504_GATEWAY_TIMEOUT=504),
        "SAIKI_SYSTEM_PROMPT": "test",
        "operational_answer": operational_answer, "forecast_answer": forecast_answer, "risk_answer": risk_answer,
    }
    exec(compile(module, "saiki_service.py", "exec"), namespace)
    return namespace["SaikiService"](), namespace


def request(message):
    return SimpleNamespace(
        message=message, history=[], context={}, id_inventario=None,
        id_producto=None, id_almacen=None, id_dispositivo=None,
        sensor_horas=24, horizonte_dias=7, model_fields_set=set(),
    )


CONVERSATIONAL_CASES = [
    ("Hola Saiki.", None),
    ("¿Cómo está mi inventario?", "get_warehouse_status"),
    ("¿Cuántos productos tengo?", "get_product"),
    ("¿Tengo almacenes?", "get_locations"),
    ("¿Cuánto stock tengo?", "get_warehouse_status"),
    ("¿Dónde está el arroz?", "get_product"),
    ("¿Qué movimientos recientes tengo?", "get_recent_movements"),
    ("¿Tengo alertas activas?", "get_active_alerts"),
    ("¿Qué productos tienen riesgo de agotarse?", "get_inventory_risk"),
    ("¿Qué me recomiendas reponer?", "get_recommendations"),
    ("¿Cuál será la demanda de la próxima semana?", "get_forecast"),
    ("Quiero una proyección de mi inventario.", "get_forecast"),
]


def conversational_measurements():
    """Execute real routing/loop with zero-delay fake tools and fake Ollama."""
    rows = []
    for message, expected in CONVERSATIONAL_CASES:
        service, _ = isolated_service()
        calls, inference_times, tool_times = [], [], []
        summary = {"estado_inventario": "stock_positivo", "total_almacenes": 1, "stock_total_unidades": 3, "productos_distintos": 1, "inventarios": [{"id_inventario": "synthetic-inventory", "id_producto": "synthetic-product"}]}
        async def execute(name, args, user=None):
            started = time.perf_counter()
            calls.append(name)
            result = summary if name == "get_warehouse_status" else []
            if name == 'get_locations':
                result = {'total_almacenes': 1, 'total_zonas': 0, 'total_racks': 0, 'almacenes': []}
            if name == "get_forecast":
                result = {"estado":"DISPONIBLE","demanda_total_estimada":7,"horizonte_dias":7}
            if name == "get_inventory_risk":
                result = {"riesgo": {"nivel": "BAJO"}, "stock_actual": 3}
            source = "AUTOGLUON" if name == "get_forecast" else "INVENTARIO"
            tool_times.append((time.perf_counter() - started) * 1000)
            return result, source
        def ollama(messages, names=None):
            started = time.perf_counter()
            if not any(item.get("role") == "tool" for item in messages):
                result = {"message": {"tool_calls": [{"function": {"name": expected, "arguments": {}}}]}}
            else:
                result = {"message": {"content": "Esta prueba usa datos simulados; no hay resultados reales disponibles."}}
            inference_times.append((time.perf_counter() - started) * 1000)
            return result
        service.tools.execute = execute
        service._call_ollama_chat = ollama
        started = time.perf_counter()
        intent = service.intent_router.classify(message)
        classify_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        result = asyncio.run(service.ask(request(message)))
        rows.append({"question": message, "intent": intent.kind, "tool": expected, "calls": calls, "total_ms": round((time.perf_counter() - started) * 1000, 3), "classification_ms": round(classify_ms, 3), "tools_ms": round(sum(tool_times), 3), "mongodb_ms": None, "ollama_calls": len(inference_times), "inferences_ms": inference_times, "answer": result["answer"], "fields": sorted(result)})
    return rows


def isolated_registry(access):
    tree = ast.parse((ROOT / "app/services/saiki_tools.py").read_text(encoding="utf-8-sig"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SaikiToolRegistry")
    names = {"execute", "_authorize", "get_active_alerts", "get_recommendations", "get_recent_movements", "get_product", "get_warehouse_status"}
    cls.body = [node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"AccesoService": access, "time": time, "asyncio": asyncio, "logger": logging.getLogger(__name__)}
    exec(compile(module, "saiki_tools.py", "exec"), namespace)
    return namespace["SaikiToolRegistry"]()


class RequestScopeTests(unittest.TestCase):
    def test_active_alerts_for_inventory_exclude_resolved_alerts(self):
        async def scenario():
            registry = isolated_registry(SimpleNamespace())
            async def alerts(inventory):
                return [{"estado": "ACTIVA"}, {"estado": "RESUELTA"}, {"estado": "VISTA"}]
            registry.alerta_service = SimpleNamespace(listar_por_inventario=alerts)
            result = await registry.get_active_alerts(SimpleNamespace(id_inventario="synthetic-inventory"))
            self.assertEqual(result, [{"estado": "ACTIVA"}])
        asyncio.run(scenario())
    def test_catalog_is_local_to_company_without_warehouse_assumptions(self):
        async def scenario():
            class Access:
                @staticmethod
                async def ids_inventarios(user):
                    return set()
            registry = isolated_registry(Access)
            async def products():
                await asyncio.sleep(0)
                return [{"id_producto": "A-product", "id_empresa": "A"}, {"id_producto": "B-product", "id_empresa": "B"}]
            class ProductCursor:
                def __init__(self, query): self.query = query
                async def to_list(self, length=None):
                    return [p for p in await products() if p['id_empresa'] == self.query['id_empresa']]
            registry.get_product.__func__.__globals__["ProductoRepository"] = SimpleNamespace(
                collection=lambda: SimpleNamespace(find=lambda query, projection: ProductCursor(query)))
            class Args:
                @staticmethod
                def model_validate(arguments):
                    return SimpleNamespace(id_producto=None)
            registry._handlers = {"get_product": (Args, registry.get_product, "PRODUCTO")}
            a, b = await asyncio.gather(registry.execute("get_product", {}, SimpleNamespace(id_empresa="A")), registry.execute("get_product", {}, SimpleNamespace(id_empresa="B")))
            self.assertEqual(a[0], [{"id_producto": "A-product", "id_empresa": "A"}])
            self.assertEqual(b[0], [{"id_producto": "B-product", "id_empresa": "B"}])
        asyncio.run(scenario())

    def test_invalid_jwt_decoder_failure_produces_401(self):
        tree = ast.parse((ROOT / "app/dependencies/dependencies.py").read_text(encoding="utf-8-sig"))
        funcs = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {"get_current_user", "_no_autorizado"}]
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *funcs], type_ignores=[])
        ast.fix_missing_locations(module)
        class InvalidToken(Exception):
            pass
        def decode(token):
            raise InvalidToken("synthetic invalid token")
        namespace = {"Depends": lambda item: None, "bearer_scheme": None, "decode_access_token": decode, "jwt": SimpleNamespace(ExpiredSignatureError=type("ExpiredToken", (Exception,), {}), InvalidTokenError=InvalidToken), "HTTPException": HttpError, "status": SimpleNamespace(HTTP_401_UNAUTHORIZED=401)}
        exec(compile(module, "dependencies.py", "exec"), namespace)
        with self.assertRaises(HttpError) as raised:
            asyncio.run(namespace["get_current_user"](SimpleNamespace(credentials="synthetic-invalid")))
        self.assertEqual(raised.exception.status_code, 401)

    def test_concurrent_companies_keep_alert_and_recommendation_scope(self):
        for tool in ("get_active_alerts", "get_recommendations", "get_recent_movements", "get_warehouse_status"):
            with self.subTest(tool=tool):
                asyncio.run(self._race(tool))

    async def _race(self, tool):
        first_query = asyncio.Event()
        second_query = asyncio.Event()

        class Access:
            @staticmethod
            async def ids_inventarios(user):
                return {user.id_empresa + "-inv"}

            @staticmethod
            async def ids_almacenes(user):
                return {user.id_empresa + "-warehouse"}

        registry = isolated_registry(Access)
        calls = 0

        async def query(*args):
            nonlocal calls
            calls += 1
            if calls == 1:
                first_query.set()
                await second_query.wait()
            else:
                second_query.set()
            if tool == 'get_warehouse_status':
                return [{"id_inventario": company + "-inv", "id_producto": company + "-product", "id_rack": company + "-rack", "stock_actual": 1} for company in ("A", "B")]
            return [{'id_inventario': args[0], **({'estado': 'ACTIVA'} if tool == 'get_active_alerts' else {})}]

        class Args:
            @staticmethod
            def model_validate(arguments):
                return SimpleNamespace(id_inventario=None)

        registry.alerta_service = SimpleNamespace(listar_por_inventario=query)
        async def active_for_company(company): return await query(company + '-inv')
        registry.alerta_service.listar_activas_por_empresa = active_for_company
        registry.recomendacion_service = SimpleNamespace(listar_por_inventario=query)
        registry.movimiento_service = SimpleNamespace(obtener_por_inventario=query)
        registry.inventario_service = SimpleNamespace(obtener_inventarios=query)
        async def warehouses(*args):
            return [{"id_almacen": c + "-warehouse"} for c in ("A", "B")]
        async def zones(*args):
            return [{"id_zona": c + "-zone", "id_almacen": c + "-warehouse"} for c in ("A", "B")]
        async def racks(*args):
            return [{"id_rack": c + "-rack", "id_zona": c + "-zone"} for c in ("A", "B")]
        async def products():
            return [{"id_producto": c + "-product", "id_empresa": c} for c in ("A", "B")]
        namespace = registry.get_warehouse_status.__func__.__globals__
        namespace["DetalleInventarioRepository"] = lambda: SimpleNamespace(obtener_por_racks=query)
        class ProductCursor:
            async def to_list(self, length=None): return await products()
        namespace.update(AlmacenRepository=SimpleNamespace(obtener_por_empresa=warehouses), ZonaRepository=SimpleNamespace(obtener_por_almacenes=zones), RackRepository=SimpleNamespace(obtener_por_zonas=racks), ProductoRepository=SimpleNamespace(collection=lambda: SimpleNamespace(find=lambda *args: ProductCursor())))
        registry._handlers = {tool: (Args, getattr(registry, tool), "SOURCE")}
        first = asyncio.create_task(registry.execute(tool, {}, SimpleNamespace(id_empresa="A")))
        await asyncio.wait_for(first_query.wait(), timeout=2)
        second = asyncio.create_task(registry.execute(tool, {}, SimpleNamespace(id_empresa="B")))
        result_a, result_b = await asyncio.wait_for(asyncio.gather(first, second), timeout=2)
        if tool == "get_warehouse_status":
            self.assertEqual([item["id_inventario"] for item in result_a[0]["inventarios"]], ["A-inv"])
            self.assertEqual([item["id_inventario"] for item in result_b[0]["inventarios"]], ["B-inv"])
        else:
            self.assertEqual([r['id_inventario'] for r in result_a[0]], ['A-inv'])
            self.assertEqual([r['id_inventario'] for r in result_b[0]], ['B-inv'])
        self.assertFalse(hasattr(registry, "_visible_inventory_ids"))

    def test_authorization_rejects_foreign_inventory_before_handler(self):
        async def scenario():
            class Access:
                @staticmethod
                async def ids_inventarios(user):
                    return {"A-inv"}

                @staticmethod
                async def verificar_inventario(user, inventory):
                    raise PermissionError("foreign inventory")

            class Args:
                @staticmethod
                def model_validate(arguments):
                    return SimpleNamespace(**arguments)

            async def forbidden_handler(args):
                self.fail("Handler must not execute")

            registry = isolated_registry(Access)
            registry._handlers = {"get_inventory": (Args, forbidden_handler, "INVENTARIO")}
            with self.assertRaises(PermissionError):
                await registry.execute("get_inventory", {"id_inventario": "B-inv"}, SimpleNamespace(id_empresa="A"))
        asyncio.run(scenario())


class IntentTests(unittest.TestCase):
    def test_specific_questions_do_not_use_general_fast_path(self):
        cases = {
            "Hola Saiki, ¿cómo está mi inventario?": "general",
            "Dame un resumen del inventario": "general",
            "¿Qué movimientos se realizaron?": "movements",
            "Muéstrame las entradas recientes": "movements",
            "¿Tengo alertas?": "alerts",
            "¿Dónde está el arroz?": "location",
            "¿Qué productos podrían agotarse?": "predictive",
            "¿Qué me recomiendas reponer?": "recommendations",
            "Hola Saiki": "greeting",
            "Ayúdame con esto": "ambiguous",
        }
        for message, kind in cases.items():
            with self.subTest(message=message):
                self.assertEqual(SaikiIntentRouter.classify(message).kind, kind)

    def test_seven_days_default_and_unsupported_horizons_are_preserved(self):
        self.assertEqual(SaikiIntentRouter.classify("Proyecta la demanda").horizon_days, 7)
        self.assertEqual(SaikiIntentRouter.classify("Pronóstico para 30 días").horizon_days, 30)
        self.assertEqual(SaikiIntentRouter.SUPPORTED_HORIZONS, {1,7,30,90})
        self.assertEqual(SaikiIntentRouter.classify("Quiero una proyección de mi inventario.").horizon_days, 7)
        self.assertEqual(SaikiIntentRouter.classify("¿Cuál será la demanda de la próxima semana?").kind, "predictive")
        self.assertNotEqual(SaikiIntentRouter.classify("¿Cuántos productos tengo con stock?").kind, "product_count")
        self.assertNotEqual(SaikiIntentRouter.classify("¿Cuánto stock tengo de arroz?").kind, "stock_total")


class RackRegressionTests(unittest.TestCase):
    def test_existing_rack_tests_against_actual_rule_without_framework_imports(self):
        source = ast.parse((ROOT / "app/services/rack_service.py").read_text(encoding="utf-8-sig"))
        kg = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "_kg")
        cls = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "RackService")
        cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "motivo_no_cabe"]
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), kg, cls], type_ignores=[])
        ast.fix_missing_locations(module)
        namespace = {"__name__": "isolated_rack_regression"}
        exec(compile(module, "rack_service.py", "exec"), namespace)
        tests = ast.parse((ROOT / "tests/test_rack_asignacion.py").read_text(encoding="utf-8-sig"))
        tests.body = [node for node in tests.body if not isinstance(node, ast.ImportFrom)]
        exec(compile(tests, "test_rack_asignacion.py", "exec"), namespace)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace["RackAsignacionTests"])
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(result.testsRun, 6)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)


class ResponseTests(unittest.TestCase):
    def test_forecast_uncertainty_and_stock_distinction_are_disclosed(self):
        service, _ = isolated_service()
        warnings = service._warnings({"AUTOGLUON"})
        self.assertTrue(any("incertidumbre" in item and "no stock futuro" in item for item in warnings))
    def test_twelve_conversational_queries_and_structured_compatibility(self):
        for row in conversational_measurements():
            with self.subTest(message=row["question"]):
                if row["tool"]:
                    self.assertIn(row["tool"], row["calls"])
                else:
                    self.assertEqual(row["calls"], [])
                if row["tool"] == "get_forecast":
                    self.assertEqual(row["intent"], "predictive")
                if row["intent"] in {"greeting", "general", "product_count", "warehouses", "stock_total", "location", "alerts", "movements", "recommendations", "predictive", "risk"}:
                    self.assertEqual(row["ollama_calls"], 1 if row["intent"] in {"predictive", "risk"} else 0)
                for field in ("answer", "data", "visualization", "sources", "warnings", "context"):
                    self.assertIn(field, row["fields"])

    def test_general_question_has_zero_inferences_and_keeps_structured_data(self):
        service, _ = isolated_service()
        async def execute(*args):
            return {"estado_inventario": "sin_almacenes", "catalogo_no_verificado": True}, "INVENTARIO"
        service.tools.execute = execute
        service._call_ollama_chat = lambda *args: self.fail("Ollama must not be called")
        result = asyncio.run(service.ask(request("Hola Saiki, ¿cómo está mi inventario?")))
        self.assertEqual(result["answer"], "Actualmente no tienes almacenes registrados en PsiTwin. Te recomiendo crear tu primer almacén para comenzar a gestionar el inventario.")
        self.assertTrue(result["data"]["get_warehouse_status"]["catalogo_no_verificado"])
        self.assertEqual(result["sources"], ["INVENTARIO"])
        for key in ("context", "visualization", "warnings"):
            self.assertIn(key, result)

    def test_unsupported_horizon_does_not_query_models_or_database(self):
        service, _ = isolated_service()
        result = asyncio.run(service.ask(request("Proyecta la demanda para 14 días")))
        self.assertIn("1, 7, 30 y 90", result["answer"])
        self.assertEqual(result["data"], {})

    def test_all_inventory_states_have_natural_answers(self):
        service, _ = isolated_service()
        for state in ("sin_almacenes", "almacen_sin_productos", "productos_sin_inventario", "stock_cero", "stock_positivo"):
            answer = service._natural_inventory_answer({"estado_inventario": state})
            self.assertNotIn("DATO REAL", answer)
            self.assertLessEqual(len(answer.split(".")), 3)

    def test_real_database_exception_type_is_not_empty_inventory(self):
        service, _ = isolated_service()
        async def execute(*args):
            raise DatabaseError("offline")
        service.tools.execute = execute
        with self.assertRaises(HttpError) as raised:
            asyncio.run(service.ask(request("¿Cómo está mi inventario?")))
        self.assertEqual(raised.exception.status_code, 503)

    def test_ollama_errors_keep_distinct_status(self):
        for name, expected in (("OllamaTimeoutError", 504), ("OllamaUnavailableError", 503)):
            service, namespace = isolated_service()
            async def fail(*args):
                raise namespace[name]("offline")
            service._agent_loop = fail
            service._ollama_chat = fail
            with self.assertRaises(HttpError) as raised:
                asyncio.run(service.ask(request("Explícame esto")))
            self.assertEqual(raised.exception.status_code, expected)

    def test_tool_selection_is_local_between_concurrent_requests(self):
        async def scenario():
            service, _ = isolated_service()
            first = asyncio.Event()
            second = asyncio.Event()
            selections = []
            async def loop(messages, user, names):
                if "get_active_alerts" in names:
                    first.set()
                    await second.wait()
                else:
                    await first.wait()
                    second.set()
                selections.append(names)
                return "Verificado.", {}, set()
            service._agent_loop = loop
            await asyncio.gather(service.ask(request("¿Qué productos tienen alertas?")), service.ask(request("¿Qué productos tuvieron movimientos?")))
            shared = {"get_product", "get_warehouse_status"}
            self.assertEqual(set(selections), {frozenset(shared | {"get_active_alerts"}), frozenset(shared | {"get_recent_movements"})})
            self.assertFalse(hasattr(service, "_requested_tool_names"))
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
