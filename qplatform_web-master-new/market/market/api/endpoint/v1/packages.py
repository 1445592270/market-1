import datetime
import logging

from fastapi import APIRouter, Depends

from market.api.share.package import search_pkg
from market.core.security import require_active_user
from market.models import MarketUser, StrategyPackage, UserOrder
from market.models.const import OrderStatus, ProductType
from market.schemas.package import (
    BuyedPkgInfo,
    BuyedPkgSearch,
    BuyedPkgSearchOut,
    PkgSearch,
    PkgSearchOut,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pkg/list", response_model=BuyedPkgSearchOut, tags=["用户端——套餐管理"])
async def list_pkg(
    schema_in: BuyedPkgSearch, current_user: MarketUser = Depends(require_active_user),
):
    """列出已购买套餐"""
    query = UserOrder.query.where(
        UserOrder.user_id == current_user.id,
        #UserOrder.product_type == int(ProductType.package),
    ).where(UserOrder.product_type == int(ProductType.package))
    if schema_in.show_payed:
        query = query.where(UserOrder.status == int(OrderStatus.payed))
    if schema_in.show_expired:
        query = query.where(UserOrder.expire_dt >= datetime.datetime.now())

    orders = await query.order_by(UserOrder.create_dt.desc()).gino.all()
    order_dict = {order.product_id: order for order in orders}
    # return packages
    packages = await StrategyPackage.query.where(
        StrategyPackage.product_id.in_(list(order_dict.keys()))
    ).gino.all()
    data = []
    for pkg in packages:
        info = dict(**pkg.__dict__)
        info.update(**order_dict[pkg.product_id].__dict__)
        #print(info["__values__"],'info-------22222222222111111111111')
        data.append(BuyedPkgInfo(**info["__values__"]))
    #print(data,'data-----4444444444444')
    return BuyedPkgSearchOut(total=len(packages), data=data)


@router.post("/pkg/find", response_model=PkgSearchOut, tags=["用户端——套餐管理"])
async def user_search_pkg(schema_in: PkgSearch):
    """搜索套餐"""
    return await search_pkg(schema_in)
