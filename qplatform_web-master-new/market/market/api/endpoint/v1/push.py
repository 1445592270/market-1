import logging

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request

from market.api.share.strategy import check_task_permission
from market.const import TaskType
from market.core.security import require_active_user
from market.models import MarketUser, PushInfo, QStrategy
from market.models.const import PushMethod, PushStatus
from market.schemas.base import CommonOut
from market.schemas.push import PushCreate, PushSearchIn

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/push/query", response_model=CommonOut, tags=["用户端——信号推送"])
async def check_push(
    schema_in: PushSearchIn, current_user: MarketUser = Depends(require_active_user)
):
    """检查是否开启推送"""
    query = PushInfo.query.where(
        PushInfo.status == int(PushStatus.normal), PushInfo.user_id == current_user.id
    )
    if schema_in.qstrategy_id:
        query = query.where(PushInfo.qstrategy_id == schema_in.qstrategy_id)
    if schema_in.task_id:
        query = query.where(PushInfo.task_id == schema_in.task_id)
    if schema_in.push_method:
        query = query.where(PushInfo.push_method == int(schema_in.push_method))
    pushs = await query.gino.all()
    data = [
        {"qstrategy_id": push.qstrategy_id, "task_id": push.task_id, "enable": True}
        for push in pushs
    ]
    return CommonOut(data=data, total=len(data))


@router.post("/push/open", response_model=CommonOut, tags=["用户端——信号推送"])
async def open_push(
    schema_in: PushCreate,
    request: Request,
    current_user: MarketUser = Depends(require_active_user),
):
    """开启推送"""
    if schema_in.push_method != PushMethod.wechat:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "push_id is needed")
    strategy = await QStrategy.get_or_404(schema_in.qstrategy_id)
    if await check_task_permission(TaskType.PAPER_TRADING, strategy.task_id, request):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "没有权限")

    push_id = schema_in.push_id
    # TODO: check wechat bind for wechat push, check push_id for other method
    await PushInfo.create(
        qstrategy_id=strategy.product_id,
        task_id=strategy.task_id,
        user_id=current_user.id,
        status=int(PushStatus.normal),
        push_method=int(schema_in.push_method),
        push_id=push_id,
    )
    return CommonOut()


@router.post("/push/close", response_model=CommonOut, tags=["用户端——信号推送"])
async def close_push(
    schema_in: PushCreate,
    # request: Request,
    current_user: MarketUser = Depends(require_active_user),
):
    """关闭推送"""
    await PushInfo.update(status=int(PushStatus.disabled)).where(
        PushInfo.user_id == current_user.id,
        PushInfo.qstrategy_id == schema_in.qstrategy_id,
    )
    return CommonOut()
