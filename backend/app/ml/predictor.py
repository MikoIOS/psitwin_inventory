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

from app.ml.feature_builder import (
    FeatureBuilder
)


class DemandPredictor:
    """
    Predictor de demanda de PsiTwin.

    Utiliza modelos LightGBM Direct Horizon:

        D+1
        D+2
        D+3
        D+4
        D+5
        D+6
        D+7

    Actualmente ejecuta el modelo GLOBAL de
    cada horizonte.

    Posteriormente se incorporará la misma lógica
    global/local/selection utilizada durante
    el entrenamiento.
    """

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        loader: Optional[
            ModelLoader
        ] = None
    ) -> None:

        if loader is None:

            self.loader = (
                ModelLoader()
            )

        else:

            self.loader = loader

        # Cargar configuración y modelos
        self.loader.load_all()

        # Constructor de features
        self.feature_builder = (
            FeatureBuilder(
                self.loader
            )
        )

    # ========================================================
    # PREDICCION D+N
    # ========================================================

    def predict_horizon(
        self,
        features: Dict[
            str,
            Any
        ],
        horizon: int
    ) -> float:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # ----------------------------------------------------
        # FEATURES
        # ----------------------------------------------------

        X = (
            self.feature_builder
            .build_row(
                features
            )
        )

        # ----------------------------------------------------
        # MODELO
        # ----------------------------------------------------

        model = (
            self.loader
            .get_global_model(
                horizon
            )
        )

        # ----------------------------------------------------
        # PREDICCION
        # ----------------------------------------------------

        try:

            prediction = (
                model.predict(
                    X
                )
            )

        except Exception as exc:

            raise RuntimeError(
                "Error realizando la "
                f"predicción D+{horizon}.\n\n"
                f"Error original: {exc}"
            ) from exc

        if prediction is None:

            raise RuntimeError(
                "LightGBM devolvió None."
            )

        if len(prediction) == 0:

            raise RuntimeError(
                "LightGBM no devolvió "
                "predicciones."
            )

        value = float(
            prediction[0]
        )

        # No permitir demanda negativa
        return max(
            0.0,
            value
        )

    # ========================================================
    # D+1 ... D+7
    # ========================================================

    def predict_7_days(
        self,
        features_by_horizon: Dict[
            int,
            Dict[str, Any]
        ],
        start_date: Optional[
            date | datetime
        ] = None
    ) -> dict:

        # ----------------------------------------------------
        # FECHA BASE
        # ----------------------------------------------------

        if start_date is None:

            base_date = (
                datetime.now()
                .date()
            )

        elif isinstance(
            start_date,
            datetime
        ):

            base_date = (
                start_date.date()
            )

        elif isinstance(
            start_date,
            date
        ):

            base_date = start_date

        else:

            raise TypeError(
                "start_date debe ser "
                "date, datetime o None."
            )

        # ----------------------------------------------------
        # RESULTADOS
        # ----------------------------------------------------

        predictions = []

        total_7d = 0.0

        # ----------------------------------------------------
        # D1 ... D7
        # ----------------------------------------------------

        for horizon in range(
            1,
            8
        ):

            if (
                horizon
                not in features_by_horizon
            ):

                raise ValueError(
                    "No se proporcionaron "
                    f"features para D+{horizon}."
                )

            features = (
                features_by_horizon[
                    horizon
                ]
            )

            predicted_demand = (
                self.predict_horizon(
                    features=features,
                    horizon=horizon
                )
            )

            prediction_date = (
                base_date
                + timedelta(
                    days=horizon
                )
            )

            predictions.append(
                {
                    "horizonte":
                        horizon,

                    "fecha":
                        prediction_date
                        .isoformat(),

                    "demanda_predicha":
                        round(
                            predicted_demand,
                            4
                        )
                }
            )

            total_7d += (
                predicted_demand
            )

        return {

            "demanda_7d":
                round(
                    total_7d,
                    4
                ),

            "predicciones_diarias":
                predictions
        }

    # ========================================================
    # DATAFRAME COMPLETO
    # ========================================================

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        horizon: int
    ) -> np.ndarray:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # Preparar features
        X = (
            self.feature_builder
            .prepare_dataframe(
                df
            )
        )

        # Obtener modelo
        model = (
            self.loader
            .get_global_model(
                horizon
            )
        )

        # Predecir
        predictions = (
            model.predict(
                X
            )
        )

        # Evitar valores negativos
        predictions = np.maximum(
            predictions,
            0
        )

        return predictions

    # ========================================================
    # BATCH
    # ========================================================

    def predict_batch(
        self,
        rows: Iterable[
            Dict[str, Any]
        ],
        horizon: int
    ) -> list[float]:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        X = (
            self.feature_builder
            .build_dataframe(
                rows
            )
        )

        model = (
            self.loader
            .get_global_model(
                horizon
            )
        )

        predictions = (
            model.predict(
                X
            )
        )

        predictions = np.maximum(
            predictions,
            0
        )

        return [
            float(value)
            for value in predictions
        ]

    # ========================================================
    # INFO
    # ========================================================

    def info(
        self
    ) -> dict:

        loader_info = (
            self.loader.info()
        )

        return {

            **loader_info,

            "forecast_horizon":
                7,

            "prediction_mode":
                "direct_horizon",

            "current_model_mode":
                "global"
        }