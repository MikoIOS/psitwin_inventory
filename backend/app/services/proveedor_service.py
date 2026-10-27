from fastapi import HTTPException, status

from app.dto.proveedor_dto import (
    ProveedorCreate,
    ProveedorUpdate
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.repositories.empresa_repository import (
    EmpresaRepository
)


from app.services.cuenta_service import (
    validar_correo_disponible
)

from app.utils.security import (
    hash_password
)


class ProveedorService:

    def __init__(self):
        self.repository = ProveedorRepository()

    async def crear(self, data: ProveedorCreate):

        empresa = await EmpresaRepository.obtener_por_id(
            data.id_empresa
        )

        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )

        existente = await self.repository.obtener_por_ruc(
            data.ruc
        )

        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proveedor con ese RUC"
            )

        documento = data.model_dump()

        # ----------------------------------------------------
        # CUENTA DE ACCESO (opcional)
        # ----------------------------------------------------

        password_temporal = documento.pop(
            "password_temporal",
            None
        )

        if password_temporal:

            if not data.correo:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "El correo es obligatorio para "
                        "crear la cuenta del proveedor"
                    )
                )

            await validar_correo_disponible(
                str(data.correo)
            )

            documento["password_hash"] = hash_password(
                password_temporal
            )
            documento["debe_cambiar_password"] = True

        documento["correo"] = str(documento.get("correo") or "").strip().lower() if documento.get("correo") else None
        documento["estado"] = data.estado.value
        documento["correo_verificado"] = False
        documento["fecha_verificacion_correo"] = None

        return await self.repository.crear(documento)

    async def obtener_todos(self):
        return await self.repository.obtener_todos()

    async def obtener_por_id(self, id_proveedor: str):

        proveedor = await self.repository.obtener_por_id(
            id_proveedor
        )

        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado"
            )

        return proveedor

    async def obtener_por_empresa(self, id_empresa: str):

        return await self.repository.obtener_por_empresa(
            id_empresa
        )

    async def obtener_por_estado(self, estado: str):

        return await self.repository.obtener_por_estado(
            estado
        )

    async def actualizar(
        self,
        id_proveedor: str,
        data: ProveedorUpdate
    ):

        proveedor = await self.obtener_por_id(id_proveedor)

        cambios = data.model_dump(
            exclude_unset=True
        )

        if "correo" in cambios and cambios["correo"] is not None:
            cambios["correo"] = str(cambios["correo"]).strip().lower()
            if proveedor.get("password_hash"):
                await validar_correo_disponible(
                    cambios["correo"],
                    id_proveedor
                )
            if proveedor.get("correo") and proveedor.get("correo").lower() != cambios["correo"]:
                cambios["correo_verificado"] = False
                cambios["fecha_verificacion_correo"] = None

        if "estado" in cambios:
            cambios["estado"] = cambios["estado"].value

        return await self.repository.actualizar(
            id_proveedor,
            cambios
        )

    # ========================================================
    # RESET PASSWORD (EMPRESA)
    #
    # Da o restablece la cuenta del proveedor.
    # ========================================================

    async def reset_password(
        self,
        id_proveedor: str,
        password_temporal: str,
        correo: str | None = None
    ):

        proveedor = await self.obtener_por_id(id_proveedor)

        correo = correo or proveedor.get("correo")

        if not correo:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El proveedor no tiene correo. "
                    "Envíe 'correo' en el body"
                )
            )

        cambios = {
            "correo": await validar_correo_disponible(
                correo,
                id_proveedor
            ),
            "password_hash": hash_password(
                password_temporal
            ),
            "debe_cambiar_password": True
        }

        if cambios["correo"] != (proveedor.get("correo") or "").lower():
            cambios["correo_verificado"] = False
            cambios["fecha_verificacion_correo"] = None

        return await self.repository.actualizar(
            id_proveedor,
            cambios
        )

    async def eliminar(self, id_proveedor: str):

        await self.obtener_por_id(id_proveedor)

        eliminado = await self.repository.eliminar(
            id_proveedor
        )

        if not eliminado:
            raise HTTPException(
                status_code=500,
                detail="No se pudo eliminar el proveedor"
            )

        return {
            "mensaje": "Proveedor eliminado correctamente"
        }