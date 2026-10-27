import asyncio
import httpx
import pytest
from fastapi import FastAPI
from app.controllers import inventario_controller, detalle_inventario_controller, forecast_controller, movimiento_controller
from app.dependencies.dependencies import require_empresa, require_empresa_u_operario, require_operario
from app.dto.auth_dto import UsuarioActual
from app.repositories.inventario_repository import InventarioRepository
from test_inventario_v2 import db, detail, run

@pytest.fixture
def app(db):
    application=FastAPI()  # sin lifespan de producción
    for router in (inventario_controller.router,detalle_inventario_controller.router,forecast_controller.router,movimiento_controller.router):
        application.include_router(router,prefix="/api/v1")
    actor=UsuarioActual(rol="OPERARIO",id_empresa="e",id_almacen="a",id_operario="op")
    company=UsuarioActual(rol="EMPRESA",id_empresa="e")
    application.dependency_overrides[require_empresa_u_operario]=lambda:actor
    application.dependency_overrides[require_operario]=lambda:actor
    application.dependency_overrides[require_empresa]=lambda:company
    return application

async def request(app,method,path,**kwargs):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
        return await client.request(method,"/api/v1"+path,**kwargs)

def test_header_and_distribution_http(app,db):
    async def scenario():
        header=await request(app,"POST","/inventarios",json={"id_almacen":"a"})
        assert header.status_code==200,header.text
        identifier=header.json()["id_inventario"]
        again=await request(app,"POST","/inventarios",json={"id_almacen":"a"})
        assert again.json()["id_inventario"]==identifier
        for rack,stock in (("r1",10),("r2",5)):
            result=await request(app,"POST","/detalles-inventario",json={"id_inventario":identifier,
                "id_producto":"p","id_rack":rack,"stock_actual":stock,"stock_minimo":1,"stock_maximo":40})
            assert result.status_code==201,result.text
        totals=await request(app,"GET",f"/inventarios/{identifier}/productos")
        assert totals.json()[0]["stock_actual"]==15
        assert "stock_minimo" not in totals.json()[0]
        filtered=await request(app,"GET",f"/inventarios/{identifier}/detalles",params={"id_zona":"z","id_rack":"r2"})
        assert len(filtered.json())==1 and filtered.json()[0]["stock_actual"]==5
        extra=await request(app,"POST","/inventarios",json={"id_almacen":"a","stock_actual":5})
        assert extra.status_code==422
    run(scenario())

@pytest.mark.parametrize("horizon",[1,7,30,90])
def test_forecast_http_horizons_and_dates(app,db,horizon):
    async def scenario():
        result=await request(app,"GET","/forecast/almacenes/a/productos/p",params={"horizonte_dias":horizon})
        assert result.status_code==200,result.text
        payload=result.json()
        assert payload["horizonte_dias"]==horizon
        expected="HISTORIAL_INSUFICIENTE" if horizon<=7 else "MODELO_NO_DISPONIBLE"
        assert payload["estado"]==expected
        assert payload["demanda_total_estimada"] is None and payload["predicciones_diarias"]==[]
    run(scenario())

def test_permissions_and_legacy_forecast_require_product(app,db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        path=f"/forecast/predict-7-days/{header['id_inventario']}"
        assert (await request(app,"GET",path)).status_code==422
        result=await request(app,"GET",path,params={"id_producto":"p"})
        assert result.status_code==200
        assert (await request(app,"GET","/forecast/almacenes/foreign/productos/p")).status_code==404
        assert (await request(app,"GET","/forecast/almacenes/a/productos/f")).status_code==404
        assert (await request(app,"GET","/forecast/almacenes/a/productos/p",params={"horizonte_dias":14})).status_code==422
        assert (await request(app,"POST","/inventarios",json={"id_almacen":"b"})).status_code==403
    run(scenario())

def test_public_movement_requires_detail_and_preserves_allowed_motives(app,db):
    async def scenario():
        header=await InventarioRepository().garantizar("a")
        row=await detail(header)
        body={"id_inventario":header["id_inventario"],"tipo_movimiento":"SALIDA","motivo_movimiento":"VENTA","cantidad":3}
        assert (await request(app,"POST","/movimientos",json=body)).status_code==422
        body["id_detalle_inventario"]=row["id_detalle_inventario"]
        result=await request(app,"POST","/movimientos",json=body)
        assert result.status_code==201,result.text
        assert result.json()["stock_nuevo"]==7 and result.json()["id_almacen"]=="a"
        history=await request(app,"GET",f"/inventarios/{header['id_inventario']}/historial")
        assert history.status_code==200,history.text
        movement=next(r for r in history.json() if r["id_movimiento"])
        assert movement["id_movimiento"]==result.json()["id_movimiento"]
        assert movement["stock_anterior"]==10 and movement["stock_nuevo"]==7
        body.update(tipo_movimiento="ENTRADA",motivo_movimiento="RECEPCION")
        assert (await request(app,"POST","/movimientos",json=body)).status_code==422
    run(scenario())
