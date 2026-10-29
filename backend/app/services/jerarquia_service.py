from datetime import datetime, timezone
from uuid import uuid4, uuid5, NAMESPACE_URL
from fastapi import HTTPException
from app.database.mongodb import get_database
from app.services.stock_lock import bloqueo_recurso
from app.services.acceso_service import AccesoService


class JerarquiaService:
    @staticmethod
    async def guardar_almacen(data, identifier=None):
        from app.services.almacen_service import AlmacenService
        from app.repositories.almacen_repository import AlmacenRepository
        current = await AlmacenRepository.obtener_por_id(identifier) if identifier else None
        if identifier and not current:
            raise HTTPException(404, 'Almacén no encontrado')
        tenant = current['id_empresa'] if current else data.id_empresa
        async with bloqueo_recurso('empresa-ubicaciones:' + tenant):
            code = getattr(data, 'codigo', None)
            if code is not None:
                code = code.strip().upper()
                if not code:
                    raise HTTPException(422, 'El código del almacén no puede estar vacío')
                data.codigo = code
                if any(row.get('id', row.get('id_almacen')) != identifier and (row.get('codigo') or '').strip().upper() == code
                       for row in await AlmacenRepository.obtener_por_empresa(tenant)):
                    raise HTTPException(409, 'Código de almacén duplicado en la empresa')
            if identifier:
                return await AlmacenService._actualizar(identifier, data)
            return await AlmacenService._crear(data)

    @staticmethod
    async def crear_zona(data):
        from app.services.zona_service import ZonaService
        from app.repositories.zona_repository import ZonaRepository
        async with bloqueo_recurso('almacen:' + data.id_almacen):
            from app.repositories.almacen_repository import AlmacenRepository
            warehouse = await AlmacenRepository.obtener_por_id(data.id_almacen)
            if not warehouse or warehouse.get('estado', 'ACTIVO') != 'ACTIVO':
                raise HTTPException(409, 'El almacén no está disponible')
            existing = await ZonaRepository.obtener_por_almacen(data.id_almacen)
            code = (data.codigo or data.nombre).strip().upper()
            if any((z.get('codigo') or z.get('nombre', '')).strip().upper() == code for z in existing):
                raise HTTPException(409, 'Código de zona duplicado en el almacén')
            data.codigo = code
            data.capacidad = data.max_racks if data.max_racks is not None else data.capacidad
            return await ZonaService._crear(data)

    @staticmethod
    async def actualizar_zona(identifier, data):
        from app.services.zona_service import ZonaService
        from app.repositories.zona_repository import ZonaRepository
        from app.repositories.rack_repository import RackRepository
        current = await ZonaRepository.obtener_por_id(identifier)
        if not current:
            raise HTTPException(404, 'Zona no encontrada')
        async with bloqueo_recurso('almacen:' + current['id_almacen']), bloqueo_recurso('zona:' + identifier):
            maximum = data.max_racks if data.max_racks is not None else data.capacidad
            if maximum is not None:
                if maximum < len(await RackRepository.obtener_por_zona(identifier)):
                    raise HTTPException(409, 'El máximo no puede ser menor que los racks existentes')
                data.capacidad = maximum
                data.max_racks = maximum
            if data.codigo is not None:
                data.codigo = data.codigo.strip().upper()
                if any(z.get('id', z.get('id_zona')) != identifier and (z.get('codigo') or z.get('nombre', '')).strip().upper() == data.codigo
                       for z in await ZonaRepository.obtener_por_almacen(current['id_almacen'])):
                    raise HTTPException(409, 'Código de zona duplicado')
            return await ZonaService._actualizar(identifier, data)

    @staticmethod
    async def crear_rack(service, data):
        from app.repositories.zona_repository import ZonaRepository
        from app.repositories.rack_repository import RackRepository
        async with bloqueo_recurso('zona:' + data.id_zona):
            zone = await ZonaRepository.obtener_por_id(data.id_zona)
            if not zone:
                raise HTTPException(404, 'Zona no encontrada')
            if zone.get('estado', 'ACTIVO') != 'ACTIVO':
                raise HTTPException(409, 'La zona no está disponible')
            racks = await RackRepository.obtener_por_zona(data.id_zona)
            if len(racks) >= (zone.get('max_racks') if zone.get('max_racks') is not None else zone.get('capacidad', 0)):
                raise HTTPException(409, 'La zona alcanzó su máximo de racks')
            result = await service._crear_rack(data)
            await JerarquiaService.asegurar_niveles(result)
            return result

    @staticmethod
    async def niveles(user, rack_id):
        await AccesoService.verificar_rack(user, rack_id)
        return await get_database()["niveles"].find({'id_rack': rack_id}, {'_id': 0}).sort('numero', 1).to_list(length=1000)

    @staticmethod
    async def crear_nivel(user, rack_id, data):
        rack = await AccesoService.verificar_rack(user, rack_id)
        async with bloqueo_recurso('rack:' + rack_id):
            rows = await get_database()["niveles"].find({'id_rack': rack_id}, {'_id': 0}).to_list(length=1000)
            maximum = rack.get('max_niveles', 1)
            if data.numero > maximum or len(rows) >= maximum:
                raise HTTPException(409, 'El rack alcanzó su máximo de niveles')
            code = data.codigo.strip().upper()
            if not code or any(r['codigo'] == code or r['numero'] == data.numero for r in rows):
                raise HTTPException(409, 'Código o número de nivel duplicado')
            row = {'id_nivel': str(uuid4()), 'id_rack': rack_id, 'codigo': code, 'numero': data.numero,
                   'id_empresa': user.id_empresa, 'fecha_creacion': datetime.now(timezone.utc)}
            await get_database()["niveles"].insert_one(row)
            row.pop('_id', None)
            return row

    @staticmethod
    async def actualizar_nivel(user, identifier, data):
        db = get_database()
        level = await db['niveles'].find_one({'id_nivel': identifier}, {'_id': 0})
        if not level:
            raise HTTPException(404, 'Nivel no encontrado')
        await AccesoService.verificar_rack(user, level['id_rack'])
        async with bloqueo_recurso('rack:' + level['id_rack']):
            changes = data.model_dump(exclude_none=True)
            if 'codigo' in changes:
                changes['codigo'] = changes['codigo'].strip().upper()
                duplicate = await db['niveles'].find_one({'id_rack': level['id_rack'], 'codigo': changes['codigo'], 'id_nivel': {'$ne': identifier}})
                if not changes['codigo'] or duplicate:
                    raise HTTPException(409, 'Código de nivel vacío o duplicado')
            changes['fecha_actualizacion'] = datetime.now(timezone.utc)
            await db['niveles'].update_one({'id_nivel': identifier}, {'$set': changes})
            return await db['niveles'].find_one({'id_nivel': identifier}, {'_id': 0})

    @staticmethod
    async def eliminar_nivel(user, identifier):
        db = get_database()
        level = await db["niveles"].find_one({'id_nivel': identifier})
        if not level:
            raise HTTPException(404, 'Nivel no encontrado')
        await AccesoService.verificar_rack(user, level['id_rack'])
        async with bloqueo_recurso('rack:' + level['id_rack']):
            if any([await db[name].find_one({'id_nivel': identifier}) for name in ('detalles_inventario', 'detalles_recepcion', 'movimientos', 'dispositivos', 'alertas', 'lecturas')]):
                raise HTTPException(409, 'El nivel tiene inventario asociado; requiere reubicación controlada')
            await db["niveles"].delete_one({'id_nivel': identifier})
            return {'mensaje': 'Nivel eliminado'}

    @staticmethod
    async def asegurar_niveles(rack):
        identifier = rack['id_rack']
        async with bloqueo_recurso('rack:' + identifier):
            db = get_database()
            rows = await db['niveles'].find({'id_rack': identifier}, {'_id': 0}).to_list(length=None)
            maximum = rack.get('max_niveles', 1)
            if any(row['numero'] > maximum for row in rows):
                raise HTTPException(409, 'Existen niveles fuera de la capacidad; requiere revisión')
            for number in range(1, maximum + 1):
                if any(row['numero'] == number for row in rows): continue
                key = str(uuid5(NAMESPACE_URL, f'psitwin-nivel:{identifier}:{number}'))
                code = f'N-{number}'
                if any(row['codigo'] == code for row in rows): code = f'AUTO-{number}-{key[:6]}'
                await db['niveles'].update_one({'id_rack': identifier, 'numero': number}, {'$setOnInsert': {
                    'id_nivel': key, 'id_rack': identifier, 'numero': number, 'codigo': code,
                    'estado': 'ACTIVO', 'fecha_creacion': datetime.now(timezone.utc)}}, upsert=True)
            return await db['niveles'].find({'id_rack': identifier}, {'_id': 0}).sort('numero', 1).to_list(length=None)
