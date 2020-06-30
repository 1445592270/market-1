import logging

from fastapi import APIRouter, Depends, HTTPException, status

from market.core.security import require_super_scope_admin, require_super_scope_su
from market.models import MarketAdminUser, QStrategy, ReviewRecord, StrategyPackage, db
from market.models.const import ListStatus, ProductType, ReviewOP, ReviewStatus
from market.schemas.base import CommonOut
from market.schemas.review import (
    ReviewInfo,
    ReviewResult,
    ReviewSearch,
    ReviewSearchOut,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/review/find", response_model=ReviewSearchOut, tags=["后台——上下架审核管理"])
async def search_review(
    schema_in: ReviewSearch,
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """查找申请"""
    count_query = db.select([db.func.count(ReviewRecord.id)])
    fetch_query = ReviewRecord.query
    if schema_in.review_id:
        count_query = count_query.where(ReviewRecord.id == schema_in.review_id)
        fetch_query = fetch_query.where(ReviewRecord.id == schema_in.review_id)
    if schema_in.review_status:
        count_query = count_query.where(
            ReviewRecord.review_status == int(schema_in.review_status)
        )
        fetch_query = fetch_query.where(
            ReviewRecord.review_status == int(schema_in.review_status)
        )
    else:
        count_query = count_query.where(
            ReviewRecord.review_status != int(ReviewStatus.deleted)
        )
        fetch_query = fetch_query.where(
            ReviewRecord.review_status != int(ReviewStatus.deleted)
        )
    if schema_in.operation:
        count_query = count_query.where(
            ReviewRecord.operation == int(schema_in.operation)
        )
        fetch_query = fetch_query.where(
            ReviewRecord.operation == int(schema_in.operation)
        )
    if schema_in.market_id:
        count_query = count_query.where(ReviewRecord.market_id == schema_in.market_id)
        fetch_query = fetch_query.where(ReviewRecord.market_id == schema_in.market_id)
    if schema_in.user_id:
        count_query = count_query.where(ReviewRecord.user_id == schema_in.user_id)
        fetch_query = fetch_query.where(ReviewRecord.user_id == schema_in.user_id)
    if schema_in.product_type:
        count_query = count_query.where(
            ReviewRecord.product_type == int(schema_in.product_type)
        )
        fetch_query = fetch_query.where(
            ReviewRecord.product_type == int(schema_in.product_type)
        )
    if schema_in.product_id:
        count_query = count_query.where(ReviewRecord.product_id == schema_in.product_id)
        fetch_query = fetch_query.where(ReviewRecord.product_id == schema_in.product_id)
    if schema_in.contact:
        count_query = count_query.where(
            ReviewRecord.contact.contains(schema_in.contact)
        )
        fetch_query = fetch_query.where(
            ReviewRecord.contact.contains(schema_in.contact)
        )

    total_count = await db.scalar(count_query)
    order_bys = []
    for key in schema_in.order_bys:
        if not key.startswith("-"):
            if not hasattr(ReviewRecord, key):
                logger.warning("get review record has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(ReviewRecord, key))
        else:
            if not hasattr(ReviewRecord, key[1:]):
                logger.warning("get review record has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(ReviewRecord, key[1:]).desc())

    if not order_bys:
        order_bys.append(ReviewRecord.update_dt.desc())
    review_list = (
        await fetch_query.order_by(*order_bys)
        .offset(schema_in.offset)
        .limit(schema_in.count).gino.all()
    )
    strategy_ids = []
    package_ids = []
    for review in review_list:
        if review.product_type == int(ProductType.qstrategy):
            strategy_ids.append(review.product_id)
        else:
            package_ids.append(review.product_id)
    strategy_rows = await QStrategy.select(
        "product_id",
        "name",
        "sim_name",
        "task_id",
        "bt_task_id",
        "sim_start_cash",
        "sim_start_dt",
        "category",
    ).where(QStrategy.product_id.in_(strategy_ids)).gino.all()
    pkg_rows = await StrategyPackage.select("name", "product_id").where(
        StrategyPackage.product_id.in_(package_ids)
    ).gino.all()
    extras = {}
    for row in strategy_rows:
        extras[row["product_id"]] = {
            "name": row["name"],
            "sim_name": row["sim_name"],
            "task_id": row["task_id"],
            "bt_task_id": row["bt_task_id"],
            "sim_start_cash": row["sim_start_cash"],
            "sim_start_dt": row["sim_start_dt"],
            "category": row["category"],
        }
    for row in pkg_rows:
        extras[row["product_id"]] = {"name": row["name"]}
    return ReviewSearchOut(
        total=total_count,
        data=[
            {**review.__dict__["__values__"], **extras.get(review.product_id, {})}
            for review in review_list
        ],
    )


@router.post("/review/result", response_model=CommonOut, tags=["后台——上下架审核管理"])
async def do_review(
    schema_in: ReviewResult,
    current_user: MarketAdminUser = Depends(require_super_scope_admin),
):
    """审核结果：通过 / 拒绝"""
    review = await ReviewRecord.get_or_404(schema_in.id)
    if review.review_status != int(ReviewStatus.wait):
        return CommonOut(errCode=-2, errMsg="操作失败，已完成审核")

    if review.product_type == int(ProductType.qstrategy):
        product = await QStrategy.get(review.product_id)
    elif review.product_type == int(ProductType.package):
        product = await StrategyPackage.get(review.product_id)
    if not product:
        return CommonOut(errCode=-2, errMsg="操作失败，没找到对应的策略 / 套餐")

    if product.status not in (int(ListStatus.online_review), int(ListStatus.offline_review)):
        return CommonOut(errCode=-2, errMsg="操作失败，策略 / 套餐已完成审核")

    if schema_in.accept:
        review = review.update(review_status=int(ReviewStatus.accepted))
        if review.operation == int(ReviewOP.online):
            product = product.update(status=int(ListStatus.online))
        else:
            product = product.update(status=int(ListStatus.offline))
    else:
        review = review.update(review_status=int(ReviewStatus.rejected))
        if review.operation == int(ReviewOP.online):
            product = product.update(status=int(ListStatus.online_rejected))
        else:
            product = product.update(status=int(ListStatus.offline_rejected))
    await review.update(review_msg=schema_in.msg).apply()
    await product.apply()
    return CommonOut()


@router.get("/review/{review_id}", response_model=ReviewInfo, tags=["后台——上下架审核管理"])
async def show_review(
    review_id: int, current_user: MarketAdminUser = Depends(require_super_scope_su)
):
    """查看策略申请"""
    review = await ReviewRecord.get_or_404(review_id)
    extras = {}
    if review.product_type == int(ProductType.qstrategy):
        strategy = await QStrategy.get(review.product_id)
        if strategy:
            extras.update(
                {
                    "name": strategy.name,
                    "sim_name": strategy.sim_name,
                    "task_id": strategy.task_id,
                    "bt_task_id": strategy.bt_task_id,
                    "sim_start_cash": strategy.sim_start_cash,
                    "sim_start_dt": strategy.sim_start_dt,
                    "category": strategy.category,
                }
            )
    else:
        pkg = await StrategyPackage.get(review.product_id)
        if pkg:
            extras["name"] = pkg.name

    return ReviewInfo(**review.__dict__, **extras)
