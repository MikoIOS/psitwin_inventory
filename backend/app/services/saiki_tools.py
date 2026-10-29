from typing import Any, Awaitable, Callable
import asyncio
import logging
import time

from pydantic import BaseModel, ConfigDict, Field

from app.services.forecast_service import ForecastService
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
from typing import Literal
from app.repositories.producto_repository import ProductoRepository
from app.repositories.almacen_repository import AlmacenRepository
from app.repositories.rack_repository import RackRepository
from app.repositories.zona_repository import ZonaRepository
from app.services.alerta_service import AlertaService
from app.services.inventario_service import InventarioService
from app.services.inventory_risk_service import InventoryRiskService
from app.services.movimiento_service import MovimientoService
from app.services.recomendacion_service import RecomendacionService
from app.services.acceso_service import AccesoService
from app.dto.auth_dto import UsuarioActual

logger = logging.getLogger(__name__)


class InventoryArgs(BaseModel):
    id_inventario: str = Field(min_length=1)
    id_producto: str | None = None


class ProductArgs(BaseModel):
    id_producto: str | None = Field(default=None, min_length=1, description="Producto específico; omitir para consultar el catálogo de la empresa autenticada.")

class NoArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ForecastArgs(BaseModel):
    id_producto: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")
    id_inventario: str = Field(min_length=1)
    id_almacen: str | None = None
    dias: int = Field(default=400, ge=7, le=500, description="Ventana histórica; no es el horizonte de predicción.")
    horizonte_dias: Literal[1, 7, 30, 90] = 7


class OptionalInventoryArgs(BaseModel):
    id_inventario: str | None = None


class SensorStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_dispositivo: str | None = Field(default=None, min_length=1)
    horas: int = Field(default=24, ge=1, le=168)
    question: str | None = Field(default=None, min_length=1, max_length=1000)
    id_almacen: str | None = Field(default=None, min_length=1)


class DemandAnalysisArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')
    horizonte_dias: Literal[1, 7, 30, 90] = 30
    id_almacen: str | None = Field(default=None, min_length=1)
    id_producto: str | None = Field(default=None, min_length=1)


class WarehouseStatusArgs(OptionalInventoryArgs):
    include_visual: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


ToolHandler = Callable[..., Awaitable[Any]]


class SaikiToolRegistry:
    """Whitelist of read-only operations available to Saiki."""

    def __init__(self):
        self.inventario_service = InventarioService()
        self.forecast_service = ForecastService()
        self.risk_service = InventoryRiskService(self.forecast_service)
        self.alerta_service = AlertaService()
        self.recomendacion_service = RecomendacionService()
        self.movimiento_service = MovimientoService()
        self._handlers: dict[str, tuple[type[BaseModel], ToolHandler, str]] = {
            'get_workforce': (NoArgs, self.get_workforce, 'OPERARIOS'),
            'get_locations': (NoArgs, self.get_locations, 'UBICACIONES'),
            'get_demand_analysis': (DemandAnalysisArgs, self.get_demand_analysis, 'AUTOGLUON'),
            "get_sensor_status": (
                SensorStatusArgs,
                self.get_sensor_status,
                "SENSORES",
            ),
            "get_inventory": (
                InventoryArgs,
                self.get_inventory,
                "INVENTARIO",
            ),
            "get_product": (
                ProductArgs,
                self.get_product,
                "PRODUCTO",
            ),
            "get_forecast": (
                ForecastArgs,
                self.get_forecast,
                "AUTOGLUON",
            ),
            "get_inventory_risk": (
                InventoryArgs,
                self.get_inventory_risk,
                "INVENTORY_RISK",
            ),
            "get_active_alerts": (
                OptionalInventoryArgs,
                self.get_active_alerts,
                "ALERTAS",
            ),
            "get_recommendations": (
                OptionalInventoryArgs,
                self.get_recommendations,
                "RECOMENDACIONES",
            ),
            "get_recent_movements": (
                OptionalInventoryArgs,
                self.get_recent_movements,
                "MOVIMIENTOS",
            ),
            "get_warehouse_status": (
                WarehouseStatusArgs,
                self.get_warehouse_status,
                "INVENTARIO",
            ),
        }

    @property
    def names(self) -> set[str]:
        return set(self._handlers)

    def definitions(
        self,
        names: set[str] | frozenset[str] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": (
                        "Consulta de solo lectura. "
                        + (
                            "Para un resumen general del almacén no requiere argumentos."
                            if name == "get_warehouse_status"
                            else "Sensores y equipos de refrigeración: lecturas, ubicaciones, alertas e historial autorizado. Opcionalmente selecciona id_dispositivo y una ventana de 1 a 168 horas." if name == "get_sensor_status"
                            else f"Tool autorizada: {name}."
                        )
                    ),
                    "parameters": model.model_json_schema(),
                },
            }
            for name, (model, _, _) in self._handlers.items()
            if names is None or name in names
        ]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        user=None,
    ) -> tuple[Any, str]:
        if name not in self._handlers:
            raise ValueError(f"Tool no autorizada: {name}")
        model, handler, source = self._handlers[name]
        try:
            validated = model.model_validate(arguments)
        except Exception as exc:
            raise ValueError(f"Argumentos inválidos para {name}: {exc}") from exc
        visible = None
        started = time.perf_counter()
        if name in {"get_sensor_status", "get_demand_analysis", 'get_workforce', 'get_locations'}:
            return await handler(validated, user), source
        if user is not None:
            visible = await self._authorize(name, validated, user)
        logger.info("saiki_authorization tool=%s duration_ms=%.3f", name, (time.perf_counter() - started) * 1000)
        started = time.perf_counter()
        try:
            if name == "get_warehouse_status":
                return await handler(validated, user, visible), source
            if name == "get_product":
                return await handler(validated, user), source
            if name == 'get_active_alerts':
                return await handler(validated, visible, user), source
            if name in {"get_active_alerts", "get_recommendations", "get_recent_movements"}:
                return await handler(validated, visible), source
            return await handler(validated), source
        finally:
            logger.info("saiki_data_query tool=%s duration_ms=%.3f", name, (time.perf_counter() - started) * 1000)

    async def _authorize(self, name: str, args: BaseModel, user):
        if name == 'get_product':
            if args.id_producto:
                await AccesoService.verificar_producto(user, args.id_producto)
            return None
        if name == "get_warehouse_status" and getattr(args, "include_visual", False) and not args.id_inventario:
            # The visual summary traverses the authorized hierarchy once itself.
            return None
        visible = frozenset(await AccesoService.ids_inventarios(user))
        if hasattr(args, "id_inventario") and args.id_inventario:
            await AccesoService.verificar_inventario(user, args.id_inventario)
        if getattr(args, "id_almacen", None):
            await AccesoService.verificar_almacen(user, args.id_almacen)
        if getattr(args, "id_producto", None):
            await AccesoService.verificar_producto(user, args.id_producto)
        return visible

    async def get_sensor_status(self, args: SensorStatusArgs, user=None):
        if args.question:
            from app.services.saiki_sensor_queries import consultar_sensores
            answer, evidence = await consultar_sensores(user, args.question, args.id_dispositivo, args.id_almacen)
            return {'resumen': answer, **evidence}
        from app.services.saiki_sensors import sensor_report
        answer, evidence = await sensor_report(user, args.id_dispositivo, args.horas)
        return {"resumen": answer, **evidence}

    async def get_workforce(self, args, user=None):
        from fastapi import HTTPException
        from app.services.operario_service import OperarioService
        if user is None or not user.es_empresa:
            raise HTTPException(403, 'Solo la empresa puede consultar su personal')
        rows = await OperarioService().obtener_por_empresa(user.id_empresa, user)
        active = sum(str(row.get('estado', '')).casefold() == 'activo' for row in rows)
        inactive = sum(str(row.get('estado', '')).casefold() == 'inactivo' for row in rows)
        return {'total': len(rows), 'activos': active, 'inactivos': inactive, 'otros_estados': len(rows) - active - inactive}

    async def get_locations(self, args, user=None):
        from fastapi import HTTPException
        from app.services.acceso_service import id_de_almacen, id_de_zona
        if user is None or not user.es_empresa:
            raise HTTPException(403, 'Se requiere una sesión de empresa')
        warehouses = await AlmacenRepository.obtener_por_empresa(user.id_empresa)
        zones = await ZonaRepository.obtener_por_almacenes([id_de_almacen(row) for row in warehouses if id_de_almacen(row)])
        racks = await RackRepository.obtener_por_zonas([id_de_zona(row) for row in zones if id_de_zona(row)])
        return {'almacenes': [{'id_almacen': id_de_almacen(row), 'nombre': row.get('nombre', '')} for row in warehouses],
            'total_almacenes': len(warehouses), 'total_zonas': len(zones), 'total_racks': len(racks)}

    async def get_demand_analysis(self, args: DemandAnalysisArgs, user=None):
        if user is None: raise ValueError('Se requiere una sesión para consultar demanda')
        from app.services.saiki_demand import demand_answer
        answer, evidence = await demand_answer(user, args.horizonte_dias, args.id_almacen, args.id_producto)
        return {'resumen': answer, **evidence}

    async def get_inventory(self, args: InventoryArgs):
        header = await self.inventario_service.obtener_inventario(args.id_inventario)
        return {**header, "stock_por_producto": await self.inventario_service.stock_por_producto(args.id_inventario),
                "detalles": await self.inventario_service.detalles_inventario(args.id_inventario, id_producto=args.id_producto)}

    async def get_product(self, args: ProductArgs, user=None):
        if args.id_producto:
            return await ProductoRepository.obtener_por_id(args.id_producto)
        query = {'id_empresa': user.id_empresa} if user is not None else {}
        if user is not None and getattr(user, 'es_proveedor', False):
            query['id_proveedor'] = user.id_proveedor
        products = await ProductoRepository.collection().find(query, {'_id': 0}).to_list(length=None) if user is not None else await ProductoRepository.obtener_todos()
        return [item for item in products if user is None or item.get("id_empresa") == user.id_empresa]

    async def get_forecast(self, args: ForecastArgs):
        header = await self.inventario_service.obtener_inventario(args.id_inventario)
        if not args.id_producto:
            raise ValueError("Forecast requiere id_producto: el inventario es general")
        if args.id_almacen and args.id_almacen != header["id_almacen"]:
            raise ValueError("Almacén incompatible con inventario")
        result = await self.forecast_service.predecir(header["id_almacen"], args.id_producto, args.horizonte_dias, dias=args.dias)
        return result.model_dump(mode="json")

    async def get_inventory_risk(self, args: InventoryArgs):
        result = await self.risk_service.evaluar(
            id_inventario=args.id_inventario,
            generar_alertas=False,
            id_producto=args.id_producto,
        )
        return result.model_dump(mode="python")

    async def get_active_alerts(self, args: OptionalInventoryArgs, visible=None, user=None):
        if user is not None and not args.id_inventario:
            return await self.alerta_service.listar_activas_por_empresa(user.id_empresa)
        if args.id_inventario:
            alerts = await self.alerta_service.listar_por_inventario(args.id_inventario)
            return [item for item in alerts if item.get("estado") == "ACTIVA"]
        if visible is not None:
            groups = await asyncio.gather(*(self.alerta_service.listar_por_inventario(i) for i in visible))
            return [item for group in groups for item in group if item.get('estado') == 'ACTIVA']
        alerts = await self.alerta_service.listar_activas()
        return [item for item in alerts if visible is None or item.get("id_inventario") in visible]

    async def get_recommendations(self, args: OptionalInventoryArgs, visible=None):
        if args.id_inventario:
            return await self.recomendacion_service.listar_por_inventario(
                args.id_inventario
            )
        if visible is not None:
            groups = await asyncio.gather(*(self.recomendacion_service.listar_por_inventario(i) for i in visible))
            return [item for group in groups for item in group]
        recommendations = await self.recomendacion_service.listar()
        return [
            item
            for item in recommendations
            if visible is None or item.get("id_inventario") in visible
        ]

    async def get_recent_movements(self, args: OptionalInventoryArgs, visible=None):
        if args.id_inventario:
            movements = await self.movimiento_service.obtener_por_inventario(args.id_inventario)
        else:
            if visible is not None:
                groups = await asyncio.gather(*(self.movimiento_service.obtener_por_inventario(i) for i in visible))
                movements = [item for group in groups for item in group]
            else:
                movements = await self.movimiento_service.obtener_movimientos()
            movements = [item for item in movements if visible is None or item.get("id_inventario") in visible]
        return sorted(
            movements,
            key=lambda item: str(item.get("fecha_hora", "")),
            reverse=True,
        )[:20]

    async def get_warehouse_status(
        self,
        args: OptionalInventoryArgs,
        user: UsuarioActual | None = None,
        visible=None,
    ):
        if getattr(args, "include_visual", False):
            from app.services.saiki_inventory_summary import inventory_summary
            return await inventory_summary(user, args.page, args.page_size)
        visible_warehouse_ids = None
        if user is not None:
            visible_warehouse_ids = await AccesoService.ids_almacenes(user)
        warehouses = await AlmacenRepository.obtener_por_empresa(user.id_empresa) if user is not None else await AlmacenRepository.obtener_todos()
        if visible_warehouse_ids is not None:
            warehouses = [
                warehouse
                for warehouse in warehouses
                if (warehouse.get("id_almacen") or warehouse.get("id"))
                in visible_warehouse_ids
            ]
        if not warehouses:
            return {
                "estado_inventario": "sin_almacenes",
                "total_almacenes": 0,
                "mensaje": (
                    "Actualmente no tienes almacenes registrados en PsiTwin. "
                    "Primero debes crear uno para comenzar a gestionar tu inventario."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": 0,
                "stock_total_unidades": 0,
                "almacenes": [],
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }

        scoped_zones, scoped_racks = None, None
        if visible_warehouse_ids is not None:
            scoped_zones = await ZonaRepository.obtener_por_almacenes(list(visible_warehouse_ids))
            visible_zone_ids = {
                zone.get("id_zona", zone.get("id"))
                for zone in scoped_zones
                if zone.get("id_almacen") in visible_warehouse_ids
            }
            scoped_racks = await RackRepository.obtener_por_zonas(list(visible_zone_ids))
            visible_rack_ids = {
                rack.get("id_rack") or rack.get("id")
                for rack in scoped_racks
                if rack.get("id_zona") in visible_zone_ids
            }
        else:
            visible_rack_ids = None

        inventories = await DetalleInventarioRepository().obtener_por_racks(list(visible_rack_ids)) if visible_rack_ids is not None else await DetalleInventarioRepository().obtener_todos()
        if visible is not None:
            inventories = [
                item for item in inventories
                if item.get("id_inventario") in visible
            ]
        if args.id_inventario:
            inventories = [
                item for item in inventories
                if item.get("id_inventario") == args.id_inventario
            ]

        if visible_rack_ids is not None:
            inventories = [
                item for item in inventories
                if item.get("id_rack") in visible_rack_ids
            ]

        product_ids = {
            item.get("id_producto")
            for item in inventories
            if item.get("id_producto")
        }
        all_products = await ProductoRepository.collection().find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=None) if user is not None else await ProductoRepository.obtener_todos()
        products = {
            product["id_producto"]: product
            for product in all_products
            if (
                product.get("id_producto") in product_ids
                or visible_rack_ids is None
                or (user is not None and product.get("id_empresa") == user.id_empresa)
            )
        }
        if user is not None:
            inventories = [item for item in inventories if item.get('id_producto') in products]
        if not inventories and not products:
            return {
                "estado_inventario": "almacen_sin_productos",
                "total_almacenes": len(warehouses),
                "mensaje": (
                    "Tu almacén está registrado, pero todavía no tienes "
                    "productos registrados."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": 0,
                "stock_total_unidades": 0,
                "almacenes": warehouses,
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }
        if not inventories:
            return {
                "estado_inventario": "productos_sin_inventario",
                "total_almacenes": len(warehouses),
                "mensaje": (
                    "Tienes productos registrados, pero todavía no hay "
                    "existencias de inventario asociadas."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": len(products),
                "stock_total_unidades": 0,
                "almacenes": warehouses,
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }
        rack_ids = {
            item.get("id_rack")
            for item in inventories
            if item.get("id_rack")
        }
        racks = {
            (rack.get("id_rack") or rack.get("id")): rack
            for rack in (scoped_racks if scoped_racks is not None else await RackRepository.obtener_todos())
            if (rack.get("id_rack") or rack.get("id")) in rack_ids
        }
        zone_ids = {
            rack.get("id_zona")
            for rack in racks.values()
            if rack.get("id_zona")
        }
        zones = {
            zone.get("id_zona", zone.get("id")): zone
            for zone in (scoped_zones if scoped_zones is not None else await ZonaRepository.obtener_todas())
            if zone.get("id_zona", zone.get("id")) in zone_ids
        }
        warehouse_ids = {
            zone.get("id_almacen")
            for zone in zones.values()
            if zone.get("id_almacen")
        }
        warehouses_by_id = {
            almacen.get("id_almacen", almacen.get("id")): almacen
            for almacen in warehouses
            if almacen.get("id_almacen", almacen.get("id")) in warehouse_ids
        }
        stock_by_product: dict[str, int | float] = {}
        for item in inventories:
            product_id = item.get("id_producto")
            stock_by_product[product_id] = (
                stock_by_product.get(product_id, 0)
                + (item.get("stock_actual", 0) or 0)
            )

        series = {}
        for item in inventories:
            rack = racks.get(item["id_rack"],{})
            warehouse_id = zones.get(rack.get("id_zona"),{}).get("id_almacen")
            key = (item["id_inventario"],item["id_producto"])
            total = series.setdefault(key,{"id_inventario":key[0],"id_producto":key[1],
                "id_almacen":warehouse_id,"stock_actual":0})
            total["stock_actual"] += item.get("stock_actual",0)
        result = {
            "stock_por_producto_almacen":list(series.values()),
            "total_almacenes": len(warehouses),
            "total_registros_inventario": len(inventories),
            "productos_distintos": len(product_ids),
            "stock_total_unidades": sum(stock_by_product.values()),
            "stock_por_producto": [
                {
                    "id_producto": product_id,
                    "nombre": products.get(product_id, {}).get("nombre"),
                    "stock_actual": stock,
                }
                for product_id, stock in stock_by_product.items()
            ],
            "almacenes": list(warehouses_by_id.values()),
            "ubicaciones": [
                {
                    "id_inventario": item.get("id_inventario"),
                    "id_detalle_inventario": item.get("id_detalle_inventario"),
                    "id_producto": item.get("id_producto"),
                    "id_rack": item.get("id_rack"),
                    "rack": racks.get(item.get("id_rack")),
                    "zona": zones.get(
                        racks.get(item.get("id_rack"), {}).get("id_zona")
                    ),
                    "stock_actual": item.get("stock_actual", 0),
                }
                for item in inventories
            ],
            "inventarios": inventories[:50],
        }
        if all(stock <= 0 for stock in stock_by_product.values()):
            result["estado_inventario"] = "stock_cero"
            result["mensaje"] = (
                "Tienes productos registrados, pero actualmente sus existencias son cero."
            )
        else:
            result["estado_inventario"] = "stock_positivo"
        return result
