from pydantic import BaseModel, Field


class EmailVerificationCodeRequest(BaseModel):
    codigo: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class EmailVerificationSendResponse(BaseModel):
    status: str
    email: str | None = None
    remaining_seconds: int | None = None
    reason: str | None = None


class EmailVerificationResponse(BaseModel):
    verified: bool
    status: str
    email: str | None = None
    attempts: int | None = None
    remaining_attempts: int | None = None