"""
backend/app/core/deps.py
REPLACES the Phase 3 version.
Change: require_role() now treats "admin" specially — a token with
is_admin=True satisfies ANY require_role(...) check, on top of also
satisfying its own primary role. This lets one test account act as both
student and admin without a role-conflict, while keeping real users
single-primary-role.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    """
    Grants access if EITHER:
    - the user's primary role is in allowed_roles, OR
    - the user has is_admin=True (admins can access any role-gated route)
    Exception: require_role("admin") alone still strictly requires is_admin=True,
    it doesn't get bypassed by itself.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        is_admin_only_check = set(allowed_roles) == {"admin"}

        if current_user.role in allowed_roles:
            return current_user

        if not is_admin_only_check and current_user.is_admin:
            return current_user

        if is_admin_only_check and current_user.is_admin:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires one of roles: {allowed_roles}",
        )
    return role_checker
