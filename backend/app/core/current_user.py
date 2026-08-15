"""
Current-user abstraction. Business endpoints depend on `CurrentUser` (via
`get_current_user`), never on the raw token or header — this keeps the auth
mechanism swappable and endpoints unit-testable via dependency_overrides.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.jwt import TokenError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: str

    def is_role(self, role: str) -> bool:
        return self.role == role


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    subject = payload.get("sub")
    role = payload.get("role")
    if not subject or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token claims")

    return CurrentUser(user_id=subject, role=role)


def require_role(*allowed_roles: str):
    """Dependency factory for simple role gates. Full permission-matrix
    enforcement (per-resource ownership checks, etc.) belongs to each
    business module — this only covers "is this role allowed to call this
    endpoint at all", which is enough for the foundation phase."""

    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _checker
