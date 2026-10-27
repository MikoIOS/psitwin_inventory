from datetime import date, datetime, timedelta, timezone
import math
import pandas as pd
from fastapi import HTTPException
from app.dto.forecast_dto import ForecastResponse, PrediccionDiaria
from app.repositories.serie_demanda_repository import SerieDemandaRepository

class ForecastService:
    """Inferencia directa D+1..D+7. No extrapola artefactos a D+30/D+90."""
    def __init__(self, repository=None, predictor=None, feature_builder=None):
        self.repository = repository or SerieDemandaRepository()
        self.predictor = predictor
        self.feature_builder = feature_builder

    async def historial(self, id_almacen, id_producto, corte, dias):
        rows = await self.repository.diarios(id_almacen, corte-timedelta(days=dias-1), corte, [id_producto])
        values = {date.fromisoformat(str(row["fecha"])[:10]): float(row["demanda"]) for row in rows}
        return pd.DataFrame([
            {"fecha": corte-timedelta(days=dias-1-i),
             "demanda": values.get(corte-timedelta(days=dias-1-i), 0.0)}
            for i in range(dias)
        ])

    async def contexto(self, id_almacen, id_producto, corte, horizon):
        products = await self.repository.productos_almacen(id_almacen)
        current = next((p for p in products if p["id_producto"] == id_producto), None)
        category = current.get("categoria") if current else None
        dept = [p["id_producto"] for p in products if category and p.get("categoria", "").casefold() == category.casefold()]
        metadata_known = corte == datetime.now(timezone.utc).date() or all(
            isinstance(p.get("fecha_actualizacion"),datetime) and p["fecha_actualizacion"].date() <= corte
            for p in products)
        groups = {"store": None, "dept": dept, "item_total": [id_producto]}
        result = {}
        for prefix, ids in groups.items():
            if prefix == "dept" and not metadata_known:
                for lag in (1,7,28):
                    result[f"dept_sales_lag_{lag}"] = float("nan")
                for window in (7,28):
                    result[f"dept_sales_mean_{window}"] = float("nan")
                result["future_dept_lag_7"] = float("nan")
                continue
            rows = await self.repository.diarios(id_almacen, corte-timedelta(days=28), corte, ids)
            series = {date.fromisoformat(str(r["fecha"])[:10]): float(r["demanda"]) for r in rows}
            for lag in (1, 7, 28):
                result[f"{prefix}_sales_lag_{lag}" if prefix != "item_total" else f"item_total_lag_{lag}"] = series.get(corte-timedelta(days=lag), 0.0)
            if prefix != "item_total":
                for window in (7, 28):
                    result[f"{prefix}_sales_mean_{window}"] = sum(series.get(corte-timedelta(days=i), 0.0) for i in range(1, window+1))/window
                result[f"future_{prefix}_lag_7"] = series.get(corte-timedelta(days=7-horizon), 0.0)
        return result

    def _cargar_modelo(self):
        if self.predictor is None:
            from app.ml.model_loader import ModelLoader
            from app.ml.feature_builder import FeatureBuilder
            from app.ml.predictor import DemandPredictor
            loader = ModelLoader()
            self.feature_builder = FeatureBuilder(loader=loader)
            self.predictor = DemandPredictor(loader=loader)

    async def predecir(self, id_almacen, id_producto, horizonte_dias=7, fecha_corte=None, dias=400):
        if horizonte_dias not in (1, 7, 30, 90):
            raise HTTPException(422, "Horizontes permitidos: 1, 7, 30, 90")
        corte = fecha_corte or (datetime.now(timezone.utc).date())
        if corte > datetime.now(timezone.utc).date():
            raise HTTPException(422, "El corte no puede estar en el futuro")
        if dias < 7 or dias > 500:
            raise HTTPException(422, "Ventana histórica: 7..500 días")
        first = await self.repository.primera_salida(id_almacen, id_producto, corte)
        first_date = first["fecha_hora"].date() if first else None
        sufficient = bool(first_date and (corte-first_date).days >= 366 and dias >= 367)
        result = ForecastResponse(
            id_almacen=id_almacen, id_producto=id_producto, fecha_generacion=datetime.now(timezone.utc),
            fecha_corte=corte, horizonte_dias=horizonte_dias, fecha_inicio=corte+timedelta(days=1),
            fecha_fin=corte+timedelta(days=horizonte_dias), estado="MODELO_NO_DISPONIBLE",
            historial_suficiente=sufficient)
        if corte == datetime.now(timezone.utc).date():
            result.advertencias.append("El día de corte UTC está en curso; demanda observada hasta la consulta, primer pronóstico = mañana UTC.")
        if horizonte_dias > 7:
            result.advertencias.append("No hay artefactos validados para 30/90 días; no se extrapolan los boosters D+1..D+7.")
            return result
        if not sufficient:
            result.estado = "HISTORIAL_INSUFICIENTE"
            result.advertencias.append("Se requieren al menos 367 días de cobertura histórica y ventana >=367; los ceros no acreditan observaciones.")
            return result
        try:
            self._cargar_modelo()
            history = await self.historial(id_almacen, id_producto, corte, dias)
            daily = []
            for horizon in range(1, horizonte_dias+1):
                context = await self.contexto(id_almacen, id_producto, corte, horizon)
                features = self.feature_builder.build_demand_features(history=history, horizon=horizon, context=context)
                prediction = float(self.predictor.predict_horizon(features=features, horizon=horizon))
                if not math.isfinite(prediction):
                    raise ValueError("Predicción no finita")
                daily.append(PrediccionDiaria(fecha=corte+timedelta(days=horizon), demanda_estimada=round(max(0, prediction), 4)))
        except Exception as exc:
            from pymongo.errors import PyMongoError
            if isinstance(exc, PyMongoError):
                raise
            result.advertencias.append(f"Artefactos/inferencia no disponibles: {type(exc).__name__}")
            return result
        result.estado = "DISPONIBLE"
        result.predicciones_diarias = daily
        result.demanda_total_estimada = round(sum(p.demanda_estimada for p in daily), 4)
        result.modelo = "LightGBM regression_l1 global directo"
        result.version_modelo = "psitwin_v3_6"
        if corte < datetime.now(timezone.utc).date():
            result.advertencias.append("Agregados de categoría ausentes si metadata no acredita conocimiento al corte; no hay snapshots históricos de maestros.")
        result.advertencias.extend([
            "Artefactos M5 existentes sin validación de precisión para estas series producto/almacén.",
            "Sin mapeo categórico M5 ni fuentes operativas de precio/eventos/SNAP; esas features permanecen ausentes.",
            "Demanda = todas las SALIDAS; días sin SALIDA se rellenan con cero."
        ])
        return result
