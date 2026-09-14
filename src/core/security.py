import base64
import hashlib
import hmac
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    AUDITOR = "auditor"


ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMIN: ["read:data", "execute:sql", "verify:policy", "create:action", "approve:hitl", "admin:all"],
    UserRole.MANAGER: ["read:data", "execute:sql", "verify:policy", "create:action", "approve:hitl"],
    UserRole.EMPLOYEE: ["read:data", "execute:sql", "verify:policy"],
    UserRole.AUDITOR: ["read:data", "read:audit", "read:checkpoints"],
}

# Pre-shared service tokens for zero-configuration testing
PRESHARED_TOKENS: Dict[str, Dict[str, Any]] = {
    "token-admin-root": {"sub": "admin_root", "role": UserRole.ADMIN},
    "token-manager-ops": {"sub": "ops_manager", "role": UserRole.MANAGER},
    "token-employee-dev": {"sub": "developer_01", "role": UserRole.EMPLOYEE},
    "token-auditor-sec": {"sub": "compliance_auditor", "role": UserRole.AUDITOR},
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(segment: str) -> bytes:
    padding = 4 - (len(segment) % 4)
    if padding != 4:
        segment += "=" * padding
    return base64.urlsafe_b64decode(segment.encode("utf-8"))


def create_jwt_token(
    subject: str,
    role: UserRole = UserRole.EMPLOYEE,
    expires_in_seconds: int = 3600,
    secret_key: Optional[str] = None
) -> str:
    key = secret_key or settings.jwt_secret_key
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role.value if isinstance(role, UserRole) else str(role),
        "iat": now,
        "exp": now + expires_in_seconds
    }

    h_enc = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_enc = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig_input = f"{h_enc}.{p_enc}".encode("utf-8")
    signature = hmac.new(key.encode("utf-8"), sig_input, hashlib.sha256).digest()
    s_enc = _b64url_encode(signature)
    return f"{h_enc}.{p_enc}.{s_enc}"


def decode_jwt_token(token: str, secret_key: Optional[str] = None) -> Dict[str, Any]:
    key = secret_key or settings.jwt_secret_key
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT: Must contain exactly 3 segments separated by dots.")

    h_enc, p_enc, s_enc = parts
    sig_input = f"{h_enc}.{p_enc}".encode("utf-8")
    expected_sig = hmac.new(key.encode("utf-8"), sig_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(s_enc)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid JWT signature: Verification failed.")

    payload = json.loads(_b64url_decode(p_enc).decode("utf-8"))
    now = int(time.time())
    if "exp" in payload and payload["exp"] < now:
        raise ValueError("Expired JWT token: Token expiration time has passed.")

    return payload


class AccessControlManager:
    @staticmethod
    def resolve_bearer_identity(
        auth_header: Optional[str],
        require_auth: bool = True
    ) -> Tuple[str, UserRole]:
        if not auth_header or not auth_header.startswith("Bearer "):
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required. Please provide a valid 'Authorization: Bearer <token>' header."
                )
            return "anonymous", UserRole.EMPLOYEE

        token = auth_header[7:].strip()

        # Check pre-shared tokens
        if token in PRESHARED_TOKENS:
            meta = PRESHARED_TOKENS[token]
            return meta["sub"], meta["role"]

        # Attempt JWT verification
        try:
            claims = decode_jwt_token(token)
            role_str = claims.get("role", "employee").lower()
            role = UserRole(role_str) if role_str in [r.value for r in UserRole] else UserRole.EMPLOYEE
            return claims.get("sub", "authenticated_user"), role
        except Exception as e:
            logger.warning("Token verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or unrecognized bearer token: {e}"
            )

    @staticmethod
    def enforce_permission(user_role: UserRole, required_permission: str, operation_name: str = "operation") -> None:
        perms = ROLE_PERMISSIONS.get(user_role, [])
        if "admin:all" in perms or required_permission in perms:
            return
        logger.warning(
            "Access denied: role '%s' lacks permission '%s' for %s",
            user_role.value, required_permission, operation_name
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: Role '{user_role.value}' does not possess required permission '{required_permission}' for {operation_name}."
        )
