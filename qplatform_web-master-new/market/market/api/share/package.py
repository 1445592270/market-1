import logging
from typing import List, Union

from fastapi import HTTPException, status
from fastapi.exceptions import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from market.models import StrategyPackage, db
from market.models.const import ListStatus
from market.schemas.base import CommonOut
from market.schemas.package import PkgCreate, PkgSearch, PkgSearchOut, PkgUpdateFields

logger = logging.getLogger(__name__)


async def show_pkg(pkg_id: str):
    """查看策略套餐"""
    return await StrategyPackage.query.where(
        StrategyPackage.product_id == pkg_id
    ).gino.first()


async def create_package(schema_in: PkgCreate):
    """添加套餐"""
    try:
        await StrategyPackage.create(**schema_in.dict())
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="创建套餐失败，请检查名字是否重复"
        )
    except Exception:
        logger.exception("create tag failed: %s", schema_in.json())
        raise HTTPException(status_code=400, detail="数据库错误")

    return CommonOut()


async def edit_pkg(product_id, changed: PkgUpdateFields):
    """编辑套餐"""
    try:
        await StrategyPackage.update.values(**changed.dict()).where(
            StrategyPackage.product_id == product_id
        ).gino.status()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="更新套餐失败，请检查名字是否重复")
    except Exception:
        logger.exception("更新套餐 (%s) 失败：%s", product_id, changed.json())
        raise HTTPException(status_code=400, detail="数据库错误")
    return CommonOut()


async def change_pkg_status(product_id: str, change_status: ListStatus):
    """更改套餐状态"""
    try:
        await StrategyPackage.update.values(status=change_status).where(
            StrategyPackage.product_id == product_id
        ).gino.status()
    except Exception:
        logger.exception("更新套餐 (%s) 状态失败：%s", product_id, change_status)
        raise HTTPException(status_code=400, detail="数据库错误")
    return CommonOut()


async def search_pkg(schema_in: PkgSearch):
    """搜索套餐"""
    # TODO: support tag search, perphaps need to use raw sql
    count_query = db.select([db.func.count(StrategyPackage.product_id)])
    fetch_query = StrategyPackage.query
    print(count_query,'3333333333333333333333333')
    print(fetch_query,'22222222222222222222')
    if schema_in.status:
        #count_query = count_query.filter(
        #    StrategyPackage.status == int(schema_in.status)
        #)
        count_query = count_query.where(StrategyPackage.status == int(schema_in.status))
        #fetch_query = fetch_query.filter(
        #    StrategyPackage.status == int(schema_in.status)
        #)
        fetch_query = fetch_query.where(StrategyPackage.status == int(schema_in.status))
    else:
        #count_query = count_query.filter(
        #    StrategyPackage.status != int(ListStatus.deleted)
        #)
        count_query = count_query.where(StrategyPackage.status != int(ListStatus.deleted))
        #fetch_query = fetch_query.filter(
        #    StrategyPackage.status != int(ListStatus.deleted)
        #)
        fetch_query = fetch_query.where(StrategyPackage.status != int(ListStatus.deleted))
    if schema_in.product_id:
        count_query = count_query.where(
            StrategyPackage.product_id == schema_in.product_id
        )
        fetch_query = fetch_query.where(
            StrategyPackage.product_id == schema_in.product_id
        )
    if schema_in.name:
        count_query = count_query.where(StrategyPackage.name.contains(schema_in.name))
        fetch_query = fetch_query.where(StrategyPackage.name.contains(schema_in.name))
    if schema_in.tag:
        # TODO: support tag search
        pass
    if schema_in.market_id:
        count_query = count_query.where(
            StrategyPackage.market_id == schema_in.market_id
        )
        fetch_query = fetch_query.where(
            StrategyPackage.market_id == schema_in.market_id
        )
    total_count = await db.scalar(count_query)
    print(total_count,'444444444444444444444')
    pkg_list = (
        await fetch_query.order_by(text("name"))
        .offset(schema_in.offset)
        .limit(schema_in.count).gino.all()
    )
    print(pkg_list,'1111111111111111111111111111111')
    return PkgSearchOut(total=total_count, data=[pkg for pkg in pkg_list])
