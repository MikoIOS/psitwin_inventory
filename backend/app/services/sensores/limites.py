# app/services/sensores/limites.py

from typing import (
    Any,
    Dict,
    Optional
)

from app.services.sensores.motor_alertas import (
    DURACIONES_DEFAULT,
    MAX_ABIERTA_DEFAULT_S
)


# ============================================================
# LIMITES EFECTIVOS
#
# - t_int sin min/max y dispositivo ligado a un rack con
#   temperatura -> se usan temperatura_min/max del rack
#   (origen: "rack").
# - duracion_s por defecto: t_int 120, t_amb 300, hum 300,
#   corriente 30.
# - puerta.max_abierta_s por defecto 60.
# ============================================================

def limites_efectivos(
    limites: Optional[Dict[str, Any]],
    rack: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    limites = limites or {}

    resultado: Dict[str, Any] = {}

    for parametro, duracion in DURACIONES_DEFAULT.items():

        config = dict(
            limites.get(parametro) or {}
        )

        if (
            parametro == "t_int"
            and config.get("min") is None
            and config.get("max") is None
            and rack
            and rack.get("temperatura_min") is not None
            and rack.get("temperatura_max") is not None
        ):

            config["min"] = rack["temperatura_min"]
            config["max"] = rack["temperatura_max"]
            config["origen"] = "rack"

        if config.get("duracion_s") is None:
            config["duracion_s"] = duracion

        config.setdefault("min", None)
        config.setdefault("max", None)

        resultado[parametro] = config

    puerta = dict(
        limites.get("puerta") or {}
    )

    if puerta.get("max_abierta_s") is None:
        puerta["max_abierta_s"] = MAX_ABIERTA_DEFAULT_S

    puerta.setdefault(
        "max_aperturas_hora",
        None
    )

    resultado["puerta"] = puerta

    return resultado
