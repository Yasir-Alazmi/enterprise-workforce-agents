import pytest
from fastapi import HTTPException

from src.core.config import Settings
from src.core.security import (
    AccessControlManager,
    UserRole,
    create_jwt_token,
    decode_jwt_token,
)


def test_jwt_token_creation_and_decoding():
    token = create_jwt_token(subject="user_123", role=UserRole.MANAGER, expires_in_seconds=600)
    claims = decode_jwt_token(token)
    assert claims["sub"] == "user_123"
    assert claims["role"] == "manager"


def test_expired_jwt_token_fails():
    token = create_jwt_token(subject="user_exp", expires_in_seconds=-10)
    with pytest.raises(ValueError, match="Expired JWT token"):
        decode_jwt_token(token)


def test_tampered_jwt_signature_fails():
    token = create_jwt_token(subject="user_tamper")
    parts = token.split(".")
    # Modify payload
    parts[1] = "eyJyYW5kb20iOiAidGFtcGVyZWQifQ"
    tampered = ".".join(parts)
    with pytest.raises(ValueError, match="signature"):
        decode_jwt_token(tampered)


def test_access_control_enforce_permission():
    # Admin has all permissions
    AccessControlManager.enforce_permission(UserRole.ADMIN, "approve:hitl")

    # Manager has approve:hitl
    AccessControlManager.enforce_permission(UserRole.MANAGER, "approve:hitl")

    # Employee lacks approve:hitl -> raises 403
    with pytest.raises(HTTPException) as exc:
        AccessControlManager.enforce_permission(UserRole.EMPLOYEE, "approve:hitl")
    assert exc.value.status_code == 403


def test_fail_fast_production_security_validation():
    prod_insecure = Settings(
        app_env="production",
        jwt_secret_key="enterprise-workforce-default-secret-key-change-in-prod"
    )
    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        prod_insecure.validate_production_security()

    prod_secure = Settings(
        app_env="production",
        jwt_secret_key="c4ca4238a0b923820dcc509a6f75849b2830f3f2d0f50"
    )
    prod_secure.validate_production_security()


def test_auditor_role_permissions():
    AccessControlManager.enforce_permission(UserRole.AUDITOR, "read:audit")
    with pytest.raises(HTTPException) as exc:
        AccessControlManager.enforce_permission(UserRole.AUDITOR, "create:action")
    assert exc.value.status_code == 403


def test_bearer_identity_preshared_tokens():
    sub, role = AccessControlManager.resolve_bearer_identity("Bearer token-admin-root")
    assert sub == "admin_root"
    assert role == UserRole.ADMIN

    sub_emp, role_emp = AccessControlManager.resolve_bearer_identity("Bearer token-employee-dev")
    assert sub_emp == "developer_01"
    assert role_emp == UserRole.EMPLOYEE


def test_anonymous_fallback_when_auth_optional():
    sub, role = AccessControlManager.resolve_bearer_identity(None, require_auth=False)
    assert sub == "anonymous"
    assert role == UserRole.EMPLOYEE
