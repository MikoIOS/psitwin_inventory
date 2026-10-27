import math
from datetime import datetime, time, timedelta, timezone
from statistics import pstdev
from fastapi import HTTPException
from app.dto.inventory_risk_dto import (InventoryRiskResponse, ConsumoInfo, CoberturaInfo, ForecastInfo,
    ForecastDiario, SeguridadInfo, RiesgoInfo, ReposicionInfo)
from app.dto.alerta_dto import AlertaCreate, TipoAlerta, NivelRiesgo
from app.dto.recomendacion_dto import RecomendacionCreate, TipoRecomendacion
from app.services.alerta_service import AlertaService
from app.services.recomendacion_service import RecomendacionService
from app.services.forecast_service import ForecastService
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.almacen_repository import AlmacenRepository

class InventoryRiskService:
    def __init__(self, forecast_service=None):
        self.forecast_service = forecast_service or ForecastService()
        self.alerta_service = AlertaService()
        self.recomendacion_service = RecomendacionService()

    @staticmethod
    def _calcular_fecha_quiebre(
        stock_actual: float,
        forecast: ForecastInfo,
        fecha_base: datetime
    ) -> datetime | None:

        # Ya no existe stock.
        if stock_actual <= 0:

            return fecha_base

        acumulado = 0.0

        for prediccion in (
            forecast.predicciones_diarias
        ):

            acumulado += (
                prediccion.demanda_predicha
            )

            if acumulado >= stock_actual:

                return (
                    prediccion.fecha
                )

        # El forecast solamente cubre 7 días.
        #
        # Si no se agota dentro de esos 7 días,
        # no inventamos una fecha posterior.
        return None

    # ========================================================
    # NIVEL DE RIESGO
    # ========================================================

    @staticmethod
    def _calcular_nivel_riesgo(
        stock_actual: float,
        dias_cobertura: float | None,
        lead_time_dias: int,
        punto_reposicion: float
    ) -> NivelRiesgo:

        if stock_actual <= 0:

            return (
                NivelRiesgo.CRITICO
            )

        if dias_cobertura is None:

            return (
                NivelRiesgo.BAJO
            )

        if (
            lead_time_dias > 0
            and
            dias_cobertura
            <= lead_time_dias
        ):

            return (
                NivelRiesgo.CRITICO
            )

        if (
            punto_reposicion > 0
            and
            stock_actual
            <= punto_reposicion
        ):

            return (
                NivelRiesgo.ALTO
            )

        if (
            lead_time_dias > 0
            and
            dias_cobertura
            <= lead_time_dias * 1.5
        ):

            return (
                NivelRiesgo.MEDIO
            )

        return NivelRiesgo.BAJO

    # ========================================================
    # SCORE DE RIESGO
    # ========================================================

    @staticmethod
    def _calcular_score(
        stock_actual: float,
        dias_cobertura: float | None,
        lead_time_dias: int,
        punto_reposicion: float
    ) -> float:

        if stock_actual <= 0:
            return 100.0

        score = 0.0

        if (
            dias_cobertura is not None
            and
            lead_time_dias > 0
        ):

            ratio_cobertura = (
                dias_cobertura
                / lead_time_dias
            )

            if ratio_cobertura <= 1:
                score += 60

            elif ratio_cobertura <= 1.5:
                score += 40

            elif ratio_cobertura <= 2:
                score += 20

        if punto_reposicion > 0:

            ratio_stock = (
                stock_actual
                / punto_reposicion
            )

            if ratio_stock <= 0.5:
                score += 40

            elif ratio_stock <= 1:
                score += 30

            elif ratio_stock <= 1.25:
                score += 15

        return round(
            min(
                score,
                100
            ),
            2
        )

    # ========================================================
    # CALCULO DE REPOSICION
    # ========================================================

    @staticmethod
    def _calcular_reposicion(
        stock_actual: float,
        promedio_diario: float,
        stock_seguridad: float,
        lead_time_dias: int
    ) -> ReposicionInfo | None:

        if promedio_diario <= 0:
            return None

        horizonte_dias = max(
            lead_time_dias + 7,
            7
        )

        demanda_horizonte = (
            promedio_diario
            * horizonte_dias
        )

        cantidad_base = max(
            0,
            demanda_horizonte
            + stock_seguridad
            - stock_actual
        )

        cantidad_recomendada = (
            math.ceil(
                cantidad_base
            )
        )

        cantidad_minima = (
            math.ceil(
                cantidad_recomendada
                * 0.85
            )
        )

        cantidad_segura = (
            math.ceil(
                cantidad_recomendada
                * 1.15
            )
        )

        return ReposicionInfo(

            cantidad_minima=
                cantidad_minima,

            cantidad_recomendada=
                cantidad_recomendada,

            cantidad_segura=
                cantidad_segura
        )

    # ========================================================
    # EVALUAR INVENTARIO
    # ========================================================


    async def evaluar(self, id_inventario, generar_alertas=True, id_producto=None):
        header = await InventarioRepository().obtener_por_id(id_inventario)
        if not header:
            raise HTTPException(404, "Inventario general no encontrado")
        details = await DetalleInventarioRepository().obtener_por_inventario(id_inventario)
        if id_producto is None:
            products = {d["id_producto"] for d in details}
            if len(products) != 1:
                raise HTTPException(422, "Indique id_producto; un inventario general contiene varios productos")
            id_producto = products.pop()
        details = [d for d in details if d["id_producto"] == id_producto]
        product = await ProductoRepository.obtener_por_id(id_producto)
        warehouse = await AlmacenRepository.obtener_por_id(header["id_almacen"])
        if not product or not warehouse or product.get("id_empresa") != warehouse.get("id_empresa"):
            raise HTTPException(409, "Producto/almacén incompatible")
        stock = sum(d["stock_actual"] for d in details)
        lead = product["lead_time_dias"]
        forecasts = {h: await self.forecast_service.predecir(header["id_almacen"], id_producto, h) for h in (1,7,30,90)}
        weekly = forecasts[7]
        history = await self.forecast_service.historial(header["id_almacen"], id_producto, weekly.fecha_corte, 28)
        values = history["demanda"].tolist()
        avg = {w: sum(values[-w:])/w for w in (7,14,28)}
        trend = (avg[7]-avg[28])/avg[28]*100 if avg[28]>0 else (100 if avg[7]>0 else 0)
        base = datetime.combine(weekly.fecha_corte, time.min, timezone.utc)
        forecast = ForecastInfo(demanda_7d=weekly.demanda_total_estimada,
            predicciones_diarias=[ForecastDiario(fecha=datetime.combine(p.fecha,time.min,timezone.utc),
            demanda_predicha=p.demanda_estimada) for p in weekly.predicciones_diarias])
        result = InventoryRiskResponse(
            id_empresa=warehouse["id_empresa"], id_almacen=header["id_almacen"],
            id_inventario=id_inventario,id_producto=id_producto, stock_actual=stock, lead_time_dias=lead,
            consumo=ConsumoInfo(promedio_7d=round(avg[7],2),promedio_14d=round(avg[14],2),
                               promedio_28d=round(avg[28],2),tendencia_porcentaje=round(trend,2)),
            cobertura=CoberturaInfo(), forecast=forecast, estado=weekly.estado,
            advertencias=weekly.advertencias, pronosticos={h:f.model_dump(mode="json") for h,f in forecasts.items()})
        if weekly.estado != "DISPONIBLE":
            result.explicacion = "Sin forecast disponible: no se calculan agotamiento, riesgo ni reposición y no se generan alertas."
            return result
        consumption = max(next((avg[w] for w in (7,14,28) if avg[w]>0),0),weekly.demanda_total_estimada/7)
        coverage = round(stock/consumption,2) if consumption>0 else None
        safety = round(1.645*pstdev(values)*math.sqrt(lead),2) if lead>0 else 0
        point = round(consumption*lead+safety,2)
        level = self._calcular_nivel_riesgo(stock,coverage,lead,point)
        result.cobertura = CoberturaInfo(dias=coverage)
        result.seguridad = SeguridadInfo(stock_seguridad=safety,punto_reposicion=point)
        result.riesgo = RiesgoInfo(nivel=level,score=self._calcular_score(stock,coverage,lead,point))
        result.reposicion = self._calcular_reposicion(stock,consumption,safety,lead)
        result.forecast.fecha_quiebre_estimada = self._calcular_fecha_quiebre(stock,forecast,base)
        result.explicacion = f"Stock agregado {stock}; forecast 7 días {weekly.demanda_total_estimada}; cobertura {coverage}; riesgo {level.value}."
        if generar_alertas:
            await self._procesar_alerta(result)
        return result

    async def _procesar_alerta(
        self,
        resultado: InventoryRiskResponse
    ):

        nivel = (
            resultado.riesgo.nivel
        )

        if nivel not in (
            NivelRiesgo.ALTO,
            NivelRiesgo.CRITICO
        ):
            await self.alerta_service.resolver_activa_por_inventario(
                resultado.id_inventario,
                TipoAlerta.RIESGO_STOCKOUT,
                id_producto=resultado.id_producto
            )
            return

        if (
            nivel
            == NivelRiesgo.CRITICO
        ):

            titulo = (
                "Riesgo crítico de "
                "quiebre de stock"
            )

        else:

            titulo = (
                "Inventario cerca del "
                "punto de reposición"
            )

        alerta = (
            await self.alerta_service.crear(

                AlertaCreate(

                    id_empresa=
                        resultado.id_empresa,

                    id_almacen=
                        resultado.id_almacen,

                    id_inventario=
                        resultado.id_inventario,

                    id_producto=
                        resultado.id_producto,

                    tipo_alerta=
                        TipoAlerta
                        .RIESGO_STOCKOUT,

                    nivel_riesgo=
                        nivel,

                    titulo=
                        titulo,

                    mensaje=
                        resultado.explicacion,

                    stock_actual=
                        resultado.stock_actual,

                    dias_cobertura=
                        resultado
                        .cobertura
                        .dias,

                    stock_seguridad=
                        resultado
                        .seguridad
                        .stock_seguridad,

                    punto_reposicion=
                        resultado
                        .seguridad
                        .punto_reposicion,

                    forecast_7d=
                        resultado
                        .forecast
                        .demanda_7d
                )
            )
        )

        if resultado.reposicion is None:
            return

        await self.recomendacion_service.crear(

            RecomendacionCreate(

                id_empresa=
                    resultado.id_empresa,

                id_almacen=
                    resultado.id_almacen,

                id_inventario=
                    resultado.id_inventario,

                id_producto=
                    resultado.id_producto,

                id_alerta=
                    alerta[
                        "id_alerta"
                    ],

                tipo_recomendacion=
                    TipoRecomendacion
                    .REABASTECER,

                nivel_riesgo=
                    nivel,

                cantidad_minima=
                    resultado
                    .reposicion
                    .cantidad_minima,

                cantidad_recomendada=
                    resultado
                    .reposicion
                    .cantidad_recomendada,

                cantidad_segura=
                    resultado
                    .reposicion
                    .cantidad_segura,

                forecast_7d=
                    resultado
                    .forecast
                    .demanda_7d,

                explicacion=
                    resultado.explicacion,

                origen=
                    "MOTOR_SEGURIDAD_LIGHTGBM"
            )
        )

    # ========================================================
    # EVALUAR TODOS
    # ========================================================


    async def evaluar_todos(self, generar_alertas=False, ids_inventario=None):
        headers = await InventarioRepository().obtener_todos()
        results = []
        for header in headers:
            key = header["id_inventario"]
            if ids_inventario is not None and key not in ids_inventario:
                continue
            details = await DetalleInventarioRepository().obtener_por_inventario(key)
            for product in sorted({d["id_producto"] for d in details}):
                results.append(await self.evaluar(key,generar_alertas,product))
        return results
