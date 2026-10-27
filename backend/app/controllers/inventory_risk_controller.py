from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Query
)

from app.dependencies.dependencies import (
    require_empresa
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.inventory_risk_dto import (
    InventoryRiskResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.inventory_risk_service import (
    InventoryRiskService
)


# ============================================================
# INVENTORY RISK: solo EMPRESA, sobre sus inventarios.
# ============================================================

router = APIRouter(
    prefix="/inventory-risk",
    tags=["Inventory Intelligence"]
)

service = InventoryRiskService()


@router.get(
    "",
    response_model=List[
        InventoryRiskResponse
    ],
    summary=(
        "Evaluar riesgo de todos "
        "los inventarios"
    )
)
async def evaluar_todos(
    generar_alertas: bool = Query(
        default=False,
        description=(
            "Si es true, crea o actualiza "
            "alertas y recomendaciones "
            "para inventarios con riesgo "
            "alto o crítico."
        )
    ),
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await service.evaluar_todos(
        generar_alertas=
            generar_alertas,
        ids_inventario=
            await AccesoService.ids_inventarios(
                user
            )
    )


@router.get(
    "/{id_inventario}",
    response_model=InventoryRiskResponse,
    summary=(
        "Evaluar riesgo de un inventario"
    )
)
async def evaluar_inventario(
    id_inventario: str,
    id_producto: str = Query(...),
    generar_alertas: bool = Query(
        default=True,
        description=(
            "Si es true, crea o actualiza "
            "automáticamente la alerta y "
            "la recomendación cuando existe "
            "riesgo alto o crítico."
        )
    ),
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    await AccesoService.verificar_producto(user, id_producto)
    return await service.evaluar(
        id_inventario=
            id_inventario,
        id_producto=id_producto,
        generar_alertas=
            generar_alertas
    )
