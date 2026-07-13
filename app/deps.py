from fastapi import Header, HTTPException, status


async def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """Temporary auth stand-in: pass user id via the X-User-Id header."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    return x_user_id
