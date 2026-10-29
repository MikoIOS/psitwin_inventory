"""Pruebas aisladas: Motor en memoria; nunca conecta a MongoDB."""
import asyncio
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
import sys
import pytest
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError
from app.dto.auth_dto import UsuarioActual
from app.dto.detalle_inventario_dto import DetalleInventarioCreate
from app.dto.movimiento_dto import MovimientoCreate
from app.dto.recepcion_mercaderia_dto import RecepcionMercaderiaCreate, ResolverEvaluacion
from app.services.inventario_service import InventarioService
from app.services.detalle_inventario_service import DetalleInventarioService
from app.services.movimiento_service import MovimientoService
from app.services.recepcion_mercaderia_service import RecepcionMercaderiaService
from app.services.detalle_recepcion_service import DetalleRecepcionService
from app.services.rack_service import RackService
from app.services.acceso_service import AccesoService
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
from app.services.stock_lock import bloqueo_rack
from app.services.alerta_service import AlertaService
from app.services.recomendacion_service import RecomendacionService
from app.dto.alerta_dto import AlertaCreate

def run(coro):
    return asyncio.run(coro)

def matches(row,query):
    for key,value in query.items():
        if key=="$or":
            if not any(matches(row,q) for q in value): return False
        elif key=="$and":
            if not all(matches(row,q) for q in value): return False
        elif isinstance(value,dict):
            actual = row.get(key)
            for op,wanted in value.items():
                if op=="$in" and actual not in wanted: return False
                if op=="$exists" and ((key in row) != wanted): return False
                if op=="$type" and (wanted=="string" and not isinstance(actual,str)): return False
                if op=="$gte" and (actual is None or actual<wanted): return False
                if op=="$lte" and (actual is None or actual>wanted): return False
        elif row.get(key)!=value:
            return False
    return True

class Cursor:
    def __init__(self,rows): self.rows=deepcopy(rows)
    def sort(self,key,direction):
        self.rows.sort(key=lambda r:str(r.get(key,"")),reverse=direction<0)
        return self
    async def to_list(self,length=None): return deepcopy(self.rows if length is None else self.rows[:length])

class Collection:
    def __init__(self,name): self.name=name; self.rows=[]; self.fail_insert=False
    def find(self,query=None,projection=None): return Cursor([r for r in self.rows if matches(r,query or {})])
    async def find_one(self,query,projection=None,sort=None):
        rows=[r for r in self.rows if matches(r,query)]
        if sort:
            for k,v in reversed(sort): rows.sort(key=lambda r:str(r.get(k,"")),reverse=v<0)
        return deepcopy(rows[0]) if rows else None
    async def insert_one(self,row):
        if self.fail_insert: raise RuntimeError("inserción fallida")
        if "_id" in row and any(r.get("_id")==row["_id"] for r in self.rows): raise DuplicateKeyError("duplicado")
        unique = {"inventarios":("id_almacen",),"detalles_inventario":("id_inventario","id_producto","id_rack")}
        if self.name in unique and any(all(r.get(k)==row.get(k) for k in unique[self.name]) for r in self.rows):
            raise DuplicateKeyError("duplicado")
        if self.name=="movimientos" and row.get("id_detalle_recepcion") and any(r.get("id_detalle_recepcion")==row["id_detalle_recepcion"] for r in self.rows):
            raise DuplicateKeyError("recepción duplicada")
        self.rows.append(deepcopy(row))
        return SimpleNamespace(inserted_id=row.get("_id"))
    async def update_one(self,query,update,upsert=False):
        for r in self.rows:
            if matches(r,query):
                r.update(deepcopy(update.get("$set",{})))
                for k,v in update.get("$inc",{}).items(): r[k]=r.get(k,0)+v
                return SimpleNamespace(matched_count=1,modified_count=1)
        if upsert:
            row={**query,**update.get("$setOnInsert",{}),**update.get("$set",{})}
            await self.insert_one(row)
        return SimpleNamespace(matched_count=0,modified_count=0)
    async def delete_one(self,query):
        for r in self.rows:
            if matches(r,query): self.rows.remove(r); return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)
    async def distinct(self,key,query=None): return list({r.get(key) for r in self.rows if matches(r,query or {})})

class Database(dict):
    def __missing__(self,key):
        self[key]=Collection(key)
        return self[key]

@pytest.fixture
def db(monkeypatch):
    database=Database()
    import app.database.mongodb as mongo
    monkeypatch.setattr(mongo,"get_database",lambda:database)
    for name,module in list(sys.modules.items()):
        if name.startswith("app.") and hasattr(module,"get_database"):
            monkeypatch.setattr(module,"get_database",lambda:database)
    database["almacenes"].rows=[{"id":"a","id_empresa":"e"},{"id":"b","id_empresa":"e"},{"id":"foreign","id_empresa":"other"}]
    database["zonas"].rows=[{"id":"z","id_almacen":"a"},{"id":"zb","id_almacen":"b"}]
    database["racks"].rows=[
        {"id_rack":"r1","id_zona":"z","codigo":"R1","capacidad":100,"estado":"DISPONIBLE","temperatura_min":2,"temperatura_max":5},
        {"id_rack":"r2","id_zona":"z","codigo":"R2","capacidad":100,"estado":"DISPONIBLE"},
        {"id_rack":"rb","id_zona":"zb","codigo":"RB","capacidad":100,"estado":"DISPONIBLE"}]
    database["productos"].rows=[
        {"id_producto":"p","id_empresa":"e","nombre":"Producto","peso":2,"lead_time_dias":2,"categoria":"C"},
        {"id_producto":"q","id_empresa":"e","nombre":"Otro","peso":1,"lead_time_dias":1,"categoria":"C"},
        {"id_producto":"f","id_empresa":"other","peso":1}]
    database["operarios"].rows=[{"id_operario":"op","id_empresa":"e","id_almacen":"a","estado":"ACTIVO","nombre":"Operario","apellido":"Uno"}]
    return database

async def detail(header,product="p",rack="r1",stock=10,maximum=100):
    return await DetalleInventarioService().crear_inventario(
        DetalleInventarioCreate(id_inventario=header["id_inventario"],id_producto=product,
            id_rack=rack,stock_actual=stock,stock_minimo=1,stock_maximo=maximum),"op")

def user():
    return UsuarioActual(rol="OPERARIO",id_empresa="e",id_operario="op",id_almacen="a")

def test_headers_idempotent_independent_and_warehouse_creation(db):
    async def scenario():
        from app.services.almacen_service import AlmacenService
        from app.dto.almacen_dto import AlmacenCreate
        db["empresas"].rows=[{"id_empresa":"e"}]
        a=await InventarioRepository().garantizar("a")
        assert await InventarioRepository().garantizar("a")==a
        b=await InventarioRepository().garantizar("b")
        assert a["id_inventario"]!=b["id_inventario"]
        created=await AlmacenService.crear(AlmacenCreate(id_empresa="e",nombre="Nuevo",longitud=0,latitud=0,area_m2=10,aforo=1,tipo_almacen="General"))
        assert await InventarioRepository().obtener_por_almacen(created["id"])
        assert "stock_actual" not in a
    run(scenario())

def test_distribution_filters_and_capacity(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        await detail(header,stock=10)
        await detail(header,rack="r2",stock=5)
        await detail(header,product="q",stock=3)
        service=InventarioService()
        rows=await service.stock_por_producto(header["id_inventario"])
        assert next(r for r in rows if r["id_producto"]=="p")["stock_actual"]==15
        assert len(await service.detalles_inventario(header["id_inventario"],id_zona="z"))==3
        assert len(await service.detalles_inventario(header["id_inventario"],id_rack="r2"))==1
        assert len(await service.detalles_inventario(header["id_inventario"],id_producto="p"))==2
        racks=await RackService.enriquecer(db["racks"].rows)
        assert racks[0]["carga_kg"]==23 and racks[0]["libre_kg"]==77
    run(scenario())

@pytest.mark.parametrize("case,status",[("duplicate",409),("tenant",404),("warehouse",409),("capacity",409),("temperature",409),("maximum",409)])
def test_reject_invalid_details(db,case,status):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        await detail(header)
        with pytest.raises(HTTPException) as caught:
            if case=="duplicate": await detail(header)
            elif case=="tenant": await detail(header,product="f")
            elif case=="warehouse": await detail(header,rack="rb")
            elif case=="capacity": await detail(header,product="q",stock=90)
            elif case=="maximum": await detail(header,product="q",stock=5,maximum=2)
            else:
                db["productos"].rows[1].update(requiere_refrigeracion=True,temperatura_min_almacenamiento=3,temperatura_max_almacenamiento=4)
                await detail(header,product="q")
        assert caught.value.status_code==status
    run(scenario())

def test_movements_negative_cas_compensation_and_history(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        row=await detail(header)
        service=MovimientoService()
        def movement(quantity,kind="SALIDA",reason="VENTA",receipt=None):
            return MovimientoCreate(id_inventario=header["id_inventario"],id_detalle_inventario=row["id_detalle_inventario"],
                id_operario="op",tipo_movimiento=kind,motivo_movimiento=reason,cantidad=quantity,id_detalle_recepcion=receipt)
        result=await service.crear_movimiento(movement(3),user())
        assert result["stock_anterior"]==10 and result["stock_nuevo"]==7
        assert result["id_almacen"]=="a"
        with pytest.raises(HTTPException): await service.crear_movimiento(movement(8),user())
        await service.crear_movimiento(movement(2,"ENTRADA","RECEPCION","rec"))
        await service.crear_movimiento(movement(2,"ENTRADA","RECEPCION","rec"))
        assert len(db["movimientos"].rows)==2
        await service.crear_movimiento(movement(4,"AJUSTE","CONTEO_FISICO"))
        assert db["detalles_inventario"].rows[0]["stock_actual"]==4
        db["movimientos"].fail_insert=True
        with pytest.raises(RuntimeError): await service.crear_movimiento(movement(1),user())
        assert db["detalles_inventario"].rows[0]["stock_actual"]==4
        hist=await InventarioRepository().obtener_historial(header["id_inventario"])
        assert len(hist)==4
        assert all(h["id_almacen"]=="a" and h["id_detalle_inventario"]==row["id_detalle_inventario"] for h in hist)
        assert not await DetalleInventarioRepository().actualizar_stock_condicional(row["id_detalle_inventario"],99,5)
        assert not db["bloqueos_stock_rack"].rows
    run(scenario())

def test_cross_tenant_and_operator_protection(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        row=await detail(header)
        with pytest.raises(HTTPException): await AccesoService.verificar_inventario(UsuarioActual(rol="EMPRESA",id_empresa="other"),header["id_inventario"])
        db["operarios"].rows[0]["id_almacen"]="b"
        with pytest.raises(HTTPException) as caught:
            await MovimientoService().crear_movimiento(MovimientoCreate(id_inventario=header["id_inventario"],
                id_detalle_inventario=row["id_detalle_inventario"],id_operario="op",
                tipo_movimiento="SALIDA",motivo_movimiento="VENTA",cantidad=1))
        assert caught.value.status_code==403
        assert db["detalles_inventario"].rows[0]["stock_actual"]==10
    run(scenario())

def test_lock_conflict_does_not_expire_writer(db):
    async def scenario():
        async with bloqueo_rack("r1"):
            async def other():
                with pytest.raises(HTTPException) as caught:
                    async with bloqueo_rack("r1"): pass
                assert caught.value.status_code==409
            await asyncio.create_task(other())
            assert len(db["bloqueos_stock_rack"].rows)==1
        assert not db["bloqueos_stock_rack"].rows
    run(scenario())

def prepare_order(db,quantity=10):
    db["ordenes_reposicion"].rows=[{"id_orden_reposicion":"order","id_empresa":"e","id_almacen":"a","estado":"ENVIADA","id_proveedor":"supplier", "fecha_orden":datetime.now(timezone.utc), "despacho":{"lineas":[{"id_detalle_reposicion":"line","cantidad":quantity}]}}]
    db["detalles_reposicion"].rows=[{"id_detalle_reposicion":"line","id_orden_reposicion":"order","id_producto":"p","cantidad_solicitada":quantity}]

def test_receipt_creates_location_once_and_preserves_ledger(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        prepare_order(db)
        request=RecepcionMercaderiaCreate(id_orden_reposicion="order",detalles=[{
            "id_inventario":header["id_inventario"],"id_rack":"r1","stock_minimo":0,"stock_maximo":0,
            "id_detalle_reposicion":"line","cantidad_recibida":10,"lote":"L1"}])
        receipt=await RecepcionMercaderiaService().crear(request,user())
        assert len(db["inventarios"].rows)==1
        assert len(db["detalles_inventario"].rows)==1
        assert db["detalles_inventario"].rows[0]["stock_actual"]==10
        saved=receipt["detalles"][0]
        assert saved["id_detalle_inventario"]==db["detalles_inventario"].rows[0]["id_detalle_inventario"]
        assert db["movimientos"].rows[0]["id_detalle_recepcion"]==saved["id_detalle_recepcion"]
        assert db["ordenes_reposicion"].rows[0]["estado"]=="RECIBIDA"
        assert not db["bloqueos_stock_rack"].rows
    run(scenario())

def test_receipt_rejects_cumulative_overdelivery_before_writes(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        prepare_order(db,5)
        request=RecepcionMercaderiaCreate(id_orden_reposicion="order",detalles=[
            {"id_inventario":header["id_inventario"],"id_rack":rack,"stock_maximo":0,"id_detalle_reposicion":"line","cantidad_recibida":3}
            for rack in ("r1","r2")])
        with pytest.raises(HTTPException) as caught: await RecepcionMercaderiaService().crear(request,user())
        assert caught.value.status_code==409
        assert not db["detalles_inventario"].rows and not db["recepciones_mercaderia"].rows
    run(scenario())

def test_evaluation_resolution_location_and_quantities(db,monkeypatch):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        prepare_order(db)
        receipt=await RecepcionMercaderiaService().crear(RecepcionMercaderiaCreate(
            id_orden_reposicion="order",detalles=[{"id_inventario":header["id_inventario"],"id_rack":"r1",
            "stock_maximo":0,"id_detalle_reposicion":"line","cantidad_recibida":10,
            "estado_recepcion":"EN_EVALUACION","comentario_recepcion":"Inspección"}]),user())
        service=DetalleRecepcionService()
        async def notify(*args): return {"status":"OMITIDO"}
        monkeypatch.setattr(service.notification_service,"enviar_resumen_reposicion",notify)
        saved=await service.resolver_evaluacion(receipt["detalles"][0]["id_detalle_recepcion"],
            ResolverEvaluacion(estado_recepcion="CONFORME",comentario_resolucion="Conforme",cantidad_aceptada=8,cantidad_rechazada=2),user())
        assert saved["cantidad_aceptada"]==8
        assert db["detalles_inventario"].rows[0]["stock_actual"]==8
        again=await service.resolver_evaluacion(saved["id_detalle_recepcion"],
            ResolverEvaluacion(estado_recepcion="CONFORME",comentario_resolucion="Reintento"),user())
        assert again["id_movimiento"]==saved["id_movimiento"]
        assert len(db["movimientos"].rows)==1
    run(scenario())

def test_alerts_deduplicate_by_product_not_header(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        await detail(header,stock=15)
        service=AlertaService()
        def request(p,stock): return AlertaCreate(id_empresa="e",id_almacen="a",id_inventario=header["id_inventario"],
            id_producto=p,tipo_alerta="RIESGO_STOCKOUT",nivel_riesgo="ALTO",titulo="Riesgo",mensaje="Stock bajo",stock_actual=stock)
        first=await service.crear(request("p",10))
        second=await service.crear(request("p",15))
        other=await service.crear(request("q",1))
        assert first["id_alerta"]==second["id_alerta"]!=other["id_alerta"]
        assert len(db["alertas"].rows)==2 and second["stock_actual"]==15
    run(scenario())

def test_legacy_schema_is_explicitly_blocked(db):
    db["inventarios"].rows=[{"id_inventario":"old","id_producto":"p","id_rack":"r1","stock_actual":10}]
    with pytest.raises(HTTPException) as caught: run(InventarioRepository().garantizar("a"))
    assert caught.value.status_code==409
    assert len(db["inventarios"].rows)==1

def test_aggregate_recommendations_ignore_rack_duplication(db):
    async def scenario():
        from app.dto.recomendacion_dto import RecomendacionCreate
        header=await InventarioRepository().garantizar("a")
        one=await detail(header)
        two=await detail(header,rack="r2")
        service=RecomendacionService()
        def request(location):
            return RecomendacionCreate(id_empresa="e",id_almacen="a",id_inventario=header["id_inventario"],
                id_producto="p",id_detalle_inventario=location,tipo_recomendacion="REABASTECER",
                nivel_riesgo="ALTO",cantidad_recomendada=10,explicacion="Reponer stock agregado")
        first=await service.crear(request(one["id_detalle_inventario"]))
        second=await service.crear(request(two["id_detalle_inventario"]))
        assert first["id_recomendacion"]==second["id_recomendacion"]
        assert second["id_detalle_inventario"] is None and len(db["recomendaciones"].rows)==1
    run(scenario())

def test_resolve_alert_only_for_selected_product(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        service=AlertaService()
        for product in ("p","q"):
            await service.crear(AlertaCreate(id_empresa="e",id_almacen="a",id_inventario=header["id_inventario"],
                id_producto=product,tipo_alerta="RIESGO_STOCKOUT",nivel_riesgo="ALTO",titulo="Riesgo",
                mensaje="Reposición requerida",stock_actual=0))
        from app.dto.alerta_dto import TipoAlerta
        await service.resolver_activa_por_inventario(header["id_inventario"],TipoAlerta.RIESGO_STOCKOUT,id_producto="p")
        assert {r["id_producto"]:r["estado"] for r in db["alertas"].rows}=={"p":"RESUELTA","q":"ACTIVA"}
    run(scenario())

def test_product_warehouse_query_uses_details_and_preserves_parent_references(db):
    async def scenario():
        from app.repositories.producto_repository import ProductoRepository
        from app.services.almacen_service import AlmacenService
        from app.services.zona_service import ZonaService
        header=await InventarioRepository().garantizar("a")
        await detail(header)
        db["productos"].rows[0]["id_rack"]="rb"  # referencia comercial no gobierna ubicación
        assert [p["id_producto"] for p in await ProductoRepository.obtener_por_almacen("a")]==["p"]
        assert await ProductoRepository.obtener_por_almacen("b")==[]
        with pytest.raises(HTTPException): await AlmacenService.eliminar("a")
        with pytest.raises(HTTPException): await ZonaService.eliminar("z")
        db["almacenes"].rows.append({"id":"empty","id_empresa":"e"})
        empty=await InventarioRepository().garantizar("empty")
        await AlmacenService.eliminar("empty")
        assert await InventarioRepository().obtener_por_id(empty["id_inventario"]) is None
    run(scenario())

def test_receipt_movement_failure_is_recoverable_without_false_acceptance(db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        prepare_order(db)
        db["movimientos"].fail_insert=True
        with pytest.raises(RuntimeError):
            await RecepcionMercaderiaService().crear(RecepcionMercaderiaCreate(id_orden_reposicion="order",
                detalles=[{"id_inventario":header["id_inventario"],"id_rack":"r1","stock_maximo":0,
                "id_detalle_reposicion":"line","cantidad_recibida":10}]),user())
        assert db["detalles_inventario"].rows[0]["stock_actual"]==0
        pending=db["detalles_recepcion"].rows[0]
        assert pending["estado_recepcion"]=="EN_EVALUACION" and pending["cantidad_aceptada"]==0
        assert db["ordenes_reposicion"].rows[0]["estado"]=="ENVIADA"
        assert not db["movimientos"].rows
    run(scenario())

def test_recommendation_cannot_link_foreign_alert(db):
    async def scenario():
        from app.dto.recomendacion_dto import RecomendacionCreate
        header=await InventarioRepository().garantizar("a")
        db["alertas"].rows=[{"id_alerta":"foreign","id_empresa":"other","id_inventario":"other","id_producto":"p","id_almacen":"foreign"}]
        with pytest.raises(HTTPException) as caught:
            await RecomendacionService().crear(RecomendacionCreate(id_empresa="e",id_inventario=header["id_inventario"],
                id_almacen="a",id_producto="p",id_alerta="foreign",tipo_recomendacion="REABASTECER",
                nivel_riesgo="ALTO",cantidad_recomendada=10,explicacion="Reponer"))
        assert caught.value.status_code==404
        assert not db["recomendaciones"].rows
    run(scenario())
