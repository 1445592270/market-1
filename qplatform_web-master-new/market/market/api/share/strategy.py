import datetime
import logging
from typing import List, Union
from sqlalchemy import and_,or_
from fastapi import HTTPException, status
from starlette.requests import Request

from market.const import TaskType
from market.core.security import get_active_user
from market.models import MarketUser, QStrategy, UserOrder, db
from market.models.const import ListStatus, OrderStatus, ProductType
from market.schemas.base import CommonOut
from market.schemas.strategy import (
    QStrategyInfo,
    QStrategySearch,
    QStrategySearchOut,
    QStrategyUpdateFields,
)

logger = logging.getLogger(__name__)


async def check_task_permission(task_type: TaskType, task_id: str, request: Request):
    """检查用户是否有该策略的权限"""
    try:
        current_user: MarketUser = await get_active_user(request)
    except Exception:
        logger.warning("check_task_permission no active user found")
        return False
    if task_type == TaskType.PAPER_TRADING:
        row = (
                await QStrategy.select("package_id")
                .where(QStrategy.task_id == task_id)
                .gino.first()
        )
    else:
        row = (
            await QStrategy.select("package_id")
            .where(QStrategy.bt_task_id == task_id)
            .gino.first()
        )
    if not row:
        logger.warning("check_task_permission no product found")
        return False
    product_id = row["package_id"]
    print(row,'row1')
    print(current_user.id,'current_user.id-------111111111111111')
    row = (
        await UserOrder.select("id")
        .where(
            and_(
            UserOrder.user_id==current_user.id,
            UserOrder.product_type==int(ProductType.package),
            UserOrder.product_id==product_id,
            UserOrder.status==int(OrderStatus.payed),
            (UserOrder.expire_dt)>datetime.datetime.now(),
            )).gino.first()
    )
    if row:
        logger.warning("check_task_permission no user order found")
        return True
    return False


async def show_strategy(strategy_id: str):
    """查看策略"""
    strategy = await QStrategy.get_or_404(strategy_id)
    return QStrategyInfo(**strategy.to_dict())


async def edit_strategy(product_id: str, changed: QStrategyUpdateFields):
    """编辑上架策略"""
    try:
        await QStrategy.update.values(**changed.dict()).where(
            QStrategy.product_id == product_id
        ).gino.status()
    except Exception:
        logger.exception("更新策略 (%s) 失败：%s", product_id, changed.json())
        return CommonOut(errCode=-1, errMsg="更新失败，请检查名字是否重复")
    return CommonOut()


async def change_strategy_status(id_list: Union[str, List[str]], status: ListStatus):
    """直接重新上架策略"""
    if isinstance(id_list, str):
        id_list = [id_list]
    await QStrategy.update.values(status=int(status)).where(
        QStrategy.product_id.in_(id_list)
    ).gino.status()
    return CommonOut()


async def search_strategy(schema_in: QStrategySearch, return_strategy_list=False):
    """搜索策略"""
    # TODO: support tag search, perphaps need to use raw sql
    count_query = db.select([db.func.count(QStrategy.product_id)])
    fetch_query = QStrategy.query

    #if schema_in.status and schema_in.status != int(ListStatus.deleted):
    #if schema_in.status:
    #    count_query = count_query.where(QStrategy.status == int(schema_in.status))
    #    fetch_query = fetch_query.where(QStrategy.status == int(schema_in.status))
    #else:
    #    #count_query = count_query.where(QStrategy.status != int(ListStatus.deleted))
    #    #fetch_query = fetch_query.where(QStrategy.status != int(ListStatus.deleted))
    #    count_query = count_query.where(QStrategy.status == int(ListStatus.online))
    #    fetch_query = fetch_query.where(QStrategy.status == int(ListStatus.online))
    if not return_strategy_list:
        if schema_in.status:
            count_query = count_query.where(QStrategy.status == int(schema_in.status))
            fetch_query = fetch_query.where(QStrategy.status == int(schema_in.status))
        else:
            count_query = count_query
            fetch_query = fetch_query
    else:
        if schema_in.status:
            count_query = count_query.where(QStrategy.status == int(schema_in.status))
            fetch_query = fetch_query.where(QStrategy.status == int(schema_in.status))
        else:
            count_query = count_query.where(QStrategy.status == int(ListStatus.online))
            fetch_query = fetch_query.where(QStrategy.status == int(ListStatus.online))
    if schema_in.product_id:
        count_query = count_query.where(QStrategy.product_id == schema_in.product_id)
        fetch_query = fetch_query.where(QStrategy.product_id == schema_in.product_id)
    if schema_in.market_id:
        count_query = count_query.where(QStrategy.market_id == schema_in.market_id)
        fetch_query = fetch_query.where(QStrategy.market_id == schema_in.market_id)
    if schema_in.package_id:
        count_query = count_query.where(QStrategy.package_id == schema_in.package_id)
        fetch_query = fetch_query.where(QStrategy.package_id == schema_in.package_id)
    if schema_in.task_id:
        count_query = count_query.where(QStrategy.task_id.contains(schema_in.task_id))
        fetch_query = fetch_query.where(QStrategy.task_id.contains(schema_in.task_id))
    if schema_in.style:
        count_query = count_query.where(QStrategy.style.contains(schema_in.style))
        fetch_query = fetch_query.where(QStrategy.style.contains(schema_in.style))
    if schema_in.category:
        count_query = count_query.where(QStrategy.category == int(schema_in.category))
        fetch_query = fetch_query.where(QStrategy.category == int(schema_in.category))
    if schema_in.name:
        count_query = count_query.where(QStrategy.name.contains(schema_in.name))
        fetch_query = fetch_query.where(QStrategy.name.contains(schema_in.name))
    if return_strategy_list:
        if schema_in.fuzzy:
            #count_query = count_query.where(QStrategy.name.contains(schema_in.fuzzy))
            count_query = count_query.where(
                    or_(
                        and_(QStrategy.name.contains(schema_in.fuzzy),QStrategy.status==ListStatus.online),
                        and_(QStrategy.author_name.contains(schema_in.fuzzy),QStrategy.status==ListStatus.online),
                        )
                    )
            #print(await db.scalar(count_query),'qqqqqqqqqqqqqqqqqqqq')
            #print(schema_in.fuzzy,'fuzzy--------1111111111111111111')
            #fetch_query = fetch_query.where(QStrategy.name.in_(schema_in.fuzzy)).where(QStrategy.author_name.in_(schema_in.fuzzy))
            fetch_query = fetch_query.where(
                    or_(
                        and_(QStrategy.name.contains(schema_in.fuzzy),QStrategy.status==ListStatus.online),
                        and_(QStrategy.author_name.contains(schema_in.fuzzy),QStrategy.status==ListStatus.online),

                        )
                    )
    else:
        if schema_in.fuzzy:
            count_query = count_query.where( 
                or_(
                    QStrategy.name.contains(schema_in.fuzzy),
                    QStrategy.author_name.contains(schema_in.fuzzy),
                    QStrategy.product_id.contains(schema_in.fuzzy),
                    )
                )
            fetch_query = fetch_query.where(
                or_(
                    QStrategy.name.contains(schema_in.fuzzy),
                    QStrategy.author_name.contains(schema_in.fuzzy),
                    QStrategy.product_id.contains(schema_in.fuzzy),
                    )
                )
    total_count = await db.scalar(count_query)
    order_bys = []
    for key in schema_in.order_bys:
        if not key.startswith("-"):
            if not hasattr(QStrategy, key):
                logger.warning("search strategy has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(QStrategy, key))
        else:
            if not hasattr(QStrategy, key[1:]):
                logger.warning("search strategy has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(QStrategy, key[1:]).desc())

    #strategy_list = (
    #    await fetch_query.order_by(*order_bys)
    #    .offset(schema_in.offset)
    #    .limit(schema_in.count).gino.all()
    #)
    print(order_bys,'order_bus---111111111111111')
    strategy_list = (
            await fetch_query.order_by(*order_bys).gino.all())
    if return_strategy_list:
        return total_count, strategy_list
    # tag_names = [tag.name for tag in tags]
    return QStrategySearchOut(
        total=total_count, data=[strategy for strategy in strategy_list],
    )

async def sortedd(data,total_cnt,sort):
    info2 = []
    info1 = []
    task = []#存在cum_returns
    task2 = []
    for i in data:
        if 'cum_returns' not in i.keys():
            info1.append(i)
        else:
            task.append(i)
    for cash in data:
        if 'sim_start_cash' not in cash.keys():
            info2.append(cash)
        else:
            task2.append(cash)
    if sort == '1':
        sort_cum = sorted(task, key=lambda s: s['cum_returns'], reverse=False)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt,sort_cum)
    elif sort == '-1':
        sort_cum = sorted(task, key=lambda s: s['cum_returns'], reverse=True)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '2':
        sort_cum = sorted(task, key=lambda s: s['daily_returns'], reverse=False)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '-2':
        sort_cum = sorted(task, key=lambda s: s['daily_returns'], reverse=True)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '3':
        sort_cum = sorted(task, key=lambda s: s['annual_returns'], reverse=False)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '-3':
        sort_cum = sorted(task, key=lambda s: s['annual_returns'], reverse=True)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '4':
        sort_cum = sorted(task, key=lambda s: s['max_drawdown'], reverse=False)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '-4':
        sort_cum = sorted(task, key=lambda s: s['max_drawdown'], reverse=True)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '5':
        sort_cum = sorted(task2, key=lambda s: s['sim_start_cash'], reverse=False)
        for j in info2:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    elif sort == '-5':
        sort_cum = sorted(task2, key=lambda s: s['sim_start_cash'], reverse=True)
        for j in info2:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
    else:
        sort_cum = sorted(task, key=lambda s: s['cum_returns'], reverse=True)
        for j in info1:
            sort_cum.append(j)
        return (total_cnt, sort_cum)
