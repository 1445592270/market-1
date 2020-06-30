import logging

from fastapi import APIRouter, Depends

from market.core.security import require_super_scope_admin
from market.models import MarketAdminUser
from market.schemas.base import CommonOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/options/v", response_model=CommonOut, tags=["后台——选项设置", "后台"])
async def show_options(
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """添加标签或者风格"""

    return CommonOut()


@router.post("/options/s", response_model=CommonOut, tags=["后台——选项设置", "后台"])
async def set_options(
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """添加标签或者风格"""
    return CommonOut()
