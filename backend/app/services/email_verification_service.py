from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.config.settings import settings
from app.database.mongodb import get_database


class EmailVerificationService:
    COLLECTION_NAME = "email_verifications"
    ENTITY_COLLECTIONS = {
        "empresa": "empresas",
        "operario": "operarios",
        "proveedor": "proveedores",
    }

    def __init__(
        self,
        database_provider: Callable[[], Any] | None = None,
        sender: Callable[..., Any] | None = None,
    ):
        self.database_provider = database_provider or get_database
        self.sender = sender or self._send_email

    def database(self):
        return self.database_provider()

    @staticmethod
    def normalize_email(email: str | None) -> str:
        return str(email or "").strip().lower()

    @staticmethod
    def generate_code(length: int = 6) -> str:
        return "".join(
            secrets.choice("0123456789")
            for _ in range(length)
        )

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    async def _get_entity_record(self, entity_type: str, entity_id: str):
        collection_name = self.ENTITY_COLLECTIONS.get(entity_type.lower())
        if not collection_name:
            return None
        collection = self.database()[collection_name]
        return await collection.find_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {"_id": 0},
        )

    async def _upsert_entity_email_status(
        self,
        entity_type: str,
        entity_id: str,
        email: str,
        *,
        verified: bool,
    ):
        entity = await self._get_entity_record(entity_type, entity_id)
        if entity is None:
            return None

        collection_name = self.ENTITY_COLLECTIONS.get(entity_type.lower())
        if not collection_name:
            return None

        collection = self.database()[collection_name]
        payload = {
            "correo": email,
            "correo_verificado": verified,
        }
        if verified:
            payload["fecha_verificacion_correo"] = datetime.now(timezone.utc)
        else:
            payload["fecha_verificacion_correo"] = None

        await collection.update_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {"$set": payload},
        )

        return await collection.find_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {"_id": 0},
        )

    async def request_entity_verification(
        self,
        entity_type: str,
        entity_id: str,
    ) -> dict[str, Any]:
        entity = await self._get_entity_record(entity_type, entity_id)
        if not entity:
            return {"status": "ERROR", "reason": "Entidad no encontrada"}

        result = await self.request_verification(
            entity_type,
            entity_id,
            entity.get("correo"),
        )
        verification = result.get("verification") or {}
        return {
            "status": result.get("status"),
            "email": result.get("email") or verification.get("email"),
            "remaining_seconds": result.get("remaining_seconds"),
            "reason": result.get("reason"),
        }

    async def verify_entity_code(
        self,
        entity_type: str,
        entity_id: str,
        code: str,
    ) -> dict[str, Any]:
        entity = await self._get_entity_record(entity_type, entity_id)
        if not entity:
            return {
                "verified": False,
                "status": "NOT_FOUND",
            }

        result = await self.verify_code(
            entity_type,
            entity_id,
            entity.get("correo"),
            code,
        )
        updated_entity = result.get("entity") or {}
        return {
            "verified": bool(result.get("verified")),
            "status": result.get("status"),
            "email": updated_entity.get("correo") or entity.get("correo"),
            "attempts": result.get("attempts"),
            "remaining_attempts": result.get("remaining_attempts"),
        }

    async def request_verification(
        self,
        entity_type: str,
        entity_id: str,
        email: str,
        *,
        expires_minutes: int | None = None,
        max_attempts: int | None = None,
        cooldown_seconds: int | None = None,
    ) -> dict[str, Any]:
        normalized_email = self.normalize_email(email)
        if not normalized_email:
            return {"status": "ERROR", "reason": "Correo requerido"}

        expires_minutes = expires_minutes or settings.email_verification_ttl_minutes
        max_attempts = max_attempts or settings.email_verification_max_attempts
        cooldown_seconds = cooldown_seconds or settings.email_verification_cooldown_seconds

        entity = await self._get_entity_record(entity_type, entity_id)
        if not entity:
            return {"status": "ERROR", "reason": "Entidad no encontrada"}

        collection = self.database()[self.COLLECTION_NAME]
        existing = await collection.find_one(
            {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": normalized_email,
            },
            {"_id": 0},
        )

        if existing:
            now = datetime.now(timezone.utc)
            expires_at = self._as_utc(existing.get("expires_at"))
            if expires_at is not None and expires_at > now:
                cooldown_until = self._as_utc(existing.get("cooldown_until"))
                if cooldown_until is not None and cooldown_until > now:
                    return {
                        "status": "COOLDOWN",
                        "remaining_seconds": max(
                            0,
                            int((cooldown_until - now).total_seconds()),
                        ),
                        "email": normalized_email,
                    }

        code = self.generate_code()
        now = datetime.now(timezone.utc)
        verification = {
            "entity_type": entity_type.lower(),
            "entity_id": entity_id,
            "email": normalized_email,
            "code_hash": self.hash_code(code),
            "expires_at": now + timedelta(minutes=expires_minutes),
            "attempts": 0,
            "max_attempts": max_attempts,
            "cooldown_until": now + timedelta(seconds=cooldown_seconds),
            "used": False,
            "status": "PENDING",
            "created_at": now,
            "updated_at": now,
        }

        await collection.update_one(
            {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": normalized_email,
            },
            {"$set": verification},
            upsert=True,
        )

        subject = f"[PsiTwin] Verificación de email - {entity_type.title()}"
        body = "\n".join(
            [
                "PsiTwin verifica tu dirección de correo.",
                f"Entidad: {entity_type.title()}",
                f"Correo: {normalized_email}",
                "Tu código temporal es:",
                code,
                f"Este código expira en {expires_minutes} minutos y solo puede usarse una vez.",
            ]
        )

        try:
            self.sender(normalized_email, subject, body)
        except Exception:
            return {
                "status": "ERROR",
                "reason": "No se pudo enviar el correo de verificación",
                "email": normalized_email,
            }
        return {
            "status": "SENT",
            "verification": {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": normalized_email,
                "expires_at": verification["expires_at"],
                "max_attempts": max_attempts,
                "cooldown_seconds": cooldown_seconds,
            },
        }

    async def verify_code(
        self,
        entity_type: str,
        entity_id: str,
        email: str,
        code: str,
    ) -> dict[str, Any]:
        normalized_email = self.normalize_email(email)
        collection = self.database()[self.COLLECTION_NAME]
        record = await collection.find_one(
            {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": normalized_email,
            },
            {"_id": 0},
        )

        if not record:
            return {"verified": False, "status": "NOT_FOUND"}

        if record.get("used"):
            return {"verified": False, "status": "REUSED"}

        now = datetime.now(timezone.utc)
        expires_at = self._as_utc(record.get("expires_at"))
        if expires_at is not None and expires_at < now:
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {"$set": {"used": True, "status": "EXPIRED", "updated_at": now}},
            )
            return {"verified": False, "status": "EXPIRED"}

        attempts = int(record.get("attempts", 0))
        max_attempts = int(record.get("max_attempts", 5))
        if attempts >= max_attempts:
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {"$set": {"used": True, "status": "LOCKED", "updated_at": now}},
            )
            return {
                "verified": False,
                "status": "MAX_ATTEMPTS",
                "attempts": attempts,
            }

        if record.get("code_hash") != self.hash_code(str(code)):
            attempts += 1
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {
                    "$set": {
                        "attempts": attempts,
                        "status": "INVALID_CODE",
                        "updated_at": now,
                    }
                },
            )
            return {
                "verified": False,
                "status": "INVALID_CODE",
                "attempts": attempts,
                "remaining_attempts": max_attempts - attempts,
            }

        await collection.update_one(
            {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": normalized_email,
            },
            {"$set": {"used": True, "status": "VERIFIED", "updated_at": now}},
        )

        updated_entity = await self._upsert_entity_email_status(
            entity_type,
            entity_id,
            normalized_email,
            verified=True,
        )

        return {
            "verified": True,
            "status": "VERIFIED",
            "entity": updated_entity,
        }

    async def invalidate_on_email_change(
        self,
        entity_type: str,
        entity_id: str,
        old_email: str,
        new_email: str,
    ):
        old_email_norm = self.normalize_email(old_email)
        new_email_norm = self.normalize_email(new_email)
        if not old_email_norm or old_email_norm == new_email_norm:
            return {"correo_verificado": False, "correo": new_email_norm}

        collection_name = self.ENTITY_COLLECTIONS.get(entity_type.lower())
        if not collection_name:
            return {"correo_verificado": False, "correo": new_email_norm}

        collection = self.database()[collection_name]
        record = await collection.find_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {"_id": 0},
        )
        if record is None:
            return {"correo_verificado": False, "correo": new_email_norm}

        updated = await collection.update_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {
                "$set": {
                    "correo": new_email_norm,
                    "correo_verificado": False,
                    "fecha_verificacion_correo": None,
                }
            },
        )

        validation_collection = self.database()[self.COLLECTION_NAME]
        await validation_collection.update_one(
            {
                "entity_type": entity_type.lower(),
                "entity_id": entity_id,
                "email": old_email_norm,
            },
            {
                "$set": {
                    "used": True,
                    "status": "INVALIDATED_BY_EMAIL_CHANGE",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        matched = getattr(updated, "matched_count", 1 if updated is not None else 0)
        if matched == 0:
            return {"correo_verificado": False, "correo": new_email_norm}

        return await collection.find_one(
            {
                "$or": [
                    {"id_empresa": entity_id},
                    {"id_operario": entity_id},
                    {"id_proveedor": entity_id},
                    {"id": entity_id},
                ]
            },
            {"_id": 0},
        )

    def _send_email(self, recipient: str, subject: str, body: str):
        if settings.email_enabled and all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_password,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            from email.message import EmailMessage
            import smtplib

            message = EmailMessage()
            message["From"] = settings.smtp_from or settings.smtp_user
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
        return {"status": "MOCKED", "recipient": recipient, "subject": subject}
