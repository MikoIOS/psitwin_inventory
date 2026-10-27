"""Motor de alertas de sensores: máquina de estados con reloj inyectable (sin broker)."""

import unittest
from datetime import datetime, timedelta, timezone

from app.services.sensores.motor_alertas import MotorAlertas


class Reloj:

    def __init__(self):
        self.t = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def avanzar(self, segundos):
        self.t += timedelta(seconds=segundos)


LIMITES = {
    "t_int": {"min": 2, "max": 6, "duracion_s": 120},
    "corriente": {"min": 1, "max": 5, "duracion_s": 30},
    "puerta": {"max_abierta_s": 20, "max_aperturas_hora": 3},
}


def nuevo(vigilar=False):
    reloj = Reloj()
    motor = MotorAlertas(reloj)
    motor.configurar("d1", LIMITES, vigilar_conexion=vigilar)
    return motor, reloj


def enviar(motor, reloj, segundos, cada=0.5, **lectura):
    """Simula `segundos` de lecturas cada `cada` s; devuelve los eventos."""
    eventos = []
    for _ in range(int(segundos / cada)):
        reloj.avanzar(cada)
        eventos += motor.procesar("d1", lectura)
    return eventos


class RangoTests(unittest.TestCase):

    def test_excursion_corta_no_alerta(self):
        motor, reloj = nuevo()
        eventos = enviar(motor, reloj, 100, t_int=8.0)
        eventos += enviar(motor, reloj, 10, t_int=4.0)
        self.assertEqual(eventos, [])

    def test_abre_tras_duracion_y_una_sola_vez(self):
        motor, reloj = nuevo()
        eventos = enviar(motor, reloj, 300, t_int=8.0)
        self.assertEqual([e.evento for e in eventos], ["ABIERTA"])
        e = eventos[0]
        self.assertEqual((e.tipo, e.parametro, e.limite), ("TEMPERATURA_FUERA_RANGO", "t_int", 6))
        self.assertAlmostEqual((reloj() - e.inicio).total_seconds(), 300 - 0.5)

    def test_histeresis_y_valor_extremo(self):
        motor, reloj = nuevo()
        enviar(motor, reloj, 125, t_int=8.0)
        enviar(motor, reloj, 5, t_int=9.5)
        # dentro del rango pero sin margen (5.8 > 6 - 0.5): sigue abierta
        self.assertEqual(enviar(motor, reloj, 5, t_int=5.8), [])
        eventos = enviar(motor, reloj, 1, t_int=5.0)
        self.assertEqual(len(eventos), 1)
        e = eventos[0]
        self.assertEqual(e.evento, "RESUELTA")
        self.assertEqual(e.valor_extremo, 9.5)
        self.assertAlmostEqual(e.duracion_s, 135.0, places=1)

    def test_por_debajo_del_minimo_extremo_minimo(self):
        motor, reloj = nuevo()
        enviar(motor, reloj, 31, corriente=0.5)
        enviar(motor, reloj, 2, corriente=0.1)
        eventos = enviar(motor, reloj, 1, corriente=2.0)
        self.assertEqual(eventos[0].evento, "RESUELTA")
        self.assertEqual(eventos[0].valor_extremo, 0.1)
        self.assertEqual(eventos[0].limite, 1)

    def test_null_no_cambia_estado(self):
        motor, reloj = nuevo()
        enviar(motor, reloj, 60, t_int=8.0)
        enviar(motor, reloj, 100, t_int=None)
        eventos = enviar(motor, reloj, 1, t_int=8.0)
        self.assertEqual([e.evento for e in eventos], ["ABIERTA"])


class PuertaTests(unittest.TestCase):

    def test_puerta_abierta_y_cierre(self):
        motor, reloj = nuevo()
        eventos = enviar(motor, reloj, 30, puerta=True)
        self.assertEqual([(e.evento, e.tipo) for e in eventos], [("ABIERTA", "PUERTA_ABIERTA")])
        eventos = enviar(motor, reloj, 1, puerta=False)
        self.assertEqual([(e.evento, e.tipo) for e in eventos], [("RESUELTA", "PUERTA_ABIERTA")])
        self.assertAlmostEqual(eventos[0].duracion_s, 30.0, places=1)

    def test_aperturas_excesivas_ventana_movil(self):
        motor, reloj = nuevo()
        eventos = []
        for _ in range(4):
            eventos += enviar(motor, reloj, 2, puerta=True)
            eventos += enviar(motor, reloj, 2, puerta=False)
        self.assertEqual([(e.evento, e.tipo, e.valor) for e in eventos],
                         [("ABIERTA", "APERTURAS_EXCESIVAS", 4)])
        # una hora después (con la puerta cerrada) la ventana se vacía
        eventos = enviar(motor, reloj, 3600, cada=1, puerta=False)
        self.assertEqual([(e.evento, e.tipo) for e in eventos], [("RESUELTA", "APERTURAS_EXCESIVAS")])


class ConexionTests(unittest.TestCase):

    def test_sin_datos_y_vuelta(self):
        motor, reloj = nuevo()
        reloj.avanzar(60)
        self.assertEqual(motor.tick(), [], "nunca envió datos: no se vigila")
        enviar(motor, reloj, 1, t_int=4.0)
        reloj.avanzar(4)
        self.assertEqual(motor.tick(), [])
        reloj.avanzar(2)
        eventos = motor.tick()
        self.assertEqual([(e.evento, e.tipo) for e in eventos], [("ABIERTA", "SENSOR_SIN_DATOS")])
        self.assertEqual(motor.tick(), [], "una alerta por episodio")
        eventos = enviar(motor, reloj, 0.5, t_int=4.0)
        self.assertEqual([(e.evento, e.tipo) for e in eventos], [("RESUELTA", "SENSOR_SIN_DATOS")])

    def test_vigilar_conexion_al_arrancar(self):
        motor, reloj = nuevo(vigilar=True)
        reloj.avanzar(6)
        self.assertEqual([e.tipo for e in motor.tick()], ["SENSOR_SIN_DATOS"])


class RestaurarTests(unittest.TestCase):

    def test_alerta_restaurada_no_se_duplica_y_se_resuelve(self):
        motor, reloj = nuevo()
        motor.restaurar("d1", "t_int", reloj() - timedelta(minutes=10), valor_extremo=9.0, limite=6)
        self.assertEqual(enviar(motor, reloj, 300, t_int=8.0), [])
        eventos = enviar(motor, reloj, 1, t_int=4.0)
        self.assertEqual([e.evento for e in eventos], ["RESUELTA"])
        self.assertEqual(eventos[0].valor_extremo, 9.0)


if __name__ == "__main__":
    unittest.main()
