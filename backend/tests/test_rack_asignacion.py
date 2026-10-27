"""Reglas de asignación producto -> rack (kg, estado, temperatura)."""

import unittest

from app.services.rack_service import RackService

RACK = {
    "id_rack": "r1",
    "codigo": "F-01",
    "estado": "DISPONIBLE",
    "temperatura_min": 2,
    "temperatura_max": 6,
    "libre_kg": 100,
}

YOGURT = {
    "peso": 1.05,
    "requiere_refrigeracion": True,
    "temperatura_min_almacenamiento": 2,
    "temperatura_max_almacenamiento": 8,
}


class RackAsignacionTests(unittest.TestCase):

    def test_cabe(self):
        assert RackService.motivo_no_cabe(RACK, YOGURT, 60) is None


    def test_excede_kg(self):
        assert "Capacidad insuficiente" in RackService.motivo_no_cabe(RACK, YOGURT, 120)


    def test_rack_no_disponible(self):
        rack = {**RACK, "estado": "MANTENIMIENTO"}
        assert "no está DISPONIBLE" in RackService.motivo_no_cabe(rack, YOGURT, 1)


    def test_temperatura_fuera_de_rango(self):
        rack = {**RACK, "temperatura_min": -5, "temperatura_max": 0}
        assert "no cabe" in RackService.motivo_no_cabe(rack, YOGURT, 1)


    def test_refrigerado_en_rack_sin_temperatura(self):
        rack = {**RACK, "temperatura_min": None, "temperatura_max": None}
        assert "no tiene temperatura" in RackService.motivo_no_cabe(rack, YOGURT, 1)


    def test_producto_seco_sin_peso_no_carga(self):
        assert RackService.motivo_no_cabe({**RACK, "libre_kg": 0}, {}, 500) is None
