"""Simulador de sensores PsiTwin (ESP32 de equipos de frío).

Publica por MQTT, cada 0,5 s y para cada dispositivo, un mensaje en
`psitwin/dispositivos/{id}/lecturas` con el formato del contrato
(docs/SENSORES.md del frontend):

    {"token": "...", "ts": "...Z", "t_int": 3.6, "puerta": false,
     "t_amb": 22.1, "hum": 55.0, "corriente": 2.4}

Escenarios (se ejecutan una vez y luego el equipo sigue en `normal`):

    normal           valores dentro de rango
    tienda           vitrina: abre la puerta 3 s cada 6 s durante ~4 min
                     (supera 30 aperturas/h)
    falla_compresor  la corriente cae y t_int sube (~3,5 min); luego se
                     recupera
    puerta_olvidada  puerta abierta --abierta-s segundos (default 30)
    desconexion      deja de publicar --silencio-s segundos (default 15)

Uso:

    .venv/bin/python tools/simulador_sensores.py \\
        --archivo ~/Documentos/PsiTwin_dispositivos_demo.json \\
        --escenario falla_compresor --solo "Cámara Fría"

    # o sin archivo:
    .venv/bin/python tools/simulador_sensores.py \\
        --dispositivo <id>:<token> --escenario normal

El archivo es el JSON con {"broker": {...}, "dispositivos":
[{"id_dispositivo", "nombre", "token"}]} que se guarda al registrar
los dispositivos (fuera del repo: contiene tokens).
"""

import argparse
import asyncio
import json
import random
import sys

from datetime import datetime, timezone
from pathlib import Path

import aiomqtt


PERIODO_S = 0.5


# ============================================================
# ESCENARIOS
#
# Cada escenario es una función f(t, base) -> lectura | None.
#   t:    segundos desde el inicio del escenario
#   base: valores normales del equipo
# None = no publicar en ese instante (desconexión).
# Devuelven también si el escenario terminó.
# ============================================================

def _ruido(valor, amplitud):
    return round(valor + random.uniform(-amplitud, amplitud), 2)


def normal(t, base, args):
    return {
        "t_int": _ruido(base["t_int"], 0.2),
        "puerta": False,
        "t_amb": _ruido(base["t_amb"], 0.3),
        "hum": _ruido(base["hum"], 1.5),
        "corriente": _ruido(base["corriente"], 0.15),
    }, True


def tienda(t, base, args):
    lectura, _ = normal(t, base, args)
    duracion = 240
    abierta = t < duracion and (t % 6) < 3
    lectura["puerta"] = abierta
    if abierta:
        lectura["t_int"] = _ruido(base["t_int"] + 0.6, 0.2)
    return lectura, t >= duracion


def falla_compresor(t, base, args):
    lectura, _ = normal(t, base, args)
    inicio, fin_falla, fin = 10, 220, 270
    if inicio <= t < fin_falla:
        # compresor detenido: corriente casi nula, t_int sube
        lectura["corriente"] = _ruido(0.2, 0.05)
        lectura["t_int"] = round(base["t_int"] + 0.03 * (t - inicio), 2)
    elif fin_falla <= t < fin:
        # vuelve a arrancar: enfría hasta la base
        pico = base["t_int"] + 0.03 * (fin_falla - inicio)
        lectura["t_int"] = round(max(base["t_int"], pico - 0.2 * (t - fin_falla)), 2)
    return lectura, t >= fin


def puerta_olvidada(t, base, args):
    lectura, _ = normal(t, base, args)
    inicio = 5
    fin = inicio + args.abierta_s
    lectura["puerta"] = inicio <= t < fin
    return lectura, t >= fin + 5


def desconexion(t, base, args):
    inicio = 10
    fin = inicio + args.silencio_s
    if inicio <= t < fin:
        return None, False
    lectura, _ = normal(t, base, args)
    return lectura, t >= fin + 5


ESCENARIOS = {
    "normal": normal,
    "tienda": tienda,
    "falla_compresor": falla_compresor,
    "puerta_olvidada": puerta_olvidada,
    "desconexion": desconexion,
}


# ============================================================
# PUBLICACION
# ============================================================

async def simular(args, dispositivos, broker):
    escenario = ESCENARIOS[args.escenario]
    base = {
        "t_int": args.t_int,
        "t_amb": args.t_amb,
        "hum": args.hum,
        "corriente": args.corriente,
    }

    async with aiomqtt.Client(
        hostname=broker["host"],
        port=int(broker["port"]),
        username=broker["usuario"],
        password=broker["password"],
    ) as cliente:

        nombres = ", ".join(d.get("nombre", d["id_dispositivo"]) for d in dispositivos)
        print(f"[simulador] {args.escenario} -> {nombres}", flush=True)

        terminado = False
        loop = asyncio.get_running_loop()
        t0 = loop.time()

        while True:
            t = loop.time() - t0

            if args.duracion and t >= args.duracion:
                break

            if terminado:
                lectura, _ = normal(t, base, args)
            else:
                lectura, terminado = escenario(t, base, args)
                if terminado:
                    print(f"[simulador] escenario {args.escenario} terminado "
                          f"({t:.0f} s); sigue en normal", flush=True)

            if lectura is not None:
                ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                for dispositivo in dispositivos:
                    await cliente.publish(
                        f"psitwin/dispositivos/{dispositivo['id_dispositivo']}/lecturas",
                        json.dumps({
                            "token": dispositivo["token"],
                            "ts": ts.replace("+00:00", "Z"),
                            **lectura,
                        }),
                    )

            await asyncio.sleep(PERIODO_S)


def cargar(args):
    broker = {
        "host": args.host,
        "port": args.port,
        "usuario": args.usuario,
        "password": args.password,
    }
    dispositivos = []

    if args.archivo:
        data = json.loads(Path(args.archivo).expanduser().read_text(encoding="utf-8"))
        broker.update({k: v for k, v in (data.get("broker") or {}).items() if v})
        dispositivos += data.get("dispositivos", [])

    for valor in args.dispositivo or []:
        id_dispositivo, _, token = valor.partition(":")
        dispositivos.append({"id_dispositivo": id_dispositivo, "token": token})

    if args.solo:
        filtro = args.solo.lower()
        dispositivos = [
            d for d in dispositivos
            if filtro in d.get("nombre", "").lower() or d["id_dispositivo"].startswith(args.solo)
        ]

    if not dispositivos:
        sys.exit("No hay dispositivos: use --archivo o --dispositivo ID:TOKEN")

    return broker, dispositivos


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensores PsiTwin (MQTT)")
    parser.add_argument("--archivo", help="JSON con broker y dispositivos (id, nombre, token)")
    parser.add_argument("--dispositivo", action="append", help="ID:TOKEN (repetible)")
    parser.add_argument("--solo", help="filtra por nombre (contiene) o prefijo de id")
    parser.add_argument("--escenario", choices=sorted(ESCENARIOS), default="normal")
    parser.add_argument("--duracion", type=float, default=0, help="segundos totales (0 = sin fin)")
    parser.add_argument("--abierta-s", type=float, default=30, help="puerta_olvidada")
    parser.add_argument("--silencio-s", type=float, default=15, help="desconexion")
    parser.add_argument("--t-int", type=float, default=3.5)
    parser.add_argument("--t-amb", type=float, default=22.0)
    parser.add_argument("--hum", type=float, default=55.0)
    parser.add_argument("--corriente", type=float, default=2.5)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--usuario", default="psitwin-dispositivo")
    parser.add_argument("--password", default="dispositivo-dev-123")
    args = parser.parse_args()

    broker, dispositivos = cargar(args)

    async def con_reintentos():
        # Como un ESP32: si el broker se cae, reintenta cada 2 s.
        while True:
            try:
                await simular(args, dispositivos, broker)
                return
            except aiomqtt.MqttError as exc:
                print(f"[simulador] broker no disponible ({exc}); reintento en 2 s", flush=True)
                await asyncio.sleep(2)

    try:
        asyncio.run(con_reintentos())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
