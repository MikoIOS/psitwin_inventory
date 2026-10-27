from __future__ import annotations

import json

from pathlib import Path
from typing import Any, Dict, Optional

import lightgbm as lgb
import pandas as pd


class ModelLoader:
    """
    Carga los artefactos del modelo LightGBM de PsiTwin.

    Estructura esperada:

    app/
    └── ml/
        └── models/
            └── psitwin_v3_6/
                ├── config_v3_6.json
                ├── selection_by_horizon.csv
                │
                └── models/
                    ├── ...global_D1.txt
                    ├── ...global_D2.txt
                    ├── ...
                    └── ...global_D7.txt
    """

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        model_dir: Optional[
            str | Path
        ] = None
    ) -> None:

        # ----------------------------------------------------
        # RUTA PRINCIPAL
        # ----------------------------------------------------

        if model_dir is None:

            self.model_dir = (
                Path(__file__)
                .resolve()
                .parent
                / "models"
                / "psitwin_v3_6"
            )

        else:

            self.model_dir = Path(
                model_dir
            ).resolve()

        # ----------------------------------------------------
        # ARCHIVOS
        # ----------------------------------------------------

        self.config_path = (
            self.model_dir
            / "config_v3_6.json"
        )

        self.selection_path = (
            self.model_dir
            / "selection_by_horizon.csv"
        )

        self.models_dir = (
            self.model_dir
            / "models"
        )

        # ----------------------------------------------------
        # DATOS CARGADOS
        # ----------------------------------------------------

        self.config: Dict[
            str,
            Any
        ] = {}

        self.selection: Optional[
            pd.DataFrame
        ] = None

        self.global_models: Dict[
            int,
            lgb.Booster
        ] = {}

        self.local_models: Dict[
            str,
            lgb.Booster
        ] = {}

        self._loaded = False

    # ========================================================
    # VALIDAR ESTRUCTURA
    # ========================================================

    def validate_paths(
        self
    ) -> None:

        if not self.model_dir.exists():

            raise FileNotFoundError(
                "No existe la carpeta principal "
                "del modelo:\n"
                f"{self.model_dir}"
            )

        if not self.config_path.exists():

            raise FileNotFoundError(
                "No se encontró "
                "config_v3_6.json:\n"
                f"{self.config_path}"
            )

        if not self.selection_path.exists():

            raise FileNotFoundError(
                "No se encontró "
                "selection_by_horizon.csv:\n"
                f"{self.selection_path}"
            )

        if not self.models_dir.exists():

            raise FileNotFoundError(
                "No se encontró la carpeta "
                "de modelos:\n"
                f"{self.models_dir}"
            )

    # ========================================================
    # CARGAR CONFIG
    # ========================================================

    def load_config(
        self
    ) -> Dict[str, Any]:

        if not self.config_path.exists():

            raise FileNotFoundError(
                f"No existe: "
                f"{self.config_path}"
            )

        with self.config_path.open(
            mode="r",
            encoding="utf-8"
        ) as file:

            self.config = json.load(
                file
            )

        return self.config

    # ========================================================
    # CARGAR SELECCION
    # ========================================================

    def load_selection(
        self
    ) -> pd.DataFrame:

        if not self.selection_path.exists():

            raise FileNotFoundError(
                f"No existe: "
                f"{self.selection_path}"
            )

        self.selection = pd.read_csv(
            self.selection_path
        )

        return self.selection

    # ========================================================
    # BUSCAR MODELO GLOBAL
    # ========================================================

    def _find_global_model(
        self,
        horizon: int
    ) -> Path:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # Primero intentamos el patrón
        # utilizado por el notebook.
        pattern = (
            f"*__global_D{horizon}.txt"
        )

        matches = sorted(
            self.models_dir.glob(
                pattern
            )
        )

        # Fallback por si el nombre cambia
        if not matches:

            pattern = (
                f"*global*D{horizon}.txt"
            )

            matches = sorted(
                self.models_dir.glob(
                    pattern
                )
            )

        if not matches:

            raise FileNotFoundError(
                "No se encontró un modelo "
                f"global para D+{horizon}.\n"
                f"Carpeta buscada:\n"
                f"{self.models_dir}"
            )

        if len(matches) > 1:

            print(
                "[ADVERTENCIA] "
                f"Se encontraron {len(matches)} "
                f"modelos globales para D+{horizon}."
            )

            print(
                "[ADVERTENCIA] "
                f"Se utilizará: "
                f"{matches[0].name}"
            )

        return matches[0]

    # ========================================================
    # CARGAR UN MODELO GLOBAL
    # ========================================================

    def load_global_model(
        self,
        horizon: int
    ) -> lgb.Booster:

        if horizon in self.global_models:

            return self.global_models[
                horizon
            ]

        model_path = (
            self._find_global_model(
                horizon
            )
        )

        try:

            model = lgb.Booster(
                model_file=str(
                    model_path
                )
            )

        except Exception as exc:

            raise RuntimeError(
                "No se pudo cargar el modelo "
                f"LightGBM D+{horizon}:\n"
                f"{model_path}\n\n"
                f"Error original: {exc}"
            ) from exc

        self.global_models[
            horizon
        ] = model

        return model

    # ========================================================
    # CARGAR D1 ... D7
    # ========================================================

    def load_global_models(
        self
    ) -> Dict[int, lgb.Booster]:

        for horizon in range(
            1,
            8
        ):

            self.load_global_model(
                horizon
            )

        return self.global_models

    # ========================================================
    # MODELO LOCAL
    # ========================================================

    def load_local_model(
        self,
        model_name: str
    ) -> lgb.Booster:

        if not model_name:

            raise ValueError(
                "model_name no puede "
                "estar vacío."
            )

        if model_name in self.local_models:

            return self.local_models[
                model_name
            ]

        model_path = (
            self.models_dir
            / model_name
        )

        if not model_path.exists():

            raise FileNotFoundError(
                "Modelo local no encontrado:\n"
                f"{model_path}"
            )

        try:

            model = lgb.Booster(
                model_file=str(
                    model_path
                )
            )

        except Exception as exc:

            raise RuntimeError(
                "No se pudo cargar el modelo "
                f"local:\n{model_path}\n\n"
                f"Error original: {exc}"
            ) from exc

        self.local_models[
            model_name
        ] = model

        return model

    # ========================================================
    # FEATURES
    # ========================================================

    def get_features(
        self
    ) -> list[str]:

        if not self.config:

            self.load_config()

        features = self.config.get(
            "features"
        )

        if features is None:

            raise KeyError(
                "config_v3_6.json no contiene "
                "la clave 'features'."
            )

        if not isinstance(
            features,
            list
        ):

            raise TypeError(
                "'features' debe ser una lista."
            )

        return features

    # ========================================================
    # CATEGORICAL FEATURES
    # ========================================================

    def get_categorical_features(
        self
    ) -> list[str]:

        if not self.config:

            self.load_config()

        categorical = self.config.get(
            "categorical_features",
            []
        )

        if categorical is None:

            return []

        if not isinstance(
            categorical,
            list
        ):

            raise TypeError(
                "'categorical_features' "
                "debe ser una lista."
            )

        return categorical

    # ========================================================
    # SELECCION POR HORIZONTE
    # ========================================================

    def get_selection_for_horizon(
        self,
        horizon: int
    ) -> Optional[dict]:

        if self.selection is None:

            self.load_selection()

        if self.selection is None:
            return None

        # Intentamos encontrar automáticamente
        # la columna que representa el horizonte.

        possible_columns = [
            "horizon",
            "h",
            "H",
            "horizonte"
        ]

        horizon_column = None

        for column in possible_columns:

            if column in self.selection.columns:

                horizon_column = column
                break

        if horizon_column is None:

            return None

        rows = self.selection[
            self.selection[
                horizon_column
            ] == horizon
        ]

        if rows.empty:

            return None

        return rows.iloc[
            0
        ].to_dict()

    # ========================================================
    # CARGAR TODO
    # ========================================================

    def load_all(
        self
    ) -> None:

        if self._loaded:
            return

        self.validate_paths()

        self.load_config()

        self.load_selection()

        self.load_global_models()

        self._loaded = True

    # ========================================================
    # OBTENER MODELO
    # ========================================================

    def get_global_model(
        self,
        horizon: int
    ) -> lgb.Booster:

        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        if horizon not in self.global_models:

            self.load_global_model(
                horizon
            )

        return self.global_models[
            horizon
        ]

    # ========================================================
    # INFO
    # ========================================================

    def info(
        self
    ) -> dict:

        if not self.config:

            self.load_config()

        if self.selection is None:

            self.load_selection()

        return {

            "model_dir":
                str(
                    self.model_dir
                ),

            "models_dir":
                str(
                    self.models_dir
                ),

            "version":
                self.config.get(
                    "version",
                    "desconocida"
                ),

            "dataset":
                self.config.get(
                    "dataset",
                    "desconocido"
                ),

            "feature_count":
                len(
                    self.get_features()
                ),

            "categorical_feature_count":
                len(
                    self.get_categorical_features()
                ),

            "global_models_loaded":
                sorted(
                    self.global_models.keys()
                ),

            "selection_rows":
                (
                    len(self.selection)
                    if self.selection
                    is not None
                    else 0
                )
        }