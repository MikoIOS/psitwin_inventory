from typing import Literal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SaikiAskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["message"],
            "examples": [
                {
                    "message": "Hola Saiki, ¿cómo está mi inventario?"
                },
                {
                    "message": "¿Qué productos tienen riesgo de quedarse sin stock?"
                },
            ],
        }
    )

    message: str | None = Field(default=None, min_length=1)
    question: str | None = Field(
        default=None,
        min_length=1,
        description="Alias legacy de message. No es necesario para nuevas consultas.",
    )
    horizonte_dias: Literal[1, 7, 30, 90] = 7
    id_inventario: str | None = None
    id_producto: str | None = None
    page: int = Field(default=1, ge=1, description="Página del detalle de inventario.")
    page_size: int = Field(default=25, ge=1, le=100)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto técnico opcional; normalmente debe omitirse.",
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historial opcional de mensajes previos.",
    )

    @model_validator(mode="after")
    def require_message(self):
        if not self.message and not self.question:
            raise ValueError("Debe indicar message o question.")
        if self.message and self.question and self.message != self.question:
            raise ValueError("message y question no pueden ser diferentes.")
        if not self.message:
            self.message = self.question
        if not self.message.strip():
            raise ValueError("message no puede contener solo espacios.")
        if len(self.history) > 40:
            raise ValueError("El historial admite hasta 40 mensajes.")
        for item in self.history:
            if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
                raise ValueError("El historial solo admite mensajes de usuario y asistente con contenido textual.")
            if len(item["content"]) > 8000:
                raise ValueError("Un mensaje del historial supera el límite de tamaño.")
            if set(item) - {"role", "content"}:
                raise ValueError("El historial no admite instrucciones de herramientas.")
        return self


class SaikiAskResponse(BaseModel):
    answer: str
    model: str
    base_url: str
    source: str = "ollama"
    context: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    visualization: dict[str, Any] = Field(
        default_factory=lambda: {"type": "none"}
    )
    sources: list[str] = Field(default_factory=list)
