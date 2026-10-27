from fastapi import APIRouter, Depends
from app.dependencies.dependencies import require_empresa_u_operario
from app.dto.auth_dto import UsuarioActual
from app.dto.inventario_dto import InventarioCreate, InventarioResponse, InventarioHistorialResponse
from app.dto.detalle_inventario_dto import DetalleInventarioResponse
from app.services.acceso_service import AccesoService
from app.services.inventario_service import InventarioService
from app.repositories.inventario_repository import InventarioRepository

router = APIRouter(prefix="/inventarios", tags=["Inventario general"])
service = InventarioService()

@router.post("", response_model=InventarioResponse)
async def garantizar(data: InventarioCreate, user: UsuarioActual = Depends(require_empresa_u_operario)):
    await AccesoService.verificar_almacen(user, data.id_almacen)
    return await service.crear_inventario(data)

@router.get("", response_model=list[InventarioResponse])
async def listar(user: UsuarioActual = Depends(require_empresa_u_operario)):
    return await InventarioRepository().obtener_por_almacenes(await AccesoService.ids_almacenes(user))

@router.get("/almacen/{id_almacen}", response_model=InventarioResponse)
async def por_almacen(id_almacen: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    from fastapi import HTTPException
    await AccesoService.verificar_almacen(user, id_almacen)
    header = await InventarioRepository().obtener_por_almacen(id_almacen)
    if not header:
        raise HTTPException(404, "Inventario general no encontrado; garantizarlo con POST /inventarios")
    return header

@router.get("/{id_inventario}/detalles", response_model=list[DetalleInventarioResponse])
async def detalles(id_inventario: str, id_producto: str | None = None,
                   id_rack: str | None = None, id_zona: str | None = None,
                   user: UsuarioActual = Depends(require_empresa_u_operario)):
    await AccesoService.verificar_inventario(user, id_inventario)
    if id_producto:
        await AccesoService.verificar_producto(user, id_producto)
    if id_rack:
        await AccesoService.verificar_rack(user, id_rack)
    if id_zona:
        await AccesoService.verificar_zona(user, id_zona)
    return await service.detalles_inventario(id_inventario, id_producto, id_rack, id_zona)

@router.get("/{id_inventario}/productos")
async def productos(id_inventario: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    await AccesoService.verificar_inventario(user, id_inventario)
    return await service.stock_por_producto(id_inventario)

@router.get("/{id_inventario}/productos/{id_producto}")
async def distribucion(id_inventario: str, id_producto: str,
                       user: UsuarioActual = Depends(require_empresa_u_operario)):
    from fastapi import HTTPException
    await AccesoService.verificar_inventario(user, id_inventario)
    await AccesoService.verificar_producto(user, id_producto)
    items = await service.stock_por_producto(id_inventario)
    return next((i for i in items if i["id_producto"] == id_producto),
                {"id_inventario": id_inventario, "id_producto": id_producto,
                 "stock_actual": 0, "stock_minimo": 0, "stock_maximo": 0, "distribucion": []})

@router.get("/{id_inventario}/historial", response_model=list[InventarioHistorialResponse])
async def historial(id_inventario: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    await AccesoService.verificar_inventario(user, id_inventario)
    return await service.obtener_historial(id_inventario)

@router.get("/{id_inventario}", response_model=InventarioResponse)
async def obtener(id_inventario: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    return await AccesoService.verificar_inventario(user, id_inventario)
