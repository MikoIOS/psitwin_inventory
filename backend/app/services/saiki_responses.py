"""Conversational rendering of verified tool results; no business calculations."""
import math


def number(value):
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return f"{value:g}"


def operational_answer(kind, rows):
    count = len(rows)
    if kind == "alerts":
        if count >= 1000:
            return 'Hay al menos 1000 alertas activas. Se muestran hasta 1000 registros; acota la consulta por inventario o sensor.'
        level = str(rows[0].get("nivel_riesgo", "")).lower() if count == 1 else ""
        detail = f" de riesgo {level}" if level in {"bajo", "medio", "alto", "critico"} else ""
        return "No tienes alertas activas." if not count else f"Tienes {count} alerta{'s' if count != 1 else ''} activa{'s' if count != 1 else ''}{detail}. Puedes consultar los detalles en los datos adjuntos."
    if kind == "movements":
        if not count:
            return "No encontré movimientos recientes."
        quantity = number(rows[0].get("cantidad"))
        movement = rows[0].get("tipo_movimiento")
        if count == 1 and quantity is not None and movement in {"SALIDA", "ENTRADA"}:
            return f"Encontré un movimiento reciente: una {movement.lower()} de {quantity} {'unidad' if quantity == '1' else 'unidades'}."
        return f"Encontré {count} movimiento{'s' if count != 1 else ''} reciente{'s' if count != 1 else ''}. Los detalles están disponibles en la respuesta."
    if kind == "recommendations":
        pending = [row for row in rows if row.get("estado") in {"PENDIENTE", "VALIDADA_OPERARIO", "CAMBIOS_SOLICITADOS", "APROBADA_EMPRESA", "ACEPTADA"}]
        if not pending:
            return "No hay recomendaciones pendientes de reposición registradas."
        if len(pending) == 1 and number(pending[0].get("cantidad_recomendada")) is not None:
            return f"La recomendación registrada propone reponer {number(pending[0]['cantidad_recomendada'])} unidades. Revisa el producto y los detalles antes de iniciar una compra."
        return f"Tienes {len(pending)} {'recomendación pendiente' if len(pending) == 1 else 'recomendaciones pendientes'}. Revisa las cantidades propuestas antes de iniciar una compra."
    raise ValueError("Unsupported operational answer")


def forecast_answer(result):
    horizon = result.get("horizonte_dias", 7)
    if result.get('estado') == 'CALCULANDO':
        return 'PsiTwin está calculando el pronóstico real. Puedes consultar el progreso en Análisis; todavía no hay una estimación válida.'
    if result.get("estado") != "DISPONIBLE":
        return f"Pronóstico de {horizon} días no disponible: {result.get('estado', 'NO_DISPONIBLE')}. No hay una estimación válida."
    total = number(result.get("demanda_total_estimada"))
    return f"La demanda estimada agregada del producto en el almacén para {horizon} días es {total} unidades. La proyección está sujeta a incertidumbre."

def risk_answer(results):
    levels = {"BAJO": 0, "MEDIO": 1, "ALTO": 2, "CRITICO": 3}
    valid = [row for row in results if (row.get("riesgo") or {}).get("nivel") in levels]
    if not valid:
        return "No pude obtener un nivel de riesgo verificado con los datos disponibles."
    highest = max(valid, key=lambda row: levels[row["riesgo"]["nivel"]])
    level = highest["riesgo"]["nivel"].lower().replace("critico", "crítico")
    stock = number(highest.get("stock_actual"))
    coverage = number(highest.get("cobertura", {}).get("dias"))
    lead = number(highest.get("lead_time_dias"))
    reason = ""
    if stock == "0":
        reason = " porque no quedan existencias"
    elif coverage is not None and lead is not None:
        reason = f": la cobertura es de {coverage} {'día' if coverage == '1' else 'días'} y la reposición tarda {lead} {'día' if lead == '1' else 'días'}"
    count = sum(row["riesgo"]["nivel"] in {"ALTO", "CRITICO"} for row in valid)
    prefix = f"Hay {count} producto{'s' if count != 1 else ''} con riesgo alto o crítico. " if len(valid) > 1 else ""
    subject = f" de {highest['nombre_producto']}" if highest.get("nombre_producto") else " calculado"
    return prefix + f"El riesgo{subject} es {level}{reason}."
