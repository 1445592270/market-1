import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from qsales import config
from qsales.core.security import (
    APIKEY_HEADER_NAME,
    authenticate_admin_user,
    create_access_token,
    get_password_hash,
    require_active_admin,
    require_super_scope_su,
    verify_password,
)
from qsales.models import MarketAdminUser, db
from qsales.models.const import UserScope2, UserStatus
from qsales.schemas.admin_user import (
    AdminUpdatePassword,
    AdminUserChangeStatusIn,
    AdminUserCreate,
    AdminUserIn,
    AdminUserInfo,
    AdminUserSearchIn,
    AdminUserSearchOut,
    AdminUserUpdate,
)
from qsales.schemas.base import CommonOut
from qsales.schemas.token import AdminToken

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/user/login", response_model=AdminToken, tags=["后台——系统管理员"])
async def admin_login(schema_in: AdminUserIn, response: Response):
    """登录管理后台"""
    if schema_in.verification_code != "1234":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect verification_code",
            # headers={"WWW-Authenticate": ""},
        )
    user = await authenticate_admin_user(schema_in.user_id, schema_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            # headers={"WWW-Authenticate": ""},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"uuid": user.id}, expires_delta=access_token_expires
    )
    # response.headers[APIKEY_HEADER_NAME] = access_token
    response.set_cookie(key=APIKEY_HEADER_NAME, value=access_token)
    return AdminToken(**user.__dict__, token=access_token)


@router.post("/user/logout", response_model=CommonOut, tags=["后台——系统管理员"])
async def admin_logout(current_user: MarketAdminUser = Depends(require_active_admin)):
    """注销管理后台"""
    return CommonOut()


@router.post("/user/add", response_model=CommonOut, tags=["后台——系统管理员"])
async def add_admin(
    schema_in: AdminUserCreate,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """添加管理员，需要总后台超管权限"""
    if current_user.scope1 != "aq" or current_user.scope2 != int(UserScope2.su):
        return CommonOut(errCode=-100, errMsg="添加失败，没有权限")

    data = schema_in.dict()
    data["password"] = get_password_hash(data["password"])
    try:
        await MarketAdminUser.create(**data)
    except Exception:
        logger.exception("create package failed: %s", schema_in.json())
        return CommonOut(errCode=-1, errMsg="添加失败，请检查名字是否重复")

    return CommonOut()


@router.post("/user/change_status", response_model=CommonOut, tags=["后台——系统管理员"])
async def change_admin_status(
    schema_in: AdminUserChangeStatusIn,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """禁用管理员"""
    if current_user.scope1 != "aq" or current_user.scope2 != int(UserScope2.su):
        return CommonOut(errCode=-100, errMsg="添加失败，没有权限")
    try:
        await MarketAdminUser.update(status=int(schema_in.status)).where(
            MarketAdminUser.id == schema_in.id
        )
    except Exception:
        logger.exception("更新管理员信息失败：%s", schema_in.json())
        return CommonOut(errCode=-1, errMsg="更新失败，请检查名字是否重复")
    return CommonOut()


@router.post("/user/edit", response_model=CommonOut, tags=["后台——系统管理员"])
async def edit_admin(
    schema_in: AdminUserUpdate,
    current_user: MarketAdminUser = Depends(require_active_admin),
):
    """编辑管理员信息"""
    try:
        await MarketAdminUser.update(**schema_in.changed.dict()).where(
            MarketAdminUser.id == schema_in.id
        )
    except Exception:
        logger.exception("更新管理员信息失败：%s", schema_in.json())
        return CommonOut(errCode=-1, errMsg="更新失败，请检查名字是否重复")
    return CommonOut()


@router.post("/user/update-password", response_model=CommonOut, tags=["后台——系统管理员"])
async def change_password(
    update_in: AdminUpdatePassword,
    current_user: MarketAdminUser = Depends(require_active_admin),
):
    """更改密码"""
    if not verify_password(update_in.old_pwd, current_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")

    current_user.password = get_password_hash(update_in.new_pwd)
    await current_user.save()
    return CommonOut()


@router.post("/user/find", response_model=AdminUserSearchOut, tags=["后台——系统管理员"])
async def search_admin(
    schema_in: AdminUserSearchIn,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """根据名字和类型查询标签或者风格"""
    count_query = db.select([db.func.count(MarketAdminUser.id)]).where(
        MarketAdminUser.status != int(UserStatus.deleted)
    )
    fetch_query = MarketAdminUser.query.where(
        MarketAdminUser.status != int(UserStatus.deleted)
    )
    if schema_in.scope1:
        count_query = count_query.where(MarketAdminUser.scope1 == schema_in.scope1)
        fetch_query = fetch_query.where(MarketAdminUser.scope1 == schema_in.scope1)
    if schema_in.scope2:
        count_query = count_query.where(MarketAdminUser.scope2 == int(schema_in.scope2))
        fetch_query = fetch_query.where(MarketAdminUser.scope2 == int(schema_in.scope2))
    if schema_in.name:
        count_query = count_query.where(MarketAdminUser.name.contains(schema_in.name))
        fetch_query = fetch_query.where(MarketAdminUser.name.contains(schema_in.name))
    if schema_in.phone:
        count_query = count_query.where(MarketAdminUser.phone.contains(schema_in.phone))
        fetch_query = fetch_query.where(MarketAdminUser.phone.contains(schema_in.phone))
    if schema_in.email:
        count_query = count_query.where(MarketAdminUser.email.contains(schema_in.email))
        fetch_query = fetch_query.where(MarketAdminUser.email.contains(schema_in.email))
    total_count = await db.scalar(count_query)
    users = (
        await fetch_query.order_by(MarketAdminUser.name.desc())
        .offset(schema_in.offset)
        .limit(schema_in.count)
        .gino.all()
    )
    return AdminUserSearchOut(
        total=total_count, data=[AdminUserInfo(**user.__dict__) for user in users]
    )
