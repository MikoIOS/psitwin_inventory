import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from app.database.mongodb import get_database

_owned = ContextVar("stock_locks_owned", default=frozenset())

@asynccontextmanager
async def bloqueo_recurso(resource):
    # Reentrancia solo en la misma tarea; una tarea hija no hereda la autorización.
    owner = (id(asyncio.current_task()), resource)
    if owner in _owned.get():
        yield
        return
    token = str(uuid4())
    collection = get_database()["bloqueos_stock_rack"]
    try:
        await collection.insert_one({"_id":resource,"token":token,"fecha":datetime.now(timezone.utc)})
    except DuplicateKeyError as exc:
        raise HTTPException(409, "Operación concurrente; reintente") from exc
    state = _owned.set(_owned.get() | {owner})
    try:
        yield
    finally:
        _owned.reset(state)
        await collection.delete_one({"_id":resource,"token":token})
    # Sin TTL: expirar un lock mientras vive el escritor permitiría corrupción.
    # Tras caída del proceso, liberar manualmente solo con escritores detenidos.

def bloqueo_rack(id_rack):
    return bloqueo_recurso("rack:" + id_rack)

def bloqueo_orden(id_orden):
    return bloqueo_recurso("orden:" + id_orden)
