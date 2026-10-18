from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from core.config import settings

SETTINGS_SCOPE = "settings"


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("scope") == SETTINGS_SCOPE:
        return None
    return payload


def create_settings_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "scope": SETTINGS_SCOPE,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.SETTINGS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_settings_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("scope") != SETTINGS_SCOPE:
        return None
    return payload
