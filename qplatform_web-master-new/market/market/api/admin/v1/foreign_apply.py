import datetime
import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder

from market.ctx import ctx
from market.models import QStrategy, ReviewRecord, StrategyMarket
from market.models.const import ListStatus, ProductType, ReviewOP, ReviewStatus
from market.schemas.base import CommonOut
from market.schemas.review import (
    ApplyQuery,
    ApplyQueryOut,
    OfflineApplyInfo,
    OnlineApplyInfo,
)
from market.utils import next_product_id

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/apply/strategy/query", response_model=ApplyQueryOut, tags=["后台——上下架申请"])
async def query_list_info(query_in: ApplyQuery):
    """查询上下架申请状态"""
    sim_ids = query_in.sim_id
    if isinstance(sim_ids, str):
        sim_ids = [sim_ids]
    async with ctx.mysql_cli as conn:
        cursor = await conn.cursor()

        # get simulation info
        query_str = f"SELECT user_id FROM wk_simulation WHERE id in ({','.join(['%s']*len(sim_ids))})"

        # get simulation info
        await cursor.execute(query_str, sim_ids)
        rows = await cursor.fetchall()
        if len(rows) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数"
            )
        user_ids = [row[0] for row in rows]
        user_id = str(user_ids[0])

        # get user
        await cursor.execute("SELECT phone FROM wk_user WHERE id=%s", user_id)
        rows = await cursor.fetchall()
        if len(rows) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数"
            )
        user_phone = rows[0][0]
    if query_in.user_id != user_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数")

    rows = (
        await QStrategy.select("product_id")
        .where(
            QStrategy.status.in_(
                [
                    int(ListStatus.online_review),
                    int(ListStatus.online),
                    int(ListStatus.offline_review),
                    int(ListStatus.online_rejected),
                    int(ListStatus.offline_rejected),
                    int(ListStatus.offline),
                ]
            ),
            QStrategy.sim_id.in_(sim_ids),
        )
        .gino.all()
    )

    if not rows:
        return ApplyQueryOut(total_cnt=0, data=[])

    product_ids = [row["product_id"] for row in rows]
    review_list = await ReviewRecord.query.where(
        ReviewRecord.product_id.in_(product_ids),
        ReviewRecord.product_type == int(ProductType.qstrategy),
    ).gino.first()
    if not review_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数")

    apply_info = {}
    for review in review_list:
        apply_info[review.product_id] = {
            "status": review.review_status,
            "review_dt": review.review_dt,
            "msg": review.review_msg,
        }

    rows = (
        await QStrategy.select("sim_id", "task_id", "name", "sell_cnt", "total_cnt")
        .where(QStrategy.product_id.in_(product_ids))
        .gino.all()
    )
    for row in rows:
        if row["product_id"] not in apply_info:
            continue
        apply_info[row["product_id"]].update(
            {
                "sim_id": row["sim_id"],
                "task_id": row["task_id"],
                "name": row["name"],
                "sell_cnt": row["sell_cnt"],
                "total_cnt": row["total_cnt"],
            }
        )
    return ApplyQueryOut(total_cnt=len(apply_info), data=list(apply_info.values()))


@router.post("/apply/strategy/list", response_model=CommonOut, tags=["后台——上下架申请"])
async def list_apply(schema_in: OnlineApplyInfo):
    """策略上架申请"""
    row = (
        await QStrategy.select("product_id")
        .where(
            QStrategy.status.in_(
                [
                    int(ListStatus.online_review),
                    int(ListStatus.online),
                    int(ListStatus.offline_review),
                ]
            ),
            sim_id=schema_in.sim_id,
        )
        .gino.first()
    )

    if row:
        return CommonOut(errCode=-1, errMsg="申请失败，该策略在商城已存在")

    async with ctx.mysql_cli as conn:
        cursor = await conn.cursor()
        # get simulation info
        await cursor.execute(
            "SELECT user_id, name, task_id, backtest_id, init_money, start_date FROM wk_simulation WHERE id=%s",
            schema_in.sim_id,
        )
        rows = await cursor.fetchall()
        if len(rows) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="未找到对应的模拟交易"
            )
        user_id = str(rows[0][0])
        user_id = str(row[0][0])
        sim_name = str(row[0][1])
        task_id = str(row[0][2])
        backtest_id = row[0][3]
        sim_start_cash = float(row[0][4])
        sim_start_dt = datetime.datetime.combine(row[0][5], datetime.time())

        await cursor.execute(
            "SELECT phone, nick_name FROM wk_user WHERE id=%s", user_id
        )
        rows = await cursor.fetchall()
        if len(rows) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="模拟交易的用户信息不一致！！！"
            )
        user_phone = row[0][0]
        author_name = row[0][1]
        if user_phone != schema_in.user_id:
            logger.error(
                "request list apply for %s user not match (apply: %s, query: %s)",
                task_id,
                schema_in.user_id,
                user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="模拟交易的用户信息不一致！！！"
            )

        # get backtest task_id
        await cursor.execute(
            "SELECT task_id FROM wk_strategy_backtest WHERE id=%s", backtest_id
        )
        rows = await cursor.fetchall()
        if len(rows) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="没找到对应的回测信息"
            )
        bt_task_id = str(row[0][0])

    if schema_in.market_id:
        market = await StrategyMarket.get(schema_in.market_id)
    else:
        market = None

    strategy = await QStrategy.create(
        sim_id=schema_in.sim_id,
        user_id=user_id,
        product_id=next_product_id(),
        task_id=task_id,
        author_name=author_name,
        sim_name=sim_name,
        bt_task_id=bt_task_id,
        sim_start_cash=sim_start_cash,
        sim_start_dt=sim_start_dt,
        status=int(ListStatus.online_review),
        name=schema_in.name,
        category=int(schema_in.category),
        style=schema_in.style,
        tags=schema_in.tags,
        ideas=schema_in.ideas if schema_in.ideas else "",
        desc=schema_in.desc if schema_in.desc else "",
        suit_money=schema_in.suit_money,
        buyout_price=jsonable_encoder(
            schema_in.buyout_price if schema_in.buyout_price else []
        ),
        total_cnt=schema_in.total_cnt,
        period_prices=jsonable_encoder(
            schema_in.period_prices if schema_in.period_prices else []
        ),
        market=market,
        limit_copy=1,
        limit_interval=1,
    )
    ReviewRecord.create(
        product_id=strategy.product_id,
        product_type=int(ProductType.qstrategy),
        operation=int(ReviewOP.online),
        review_status=int(ReviewStatus.wait),
        review_msg=schema_in.msg if schema_in.msg else "",
        user_id=user_id,  # 申请人
        contact=schema_in.contact,  # 申请人手机号
        market=market,
    )
    return CommonOut()


@router.post("/apply/strategy/delist", response_model=CommonOut, tags=["后台——上下架申请"])
async def delist_apply(query_in: OfflineApplyInfo):
    """策略下架申请"""
    async with ctx.mysql_cli as conn:
        cursor = await conn.cursor()
        # get simulation info
        await cursor.execute(
            "SELECT user_id FROM wk_simulation WHERE id=%s", query_in.sim_id
        )
        rows = await cursor.fetchall()
        if len(rows) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数"
            )
        user_id = str(rows[0][0])

        # get user
        await cursor.execute("SELECT phone FROM wk_user WHERE id=%s", user_id)
        rows = await cursor.fetchall()
        if len(rows) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数"
            )
        user_phone = rows[0][0]

    if query_in.user_id != user_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数")

    strategy = await QStrategy.query.where(
        QStrategy.sim_id == query_in.sim_id
    ).gino.first()
    if not strategy:
        logger.error("delist apply with strategy not in market: %s", query_in)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请检查查询参数")
    await strategy.update(status=int(ListStatus.offline_review)).apply()
    await ReviewRecord.create(
        product_id=strategy.product_id,
        product_type=int(ProductType.qstrategy),
        operation=int(ReviewOP.offline),
        review_status=int(ReviewStatus.wait),
        review_msg=query_in.msg,
        user_id=user_id,  # 申请人
        contact=query_in.contact,  # 申请人手机号
        market=strategy.market,
    )
    return CommonOut()
