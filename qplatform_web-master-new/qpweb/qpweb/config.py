import os
from typing import Union

from sqlalchemy.engine.url import URL, make_url
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

SERVER_NAME = config("SERVER_NAME", default="qpweb")
SERVER_HOST = config("SERVER_HOST ", default="qpweb")
PROJECT_NAME = config("PROJECT_NAME", default="qpweb")

DEBUG = config("QPWEB_APP_DEBUG", cast=bool, default=False)
GEN_DOCS = config("GEN_DOCS", cast=bool, default=False)

ENABLE_ENDUSER = config("ENABLE_ENDUSER", cast=bool, default=True)
ENABLE_ADMIN = config("ENABLE_ADMIN", cast=bool, default=False)
API_PREFIX = config("API_PREFIX", default="/")
ADMIN_API_PREFIX = config("ADMIN_API_PREFIX", default="/fake")

DEFAULT_PAGE_SIZE = config("DEFAULT_PAGE_SIZE", cast=int, default=20)
PAGE_SIZE_LIMIT = config("PAGE_SIZE_LIMIT", cast=int, default=300)

# a string of origins separated by commas, e.g:
# "http://localhost, http://localhost:8080, http://local.dockertoolbox.tiangolo.com"
BACKEND_CORS_ORIGINS = config("BACKEND_CORS_ORIGINS", default="http://localhost:8000")

# qp_tracker mongo
MONGODB_MIN_POOL_SIZE = config("MONGODB_MIN_POOL_SIZE", cast=int, default=0)
MONGODB_MAX_POOL_SIZE = config("MONGODB_MAX_POOL_SIZE", cast=int, default=100)
MONGO_SERVER = config("MONGO_SERVER", default="mongodb://192.168.0.115:27017")
# redis connection
REDIS_URL = config(
    "REDIS_URL", default="redis://:123456@localhost:6379/0?encoding=utf-8"
)

PG_DB_DRIVER = config("PG_DB_DRIVER", default="postgresql")
PG_DB_HOST = config("PG_DB_HOST", default=None)
PG_DB_PORT = config("PG_DB_PORT", cast=int, default=None)
PG_DB_USER = config("PG_DB_USER", default=None)
PG_DB_PASSWORD = config("PG_DB_PASSWORD", cast=Secret, default=None)
PG_DB_DATABASE = config("PG_DB_DATABASE", default=None)

# TESTING = config("TESTING", cast=bool, default=False)
# if TESTING:
#     if PG_DB_DATABASE:
#         PG_DB_DATABASE += "_test"
#     else:
#         PG_DB_DATABASE = "qpweb_test"

PG_DB_DSN = config(
    "PG_DB_DSN",
    cast=make_url,
    default=URL(
        drivername=PG_DB_DRIVER,
        username=PG_DB_USER,
        password=PG_DB_PASSWORD,
        host=PG_DB_HOST,
        port=PG_DB_PORT,
        database=PG_DB_DATABASE,
    ),
)
PG_DB_POOL_MIN_SIZE = config("PG_DB_POOL_MIN_SIZE", cast=int, default=1)
PG_DB_POOL_MAX_SIZE = config("PG_DB_POOL_MAX_SIZE", cast=int, default=16)
PG_DB_ECHO = config("PG_DB_ECHO", cast=bool, default=False)
PG_DB_SSL = config("PG_DB_SSL", default=None)
PG_DB_USE_CONNECTION_FOR_REQUEST = config(
    "PG_DB_USE_CONNECTION_FOR_REQUEST", cast=bool, default=True
)
PG_DB_RETRY_LIMIT = config("PG_DB_RETRY_LIMIT", cast=int, default=1)
PG_DB_RETRY_INTERVAL = config("PG_DB_RETRY_INTERVAL", cast=int, default=1)

# first user infos
FIRST_SUPERUSER = config("FIRST_SUPERUSER", default="admin@aq.cn")
FIRST_SUPERUSER_PASSWORD = config(
    "FIRST_SUPERUSER_PASSWORD",
    default="qpweb.12345"
)

# verify code and sms config
VERIFY_CODE_TIMEOUT = config("VERIFY_CODE_TIMEOUT", cast=int, default=180)  # 秒超时时间
ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    cast=int,
    default=60 * 24 * 8,  # 60 minutes * 24 hours * 8 days = 8 days
)

SMS_LIMIT_TIME = config("SMS_LIMIT_TIME", cast=int, default=60)  # 秒超时时间
SMS_VERIFY_CODE_TIMEOUT = config(
    "SMS_VERIFY_CODE_TIMEOUT", cast=int, default=300
)  # 秒超时时间

SMS_CLI_ACCESSKEYID = config("SMS_CLI_ACCESSKEYID", default="NOOP")
SMS_CLI_ACCESSSECRET = config(
    "SMS_CLI_ACCESSSECRET", default="NOOP"
)
SMS_CLI_REGION = config("SMS_CLI_REGION", default="cn-hangzhou")
SMS_REQ_REGION_ID = config("SMS_REQ_REGION_ID", default="cn-hangzhou")
SMS_REQ_REGION_SIGN_NAME = config("SMS_REQ_REGION_SIGN_NAME", default="NOOP")

QP_WEB_DSN = config("QP_WEB_DSN", default="sqlite://:memory:")

SECRET_KEY = config(
    "SECRET_KEY",
    default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
)
SECRET_ALGORITHM = config("SECRET_ALGORITHM", default="HS256")


# SMTP_TLS = getenv_boolean("SMTP_TLS", True)
# SMTP_PORT = None
# _SMTP_PORT = os.getenv("SMTP_PORT")
# if _SMTP_PORT is not None:
#     SMTP_PORT = int(_SMTP_PORT)
# SMTP_HOST = os.getenv("SMTP_HOST")
# SMTP_USER = os.getenv("SMTP_USER")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
# EMAILS_FROM_EMAIL = os.getenv("EMAILS_FROM_EMAIL")
# EMAILS_FROM_NAME = PROJECT_NAME
# EMAIL_RESET_TOKEN_EXPIRE_HOURS = 48
# EMAIL_TEMPLATES_DIR = "/app/app/email-templates/build"
# EMAILS_ENABLED = SMTP_HOST and SMTP_PORT and EMAILS_FROM_EMAIL

# FIRST_SUPERUSER = os.getenv("FIRST_SUPERUSER")
# FIRST_SUPERUSER_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD")
# PAY_PARAMS = {
#     "wx": {
#         "app_id": "",
#         "mch_id": "",
#         "mch_key": "",
#         "notify_url": "",
#         "key": "",
#         "cert": "",
#         "sess": "",
#     }
# }

# USERS_OPEN_REGISTRATION = config("USERS_OPEN_REGISTRATION", cast=bool, default=True)
#
# EMAIL_TEST_USER = "test@example.com"
