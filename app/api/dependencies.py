from base64 import urlsafe_b64decode
import json
from typing import Annotated, Any, Iterable

from fastapi import HTTPException, Query, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.enums import TenantEnum

security = HTTPBearer()

def _normalize_scope_values(scope: Any) -> set[str]:
    if scope is None:
        return set()
    if isinstance(scope, str):
        return {item for item in scope.split() if item}
    if isinstance(scope, Iterable):
        return {str(item) for item in scope if str(item)}
    return {str(scope)}


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}

    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    try:
        decoded = urlsafe_b64decode((payload_segment + padding).encode("ascii"))
        return json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested.",
        )


def _resolve_tenant_id(token: str) -> tuple[str, set[str]]:
    try:
        return TenantEnum(token).value, set()
    except ValueError:
        pass

    payload = _decode_jwt_payload(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested.",
        )

    tenant_id = payload.get("tenant_id") or payload.get("tenant") or payload.get("namespace")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested.",
        )

    return str(tenant_id), _normalize_scope_values(payload.get("scope") or payload.get("scopes") or payload.get("roles"))


def verify_tenant_namespace(
    credentials: HTTPAuthorizationCredentials = Security(security),
    requested_namespace: Annotated[str | None, Query(alias="namespace")] = None,
) -> TenantEnum:
    """
    Validates the user token, extracts the tenant ID, and ensures it matches an authorized Enum.
    """
    token = credentials.credentials

    tenant_id, scope_values = _resolve_tenant_id(token)

    if requested_namespace and requested_namespace != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested.",
        )

    try:
        validated_namespace = TenantEnum(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested."
        )

    if scope_values and validated_namespace.value not in scope_values and validated_namespace.name not in scope_values:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested.",
        )

    return validated_namespace
