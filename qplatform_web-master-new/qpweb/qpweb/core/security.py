import datetime
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, APIKeyHeader
from passlib.context import CryptContext
from starlette.requests import Request

from qpweb.config import SECRET_ALGORITHM, SECRET_KEY
from qpweb.models import MarketAdminUser, MarketUser
from qpweb.models.const import SUPER_SCOPE, UserScope2, UserStatus

logger = logging.getLogger(__name__)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

APIKEY_HEADER_NAME = "X-API-KEY"
# api_key_schema = APIKeyCookie(name=APIKEY_HEADER_NAME)
api_key_schema = APIKeyHeader(name=APIKEY_HEADER_NAME)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(*, data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now() + expires_delta
    else:
        expire = datetime.datetime.now() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=SECRET_ALGORITHM)
    return encoded_jwt.decode("utf-8")


# -----
async def authenticate_user(user_id: str, password: str):
    user = await MarketUser.query.where(MarketAdminUser.phone == user_id).gino.first()
    if not user:
        user = await MarketUser.query.where(
            MarketAdminUser.email == user_id
        ).gino.first()
    if not user:
        user = await MarketUser.query.where(
            MarketAdminUser.name == user_id
        ).gino.first()

    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_user(uid: int):
    return MarketUser.query.where(MarketAdminUser.id == uid).gino.first()


async def require_user(token: str = Depends(api_key_schema)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )
    uid_str = payload.get("uuid", None)
    if not uid_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )
    try:
        uid = int(uid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )

    expire = payload.get("exp")
    if not expire or datetime.datetime.now().timestamp() > float(expire):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credentials expired",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )
    user = await get_user(int(uid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )
    return user


async def require_active_user(current_user: MarketUser = Depends(require_user)):
    if current_user.status != int(UserStatus.normal):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_active_user(request: Request) -> MarketUser:
    """获取当前登录用户信息，获取失败时异常"""
    return await require_active_user(await require_user(await api_key_schema(request)))


# -------------------------------------
async def authenticate_admin_user(user_id: str, password: str):
    user = await MarketAdminUser.query.where(
        MarketAdminUser.phone == user_id
    ).gino.first()
    if not user:
        user = await MarketAdminUser.query.where(
            MarketAdminUser.email == user_id
        ).gino.first()
    if not user:
        user = await MarketAdminUser.query.where(
            MarketAdminUser.name == user_id
        ).gino.first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_admin_user(uid: int):
    return await MarketAdminUser.query.where(MarketAdminUser.id == uid).gino.first()


async def require_admin(token: str = Depends(api_key_schema)):
    """管理员"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_exception

    uid_str = payload.get("uuid", None)
    if not uid_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={APIKEY_HEADER_NAME: SECRET_ALGORITHM},
        )
    try:
        uid = int(uid_str)
    except ValueError:
        raise credentials_exception
    user = await get_admin_user(uid)
    if not user:
        raise credentials_exception
    return user


async def require_active_admin(current_user: MarketAdminUser = Depends(require_admin)):
# async def require_active_admin():
    """激活状态的管理员"""
    # return MarketAdminUser(
    #     id=1,
    #     name="fakeuser",
    #     phone="1234",
    #     email="admin@test.cn",
    #     password="1232132",
    #     scope1="aq",
    #     scope2=1,
    #     status=1,
    # )
    if current_user.status != int(UserStatus.normal):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_super_scope_admin(
    current_user: MarketAdminUser = Depends(require_active_admin),
):
    """总后台的管理员"""
    if current_user.scope1 != SUPER_SCOPE:
        raise HTTPException(status_code=400, detail="Insufficient permissions")
    return current_user


async def require_super_scope_su(
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """总后台的超管"""
    if current_user.scope2 != int(UserScope2.su):
        raise HTTPException(status_code=400, detail="Insufficient permissions")
    return current_user
