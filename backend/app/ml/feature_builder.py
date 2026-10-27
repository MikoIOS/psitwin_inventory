# app/ml/feature_builder.py

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta
)

from typing import (
    Any,
    Dict,
    Iterable,
    Optional
)

import numpy as np
import pandas as pd

from app.ml.model_loader import (
    ModelLoader
)


class FeatureBuilder:
    """
    Construye y prepara las variables utilizadas por los
    modelos LightGBM de PsiTwin.

    Responsabilidades:

    1. Obtener la lista exacta de features del modelo.
    2. Construir features temporales.
    3. Construir lags.
    4. Construir rolling statistics.
    5. Construir EWMA.
    6. Construir variables de comportamiento/tendencia.
    7. Preparar features del horizonte D+1 ... D+7.
    8. Validar y ordenar las columnas exactamente como
       fueron utilizadas durante el entrenamiento.

    IMPORTANTE:

    Esta versión construye las variables que pueden obtenerse
    directamente del historial diario de demanda.

    Las variables de:

    - precio
    - eventos
    - SNAP
    - agregaciones de tienda
    - agregaciones de departamento
    - agregaciones globales del producto

    serán incorporadas posteriormente con sus fuentes reales.
    """

    EPSILON = 1e-8

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        loader: ModelLoader
    ) -> None:

        self.loader = loader

        self.features = (
            self.loader.get_features()
        )

        self.categorical_features = (
            self.loader
            .get_categorical_features()
        )

    # ============================================================
    # UTILIDADES
    # ============================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0
    ) -> float:

        try:

            result = float(
                value
            )

            if np.isnan(result):

                return default

            if np.isinf(result):

                return default

            return result

        except (
            TypeError,
            ValueError
        ):

            return default

    # ============================================================
    # DIVISION SEGURA
    # ============================================================

    @classmethod
    def _safe_divide(
        cls,
        numerator: float,
        denominator: float,
        default: float = 0.0
    ) -> float:

        numerator = cls._safe_float(
            numerator
        )

        denominator = cls._safe_float(
            denominator
        )

        if abs(
            denominator
        ) < cls.EPSILON:

            return default

        return (
            numerator
            / denominator
        )

    # ============================================================
    # NORMALIZAR HISTORIAL
    # ============================================================

    @staticmethod
    def _prepare_history(
        history: pd.DataFrame
    ) -> pd.DataFrame:

        if not isinstance(
            history,
            pd.DataFrame
        ):

            raise TypeError(
                "history debe ser un pandas.DataFrame."
            )

        if history.empty:

            raise ValueError(
                "El historial de demanda está vacío."
            )

        required = {
            "fecha",
            "demanda"
        }

        missing = (
            required
            - set(history.columns)
        )

        if missing:

            raise ValueError(
                "El historial debe contener las columnas: "
                "fecha y demanda."
            )

        df = history[
            [
                "fecha",
                "demanda"
            ]
        ].copy()

        df[
            "fecha"
        ] = pd.to_datetime(
            df["fecha"],
            errors="coerce"
        )

        df[
            "demanda"
        ] = pd.to_numeric(
            df["demanda"],
            errors="coerce"
        ).fillna(
            0.0
        )

        df = (
            df
            .dropna(
                subset=[
                    "fecha"
                ]
            )
            .sort_values(
                "fecha"
            )
            .drop_duplicates(
                subset=[
                    "fecha"
                ],
                keep="last"
            )
            .reset_index(
                drop=True
            )
        )

        if df.empty:

            raise ValueError(
                "No existen fechas válidas "
                "en el historial."
            )

        return df

    # ============================================================
    # OBTENER SERIE
    # ============================================================

    @classmethod
    def _series(
        cls,
        history: pd.DataFrame
    ) -> pd.Series:

        df = cls._prepare_history(
            history
        )

        return (
            df[
                "demanda"
            ]
            .astype(float)
            .reset_index(
                drop=True
            )
        )

    # ============================================================
    # OBTENER FECHA BASE
    # ============================================================

    @classmethod
    def _base_date(
        cls,
        history: pd.DataFrame
    ) -> pd.Timestamp:

        df = cls._prepare_history(
            history
        )

        return pd.Timestamp(
            df[
                "fecha"
            ].iloc[-1]
        )

    # ============================================================
    # LAG
    #
    # lag_1 = demanda del último día disponible
    # lag_7 = demanda de hace 7 días
    # ============================================================

    @staticmethod
    def _lag(
        series: pd.Series,
        lag: int
    ) -> float:

        if lag <= 0:

            raise ValueError(
                "lag debe ser mayor que 0."
            )

        if len(series) < lag:

            return np.nan

        return float(
            series.iloc[
                -lag
            ]
        )

    # ============================================================
    # ULTIMOS N VALORES
    # ============================================================

    @staticmethod
    def _last_values(
        series: pd.Series,
        window: int
    ) -> pd.Series:

        if window <= 0:

            raise ValueError(
                "window debe ser mayor que 0."
            )

        if series.empty:

            return pd.Series(
                dtype=float
            )

        return (
            series
            .iloc[
                -window:
            ]
            .astype(float)
        )

    # ============================================================
    # ROLLING MEAN
    # ============================================================

    @classmethod
    def _rolling_mean(
        cls,
        series: pd.Series,
        window: int
    ) -> float:

        values = cls._last_values(
            series,
            window
        )

        if len(values) < window:

            return np.nan

        return float(
            values.mean()
        )

    # ============================================================
    # ROLLING STD
    # ============================================================

    @classmethod
    def _rolling_std(
        cls,
        series: pd.Series,
        window: int
    ) -> float:

        values = cls._last_values(
            series,
            window
        )

        if len(values) < window:

            return np.nan

        return float(
            values.std(
                ddof=0
            )
        )

    # ============================================================
    # ROLLING MAX
    # ============================================================

    @classmethod
    def _rolling_max(
        cls,
        series: pd.Series,
        window: int
    ) -> float:

        values = cls._last_values(
            series,
            window
        )

        if len(values) < window:

            return np.nan

        return float(
            values.max()
        )

    # ============================================================
    # EWMA
    # ============================================================

    @classmethod
    def _ewma(
        cls,
        series: pd.Series,
        span: int
    ) -> float:

        if series.empty:

            return np.nan

        value = (
            series
            .astype(float)
            .ewm(
                span=span,
                adjust=False
            )
            .mean()
            .iloc[-1]
        )

        return float(
            value
        )

    # ============================================================
    # ZERO RATIO
    # ============================================================

    @classmethod
    def _zero_ratio(
        cls,
        series: pd.Series,
        window: int
    ) -> float:

        values = cls._last_values(
            series,
            window
        )

        if len(values) < window:

            return np.nan

        return float(
            (
                values == 0
            ).mean()
        )

    # ============================================================
    # DAYS SINCE SALE
    # ============================================================

    @staticmethod
    def _days_since_sale(
        series: pd.Series
    ) -> float:

        if series.empty:

            return np.nan

        values = (
            series
            .astype(float)
            .to_numpy()
        )

        positive_indices = np.where(
            values > 0
        )[0]

        if len(
            positive_indices
        ) == 0:

            return float(
                len(values)
            )

        last_index = int(
            positive_indices[-1]
        )

        return float(
            len(values)
            - 1
            - last_index
        )

    # ============================================================
    # SALE RATE
    # ============================================================

    @classmethod
    def _sale_rate(
        cls,
        series: pd.Series,
        window: int
    ) -> float:

        values = cls._last_values(
            series,
            window
        )

        if len(values) < window:

            return np.nan

        return float(
            (
                values > 0
            ).mean()
        )

    # ============================================================
    # GROWTH STREAK
    # ============================================================

    @classmethod
    def _growth_streak_3(
        cls,
        series: pd.Series
    ) -> float:

        values = cls._last_values(
            series,
            4
        )

        if len(values) < 4:

            return np.nan

        diffs = (
            values
            .diff()
            .dropna()
        )

        return float(
            (
                diffs > 0
            ).all()
        )

    # ============================================================
    # PEAK COUNT
    # ============================================================

    @classmethod
    def _peak_count_7(
        cls,
        series: pd.Series
    ) -> float:

        values = cls._last_values(
            series,
            7
        )

        if len(values) < 7:

            return np.nan

        mean_28 = cls._rolling_mean(
            series,
            28
        )

        if np.isnan(
            mean_28
        ):

            return np.nan

        return float(
            (
                values > mean_28
            ).sum()
        )

    # ============================================================
    # INCREMENTOS
    # ============================================================

    @staticmethod
    def _increments(
        series: pd.Series
    ) -> pd.Series:

        return (
            series
            .astype(float)
            .diff()
            .dropna()
            .reset_index(
                drop=True
            )
        )

    # ============================================================
    # DOW MEAN
    #
    # Promedio histórico para el mismo día de la semana.
    # ============================================================

    @classmethod
    def _dow_mean(
        cls,
        history: pd.DataFrame,
        target_date: pd.Timestamp,
        weeks: int
    ) -> float:

        df = cls._prepare_history(
            history
        )

        target_dow = (
            target_date.dayofweek
        )

        filtered = df[
            df[
                "fecha"
            ].dt.dayofweek
            == target_dow
        ]

        filtered = (
            filtered.tail(
                weeks
            )
        )

        if len(
            filtered
        ) < 1:

            return np.nan

        return float(
            filtered[
                "demanda"
            ].mean()
        )

    # ============================================================
    # DOW STD
    # ============================================================

    @classmethod
    def _dow_std(
        cls,
        history: pd.DataFrame,
        target_date: pd.Timestamp,
        weeks: int
    ) -> float:

        df = cls._prepare_history(
            history
        )

        target_dow = (
            target_date.dayofweek
        )

        filtered = df[
            df[
                "fecha"
            ].dt.dayofweek
            == target_dow
        ].tail(
            weeks
        )

        if len(filtered) < 2:

            return np.nan

        return float(
            filtered[
                "demanda"
            ].std(
                ddof=0
            )
        )

    # ============================================================
    # FEATURES DE CALENDARIO
    # ============================================================

    @staticmethod
    def _calendar_features(
        fecha: pd.Timestamp
    ) -> Dict[str, Any]:

        iso_calendar = (
            fecha.isocalendar()
        )

        return {

            "month":
                int(fecha.month),

            "year":
                int(fecha.year),

            "dayofweek":
                int(fecha.dayofweek),

            "day":
                int(fecha.day),

            "weekofyear":
                int(
                    iso_calendar.week
                ),

            "is_weekend":
                int(
                    fecha.dayofweek >= 5
                ),

            "quarter":
                int(fecha.quarter),

            "dayofyear":
                int(fecha.dayofyear),

            "is_month_start":
                int(
                    fecha.is_month_start
                ),

            "is_month_end":
                int(
                    fecha.is_month_end
                )
        }

    # ============================================================
    # FEATURES DE FECHA FUTURA
    # ============================================================

    @staticmethod
    def _target_calendar_features(
        fecha: pd.Timestamp
    ) -> Dict[str, Any]:

        iso_calendar = (
            fecha.isocalendar()
        )

        return {

            "target_month":
                int(fecha.month),

            "target_dayofweek":
                int(fecha.dayofweek),

            "target_day":
                int(fecha.day),

            "target_weekofyear":
                int(
                    iso_calendar.week
                ),

            "target_is_weekend":
                int(
                    fecha.dayofweek >= 5
                ),

            "target_quarter":
                int(fecha.quarter),

            "target_dayofyear":
                int(fecha.dayofyear)
        }

    # ============================================================
    # CONSTRUIR FEATURES DE DEMANDA
    # ============================================================

    def build_demand_features(
        self,
        history: pd.DataFrame,
        horizon: int,
        context: Optional[
            Dict[str, Any]
        ] = None
    ) -> Dict[str, Any]:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "horizon debe estar entre 1 y 7."
            )

        df = self._prepare_history(
            history
        )

        series = (
            df[
                "demanda"
            ]
            .astype(float)
            .reset_index(
                drop=True
            )
        )

        base_date = pd.Timestamp(
            df[
                "fecha"
            ].iloc[-1]
        )

        target_date = (
            base_date
            + pd.Timedelta(
                days=horizon
            )
        )

        context = (
            dict(context)
            if context
            else {}
        )

        result: Dict[
            str,
            Any
        ] = {}

        # ========================================================
        # CONTEXTO EXTERNO
        # ========================================================

        result.update(
            context
        )

        # ========================================================
        # CALENDARIO ACTUAL
        # ========================================================

        result.update(
            self._calendar_features(
                base_date
            )
        )

        # ========================================================
        # CALENDARIO OBJETIVO D+N
        # ========================================================

        result.update(
            self._target_calendar_features(
                target_date
            )
        )

        # ========================================================
        # DEMANDA ACTUAL
        # ========================================================

        result[
            "current_y"
        ] = float(
            series.iloc[-1]
        )

        # ========================================================
        # AGE DAYS
        # ========================================================

        result[
            "age_days"
        ] = float(
            len(series)
            - 1
        )

        # ========================================================
        # LAGS
        # ========================================================

        lags = [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            14,
            21,
            28,
            35,
            42,
            56,
            364,
            365,
            366
        ]

        for lag in lags:

            result[
                f"lag_{lag}"
            ] = self._lag(
                series,
                lag
            )

        # ========================================================
        # ROLLING MEANS
        # ========================================================

        for window in [
            3,
            7,
            14,
            28,
            56,
            180
        ]:

            result[
                f"rolling_mean_{window}"
            ] = self._rolling_mean(
                series,
                window
            )

        # ========================================================
        # ROLLING STD
        # ========================================================

        for window in [
            3,
            7,
            28,
            56
        ]:

            result[
                f"rolling_std_{window}"
            ] = self._rolling_std(
                series,
                window
            )

        # ========================================================
        # ROLLING MAX
        # ========================================================

        for window in [
            3,
            7,
            28
        ]:

            result[
                f"rolling_max_{window}"
            ] = self._rolling_max(
                series,
                window
            )

        # ========================================================
        # EWMA
        # ========================================================

        for span in [
            3,
            7,
            14,
            28
        ]:

            result[
                f"ewma_{span}"
            ] = self._ewma(
                series,
                span
            )

        # ========================================================
        # ZERO RATIOS
        # ========================================================

        result[
            "zero_ratio_7"
        ] = self._zero_ratio(
            series,
            7
        )

        result[
            "zero_ratio_28"
        ] = self._zero_ratio(
            series,
            28
        )

        # ========================================================
        # CAMBIOS
        # ========================================================

        lag_1 = result.get(
            "lag_1"
        )

        lag_2 = result.get(
            "lag_2"
        )

        lag_3 = result.get(
            "lag_3"
        )

        lag_7 = result.get(
            "lag_7"
        )

        result[
            "change_1_2"
        ] = (
            lag_1 - lag_2
            if not (
                pd.isna(lag_1)
                or pd.isna(lag_2)
            )
            else np.nan
        )

        result[
            "change_1_3"
        ] = (
            lag_1 - lag_3
            if not (
                pd.isna(lag_1)
                or pd.isna(lag_3)
            )
            else np.nan
        )

        result[
            "change_1_7"
        ] = (
            lag_1 - lag_7
            if not (
                pd.isna(lag_1)
                or pd.isna(lag_7)
            )
            else np.nan
        )

        # ========================================================
        # RATIOS
        # ========================================================

        mean_3 = result.get(
            "rolling_mean_3"
        )

        mean_7 = result.get(
            "rolling_mean_7"
        )

        mean_14 = result.get(
            "rolling_mean_14"
        )

        mean_28 = result.get(
            "rolling_mean_28"
        )

        max_3 = result.get(
            "rolling_max_3"
        )

        max_7 = result.get(
            "rolling_max_7"
        )

        result[
            "ratio_mean3_mean14"
        ] = self._safe_divide(
            mean_3,
            mean_14
        )

        result[
            "ratio_mean7_mean28"
        ] = self._safe_divide(
            mean_7,
            mean_28
        )

        result[
            "acceleration_3_7"
        ] = (
            mean_3 - mean_7
            if not (
                pd.isna(mean_3)
                or pd.isna(mean_7)
            )
            else np.nan
        )

        result[
            "acceleration_7_28"
        ] = (
            mean_7 - mean_28
            if not (
                pd.isna(mean_7)
                or pd.isna(mean_28)
            )
            else np.nan
        )

        result[
            "max7_vs_mean28"
        ] = self._safe_divide(
            max_7,
            mean_28
        )

        result[
            "max3_vs_mean28"
        ] = self._safe_divide(
            max_3,
            mean_28
        )

        # ========================================================
        # ULTIMOS 7 VS 7 ANTERIORES
        # ========================================================

        if len(series) >= 14:

            recent_7 = (
                series.iloc[
                    -7:
                ].mean()
            )

            previous_7 = (
                series.iloc[
                    -14:-7
                ].mean()
            )

            result[
                "previous_7_mean"
            ] = float(
                previous_7
            )

            result[
                "recent7_vs_previous7"
            ] = self._safe_divide(
                recent_7,
                previous_7
            )

        else:

            result[
                "previous_7_mean"
            ] = np.nan

            result[
                "recent7_vs_previous7"
            ] = np.nan

        # ========================================================
        # PROMEDIO POR DIA DE SEMANA
        # ========================================================

        result[
            "dow_mean_4w"
        ] = self._dow_mean(
            df,
            base_date,
            4
        )

        # ========================================================
        # CRECIMIENTO
        # ========================================================

        result[
            "growth_streak_3"
        ] = self._growth_streak_3(
            series
        )

        # ========================================================
        # PICOS
        # ========================================================

        result[
            "peak_count_7"
        ] = self._peak_count_7(
            series
        )

        # ========================================================
        # INCREMENTOS
        # ========================================================

        increments = (
            self._increments(
                series
            )
        )

        for window in [
            3,
            7,
            14,
            28
        ]:

            result[
                f"rolling_inc_mean_{window}"
            ] = self._rolling_mean(
                increments,
                window
            )

        for window in [
            7,
            28
        ]:

            result[
                f"rolling_inc_std_{window}"
            ] = self._rolling_std(
                increments,
                window
            )

        # ========================================================
        # ACTIVIDAD DE VENTA
        # ========================================================

        result[
            "days_since_sale"
        ] = self._days_since_sale(
            series
        )

        result[
            "sale_rate_28"
        ] = self._sale_rate(
            series,
            28
        )

        # ========================================================
        # CURRENT VS MEAN
        # ========================================================

        current_y = result[
            "current_y"
        ]

        result[
            "current_vs_mean7"
        ] = self._safe_divide(
            current_y,
            mean_7
        )

        result[
            "current_vs_mean28"
        ] = self._safe_divide(
            current_y,
            mean_28
        )

        # ========================================================
        # FUTURE LAGS
        #
        # Para D+h:
        #
        # future_lag_7 representa el valor conocido que quedaría
        # a 7 días respecto de la fecha objetivo.
        #
        # Ejemplo:
        #
        # D+1, future_lag_7 -> observación de hace 6 días.
        # ========================================================

        future_lags = [
            7,
            14,
            21,
            28,
            35,
            42,
            364,
            365,
            366
        ]

        for lag in future_lags:

            effective_lag = (
                lag
                - horizon
            )

            if effective_lag >= 1:

                value = self._lag(
                    series,
                    effective_lag
                )

            elif effective_lag == 0:

                value = float(
                    series.iloc[-1]
                )

            else:

                # Para los horizontes actuales D1-D7,
                # solo podría ocurrir en casos no esperados.
                value = np.nan

            result[
                f"future_lag_{lag}"
            ] = value

        # ========================================================
        # FUTURE DOW
        # ========================================================

        result[
            "future_dow_mean_6w"
        ] = self._dow_mean(
            df,
            target_date,
            6
        )

        result[
            "future_dow_std_6w"
        ] = self._dow_std(
            df,
            target_date,
            6
        )

        # ========================================================
        # FEATURES TODAVIA DEPENDIENTES DE OTRAS FUENTES
        #
        # No inventamos sus valores.
        #
        # Si context las contiene, se conservan.
        # Si no, quedan como NaN temporalmente.
        # ========================================================

        pending_features = [

            # ----------------------------------------------------
            # IDENTIFICACION / JERARQUIA
            # ----------------------------------------------------

            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "state_id",

            # ----------------------------------------------------
            # EVENTOS / SNAP
            # ----------------------------------------------------

            "snap",
            "has_event",
            "event_name_1",
            "event_type_1",
            "event_name_2",
            "event_type_2",

            # ----------------------------------------------------
            # PRECIO
            # ----------------------------------------------------

            "sell_price",
            "price_available",
            "price_lag_1",
            "price_lag_7",
            "price_change_1",
            "price_change_7",
            "price_mean_28",
            "price_relative_28",
            "price_mean_180",
            "price_std_180",
            "price_min_180",
            "price_max_180",
            "price_relative_180",
            "price_to_max_180",
            "price_range_position_180",

            # ----------------------------------------------------
            # STORE
            # ----------------------------------------------------

            "store_sales_lag_1",
            "store_sales_lag_7",
            "store_sales_lag_28",
            "store_sales_mean_7",
            "store_sales_mean_28",

            # ----------------------------------------------------
            # DEPARTMENT
            # ----------------------------------------------------

            "dept_sales_lag_1",
            "dept_sales_lag_7",
            "dept_sales_lag_28",
            "dept_sales_mean_7",
            "dept_sales_mean_28",

            # ----------------------------------------------------
            # ITEM TOTAL
            # ----------------------------------------------------

            "item_total_lag_1",
            "item_total_lag_7",
            "item_total_lag_28",

            # ----------------------------------------------------
            # FUTURO
            # ----------------------------------------------------

            "future_sell_price",
            "future_price_available",
            "future_snap",
            "future_has_event",
            "future_event_name_1_code",
            "future_event_type_1_code",

            "future_store_lag_7",
            "future_dept_lag_7"
        ]

        for feature in pending_features:

            if feature not in result:

                result[
                    feature
                ] = np.nan

        return result

    # ============================================================
    # CONSTRUIR FEATURES PARA D1-D7
    # ============================================================

    def build_horizons(
        self,
        history: pd.DataFrame,
        context: Optional[
            Dict[str, Any]
        ] = None
    ) -> Dict[
        int,
        Dict[str, Any]
    ]:

        result = {}

        for horizon in range(
            1,
            8
        ):

            result[
                horizon
            ] = self.build_demand_features(
                history=
                    history,

                horizon=
                    horizon,

                context=
                    context
            )

        return result

    # ============================================================
    # VALIDAR DICCIONARIO
    # ============================================================

    def validate_features(
        self,
        data: Dict[
            str,
            Any
        ]
    ) -> None:

        if not isinstance(
            data,
            dict
        ):

            raise TypeError(
                "data debe ser un diccionario."
            )

        missing = [

            feature

            for feature
            in self.features

            if feature
            not in data
        ]

        if missing:

            raise ValueError(
                "Faltan features requeridas "
                "por LightGBM:\n\n"
                + "\n".join(
                    missing
                )
            )

    # ============================================================
    # FEATURES FALTANTES
    # ============================================================

    def missing_features(
        self,
        data: Dict[
            str,
            Any
        ]
    ) -> list[str]:

        return [

            feature

            for feature
            in self.features

            if feature
            not in data
        ]

    # ============================================================
    # FEATURES EXTRA
    # ============================================================

    def extra_features(
        self,
        data: Dict[
            str,
            Any
        ]
    ) -> list[str]:

        expected = set(
            self.features
        )

        return [

            column

            for column
            in data.keys()

            if column
            not in expected
        ]

    # ============================================================
    # UNA FILA
    # ============================================================

    def build_row(
        self,
        data: Dict[
            str,
            Any
        ]
    ) -> pd.DataFrame:

        self.validate_features(
            data
        )

        row = {

            feature:
                data[
                    feature
                ]

            for feature
            in self.features
        }

        df = pd.DataFrame(
            [
                row
            ]
        )

        return self.prepare_dataframe(
            df
        )

    # ============================================================
    # VARIAS FILAS
    # ============================================================

    def build_dataframe(
        self,
        rows: Iterable[
            Dict[
                str,
                Any
            ]
        ]
    ) -> pd.DataFrame:

        rows = list(
            rows
        )

        if not rows:

            raise ValueError(
                "No se recibieron filas "
                "para construir features."
            )

        df = pd.DataFrame(
            rows
        )

        return self.prepare_dataframe(
            df
        )

    # ============================================================
    # PREPARAR DATAFRAME
    # ============================================================

    def prepare_dataframe(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        if not isinstance(
            df,
            pd.DataFrame
        ):

            raise TypeError(
                "df debe ser un pandas.DataFrame."
            )

        if df.empty:

            raise ValueError(
                "El DataFrame está vacío."
            )

        df = df.copy()

        # --------------------------------------------------------
        # VALIDAR COLUMNAS
        # --------------------------------------------------------

        missing = [

            feature

            for feature
            in self.features

            if feature
            not in df.columns
        ]

        if missing:

            raise ValueError(
                "El DataFrame no contiene "
                "todas las features requeridas:\n\n"
                + "\n".join(
                    missing
                )
            )

        # --------------------------------------------------------
        # ORDEN EXACTO DEL ENTRENAMIENTO
        # --------------------------------------------------------

        df = df[
            self.features
        ].copy()

        categorical_set = set(
            self.categorical_features
        )

        # --------------------------------------------------------
        # CATEGORICAS
        # --------------------------------------------------------

        for column in (
            self.categorical_features
        ):

            if column not in df.columns:

                continue

            df[
                column
            ] = (
                df[
                    column
                ]
                .astype(
                    "category"
                )
            )

        # --------------------------------------------------------
        # NUMERICAS
        # --------------------------------------------------------

        numerical_columns = [

            column

            for column
            in self.features

            if column
            not in categorical_set
        ]

        for column in numerical_columns:

            df[
                column
            ] = pd.to_numeric(
                df[
                    column
                ],
                errors="coerce"
            )

        # --------------------------------------------------------
        # INFINITOS -> NaN
        # --------------------------------------------------------

        df.replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan,
            inplace=True
        )

        return df

    # ============================================================
    # INFO
    # ============================================================

    def info(
        self
    ) -> dict:

        return {

            "feature_count":
                len(
                    self.features
                ),

            "categorical_feature_count":
                len(
                    self.categorical_features
                ),

            "features":
                self.features,

            "categorical_features":
                self.categorical_features
        }