import datetime
import logging
from typing import Any, Dict
from market.api.share.strategy import sortedd
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request
from sqlalchemy import create_engine
from market.api.share.run_info import (
    get_curves,
    get_indicators,
    get_period_returns,
    get_portfolio_info,
    get_today_positons,
    get_today_returns,
)
from market.api.share.strategy import check_task_permission, search_strategy
from market.const import TaskType
from market.core.security import require_active_user
from market.ctx import ctx
from market.models import MarketUser, QStrategy, UserOrder, db
from market.models.const import ListStatus, ProductType
from market.schemas.base import CommonOut
from market.schemas.runinfo import PortfolioRatio
from market.schemas.strategy import BuyedQStrategySearch  # QStrategyInfo,
from market.schemas.strategy import (
    BuyedQStrategyInfo,
    BuyedQStrategySearchOut,
    QStrategyBasicInfo,
    QStrategySearch,
    QStrategySearchOut,
    QStrategySearchOVOut,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/strategy/check/{task_id}", response_model=CommonOut, tags=["用户端——策略运行信息"]
)
async def check_buyed(task_id: str, request: Request):
    """检查是否需要因此策略信息"""
    try:
        if await check_task_permission(TaskType.PAPER_TRADING, task_id, request):
            return CommonOut()
    except Exception:
        pass
    return CommonOut(errCode=-1, errMsg="没有权限")

import MySQLdb
@router.post("/strategy/copy/{task_id}", response_model=CommonOut, tags=["用户端——策略运行信息"])
async def get_strategy_code(task_id: str, request: Request):
    """检查是否需要因此策略信息"""
    if not await check_task_permission(TaskType.PAPER_TRADING, task_id, request):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "没有权限")
    async with ctx.mysql_cli.acquire() as conn:
        # get code
        cursor = await conn.cursor()
        query_str = "SELECT backtest_id FROM wk_simulation WHERE task_id=%s"
        await cursor.execute(query_str, task_id)
        rows = await cursor.fetchall()
        if len(rows) != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="复制错误，策略已不存在"
            )
        backtest_id = rows[0][0]
    
        query_str = f"SELECT code FROM wk_strategy_backtest WHERE id=%s"
        await cursor.execute(query_str, backtest_id)
        rows = await cursor.fetchall()
        if len(rows) != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="复制错误，策略已不存在"
            )
        code = rows[0][0]
        return CommonOut(data=code)


@router.get(
    "/strategy/portfolio/{product_id}",
    response_model=PortfolioRatio,
    tags=["用户端——策略信息"],
)
async def get_portfolio(product_id: str):
    """获取策略仓位占比信息"""
    strategy = await QStrategy.query.where(
        QStrategy.product_id == product_id
    ).where(QStrategy.status == int(ListStatus.online)).gino.first()
    if not strategy:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "未找到该策略")
    portfolio_info = await get_portfolio_info(TaskType.PAPER_TRADING, strategy.task_id)
    positions = await get_today_positons(TaskType.PAPER_TRADING, strategy.task_id)
    try:
        pos_ratio = round(
            float(portfolio_info["positions_value"])
            / float(portfolio_info["net_value"]),
            2,
        )
    except (ZeroDivisionError, KeyError):
        pos_ratio = 0.0
    return {
        "name": strategy.name,
        "task_id": strategy.task_id,
        "start_cash": portfolio_info.get("start_cash", 0),
        "net_value": portfolio_info.get("net_value", 0),
        "positions_value": portfolio_info.get("positions_value", 0),
        "hold_ratio": pos_ratio,
        "pos_cnt": len(positions),
        "start_dt": strategy.sim_start_dt,
    }


@router.get(
    "/strategy/show/{product_id}", response_model=QStrategyBasicInfo, tags=["用户端——策略信息"]
)
async def get_strategy_info(product_id: str):
    """获取策略概览信息"""
    strategy = await QStrategy.query.where(
        QStrategy.product_id == product_id).where(QStrategy.status == int(ListStatus.online)).gino.first()
    if not strategy:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "未找到该策略")
    data = {
        "product_id": strategy.product_id,
        "name": strategy.name,
        "style": strategy.style,
        "category": strategy.category,
        "tags": strategy.tags,
        "author_name": strategy.author_name,
        "ideas": strategy.ideas,
        "desc": strategy.desc,
        "buyout_price": strategy.buyout_price,
        "task_id": strategy.task_id,
        "sell_cnt": strategy.sell_cnt_show,
        "total_cnt": strategy.total_cnt,
        "sim_start_dt": strategy.sim_start_dt,
        "online_dt": strategy.online_dt,
        "period_prices": strategy.period_prices,
        "enable_discount": strategy.enable_discount,
        "discount_info": strategy.discount_info,
        "allow_coupon": strategy.allow_coupon,
    }
    indicators = await get_indicators(TaskType.PAPER_TRADING, strategy.task_id)
    data.update(indicators)
    return_info = await get_today_returns(TaskType.PAPER_TRADING, strategy.task_id)
    if return_info:
        data.update(return_info[0])
    data["unv"] = round(data.get("returns", 0) + 1, 2)
    period_returns = await get_period_returns(strategy.task_id)
    data.update(period_returns)
    return data


@router.post(
    "/strategy/list", response_model=BuyedQStrategySearchOut, tags=["用户端——策略信息"]
)
async def list_strategies(
    schema_in: BuyedQStrategySearch,
    current_user: MarketUser = Depends(require_active_user),
):
    """列出已购买策略"""
    count_query = db.select([db.func.count(UserOrder.id)]).where(
        UserOrder.user_id == current_user.id,
    ).where(UserOrder.product_type == int(ProductType.package))
    fetch_query = UserOrder.query.where(
        UserOrder.user_id == current_user.id,
    ).where(UserOrder.product_type == int(ProductType.package))
    if schema_in.product_id:
        count_query = count_query.where(QStrategy.product_id == schema_in.product_id)
        fetch_query = fetch_query.where(QStrategy.product_id == schema_in.product_id)
    if schema_in.status:
        count_query = count_query.where(QStrategy.status == int(schema_in.status))
        fetch_query = fetch_query.where(QStrategy.status == int(schema_in.status))
    #if not schema_in.show_expired:
    #    count_query = count_query.where(QStrategy.expire_dt >= datetime.datetime.now())
    #    fetch_query = fetch_query.where(QStrategy.expire_dt >= datetime.datetime.now())

    #total_count = await db.scalar(count_query)
    total_count = 0
    #orders = (
    #    await fetch_query.offset(schema_in.offset).limit(schema_in.count).gino.all()
    #)
    orders = (await fetch_query.gino.all())
    product_ids = []
    order_info_dict = {}
    for order in orders:
        product_ids.append((order.product_id))
        order_info_dict[order.product_id] = {
            "order_id": order.id,
            "total_cash": order.total_cash,
            "total_days": order.total_days,
            "days": order.days,
            "gift_days": order.gift_days,
            "coupon_days": order.coupon_days,
            "coupon_cash": order.coupon_cash,
            "payed_cash": order.payed_cash,
            "expire_dt": order.expire_dt,
            "create_dt": order.create_dt,
            "pay_dt": order.pay_dt,
        }
    strategy_list = await QStrategy.query.where(
        QStrategy.package_id.in_(product_ids)
    ).where(QStrategy.status == int(ListStatus.online)).gino.all()
    strategy_list1 = []
    strategy_list2 = []
    for j in strategy_list:
        strategy_list1.append(j)
    for i in strategy_list1:
        if i not in strategy_list2:
            strategy_list2.append(i)
    data = []
    for strategy in strategy_list2:
        total_count+=1
        info = dict(**strategy.to_dict())
        info.update(**order_info_dict[strategy.package_id])
        data.append(BuyedQStrategyInfo(**info))
    return BuyedQStrategySearchOut(total=total_count, data=data,)


@router.post("/strategy/find", response_model=QStrategySearchOut, tags=["用户端——策略信息"])
async def user_search_strategy(schema_in: QStrategySearch):
    """搜索策略"""
    return await search_strategy(schema_in)


@router.post(
    "/strategy/find/ov", response_model=QStrategySearchOVOut, tags=["用户端——策略信息"]
)
async def strategy_overview(schema_in: QStrategySearch):
    """首页策略列表"""
    sort = schema_in.sort
    data = []
    total_cnt, strategies = await search_strategy(schema_in, return_strategy_list=True)
    for strategy in strategies:
        indicators = await get_indicators(TaskType.PAPER_TRADING, strategy.task_id)
        _, curve = await get_curves(TaskType.PAPER_TRADING, strategy.task_id)
        return_info = await get_today_returns(TaskType.PAPER_TRADING, strategy.task_id)
        # info: Dict[str, Any] = {"curve": [], "bench_curve": []}
        info: Dict[str, Any] = {"curve": [], "bench_curve": []}
        for daily_curve in curve:
            info["curve"].append((daily_curve["day"], daily_curve["returns"]))
            info["bench_curve"].append(
                (daily_curve["day"], daily_curve["bench_returns"])
            )
        info.update(indicators)
        if return_info:
            info.update(return_info[0])
        info.update(strategy.__dict__['__values__'])
        data.append(info)
    #return QStrategySearchOVOut(total=total_cnt, data=data)
    total_cnt, sort_cum = await sortedd(data, total_cnt, sort)
    #print(total_cnt,'total_cnt---111111111111111111')
    #print(sort_cum,'sort_cum------222222222222222')
    #print(schema_in.offset,'offset--33333333333333333')
    #print(schema_in.count,'count--4444444444444444444')
    #return QStrategySearchOVOut(total=total_cnt, data=sort_cum)
    return QStrategySearchOVOut(total=total_cnt, data=sort_cum[schema_in.offset:schema_in.count + schema_in.offset])
