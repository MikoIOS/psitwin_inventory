from copy import deepcopy
from datetime import datetime, timezone
import subprocess
import sys
from bson import json_util
from scripts.migrar_inventario_v2 import planificar

def snapshot():
    now=datetime(2026,10,12,tzinfo=timezone.utc)
    return {
        "operarios":[],"proveedores":[],"alertas":[],"recomendaciones":[],
        "almacenes":[{"id":"a","id_empresa":"e"},{"id":"empty","id_empresa":"e"}],
        "zonas":[{"id":"z","id_almacen":"a"}],
        "racks":[{"id_rack":"r1","id_zona":"z","capacidad":250},{"id_rack":"r2","id_zona":"z","capacidad":250}],
        "productos":[{"id_producto":"p","id_empresa":"e","peso":2}],
        "ordenes_reposicion":[{"id_orden_reposicion":"order"}],
        "detalles_reposicion":[{"id_detalle_reposicion":"line","id_orden_reposicion":"order","id_producto":"p"}],
        "inventarios":[
            {"id_inventario":"old1","id_producto":"p","id_rack":"r1","stock_actual":100,"stock_minimo":10,"stock_maximo":200,"fecha_creacion":now,"fecha_actualizacion":now},
            {"id_inventario":"old2","id_producto":"p","id_rack":"r2","stock_actual":50,"stock_minimo":5,"stock_maximo":80,"fecha_creacion":now,"fecha_actualizacion":now}],
        "movimientos":[{"id_movimiento":"move","id_inventario":"old1","id_producto":"p","id_rack":"r1",
            "stock_anterior":105,"stock_nuevo":100,"cantidad":5,"tipo_movimiento":"SALIDA","fecha_hora":now}],
        "inventario_historial":[{"id_inventario":"old1","fecha":now,"accion":"CREAR","despues":{"stock_actual":105}}],
        "detalles_recepcion":[{"id_detalle_recepcion":"receipt","id_inventario":"old2","id_recepcion":"recepcion","id_detalle_reposicion":"line"}],
        "recepciones_mercaderia":[{"id_recepcion":"recepcion","detalles":[{"id_inventario":"old2"}]}]}

def test_migration_preserves_locations_stock_limits_ids_and_references():
    source=snapshot(); original=deepcopy(source)
    data,report=planificar(source)
    assert not report["errores"]
    assert report["stock_antes"]==report["stock_convertido"]==150
    assert source==original
    assert len(data["inventarios"])==2
    assert len(data["inventarios_legacy"])==2
    assert [d["stock_actual"] for d in data["detalles_inventario"]]==[100,50]
    assert [d["stock_minimo"] for d in data["detalles_inventario"]]==[10,5]
    assert [d["stock_maximo"] for d in data["detalles_inventario"]]==[200,80]
    mapping={r["id_inventario_antiguo"]:r for r in data["migracion_inventario_mapeo"]}
    assert mapping["old1"]["id_inventario"]==mapping["old2"]["id_inventario"]
    assert mapping["old1"]["id_detalle_inventario"] not in {"old1","old2"}
    move=data["movimientos"][0]
    assert move["id_detalle_inventario"]==mapping["old1"]["id_detalle_inventario"]
    assert move["stock_anterior"]==105 and move["stock_nuevo"]==100 and move["id_almacen"]=="a"
    assert data["inventario_historial"][0]["id_detalle_inventario"]==mapping["old1"]["id_detalle_inventario"]
    assert data["recepciones_mercaderia"][0]["detalles"][0]["id_detalle_inventario"]==mapping["old2"]["id_detalle_inventario"]

def test_migration_idempotent():
    data,report=planificar(snapshot())
    again,second=planificar(data)
    assert not second["errores"] and second["convertidos"]==0
    assert data==again

def test_orphans_duplicate_incompatible_tenant_and_ledger_are_blocked():
    for change in ("rack","tenant","duplicate","ledger","reference"):
        source=snapshot()
        if change=="rack": source["inventarios"][0]["id_rack"]="unknown"
        elif change=="tenant": source["productos"][0]["id_empresa"]="other"
        elif change=="duplicate": source["inventarios"][1]["id_rack"]="r1"
        elif change=="ledger": source["movimientos"][0]["stock_nuevo"]=99
        else: source["movimientos"][0]["id_inventario"]="unknown"
        _,report=planificar(source)
        assert report["errores"],change

def test_dry_run_cli_writes_nothing_and_has_no_db_connector(tmp_path):
    source=tmp_path/"snapshot.json"
    source.write_text(json_util.dumps(snapshot()),encoding="utf-8")
    before=source.read_bytes()
    output=tmp_path/"transformed.json"
    result=subprocess.run([sys.executable,"scripts/migrar_inventario_v2.py","--input",str(source),
        "--dry-run","--output",str(output)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert source.read_bytes()==before and not output.exists()
    assert "sha256_fuente" in result.stdout

def test_aggregate_alerts_consolidate_without_removing_audit():
    source=snapshot()
    source["alertas"]=[{"id_alerta":str(i),"id_inventario":old,"id_producto":"p",
        "tipo_alerta":"RIESGO_STOCKOUT","estado":"ACTIVA","fecha_creacion":source["inventarios"][0]["fecha_creacion"]}
        for i,old in enumerate(("old1","old2"))]
    data,report=planificar(source)
    assert not report["errores"]
    assert len(data["alertas"])==2
    assert [r["estado"] for r in data["alertas"]]==["ACTIVA","IGNORADA"]
    assert data["alertas"][0]["stock_actual"]==150
    assert all(r["id_detalle_inventario"] is None for r in data["alertas"])

def test_migration_rejects_invalid_physical_capacity_and_temperature():
    source=snapshot()
    source["racks"][0]["capacidad"]=100
    assert any("Capacidad excedida" in error for error in planificar(source)[1]["errores"])
    source=snapshot()
    source["productos"][0].update(requiere_refrigeracion=True,temperatura_min_almacenamiento=2,temperatura_max_almacenamiento=5)
    assert any("Rango térmico" in error for error in planificar(source)[1]["errores"])

def test_partial_snapshot_is_explicitly_rejected():
    source=snapshot()
    del source["movimientos"]
    data,report=planificar(source)
    assert any("Colecciones no exportadas" in e for e in report["errores"])
    assert data==source  # no plan parcial apto para importar
