from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response

from qpweb import config
from qpweb.api.share.sms import send_verify_email, send_verify_sms, verify_auth_code
from qpweb.api.share.verification_code import generate_verification_code, verify_code
from qpweb.core.security import (
    APIKEY_HEADER_NAME,
    authenticate_user,
    create_access_token,
    get_password_hash,
    require_active_user,
    verify_password,
)
from qpweb.models import MarketUser, StrategyMarket
from qpweb.models.const import UserStatus
from qpweb.schemas.base import CommonOut
from qpweb.schemas.sms import EmailIn, SMSIn
from qpweb.schemas.token import AuthCodeRsp, UserToken
from qpweb.schemas.user import (
    ResetPassword,
    UpdatePassword,
    UserCreate,
    UserIn,
    UserRsp,
    UserUpdate,
)

router = APIRouter()


@router.get("/common/verification_code", response_model=CommonOut, tags=["common"])
async def generate_code():
    """生成图片验证码"""
    return await generate_verification_code()


@router.post("/common/sms_code", response_model=AuthCodeRsp, tags=["common"])
async def send_sms_code(schema_in: SMSIn):
    """发送短信验证码"""
    return await send_verify_sms(schema_in.phone, schema_in.smstype)


@router.post("/common/email_code", response_model=AuthCodeRsp, tags=["common"])
async def send_email_code(schema_in: EmailIn):
    """发送邮件验证码"""
    return await send_verify_email(schema_in.email, schema_in.smstype)


@router.get(
    "/user/dup/username/{user_name}", response_model=CommonOut, tags=["用户端——用户和登录"]
)
async def check_username_dup(user_name: str):
    """检查用户名是否重复"""
    row = await MarketUser.select("id").where(MarketUser.name == user_name)
    if not row:
        raise HTTPException(status_code=404, detail="用户名已注册")
    return CommonOut()


@router.post("/user/dup/phone/{phone}", response_model=CommonOut, tags=["用户端——用户和登录"])
async def check_phone_dup(phone: str):
    """检查手机号是否重复"""
    row = await MarketUser.select("id").where(MarketUser.phone == phone)
    if not row:
        raise HTTPException(status_code=404, detail="手机号已注册")
    return CommonOut()


@router.post("/user/dup/email/{email}", response_model=CommonOut, tags=["用户端——用户和登录"])
async def check_email_dup(email: str):
    """检查邮箱是否重复"""
    row = await MarketUser.select("id").where(MarketUser.email == email)
    if not row:
        raise HTTPException(status_code=404, detail="邮箱已注册")
    return CommonOut()


@router.post("/user/register", response_model=UserToken, tags=["用户端——用户和登录"])
async def register_user(user_in: UserCreate, response: Response):
    """
    Create new user.
    """
    # 验证验证码
    # await verify_code(user_in.vcode_id, user_in.vcode)
    await verify_auth_code(user_in.phone, user_in.email, user_in.sms_code)

    if not (user_in.phone or user_in.email):
        raise HTTPException(status_code=400, detail="Must specify phone/email")

    row = await MarketUser.select("id").where(MarketUser.name == user_in.name)
    if row:
        raise HTTPException(
            status_code=404,
            detail="The user with this name already exists in the system.",
        )
    if user_in.phone:
        row = await MarketUser.select("id").where(MarketUser.phone == user_in.phone)
        if row:
            raise HTTPException(
                status_code=404,
                detail="The user with this phone already exists in the system.",
            )
    if user_in.email:
        row = await MarketUser.select("id").where(MarketUser.email == user_in.email)
        if row:
            raise HTTPException(
                status_code=404,
                detail="The user with this email already exists in the system.",
            )
    market = await StrategyMarket.get(config.MARKET_ID)
    if not market:
        raise HTTPException(status_code=500, detail="配置错误，请联系管理员！")
    user_data = user_in.dict()
    user_data["password"] = get_password_hash(user_in.password)
    user_data["market"] = market
    user_data["status"] = int(UserStatus.normal)
    user = await MarketUser.create(**user_data)

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"uuid": user.id}, expires_delta=access_token_expires
    )
    # response.headers[APIKEY_HEADER_NAME] = access_token
    response.set_cookie(key=APIKEY_HEADER_NAME, value=access_token)
    return UserToken(**user.__dict__, token=access_token)


@router.post("/user/login", response_model=UserToken, tags=["用户端——用户和登录"])
async def login(user_in: UserIn, response: Response):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    if user_in.sms_code:
        await verify_auth_code(user_in.uid, None, user_in.sms_code)
        user = await MarketUser.query.where(
            MarketUser.phone == user_in.uid
        ).gino.first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    elif user_in.password:
        await verify_code(user_in.vcode_id, user_in.vcode)
        user = await authenticate_user(user_in.uid, user_in.password)
        if not user:
            raise HTTPException(status_code=400, detail="用户 ID/ 密码错误")
    else:
        raise HTTPException(status_code=400, detail="登录失败，请输入密码 / 登录码")

    if user.status != int(UserStatus.normal):
        raise HTTPException(status_code=400, detail="用户未激活 / 已禁用")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"uuid": user.id}, expires_delta=access_token_expires
    )
    # response.headers[APIKEY_HEADER_NAME] = access_token
    response.set_cookie(key=APIKEY_HEADER_NAME, value=access_token)
    return UserToken(**user.to_dict(), token=access_token)


@router.post("/user/logout", response_model=CommonOut, tags=["用户端——用户和登录"])
def user_logout(current_user: MarketUser = Depends(require_active_user)):
    """
    Update own user.
    """
    return CommonOut()


@router.post("/user/reset-password", response_model=CommonOut, tags=["用户端——用户和登录"])
async def recover_password(schema_in: ResetPassword):
    """
    Password Recovery
    """
    await verify_code(schema_in.vcode_id, schema_in.vcode)
    await verify_auth_code(schema_in.phone, schema_in.email, schema_in.sms_code)
    if schema_in.phone:
        user = await MarketUser.query.where(MarketUser.phone==schema_in.phone)
    else:
        user = await MarketUser.query.where(MarketUser.email==schema_in.email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email/phone does not exist in the system.",
        )
    user.password = get_password_hash(schema_in.password)
    await user.save()
    # verify_code = "1234"
    # if schema_in.phone:
    #     send_sms(verify_code)
    # else:
    #     send_email(verify_code)
    return CommonOut(msg="Password recovery message sent")


@router.post(
    "/user/update-password", response_model=CommonOut, tags=["用户端——用户和登录"],
)
async def update_password(
    update_in: UpdatePassword, current_user: MarketUser = Depends(require_active_user)
):
    """
    Reset password
    """
    if not verify_password(update_in.old_pwd, current_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")

    current_user.password = get_password_hash(update_in.new_pwd)
    await current_user.save()
    return CommonOut()


@router.post("/user/edit", response_model=UserRsp, tags=["用户端——用户和登录"])
def update_user_me(
    schema_in: UserUpdate, current_user: MarketUser = Depends(require_active_user)
):
    """
    Update own user.
    """
    pass


@router.get("/user/{user_id}", response_model=UserRsp, tags=["用户端——用户和登录"])
def read_user_me(current_user: MarketUser = Depends(require_active_user)):
    """
    Get current user.
    """
    return current_user
