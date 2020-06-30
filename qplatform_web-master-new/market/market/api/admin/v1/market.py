import logging

from fastapi import APIRouter, Depends, HTTPException, status

from market.core.security import require_super_scope_admin, require_super_scope_su
from market.models import MarketAdminUser, StrategyMarket, db
from market.models.const import MarketStatus
from market.schemas.base import CommonOut
from market.schemas.market import (
    MarketCreate,
    MarketDisable,
    MarketInfo,
    MarketSearch,
    MarketSearchOut,
    MarketUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/market/new", response_model=CommonOut, tags=["后台——超市管理"])
async def add_market(
    schema_in: MarketCreate,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """添加新的策略超市"""
    await StrategyMarket.create(**schema_in.dict(), status=int(MarketStatus.normal))
    return CommonOut()


@router.post("/market/edit", response_model=CommonOut, tags=["后台——超市管理"])
async def edit_market(
    schema_in: MarketUpdate,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """编辑策略超市信息"""
    market = await StrategyMarket.get_or_404(schema_in.id)
    # if not market:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到要编辑的策略")
    if schema_in.name:
        market = market.update(name=schema_in.name)
    if schema_in.domain:
        market = market.update(domain=schema_in.domain)
    await market.apply()
    return CommonOut()


@router.post("/market/disable", response_model=CommonOut, tags=["后台——超市管理"])
async def disable_market(
    schema_in: MarketDisable,
    current_user: MarketAdminUser = Depends(require_super_scope_su),
):
    """禁用 / 删除超市"""
    id_list = schema_in.id
    if isinstance(id_list, int):
        id_list = [id_list]
    await StrategyMarket.update(status=schema_in.status).where(
        StrategyMarket.id.in_(id_list)
    ).gino.status()
    return CommonOut()


@router.post("/market/find", response_model=MarketSearchOut, tags=["后台——超市管理"])
async def search_market(
    schema_in: MarketSearch,
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """查找超市"""
    count_query = db.select([db.func.count(StrategyMarket.id)]).where(
        StrategyMarket.status == int(MarketStatus.normal)
    )
    fetch_query = StrategyMarket.query.where(
        StrategyMarket.status == int(MarketStatus.normal)
    )

    if schema_in.id:
        count_query = count_query.where(StrategyMarket.id == schema_in.id)
        fetch_query = fetch_query.where(StrategyMarket.id == schema_in.id)
    if schema_in.name:
        count_query = count_query.where(StrategyMarket.name.contains(schema_in.name))
        fetch_query = fetch_query.where(StrategyMarket.name.contains(schema_in.name))
    total_count = await db.scalar(count_query)
    order_bys = []
    for key in schema_in.order_bys:
        if not key.startswith("-"):
            if not hasattr(StrategyMarket, key):
                logger.warning("get strategy market has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(StrategyMarket, key))
        else:
            if not hasattr(StrategyMarket, key[1:]):
                logger.warning("get strategy market has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(StrategyMarket, key[1:]).desc())
    markets = (
        await fetch_query.order_by(*order_bys).offset(schema_in.offset).limit(schema_in.count).gino.all()
    )
    return MarketSearchOut(total=total_count, data=markets)


@router.get("/market/{market_id}", response_model=MarketInfo, tags=["后台——超市管理"])
async def show_market(
    market_id: int, current_user: MarketAdminUser = Depends(require_super_scope_admin)
):
    """查看超市详情"""
    return await StrategyMarket.get_or_404(market_id)
