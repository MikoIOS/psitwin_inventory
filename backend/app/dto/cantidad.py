"""Quantities: at most three decimals; money is stored separately as PEN cents."""
from decimal import Decimal
from typing import Annotated
from pydantic import AfterValidator, Field


def precision(value):
    if Decimal(str(value)) != Decimal(str(value)).quantize(Decimal('.001')):
        raise ValueError('La cantidad admite como máximo tres decimales')
    return value


Cantidad = Annotated[float, Field(ge=0, le=1_000_000_000, allow_inf_nan=False), AfterValidator(precision)]
