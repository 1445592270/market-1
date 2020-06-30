from fastapi import APIRouter

# from . import login, order, packages, pay, strategy, users
from . import runinfo, user

api_router = APIRouter()


api_router.include_router(user.router)
api_router.include_router(runinfo.router)
