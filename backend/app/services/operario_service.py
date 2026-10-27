from typing import (
    Any,
    Dict,
    List
)

from fastapi import HTTPException, status

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.operario_dto import (
    OperarioCreate,
    OperarioUpdate,
    OperarioResetPassword
)

from app.services.cuenta_service import (
    sanitizar_cuenta,
    validar_correo_disponible
)

from app.repositories.operario_repository import (
    OperarioRepository
)

from app.repositories.empresa_repository import (
    EmpresaRepository
)

from app.repositories.almacen_repository import (
    AlmacenRepository
)

from app.utils.security import (
    hash_password
)


class OperarioService:

    # ============================================================
    # SANITIZAR
    #
    # Nunca exponer password_hash.
    # ============================================================

    @staticmethod
    def sanitizar(
        operario: Dict[str, Any]
    ) -> Dict[str, Any]:

        return sanitizar_cuenta(
            operario
        )


    def sanitizar_lista(
        self,
        operarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        return [
            self.sanitizar(operario)
            for operario in operarios
        ]


    # ============================================================
    # VALIDAR CORREO UNICO
    #
    # Único entre empresas, operarios y proveedores.
    # ============================================================

    @staticmethod
    async def validar_correo_disponible(
        correo: str,
        id_operario_actual: str | None = None
    ) -> str:

        return await validar_correo_disponible(
            correo,
            id_operario_actual
        )


    # ============================================================
    # VALIDAR ALMACEN DE LA EMPRESA
    # ============================================================

    @staticmethod
    async def validar_almacen(
        id_empresa: str,
        id_almacen: str
    ) -> None:

        almacen = await (
            AlmacenRepository
            .obtener_por_id(
                id_almacen
            )
        )

        if (
            not almacen
            or
            almacen.get("id_empresa")
            != id_empresa
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El almacén del operario no pertenece "
                    "a la empresa"
                )
            )


    # ============================================================
    # CREAR
    #
    # id_empresa se toma del token.
    # Queda con debe_cambiar_password = true.
    # ============================================================

    async def crear_operario(
        self,
        data: OperarioCreate,
        user: UsuarioActual
    ):

        empresa = await (
            EmpresaRepository
            .obtener_por_id(
                user.id_empresa
            )
        )

        if not empresa:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Empresa no encontrada"
            )

        await self.validar_almacen(
            user.id_empresa,
            data.id_almacen
        )

        correo = await (
            self.validar_correo_disponible(
                str(data.correo)
            )
        )

        operario_data = {

            "id_empresa":
                user.id_empresa,

            "id_almacen":
                data.id_almacen,

            "nombre":
                data.nombre.strip(),

            "apellido":
                data.apellido.strip(),

            "cargo":
                data.cargo.strip(),

            "turno":
                data.turno.strip().upper(),

            "estado":
                data.estado.strip().upper(),

            "correo":
                correo,

            "correo_verificado":
                False,

            "fecha_verificacion_correo":
                None,

            "password_hash":
                hash_password(
                    data.password_temporal
                ),

            "debe_cambiar_password":
                True
        }

        creado = await (
            OperarioRepository
            .crear(
                operario_data
            )
        )

        return self.sanitizar(
            creado
        )


    # ============================================================
    # OBTENER TODOS (DE LA EMPRESA)
    # ============================================================

    async def obtener_operarios(
        self,
        user: UsuarioActual
    ):

        return self.sanitizar_lista(
            await (
                OperarioRepository
                .obtener_por_empresa(
                    user.id_empresa
                )
            )
        )


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    async def obtener_operario(
        self,
        id_operario: str,
        user: UsuarioActual
    ):

        operario = await (
            OperarioRepository
            .obtener_por_id(
                id_operario
            )
        )

        if (
            not operario
            or
            operario.get("id_empresa")
            != user.id_empresa
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Operario no encontrado"
            )

        return self.sanitizar(
            operario
        )


    # ============================================================
    # OBTENER POR EMPRESA
    # ============================================================

    async def obtener_por_empresa(
        self,
        id_empresa: str,
        user: UsuarioActual
    ):

        if id_empresa != user.id_empresa:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Empresa no encontrada"
            )

        return await self.obtener_operarios(
            user
        )


    # ============================================================
    # OBTENER POR ESTADO
    # ============================================================

    async def obtener_por_estado(
        self,
        estado: str,
        user: UsuarioActual
    ):

        estado = (
            estado
            .strip()
            .upper()
        )

        operarios = await (
            OperarioRepository
            .obtener_por_estado(
                estado
            )
        )

        return self.sanitizar_lista(
            [
                operario
                for operario in operarios
                if operario.get("id_empresa")
                == user.id_empresa
            ]
        )


    # ============================================================
    # OBTENER POR TURNO
    # ============================================================

    async def obtener_por_turno(
        self,
        turno: str,
        user: UsuarioActual
    ):

        turno = (
            turno
            .strip()
            .upper()
        )

        operarios = await (
            OperarioRepository
            .obtener_por_turno(
                turno
            )
        )

        return self.sanitizar_lista(
            [
                operario
                for operario in operarios
                if operario.get("id_empresa")
                == user.id_empresa
            ]
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    async def actualizar_operario(
        self,
        id_operario: str,
        data: OperarioUpdate,
        user: UsuarioActual
    ):

        operario = await self.obtener_operario(
            id_operario,
            user
        )

        update_data = (
            data.model_dump(
                exclude_unset=True
            )
        )

        update_data = {
            campo: valor
            for campo, valor in update_data.items()
            if valor is not None
        }

        if not update_data:
            return operario


        if "id_almacen" in update_data:

            await self.validar_almacen(
                user.id_empresa,
                update_data["id_almacen"]
            )


        if "correo" in update_data:

            update_data[
                "correo"
            ] = await (
                self.validar_correo_disponible(
                    str(update_data["correo"]),
                    id_operario
                )
            )

            # Correo distinto -> hay que verificarlo de nuevo
            if (
                (operario.get("correo") or "").lower()
                != update_data["correo"]
            ):
                update_data["correo_verificado"] = False
                update_data["fecha_verificacion_correo"] = None


        for campo in [
            "nombre",
            "apellido",
            "cargo"
        ]:

            if campo in update_data:

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ].strip()
                )


        for campo in [
            "turno",
            "estado"
        ]:

            if campo in update_data:

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ]
                    .strip()
                    .upper()
                )


        actualizado = await (
            OperarioRepository
            .actualizar(
                id_operario,
                update_data
            )
        )

        if not actualizado:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Operario no encontrado"
            )

        return self.sanitizar(
            actualizado
        )


    # ============================================================
    # RESET PASSWORD (EMPRESA)
    #
    # También da credenciales a operarios antiguos:
    # si no tienen correo, deben tenerlo antes
    # (PUT /operarios/{id} con "correo").
    # ============================================================

    async def reset_password(
        self,
        id_operario: str,
        data: OperarioResetPassword,
        user: UsuarioActual
    ):

        operario = await self.obtener_operario(
            id_operario,
            user
        )

        if data.correo is not None:

            correo = await (
                self.validar_correo_disponible(
                    str(data.correo),
                    id_operario
                )
            )

            await (
                OperarioRepository
                .actualizar(
                    id_operario,
                    {
                        "correo": correo
                    }
                )
            )

        elif not operario.get("correo"):

            raise HTTPException(
                status_code=
                    status.HTTP_409_CONFLICT,
                detail=(
                    "El operario no tiene correo. "
                    "Envíe 'correo' en el body "
                    "(o asígnelo con PUT /operarios/{id})"
                )
            )

        actualizado = await (
            OperarioRepository
            .actualizar_password(
                id_operario,
                hash_password(
                    data.password_temporal
                ),
                True
            )
        )

        return self.sanitizar(
            actualizado
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    async def eliminar_operario(
        self,
        id_operario: str,
        user: UsuarioActual
    ):

        await self.obtener_operario(
            id_operario,
            user
        )

        eliminado = await (
            OperarioRepository
            .eliminar(
                id_operario
            )
        )

        if not eliminado:

            raise HTTPException(
                status_code=
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=
                    "No se pudo eliminar el operario"
            )

        return {
            "mensaje":
                "Operario eliminado correctamente"
        }
