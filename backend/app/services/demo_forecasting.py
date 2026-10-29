"""Explicit operational demo fixtures, separate from historical CSV observations."""
from collections import defaultdict

from app.database.mongodb import get_database
from app.dto.almacen_dto import AlmacenCreate
from app.dto.producto_dto import ProductoCreate
from app.dto.zona_dto import ZonaCreate
from app.dto.rack_dto import RackCreate
from app.dto.proveedor_dto import ProveedorCreate
from app.dto.detalle_inventario_dto import DetalleInventarioCreate
from app.dto.orden_reposicion_dto import OrdenReposicionCreate
from app.dto.detalle_reposicion_dto import DetalleReposicionCreate
from app.services.almacen_service import AlmacenService
from app.services.producto_service import ProductoService
from app.services.zona_service import ZonaService
from app.services.rack_service import RackService
from app.services.proveedor_service import ProveedorService
from app.services.detalle_inventario_service import DetalleInventarioService
from app.services.orden_reposicion_service import OrdenReposicionService
from app.repositories.inventario_repository import InventarioRepository
from app.services.importar_demanda import import_rows


async def prepare_demo(tenant, rows):
    db = get_database()
    if db.name != 'psitwin_demo10_test': raise ValueError('La demo solo puede escribirse en psitwin_demo10_test')
    products = {r['id_producto'] for r in rows}
    if len(products) != 10: raise ValueError('La demo requiere exactamente 10 productos distintos')
    inserted = defaultdict(int)

    async def ensure(collection, query, creator):
        doc = await db[collection].find_one(query, {'_id': 0})
        if doc: return doc
        doc = await creator()
        inserted[collection] += 1
        return doc

    warehouse_map, rack_map, inventory_map, product_map = {}, {}, {}, {}
    for i, source in enumerate(sorted({r['id_almacen'] for r in rows}), 1):
        name = f'Almacén demo {i:02d}'
        warehouse = await ensure('almacenes', {'id_empresa': tenant, 'nombre': name}, lambda: AlmacenService.crear(
            AlmacenCreate(id_empresa=tenant, nombre=name, longitud=-77.0428, latitud=-12.0464,
                          area_m2=1000, aforo=20, tipo_almacen='DEMO - datos de prueba')))
        wid = warehouse.get('id', warehouse.get('id_almacen'))
        warehouse_map[source] = wid
        zone = await ensure('zonas', {'id_almacen': wid, 'nombre': 'Zona demo'}, lambda: ZonaService.crear(
            ZonaCreate(id_almacen=wid, nombre='Zona demo', tipo_zona='DEMO', capacidad=1)))
        zid = zone.get('id', zone.get('id_zona'))
        rack = await ensure('racks', {'id_zona': zid, 'codigo': 'DEMO-01'}, lambda: RackService().crear_rack(
            RackCreate(id_zona=zid, codigo='DEMO-01', nivel=1, capacidad=10000)))
        rack_map[source] = rack.get('id_rack', rack.get('id'))
        inventory_map[source] = (await InventarioRepository().garantizar(wid))['id_inventario']

    supplier = await ensure('proveedores', {'id_empresa': tenant, 'ruc': '00000000001'}, lambda: ProveedorService().crear(
        ProveedorCreate(id_empresa=tenant, nombre='Proveedor demo (sin envíos reales)', ruc='00000000001', tiempo_entrega_estimado_dias=3)))
    for i, source in enumerate(sorted(products)):
        sample = next(r for r in rows if r['id_producto'] == source)
        name = f"Producto {sample['producto_original']} (demo)"
        product = await ensure('productos', {'id_empresa': tenant, 'nombre': name}, lambda: ProductoService.crear(
            ProductoCreate(id_empresa=tenant, id_proveedor=supplier['id_proveedor'], nombre=name,
                           categoria=sample['categoria'], familia=sample['categoria'], marca='DEMO',
                           peso=1, lead_time_dias=3, vida_util_dias=365)))
        product_map[source] = product['id_producto']
    pairs = sorted({(r['id_almacen'], r['id_producto']) for r in rows})
    for i, (w, p) in enumerate(pairs):
        query = {'id_inventario': inventory_map[w], 'id_producto': product_map[p], 'id_rack': rack_map[w]}
        await ensure('detalles_inventario', query, lambda: DetalleInventarioService()._crear_detalle(
            DetalleInventarioCreate(**query, stock_actual=25 + 5 * (i % 10), stock_minimo=30, stock_maximo=500)))
    mapped = [{**row, 'id_almacen_origen': row['id_almacen'], 'id_producto_origen': row['id_producto'],
               'id_almacen': warehouse_map[row['id_almacen']], 'id_producto': product_map[row['id_producto']]}
              for row in rows]
    history = await import_rows(tenant, mapped, dry_run=False)
    for i in range(3):
        w = pairs[i % len(pairs)][0]
        selected = sorted({p for source_w, p in pairs if source_w == w})[i::3]
        if not selected: selected = [pairs[i % len(pairs)][1]]
        note = f'DEMO10-{i + 1}: solicitud de prueba, sin compra ni envío real'
        await ensure('ordenes_reposicion', {'id_empresa': tenant, 'observacion': note}, lambda: OrdenReposicionService().crear(
            OrdenReposicionCreate(id_empresa=tenant, id_almacen=warehouse_map[w], id_proveedor=supplier['id_proveedor'],
                observacion=note, lineas=[DetalleReposicionCreate(id_producto=product_map[p], cantidad_solicitada=20) for p in selected])))
    await db['demo_config'].update_one({'id_empresa': tenant}, {'$setOnInsert': {
        'id_empresa': tenant, 'tipo': 'DEMO10', 'productos': 10,
        'stock_origen': 'Fixture demo: 25 + 5 * índice de ubicación; nunca cantidad del CSV',
        'metadatos_origen': 'Ubicación, peso, capacidad, plazos y solicitudes son configuración ficticia de prueba',
        'mapeo_productos': product_map, 'mapeo_almacenes': warehouse_map}}, upsert=True)
    return {'creados': dict(inserted), 'historico': history, 'productos': len(products), 'series': len(pairs)}
