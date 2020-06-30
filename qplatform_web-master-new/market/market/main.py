import asyncio
import logging

import aiomysql
import motor.motor_asyncio
from aioredis import create_redis_pool
from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware

from market import config
from market.api.admin.api import api_router as admin_router
from market.api.endpoint.api import api_router as endpoint_router
from market.ctx import ctx
from market.models import db

try:
    from importlib.metadata import entry_points
except ImportError:  # pragma: no cover
    from importlib_metadata import entry_points

logger = logging.getLogger(__name__)


# from fastapi import BackgroundTasks
#
#
# @app.post("/send-notification/{email}")
# async def send_notification(email: str, background_tasks: BackgroundTasks):
#     background_tasks.add_task(write_notification, email, message="some notification")
#     return {"message": "Notification sent in the background"}


async def create_first_user():
    from market.models.const import SUPER_SCOPE, UserScope2
    from market.models import MarketAdminUser
    from market.core.security import get_password_hash

    # user = await MarketAdminUser.get_or_none(email=config.FIRST_SUPERUSER)
    user = await MarketAdminUser.query.where(
        MarketAdminUser.email == config.FIRST_SUPERUSER
    ).gino.first()
    if not user:
        await MarketAdminUser.create(
            name="aqfake",
            phone="12300000000",
            email=config.FIRST_SUPERUSER,
            password=get_password_hash(config.FIRST_SUPERUSER_PASSWORD),
            scope1=SUPER_SCOPE,
            scope2=int(UserScope2.su),
        )
        print("!!! Created super super aqfake")


def load_modules(app=None):
    from market import models

    # for ep in entry_points()["market.modules"]:
    #     logger.info(
    #         "Loading module: %s",
    #         ep.name,
    #         extra={"color_message": "Loading module: " + click.style("%s", fg="cyan")},
    #     )
    #     mod = ep.load()
    #     if app:
    #         init_app = getattr(mod, "init_app", None)
    #         if init_app:
    #             init_app(app)


async def config_app(app):
    # CORS
    origins = []

    # Set all CORS enabled origins
    if config.BACKEND_CORS_ORIGINS:
        origins_raw = config.BACKEND_CORS_ORIGINS.split(",")
        for origin in origins_raw:
            use_origin = origin.strip()
            origins.append(use_origin)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    root_router = APIRouter()
    if config.ENABLE_ENDUSER:
        root_router.include_router(endpoint_router)
    if config.ENABLE_ADMIN:
        root_router.include_router(admin_router, prefix=config.ADMIN_API_PREFIX)

    app.include_router(root_router, prefix=config.API_PREFIX)
    db.init_app(app)
    load_modules(app)

    @app.on_event("startup")
    async def init_middlewares() -> None:  # pylint: disable=W0612
        # qplatform mysql db
        ctx.mysql_cli = await aiomysql.create_pool(
            host=config.QP_WEB_DB_HOST,
            port=config.QP_WEB_DB_PORT,
            user=config.QP_WEB_DB_USER,
            password=config.QP_WEB_DB_PASSWORD,
            db=config.QP_WEB_DB_NAME,
            unix_socket=config.QP_WEB_DB_UNIX_SOCKET,
            charset=config.QP_WEB_DB_CHARSET,
            autocommit=False,
        )

        # mongodb
        ctx.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
            config.MONGO_SERVER,
            minPoolSize=config.MONGODB_MIN_POOL_SIZE,
            maxPoolSize=config.MONGODB_MAX_POOL_SIZE,
        )
        logger.info("motor-Mogodb startup")

        # redis
        ctx.redis_client = await create_redis_pool(config.REDIS_URL)
        logger.info("aio-redis startup")

        # aliyu sms
        try:
            from aliyunsdkcore.client import AcsClient

            ctx.sms_client = AcsClient(
                config.SMS_CLI_ACCESSKEYID,
                config.SMS_CLI_ACCESSSECRET,
                config.SMS_CLI_REGION,
            )
            # check send params
            reg = config.SMS_REQ_REGION_ID
            sign = config.SMS_REQ_REGION_SIGN_NAME
            if not reg or not sign:
                raise ValueError("sms config error")
        except ImportError:
            logger.exception(
                "set up sms client failed, please install aliyun-python-sdk-core"
            )
        except (KeyError, ValueError):
            logger.exception("set up sms client failed, please check config")
        await db.gino.create_all()
        await create_first_user()

    @app.on_event("shutdown")
    async def deinit_middlewares() -> None:  # pylint: disable=W0612
        # qplatform mysql db
        ctx.mysql_cli.close()
        await ctx.mysql_cli.wait_closed()
        # mongodb
        if ctx.mongo_client:
            await ctx.mongo_client.close()
        logger.info("motor-Mogodb shutdown")

        # redis
        if ctx.redis_client:
            await ctx.redis_client.close()
        logger.info("aio-redis shutdown")

        # aliyu sms
        if ctx.sms_client:
            pass
        logger.info("sms client shutdown")

    return app


def get_app():
    # XXX: The default JSONResponse encoder cannot handle nan for json
    # so we use orjson, refer: https://github.com/tiangolo/fastapi/issues/459
    app_params = {
        "title": config.PROJECT_NAME,
        "default_response_class": ORJSONResponse,
        "debug": config.DEBUG,
    }
    if config.GEN_DOCS:
        app_params["openapi_url"] = config.API_PREFIX + "/api/openapi.json"
        app_params["docs_url"] = config.API_PREFIX + "/doc"
        app_params["redoc_url"] = config.API_PREFIX + "/redoc"
    app = FastAPI(**app_params)
    asyncio.run(config_app(app))
    return app
