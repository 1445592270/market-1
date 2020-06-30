from fastapi import APIRouter

from . import (
    admin_user,
    run_info,
)

api_router = APIRouter()


api_router.include_router(admin_user.router)
api_router.include_router(run_info.router)
