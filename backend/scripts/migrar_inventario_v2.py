"""Planificador offline. Entrada: BSON Extended JSON {coleccion: [documentos]}.
Nunca abre una conexión MongoDB. Conserva snapshot fuente y archivo legacy.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from bson import json_util

DEPENDIENTES = ("movimientos", "detalles_recepcion", "recepciones_mercaderia",
                "inventario_historial", "alertas", "recomendaciones")
VERSION = "inventario-v2"

def key(row, name):
    return row.get(name) or row.get("id")

def uid(kind, value):
    return str(uuid5(NAMESPACE_URL, f"psitwin:{VERSION}:{kind}:{value}"))

def planificar(snapshot):
    data = deepcopy(snapshot)
    errors, warnings, mapping = [], [], {}
    required = {"inventarios","almacenes","zonas","racks","productos","operarios","proveedores",
                "ordenes_reposicion","detalles_reposicion",*DEPENDIENTES}
    missing = sorted(required-set(data))
    if missing:
        return data, {"version":VERSION,"errores":["Colecciones no exportadas: "+", ".join(missing)],
                      "advertencias":[],"inventarios_generales":0,"detalles":0,
                      "stock_antes":0,"stock_convertido":0,"convertidos":0}

    warehouses = {key(d,"id_almacen"):d for d in data.get("almacenes",[])}
    zones = {key(d,"id_zona"):d for d in data.get("zonas",[])}
    racks = {key(d,"id_rack"):d for d in data.get("racks",[])}
    products = {key(d,"id_producto"):d for d in data.get("productos",[])}
    now = datetime.now(timezone.utc)
    headers, header_by_warehouse = [], {}
    legacy = []
    for row in data.get("inventarios",[]):
        if "id_producto" in row:
            legacy.append(row)
        else:
            warehouse = row.get("id_almacen")
            if warehouse not in warehouses or warehouse in header_by_warehouse:
                errors.append(f"Cabecera huérfana/duplicada: {row.get('id_inventario')}")
            header_by_warehouse[warehouse] = row
            headers.append(row)
    for warehouse in sorted(warehouses,key=str):
        if warehouse not in header_by_warehouse:
            row = {"id_inventario":uid("cabecera",warehouse),"id_almacen":warehouse,
                   "fecha_creacion":now,"fecha_actualizacion":now}
            headers.append(row)
            header_by_warehouse[warehouse] = row
    details = data.setdefault("detalles_inventario",[])
    combinations = {(d["id_inventario"],d["id_producto"],d["id_rack"]):d for d in details}
    if len(combinations) != len(details):
        errors.append("Detalles existentes duplicados")
    known_headers = {h["id_inventario"]:h for h in headers}
    for row in legacy:
        old = key(row,"id_inventario")
        rack = racks.get(row.get("id_rack"))
        zone = zones.get(rack.get("id_zona")) if rack else None
        warehouse = warehouses.get(zone.get("id_almacen")) if zone else None
        product = products.get(row.get("id_producto"))
        if not old or old in mapping or not warehouse or not product:
            errors.append(f"Inventario antiguo huérfano/ID duplicado: {old}")
            continue
        warehouse_id = key(warehouse,"id_almacen")
        if product.get("id_empresa") != warehouse.get("id_empresa"):
            errors.append(f"Empresa incompatible: {old}")
            continue
        quantities = [row.get(k) for k in ("stock_actual","stock_minimo","stock_maximo")]
        if any(type(q) is not int or q < 0 for q in quantities) or quantities[1] > quantities[2]:
            errors.append(f"Saldos/límites inválidos: {old}")
            continue
        # U antigua permitía bajar máximo por debajo del saldo; conservarlo.
        header_id = header_by_warehouse[warehouse_id]["id_inventario"]
        combination = (header_id,row["id_producto"],row["id_rack"])
        detail_id = uid("detalle",old)
        if combination in combinations:
            errors.append(f"Ubicación duplicada: {old}; no sumar límites silenciosamente")
            continue
        detail = {k:row[k] for k in ("id_producto","id_rack","stock_actual","stock_minimo","stock_maximo",
                                     "fecha_creacion","fecha_actualizacion") if k in row}
        detail.update(id_inventario=header_id,id_detalle_inventario=detail_id)
        detail.setdefault("fecha_creacion",now)
        detail.setdefault("fecha_actualizacion",now)
        details.append(detail)
        combinations[combination] = detail
        mapping[old] = {"id_inventario_antiguo":old,"id_inventario":header_id,
                        "id_detalle_inventario":detail_id,"id_almacen":warehouse_id,
                        "id_producto":row["id_producto"],"id_rack":row["id_rack"]}
    for detail in details:
        header = known_headers.get(detail["id_inventario"])
        rack = racks.get(detail.get("id_rack"))
        zone = zones.get(rack.get("id_zona")) if rack else None
        product = products.get(detail.get("id_producto"))
        warehouse = warehouses.get(header["id_almacen"]) if header else None
        if not header or not zone or not product or not warehouse or zone["id_almacen"] != header["id_almacen"] or product.get("id_empresa") != warehouse.get("id_empresa"):
            errors.append(f"Detalle incompatible: {detail.get('id_detalle_inventario')}")
    def convert(value, collection):
        if isinstance(value,list):
            for item in value:
                convert(item,collection)
        elif isinstance(value,dict):
            old = value.get("id_inventario")
            if old in mapping:
                relation = mapping[old]
                for name in ("id_producto","id_rack","id_almacen"):
                    if value.get(name) and value[name] != relation[name]:
                        errors.append(f"Referencia incompatible {collection}/{old}/{name}")
                value["id_inventario"] = relation["id_inventario"]
                value["id_detalle_inventario"] = relation["id_detalle_inventario"]
                if collection in ("movimientos","inventario_historial"):
                    value.update({k:relation[k] for k in ("id_almacen","id_producto","id_rack")})
            elif old is not None and old not in known_headers:
                errors.append(f"Referencia huérfana {collection}/{old}")
            for nested in value.values():
                if isinstance(nested,(dict,list)):
                    convert(nested,collection)
    for collection in DEPENDIENTES:
        convert(data.get(collection,[]),collection)
    for collection,pk in (
        ("almacenes","id_almacen"),("zonas","id_zona"),("racks","id_rack"),("productos","id_producto"),
        ("movimientos","id_movimiento"),("ordenes_reposicion","id_orden_reposicion"),
        ("detalles_reposicion","id_detalle_reposicion"),("recepciones_mercaderia","id_recepcion"),
        ("detalles_recepcion","id_detalle_recepcion"),("alertas","id_alerta"),("recomendaciones","id_recomendacion")):
        ids=[key(row,pk) for row in data.get(collection,[])]
        if None in ids or len(ids)!=len(set(ids)):
            errors.append(f"Identificador ausente/duplicado: {collection}")
    receipt_moves=[m["id_detalle_recepcion"] for m in data.get("movimientos",[])
                   if isinstance(m.get("id_detalle_recepcion"),str)]
    if len(receipt_moves)!=len(set(receipt_moves)):
        errors.append("Movimientos de recepción duplicados: índice idempotente incompatible")
    references = {
        "ordenes_reposicion": (("id_almacen","almacenes","id_almacen"),("id_proveedor","proveedores","id_proveedor")),
        "detalles_reposicion": (("id_orden_reposicion","ordenes_reposicion","id_orden_reposicion"),("id_producto","productos","id_producto")),
        "recepciones_mercaderia": (("id_orden_reposicion","ordenes_reposicion","id_orden_reposicion"),("id_operario","operarios","id_operario")),
        "detalles_recepcion": (("id_recepcion","recepciones_mercaderia","id_recepcion"),("id_detalle_reposicion","detalles_reposicion","id_detalle_reposicion"),("id_movimiento","movimientos","id_movimiento")),
        "movimientos": (("id_operario","operarios","id_operario"),("id_detalle_recepcion","detalles_recepcion","id_detalle_recepcion")),
        "inventario_historial": (("id_operario","operarios","id_operario"),),
        "alertas": (("id_almacen","almacenes","id_almacen"),("id_producto","productos","id_producto")),
        "recomendaciones": (("id_almacen","almacenes","id_almacen"),("id_producto","productos","id_producto"),("id_alerta","alertas","id_alerta"))
    }
    for collection,refs in references.items():
        for row in data.get(collection,[]):
            for field,target,target_key in refs:
                value=row.get(field)
                if value is not None and not any(key(candidate,target_key)==value for candidate in data.get(target,[])):
                    errors.append(f"Referencia huérfana {collection}/{field}/{value}")
    for collection,pk in (("inventarios","id_inventario"),("detalles_inventario","id_detalle_inventario")):
        rows = headers if collection=="inventarios" else details
        ids=[row.get(pk) for row in rows]
        if None in ids or len(ids)!=len(set(ids)):
            errors.append(f"Identificador ausente/duplicado: {collection}")
    detail_map = {d["id_detalle_inventario"]:d for d in details}
    for move in data.get("movimientos",[]):
        detail=detail_map.get(move.get("id_detalle_inventario"))
        if detail:
            header=known_headers[detail["id_inventario"]]
            expected={"id_inventario":detail["id_inventario"],"id_almacen":header["id_almacen"],
                      "id_producto":detail["id_producto"],"id_rack":detail["id_rack"]}
            for field,value in expected.items():
                if move.get(field) is not None and move[field] != value:
                    errors.append(f"Movimiento incompatible: {move.get('id_movimiento')}/{field}")
            move.update(expected)
        for field in ("stock_anterior","stock_nuevo"):
            if field in move and (type(move[field]) is not int or move[field]<0):
                errors.append(f"Saldo de movimiento inválido: {move.get('id_movimiento')}/{field}")
        if "cantidad" in move and (type(move["cantidad"]) is not int or move["cantidad"]<=0):
            errors.append(f"Cantidad de movimiento inválida: {move.get('id_movimiento')}")
    for collection in ("movimientos","detalles_recepcion","inventario_historial"):
        for row in data.get(collection,[]):
            did = row.get("id_detalle_inventario")
            if row.get("id_inventario") and (not did or did not in detail_map):
                errors.append(f"Detalle huérfano en {collection}: {did}")
    load_by_rack = defaultdict(float)
    for detail in details:
        product = products.get(detail.get("id_producto"),{})
        rack = racks.get(detail.get("id_rack"),{})
        weight = product.get("peso")
        capacity = rack.get("capacidad")
        if not isinstance(weight,(int,float)) or weight <= 0 or not isinstance(capacity,(int,float)) or capacity <= 0:
            errors.append(f"Peso/capacidad no verificables: {detail.get('id_detalle_inventario')}")
            continue
        load_by_rack[detail["id_rack"]] += detail["stock_actual"]*weight
        if product.get("requiere_refrigeracion"):
            pmin,pmax=product.get("temperatura_min_almacenamiento"),product.get("temperatura_max_almacenamiento")
            rmin,rmax=rack.get("temperatura_min"),rack.get("temperatura_max")
            if any(v is None for v in (pmin,pmax,rmin,rmax)) or pmin>pmax or rmin>rmax or rmin<pmin or rmax>pmax:
                errors.append(f"Rango térmico incompatible: {detail.get('id_detalle_inventario')}")
    for rack_id,load in load_by_rack.items():
        if load > racks[rack_id]["capacidad"]+1e-9:
            errors.append(f"Capacidad excedida: {rack_id}")
    totals = defaultdict(int)
    for d in details:
        totals[(d["id_inventario"],d["id_producto"])] += d["stock_actual"]
    for collection, type_key, aggregate_type, active, terminal in (
        ("alertas","tipo_alerta","RIESGO_STOCKOUT",{"ACTIVA","VISTA"},"IGNORADA"),
        ("recomendaciones","tipo_recomendacion","REABASTECER",{"PENDIENTE","ACEPTADA"},"RECHAZADA")):
        grouped = defaultdict(list)
        for row in data.get(collection,[]):
            if row.get(type_key)==aggregate_type and row.get("estado") in active:
                grouped[(row.get("id_inventario"),row.get("id_producto"),row[type_key])].append(row)
        for group in grouped.values():
            group.sort(key=lambda r:str(r.get("fecha_creacion","")))
            for index,row in enumerate(group):
                row["id_detalle_inventario"] = None
                if collection=="alertas":
                    row["stock_actual"] = totals[(row["id_inventario"],row["id_producto"])]
                if index:
                    row["estado"] = terminal
                    row["migracion_estado_anterior"] = snapshot.get(collection,[])[data[collection].index(row)].get("estado")
                    warnings.append(f"Duplicado agregado archivado lógicamente en {collection}")
    # Verificar continuidad del ledger sin inventar apertura ni rellenar movimientos.
    ledgers = defaultdict(list)
    for move in data.get("movimientos",[]):
        if move.get("id_detalle_inventario"):
            ledgers[move["id_detalle_inventario"]].append(move)
    for did,moves in ledgers.items():
        moves.sort(key=lambda r:str(r.get("fecha_hora","")))
        for before,after in zip(moves,moves[1:]):
            if before.get("stock_nuevo") != after.get("stock_anterior"):
                errors.append(f"Ledger discontinuo: {did}")
        if did in detail_map and moves[-1].get("stock_nuevo") != detail_map[did]["stock_actual"]:
            errors.append(f"Saldo ledger incompatible: {did}")
    old_stock = sum(r.get("stock_actual",0) for r in legacy)
    converted_stock = sum(detail_map[m["id_detalle_inventario"]]["stock_actual"] for m in mapping.values())
    if old_stock != converted_stock:
        errors.append("Stock no conservado")
    for collection,allowed in (("alertas",{"ACTIVA","VISTA"}),("recomendaciones",{"PENDIENTE","ACEPTADA"})):
        seen=set()
        type_key="tipo_alerta" if collection=="alertas" else "tipo_recomendacion"
        for row in data.get(collection,[]):
            if row.get("estado") in allowed:
                scope=(row.get("id_inventario"),row.get("id_producto"),row.get("id_detalle_inventario"),row.get(type_key))
                if scope in seen:
                    errors.append(f"Decisión activa duplicada incompatible con índice: {collection}/{scope}")
                seen.add(scope)
    data["inventarios"] = headers
    archive = data.setdefault("inventarios_legacy",[])
    archived = {key(r,"id_inventario") for r in archive}
    archive.extend(deepcopy(r) for r in legacy if key(r,"id_inventario") not in archived)
    previous_map = data.setdefault("migracion_inventario_mapeo",[])
    map_ids = {r["id_inventario_antiguo"] for r in previous_map}
    previous_map.extend(m for old,m in mapping.items() if old not in map_ids)
    report = {"version":VERSION,"errores":sorted(set(errors)),"advertencias":warnings,
              "inventarios_generales":len(headers),"detalles":len(details),
              "stock_antes":old_stock,"stock_convertido":converted_stock,"convertidos":len(mapping)}
    return data,report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True,help="Snapshot offline Extended JSON; nunca URI Mongo")
    parser.add_argument("--dry-run",action="store_true",help="Solo verificar, sin escribir (también es el default)")
    parser.add_argument("--output",type=Path,help="Escribir snapshot transformado; no importa ni modifica MongoDB")
    args = parser.parse_args()
    raw = args.input.read_bytes()
    data,report = planificar(json_util.loads(raw.decode("utf-8-sig")))
    report["sha256_fuente"] = hashlib.sha256(raw).hexdigest()
    print(json_util.dumps(report,indent=2))
    if report["errores"]:
        raise SystemExit(2)
    if args.output and not args.dry_run:
        target = args.output.resolve()
        if target == args.input.resolve() or target.exists():
            raise SystemExit("Salida debe ser nueva y distinta de la fuente")
        data["_migracion_manifest"] = [{"version":VERSION,"sha256_fuente":report["sha256_fuente"],
                                       "recuperacion":"Restaurar snapshot fuente completo; no revertir solo inventarios."}]
        temporary = target.with_suffix(target.suffix+".tmp")
        with temporary.open("x",encoding="utf-8") as stream:
            stream.write(json_util.dumps(data,indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)

if __name__=="__main__":
    main()
