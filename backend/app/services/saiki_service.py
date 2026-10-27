import asyncio
import http.client
import json
import logging
import socket
import time
import hashlib
import re
from uuid import uuid4
from typing import Any
from urllib.parse import urlsplit
from urllib import error, request

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError

from app.config.settings import get_settings
from app.dto.saiki_dto import SaikiAskRequest
from app.dto.auth_dto import UsuarioActual
from app.prompts.saiki_system_prompt import SAIKI_SYSTEM_PROMPT
from app.services.saiki_intent_router import SaikiIntentRouter
from app.services.saiki_tools import SaikiToolRegistry
from app.services.saiki_responses import operational_answer, forecast_answer, risk_answer

logger = logging.getLogger(__name__)


class OllamaTimeoutError(RuntimeError):
    pass


class OllamaUnavailableError(RuntimeError):
    pass


class SaikiDatabaseError(RuntimeError):
    pass


class SaikiService:
    max_tool_iterations = 4

    def __init__(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        files = ("services/saiki_service.py", "services/saiki_tools.py", "services/saiki_inventory_summary.py", "services/saiki_intent_router.py", "services/saiki_responses.py", "dto/saiki_dto.py", "prompts/saiki_system_prompt.py", "controllers/saiki_controller.py")
        files = (*files, "services/saiki_sensors.py")
        self.code_revision = hashlib.sha256(b"".join((root / name).read_bytes() for name in files)).hexdigest()[:12]
        self.settings = get_settings()
        self.tools = SaikiToolRegistry()
        self.intent_router = SaikiIntentRouter()

    @staticmethod
    def get_system_prompt() -> str:
        return SAIKI_SYSTEM_PROMPT

    async def health(self) -> dict:
        base = {
            "ollama_base_url": self.settings.ollama_base_url,
            "model": self.settings.ollama_model,
        }
        try:
            models = await asyncio.to_thread(self._installed_models)
        except RuntimeError as exc:
            return {"status": "unavailable", "ready": False, **base, "detail": str(exc)}
        if self.settings.ollama_model not in models:
            return {
                "status": "unavailable",
                "ready": False,
                **base,
                "detail": f"El modelo {self.settings.ollama_model} no está descargado en Ollama.",
            }
        return {"status": "ok", "ready": True, **base}

    def _installed_models(self) -> list[str]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            with request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"No se pudo conectar con Ollama en {url}: {exc}") from exc
        return [model.get("name", "") for model in data.get("models", [])]

    async def ask(
        self, data: SaikiAskRequest, user: UsuarioActual | None = None, *, request_id: str | None = None,
    ) -> dict:
        started = time.perf_counter()
        request_id = request_id or uuid4().hex
        classified = time.perf_counter()
        intent = self.intent_router.classify(data.message or "", data.history)
        logger.info("saiki_classification request_id=%s duration_ms=%.3f", request_id, (time.perf_counter() - classified) * 1000)
        logger.info(
            "saiki_request_start request_id=%s revision=%s intent=%s has_inventory_id=%s has_product_id=%s history_count=%d",
            request_id, self._code_revision(), intent.kind,
            bool(data.id_inventario), bool(data.id_producto), len(data.history),
        )
        try:
            return await self._ask(data, user, intent)
        except PyMongoError as exc:
            logger.warning("saiki_request_error request_id=%s type=mongodb_unavailable", request_id)
            raise HTTPException(status_code=503, detail="No se pudo verificar el inventario en MongoDB.") from exc
        except RuntimeError as exc:
            if isinstance(exc, SaikiDatabaseError) or "MongoDB" in str(exc) or "motor" in str(exc):
                raise HTTPException(status_code=503, detail="No se pudo verificar el inventario en MongoDB.") from exc
            raise
        finally:
            logger.info("saiki_request_complete request_id=%s duration_ms=%.3f", request_id, (time.perf_counter() - started) * 1000)

    def _code_revision(self):
        return self.code_revision

    async def _ask(
        self,
        data: SaikiAskRequest,
        user: UsuarioActual | None = None,
        intent=None,
    ) -> dict:
        context = dict(data.context)
        intent = intent or self.intent_router.classify(data.message or "", data.history)
        if intent.kind == "sensors":
            from app.services.saiki_sensors import sensor_report
            answer, evidence = await sensor_report(user)
            return self._simple_response(answer, "backend", {"sensores": evidence})
        if intent.kind == "greeting":
            return self._simple_response(
                "¡Hola, soy Saiki!",
                source="router",
            )
        if intent.horizon_days is not None and intent.horizon_days not in self.intent_router.SUPPORTED_HORIZONS:
            return self._clarification_response(
                "Los horizontes admitidos son 1, 7, 30 y 90 días. El pronóstico depende de la disponibilidad del modelo."
            )
        if intent.horizon_days is not None:
            context["horizonte_dias_solicitado"] = intent.horizon_days
            if "horizonte_dias" not in data.model_fields_set:
                data.horizonte_dias = intent.horizon_days
            context["tipo_prediccion"] = "demanda"
        if data.id_inventario and user is not None:
            context["inventario"] = await self._authorized_tool("get_inventory", {"id_inventario": data.id_inventario}, user)
        if data.id_producto and user is not None:
            context["producto"] = await self._authorized_tool("get_product", {"id_producto": data.id_producto}, user)
        if intent.kind in {"product_quantities", "inventory_detail"} and not data.id_producto and not data.id_inventario:
            return await self._fast_detail_response(data, context, user, intent.kind)
        if intent.kind in {"alerts", "movements", "recommendations"} and not data.id_producto:
            return await self._fast_operational_response(intent.kind, data, context, user)
        if intent.kind in {"predictive", "risk"} and not re.search(r"\b(?:alerta|movimiento|recomend|comprar)", self.intent_router._normalize(data.message or "")):
            return await self._fast_analysis_response(intent.kind, data, context, user)
        if intent.kind == "products" and not data.id_inventario and not data.id_producto:
            return await self._fast_products_response(data, context, user)
        location_name = self._location_name(data.message or "") if intent.kind == "location" else None
        if location_name and not data.id_inventario and not data.id_producto:
            return await self._fast_location_response(location_name, context, user)
        if (
            intent.kind in {"general", "product_count", "warehouses", "stock_total"}
            and not data.id_inventario
            and not data.id_producto
        ):
            try:
                return await self._fast_current_response(context, user, intent.kind, data)
            except SaikiDatabaseError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No se pudo verificar el inventario en MongoDB.",
                ) from exc
            except RuntimeError as exc:
                logger.exception("saiki_request_error type=unexpected_runtime")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Saiki no está disponible en este momento.",
                ) from exc
        analysis_data, analysis_sources = {}, set()
        if intent.kind == "analysis":
            summary, summary_source = await self._execute_tool("get_warehouse_status", {"include_visual": True}, user)
            recommendations, recommendation_source = await self._execute_tool("get_recommendations", {}, user)
            analysis_data = {"get_warehouse_status": summary, "get_recommendations": recommendations}
            analysis_sources = {summary_source, recommendation_source}
            context["datos_verificados_analisis"] = analysis_data
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *data.history,
            {
                "role": "user",
                "content": self._build_prompt(data.message or "", context),
            },
        ]
        started = time.perf_counter()
        try:
            answer, tool_data, sources = await self._agent_loop(messages, user, intent.tool_names or None)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            logger.warning("saiki_request_error type=ollama_timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Ollama tardó demasiado en responder.",
            ) from exc
        except OllamaUnavailableError as exc:
            logger.warning("saiki_request_error type=ollama_unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama no está disponible en este momento.",
            ) from exc
        except SaikiDatabaseError as exc:
            logger.warning("saiki_request_error type=mongodb_unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo verificar el inventario en MongoDB.",
            ) from exc
        except RuntimeError as exc:
            logger.exception("saiki_request_error type=unexpected_runtime")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Saiki no está disponible en este momento.",
            ) from exc
        finally:
            logger.info(
                "saiki_request duration_ms=%d",
                round((time.perf_counter() - started) * 1000),
            )

        if analysis_data:
            tool_data = {**analysis_data, **tool_data}
            sources.update(analysis_sources)
        if "LIGHTGBM" in sources and intent.horizon_days == 7:
            answer = "La proyección corresponde a la demanda de los próximos 7 días. " + answer
        return {
            "answer": answer,
            "model": self.settings.ollama_model,
            "base_url": self.settings.ollama_base_url,
            "source": "ollama",
            "context": context,
            "data": tool_data,
            "visualization": self._visualization(tool_data),
            "sources": sorted(sources),
            "warnings": self._warnings(sources, tool_data),
        }

    def _clarification_response(self, answer: str) -> dict:
        return self._simple_response(answer, source="router")

    def _verified_response(self, answer, context, data, sources):
        response = self._simple_response(answer, "backend", data)
        response.update(context=context, sources=sorted(sources), warnings=self._warnings(sources, data))
        return response

    async def _fast_detail_response(self, request_data, context, user, kind):
        summary, source = await self._execute_tool("get_warehouse_status", {"include_visual": True, "page": request_data.page, "page_size": request_data.page_size}, user)
        structured = summary["inventory_summary"]
        data, sources = {"get_warehouse_status": summary, "inventory_summary": structured}, {source}
        if kind == "product_quantities":
            products, product_source = await self._execute_tool("get_product", {}, user)
            sources.add(product_source)
            stock = {row["id_producto"]: row["stock_actual"] for row in summary["stock_por_producto"]}
            rows = [{"id_producto": item["id_producto"], "product_name": item.get("nombre"),
                     "stock": stock.get(item["id_producto"]), "has_inventory": item["id_producto"] in stock} for item in products]
            data["product_quantities"] = rows
            answer = "; ".join(f"{row['product_name'] or 'Producto sin nombre'}: {row['stock']} unidades" if row['has_inventory'] else f"{row['product_name'] or 'Producto sin nombre'}: sin inventario registrado" for row in rows)
            answer = answer + "." if answer else "No tienes productos registrados en tu catálogo."
        else:
            rows = structured["rows"]
            parts = []
            for row in rows:
                location = ", ".join(("almacén " + (row["warehouse_name"] or "sin información"), "zona " + (row["zone_name"] or "sin información"), "rack " + (row["rack_name"] or "sin información")))
                parts.append(f"{row['product_name'] or 'Producto sin nombre'}: {row['stock']} unidades en {location}")
            answer = "; ".join(parts) + "." if parts else "No hay ubicaciones de inventario en esta página."
            if structured["pagination"]["total_pages"] > 1:
                answer += f" Página {request_data.page} de {structured['pagination']['total_pages']}; puedes consultar las demás páginas."
        response = self._verified_response(answer, context, data, sources)
        response["visualization"] = summary["visualization"]
        if kind == "product_quantities":
            response["visualization"] = {"type": "table", "rows_path": "data.product_quantities", "columns": [{"key": "product_name", "label": "Producto"}, {"key": "stock", "label": "Stock"}, {"key": "has_inventory", "label": "Inventario registrado"}]}
        return response

    async def _fast_operational_response(self, kind, request_data, context, user):
        tool = {"alerts": "get_active_alerts", "movements": "get_recent_movements", "recommendations": "get_recommendations"}[kind]
        arguments = {"id_inventario": request_data.id_inventario} if request_data.id_inventario else {}
        rows, source = await self._execute_tool(tool, arguments, user)
        text = self.intent_router._normalize(request_data.message or "")
        if kind == "movements" and re.search(r"\bsalidas?\b|\bentradas?\b", text):
            movement_type = "SALIDA" if re.search(r"\bsalidas?\b", text) else "ENTRADA"
            rows = [row for row in rows if row.get("tipo_movimiento") == movement_type]
            answer = f"Encontré {len(rows)} {movement_type.lower()}{'s' if len(rows) != 1 else ''} entre los movimientos recientes consultados."
        else:
            answer = operational_answer(kind, rows)
        return self._verified_response(answer, context, {tool: rows}, {source})

    async def _fast_products_response(self, request_data, context, user):
        text = self.intent_router._normalize(request_data.message or "")
        if re.search(r"quedan|disponibles|existencias", text):
            summary, source = await self._execute_tool("get_warehouse_status", {}, user)
            products = [row for row in summary.get("stock_por_producto", []) if row.get("stock_actual", 0) > 0]
            details = "; ".join(f"{row.get('nombre') or 'Producto sin nombre'}: {row['stock_actual']} unidades" for row in products[:5])
            answer = f"Tienes estas existencias: {details}." if products else "No encontré productos con existencias positivas en tus inventarios visibles."
            if len(products) == 1:
                answer = f"Quedan {products[0]['stock_actual']} unidades de {products[0].get('nombre') or 'un producto sin nombre registrado'}."
            if len(products) > 5:
                answer += " Puedes consultar el resto en los datos adjuntos."
            return self._verified_response(answer, context, {"get_warehouse_status": summary}, {source})
        products, source = await self._execute_tool("get_product", {}, user)
        selected = self._product_from_history(products, [{"role": "user", "content": request_data.message or ""}])
        if selected:
            context["producto_consultado"] = {"id_producto": selected["id_producto"], "nombre": selected.get("nombre")}
            answer = f"{selected.get('nombre') or 'El producto'} está registrado en tu catálogo."
        elif "muestrame" in text:
            answer = "No pude identificar un único producto de tu catálogo. Indica su nombre completo para consultarlo."
        else:
            answer = f"Tienes {len(products)} {'producto registrado' if len(products) == 1 else 'productos registrados'} en tu catálogo."
        return self._verified_response(answer, context, {"get_product": products}, {source})

    def _product_from_history(self, products, history):
        for item in reversed((history or [])[-4:]):
            if item.get("role") != "user":
                continue
            text = self.intent_router._normalize(str(item.get("content", "")))
            matches = [product for product in products if product.get("nombre") and re.search(r"\b" + re.escape(self.intent_router._normalize(product["nombre"])) + r"\b", text)]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return None
        return None

    async def _fast_analysis_response(self, kind, request_data, context, user):
        arguments = {"id_inventario": request_data.id_inventario} if request_data.id_inventario else {}
        summary, source = await self._execute_tool("get_warehouse_status", arguments, user)
        data, sources = {"get_warehouse_status": summary}, {source}
        inventories = summary.get("stock_por_producto_almacen", summary.get("inventarios", []))
        if request_data.id_producto:
            product, product_source = await self._execute_tool("get_product", {"id_producto": request_data.id_producto}, user)
            sources.add(product_source)
            data["get_product"] = product
            inventories = [row for row in inventories if row.get("id_producto") == request_data.id_producto]
        elif request_data.history:
            products, product_source = await self._execute_tool("get_product", {}, user)
            sources.add(product_source)
            data["get_product"] = products
            product = self._product_from_history(products, request_data.history)
            if product:
                inventories = [row for row in inventories if row.get("id_producto") == product["id_producto"]]
                context["producto_consultado"] = {"id_producto": product["id_producto"], "nombre": product.get("nombre")}
            elif any(item.get("role") == "user" and re.search(r"muestrame|donde", self.intent_router._normalize(str(item.get("content", "")))) for item in request_data.history[-4:]):
                return self._verified_response("No pude identificar un único producto de tu catálogo en el historial. ¿Qué producto deseas consultar?", context, data, sources)
        if not inventories:
            return self._verified_response("No hay inventarios visibles para calcular esta consulta. Registra existencias o indica un producto con inventario.", context, data, sources)
        text = self.intent_router._normalize(request_data.message or "")
        is_risk = kind == "risk" or bool(re.search(r"agot|riesgo|desabastec", text))
        inventories = list({(row["id_inventario"], row["id_producto"]): row for row in inventories}.values())
        if not is_risk and len(inventories) != 1:
            return self._verified_response("¿Para qué producto y almacén deseas consultar la demanda?", context, data, sources)
        if not is_risk:
            forecast, forecast_source = await self._execute_tool("get_forecast", {"id_inventario": inventories[0]["id_inventario"], "id_producto": inventories[0]["id_producto"], "horizonte_dias": request_data.horizonte_dias}, user)
            data["get_forecast"] = forecast
            sources.add(forecast_source)
            return self._verified_response(forecast_answer(forecast), context, data, sources)
        results = []
        product_names = {row.get("id_producto"): row.get("nombre") for row in summary.get("stock_por_producto", [])}
        seen_series = set()
        for inventory in inventories:
            series_key = (inventory["id_inventario"], inventory["id_producto"])
            if series_key in seen_series:
                continue
            seen_series.add(series_key)
            result, risk_source = await self._execute_tool("get_inventory_risk", {"id_inventario": inventory["id_inventario"], "id_producto": inventory["id_producto"]}, user)
            result = dict(result)
            if product_names.get(inventory.get("id_producto")):
                result["nombre_producto"] = product_names[inventory["id_producto"]]
            results.append(result)
            sources.add(risk_source)
        data["get_inventory_risk"] = results[0] if len(results) == 1 else results
        response = self._verified_response(risk_answer(results), context, data, sources)
        if "stock_por_producto_almacen" not in summary and summary.get("total_registros_inventario", len(inventories)) > len(summary.get("inventarios", [])):
            response["warnings"].append("El riesgo se evaluó solo para los inventarios incluidos en el resumen; no representa todos los inventarios.")
        return response

    @staticmethod
    def _location_name(message: str) -> str | None:
        match = re.search(r"(?:d[oó]nde\s+(?:est[aá]n?|se\s+encuentran?)|ubicaci[oó]n\s+de)\s+(?:(?:el|la|los|las|producto)\s+)?(.+?)[?!.]*$", message, re.IGNORECASE)
        if not match:
            return None
        name = match[1].strip()
        if re.search(r"\b(?:y|o|en|cu[aá]nt|explica|busco)\b", name, re.IGNORECASE):
            return None
        return name or None

    async def _fast_location_response(self, name: str, context: dict, user) -> dict:
        products, source = await self._execute_tool("get_product", {}, user)
        normalized = self.intent_router._normalize(name)
        matches = [product for product in products if self.intent_router._normalize(product.get("nombre", "")) == normalized]
        if not matches:
            matches = [product for product in products if re.search(r"\b" + re.escape(normalized) + r"\b", self.intent_router._normalize(product.get("nombre", "")))]
        data = {"get_product": products}
        sources = {source}
        if not matches:
            answer = f"No encontré {name} en el catálogo de tu empresa."
        elif len(matches) > 1:
            answer = f"Encontré varios productos que coinciden con {name}. ¿Cuál deseas localizar?"
        else:
            summary, inventory_source = await self._execute_tool("get_warehouse_status", {}, user)
            data["get_warehouse_status"] = summary
            sources.add(inventory_source)
            product = matches[0]
            locations = [item for item in summary.get("ubicaciones", []) if item.get("id_producto") == product["id_producto"]]
            if not locations:
                answer = f"{product['nombre']} está registrado, pero no encontré una ubicación de inventario en tus almacenes visibles."
            elif len(locations) == 1:
                rack = locations[0].get("rack") or {}
                label = rack.get("codigo") or rack.get("nombre")
                answer = f"{product['nombre']} está en el rack {label}." if label else f"{product['nombre']} tiene una ubicación registrada; puedes consultarla en el detalle de inventario."
            else:
                answer = f"{product['nombre']} está distribuido en {len(locations)} ubicaciones. Puedes consultar los racks en el detalle de inventario."
        response = self._simple_response(answer, "backend", data)
        response.update(context=context, sources=sorted(sources))
        logger.info("saiki_agent_summary ollama_calls=0 tool_calls=%d source=backend", len(data))
        return response

    def _simple_response(self, answer: str, source: str, data: dict | None = None):
        return {
            "answer": answer,
            "model": self.settings.ollama_model,
            "base_url": self.settings.ollama_base_url,
            "source": source,
            "context": {},
            "data": data or {},
            "visualization": {"type": "none"},
            "sources": [],
            "warnings": [],
        }

    async def _fast_current_response(self, context: dict, user, kind="general", request_data=None) -> dict:
        started = time.perf_counter()
        tool = "get_product" if kind == "product_count" else "get_warehouse_status"
        try:
            result, source = await self._execute_tool(
                tool, ({"include_visual": True, "page": getattr(request_data, "page", 1), "page_size": getattr(request_data, "page_size", 25)} if kind == "general" and request_data is not None else {}), user
            )
        except RuntimeError as exc:
            if "MongoDB" in str(exc) or "motor" in str(exc):
                raise SaikiDatabaseError(str(exc)) from exc
            raise
        finally:
            logger.info(
                "saiki_fast_path tool=%s duration_ms=%d",
                tool,
                round((time.perf_counter() - started) * 1000),
            )
        if kind == "product_count":
            answer = f"Tienes {len(result)} {'producto registrado' if len(result) == 1 else 'productos registrados'} en tu catálogo."
        elif kind == "warehouses":
            count = result["total_almacenes"]
            answer = f"Tienes {count} {'almacén registrado' if count == 1 else 'almacenes registrados'} en PsiTwin." if count else "Actualmente no tienes almacenes registrados en PsiTwin. Te recomiendo crear tu primer almacén."
        elif kind == "stock_total":
            answer = f"Actualmente tienes {result['stock_total_unidades']} unidades en tu inventario."
        else:
            answer = self._natural_inventory_answer(result)
            if result.get("estado_inventario") == "stock_positivo" and "inventory_summary" in result:
                summary = result["inventory_summary"]
                products_label = "producto diferente" if summary['distinct_products'] == 1 else "productos diferentes"
                warehouses_label = "almacén" if summary['warehouse_count'] == 1 else "almacenes"
                answer = f"Actualmente tienes {summary['distinct_products']} {products_label} y {summary['total_units']} unidades distribuidas en {summary['warehouse_count']} {warehouses_label}."
        payload_data = {tool: result}
        visualization = {"type": "none"}
        if "inventory_summary" in result and kind == "general":
            payload_data["inventory_summary"] = result["inventory_summary"]
            visualization = result["visualization"]
        logger.info("saiki_agent_summary ollama_calls=0 tool_calls=1 source=backend")
        return {
            "answer": answer,
            "model": self.settings.ollama_model,
            "base_url": self.settings.ollama_base_url,
            "source": "backend",
            "context": context,
            "data": payload_data,
            "visualization": visualization,
            "sources": [source],
            "warnings": [],
        }

    @staticmethod
    def _natural_inventory_answer(result: dict) -> str:
        state = result.get("estado_inventario")
        if state == "sin_almacenes":
            return (
                "Actualmente no tienes almacenes registrados en PsiTwin. Te "
                "recomiendo crear tu primer almacén para comenzar a gestionar "
                "el inventario."
            )
        if state == "almacen_sin_productos":
            return (
                "Tu almacén está registrado, pero todavía no tienes productos "
                "registrados."
            )
        if state == "productos_sin_inventario":
            return (
                "Tienes productos registrados, pero todavía no hay existencias "
                "de inventario asociadas."
            )
        if state == "stock_cero":
            return (
                "Tienes productos registrados, pero actualmente sus existencias "
                "son cero."
            )
        if state == "stock_positivo":
            products = result.get("productos_distintos", 0)
            units = result.get("stock_total_unidades", 0)
            return (
                f"Actualmente tienes {products} {'producto distinto' if products == 1 else 'productos distintos'} y "
                f"{units} {'unidad registrada' if units == 1 else 'unidades registradas'} en tu inventario."
            )
        raise RuntimeError("La consulta de inventario no devolvió un estado válido.")

    async def _authorized_tool(self, name, arguments, user):
        result, _ = await self.tools.execute(name, arguments, user)
        return result

    async def _execute_tool(self, name, arguments, user=None):
        if user is None:
            return await self.tools.execute(name, arguments)
        return await self.tools.execute(name, arguments, user)

    async def _agent_loop(
        self,
        messages: list[dict],
        user: UsuarioActual | None = None,
        tool_names: frozenset[str] | None = None,
    ) -> tuple[str, dict, set[str]]:
        tool_data: dict[str, object] = {}
        sources: set[str] = set()
        seen_calls: dict[str, Any] = {}
        ollama_calls = 0
        tool_calls_count = 0
        for iteration in range(1, self.max_tool_iterations + 1):
            call_started = time.perf_counter()
            response = await asyncio.to_thread(self._call_ollama_chat, messages, tool_names)
            ollama_calls += 1
            logger.info(
                "saiki_agent_iteration iteration=%d ollama_duration_ms=%d",
                iteration,
                round((time.perf_counter() - call_started) * 1000),
            )
            message = response.get("message")
            if not isinstance(message, dict):
                raise RuntimeError("Ollama devolvió un mensaje inválido.")
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                answer = message.get("content")
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("Ollama no devolvió una respuesta útil.")
                logger.info(
                    "saiki_agent_summary ollama_calls=%d tool_calls=%d",
                    ollama_calls,
                    tool_calls_count,
                )
                answer = self._clean_answer(answer)
                if not answer:
                    raise RuntimeError("Ollama solo devolvió razonamiento interno.")
                return answer, tool_data, sources

            messages.append(message)
            for tool_call in tool_calls:
                name, arguments = self._parse_tool_call(tool_call)
                if tool_names is not None and name not in tool_names:
                    raise ValueError(f"Tool no autorizada para esta consulta: {name}")
                call_key = json.dumps(
                    [name, arguments], sort_keys=True, ensure_ascii=False
                )
                if call_key in seen_calls:
                    result, source = seen_calls[call_key]
                    logger.info("saiki_tool_duplicate name=%s", name)
                else:
                    tool_started = time.perf_counter()
                    try:
                        result, source = await self._execute_tool(name, arguments, user)
                    except RuntimeError as exc:
                        if "MongoDB" in str(exc) or "motor" in str(exc):
                            raise SaikiDatabaseError(str(exc)) from exc
                        raise
                    finally:
                        logger.info(
                            "saiki_tool name=%s duration_ms=%d",
                            name,
                            round((time.perf_counter() - tool_started) * 1000),
                        )
                    seen_calls[call_key] = (result, source)
                tool_calls_count += 1
                sources.add(source)
                tool_data[name] = result
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
        logger.warning(
            "saiki_agent_limit iterations=%d ollama_calls=%d tool_calls=%d",
            self.max_tool_iterations,
            ollama_calls,
            tool_calls_count,
        )
        raise RuntimeError("Se alcanzó el límite de consultas de Saiki.")

    def _call_ollama_chat(self, messages: list[dict], tool_names=None) -> dict:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "tools": self.tools.definitions(tool_names),
            "stream": False,
            "think": False,
        }
        req = request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        parsed = urlsplit(url)
        connection_class = (
            http.client.HTTPSConnection
            if parsed.scheme == "https"
            else http.client.HTTPConnection
        )
        started = time.perf_counter()
        connection = None
        try:
            connection = connection_class(
                parsed.hostname,
                parsed.port,
                timeout=self.settings.ollama_connect_timeout_seconds,
            )
            connection.request(
                "POST",
                parsed.path or "/",
                body=req.data,
                headers=dict(req.headers),
            )
            if connection.sock is not None:
                connection.sock.settimeout(self.settings.ollama_read_timeout_seconds)
            response = connection.getresponse()
            result = json.loads(response.read().decode("utf-8"))
            if response.status >= 400:
                raise OllamaUnavailableError(
                    f"Ollama respondió HTTP {response.status}."
                )
        except (TimeoutError, socket.timeout) as exc:
            raise OllamaTimeoutError("Tiempo de espera agotado con Ollama.") from exc
        except (OSError, http.client.HTTPException, error.URLError) as exc:
            raise OllamaUnavailableError("No se pudo conectar con Ollama.") from exc
        except json.JSONDecodeError as exc:
            raise OllamaUnavailableError("Ollama devolvió JSON inválido.") from exc
        finally:
            if connection is not None:
                connection.close()
            logger.info(
                "saiki_ollama duration_ms=%d",
                round((time.perf_counter() - started) * 1000),
            )
        if not isinstance(result, dict):
            raise RuntimeError("Ollama devolvió una respuesta inválida.")
        logger.info("saiki_ollama_metrics total_ns=%s load_ns=%s prompt_tokens=%s output_tokens=%s", result.get("total_duration"), result.get("load_duration"), result.get("prompt_eval_count"), result.get("eval_count"))
        return result

    @staticmethod
    def _clean_answer(answer: str) -> str:
        if "</think>" in answer:
            answer = answer.rsplit("</think>", 1)[1]
        if "<think>" in answer:
            answer = answer.split("<think>", 1)[0]
        return answer.strip()

    def _parse_tool_call(self, tool_call: object) -> tuple[str, dict]:
        if not isinstance(tool_call, dict):
            raise ValueError("Tool call inválida.")
        function = tool_call.get("function")
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            raise ValueError("Tool call inválida.")
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Los argumentos de la tool no son JSON válido.") from exc
        if not isinstance(arguments, dict):
            raise ValueError("Los argumentos de la tool deben ser un objeto.")
        return function["name"], arguments

    @staticmethod
    def _build_prompt(question: str, context: dict) -> str:
        return (
            "Usa únicamente el contexto y las tools autorizadas. No inventes datos. "
            "Si falta información, dilo claramente.\n\n"
            f"CONTEXTO PSI TWIN:\n{json.dumps(context, ensure_ascii=False, default=str, indent=2)}"
            f"\n\nPREGUNTA:\n{question}"
        )

    @staticmethod
    def _visualization(data: dict) -> dict:
        return {"type": "none"} if not data else {"type": "table", "data": data}

    @staticmethod
    def _warnings(sources: set[str], data: dict | None = None) -> list[str]:
        warnings = []
        if "INVENTORY_RISK" in sources:
            warnings.append("El riesgo proviene de InventoryRiskService.")
        if "LIGHTGBM" in sources:
            warnings.append("La predicción proviene del pipeline LightGBM.")
            warnings.append("La predicción depende del historial disponible y representa demanda, no stock futuro.")
            forecast = (data or {}).get("get_forecast")
            if isinstance(forecast, dict) and any(item.get("sin_datos", 0) > 0 for item in forecast.get("features_por_horizonte", {}).values() if isinstance(item, dict)):
                warnings.append("Hay variables sin datos en el modelo; interpreta la predicción con esa limitación.")
        return warnings
