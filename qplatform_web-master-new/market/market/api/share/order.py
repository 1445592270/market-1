import logging

from sqlalchemy import text

from market.models import MarketUser, UserOrder, db
from market.models.const import OrderStatus
from market.schemas.order import OrderInfo, OrderSearch, OrderSearchOut

logger = logging.getLogger(__name__)


async def show_order(order_id: int):
    """查看订单详情"""
    order = UserOrder.get_or_none(id=order_id)
    if order:
        return OrderInfo(**order.__dict__)
    return None


async def search_order(schema_in: OrderSearch):
    """搜索用户的订单列表"""
    count_query = db.select([db.func.count(UserOrder.id)]).where(
        UserOrder.status != int(OrderStatus.deleted)
    )
    fetch_query = UserOrder.query.where(UserOrder.status != int(OrderStatus.deleted))
    if schema_in.fuzzy:  # 订单模糊搜索，账户和订单 ID
        fuzzy_check = (
            UserOrder.user_id.phone.contains(schema_in.fuzzy)
            | UserOrder.user_id.email.contains(schema_in.fuzzy)
            | UserOrder.user_id.name.contains(schema_in.fuzzy)
        )
        try:
            order_id = int(schema_in.fuzzy)
            fuzzy_check |= UserOrder.id == order_id
        except ValueError:
            pass
        fetch_query = fetch_query.where(fuzzy_check)
        count_query = count_query.where(fuzzy_check)
    if schema_in.product_id:
        product_id = schema_in.product_id
        try:
            fetch_query = fetch_query.where(UserOrder.product_id.contains(product_id))
            count_query = count_query.where(UserOrder.product_id.contains(product_id))
        except ValueError:
            pass
    if schema_in.order_id:
        fetch_query = fetch_query.where(UserOrder.id == schema_in.order_id)
        count_query = count_query.where(UserOrder.id == schema_in.order_id)
    if schema_in.user_id:
        fetch_query = fetch_query.where(UserOrder.user_id == schema_in.user_id)
        count_query = count_query.where(UserOrder.user_id == schema_in.user_id)
    if schema_in.product_id:
        fetch_query = fetch_query.filter(UserOrder.product_id == schema_in.product_id)
        count_query = count_query.where(UserOrder.user_id == schema_in.user_id)
    if schema_in.product_type:
        fetch_query = fetch_query.where(
            UserOrder.product_type == int(schema_in.product_type)
        )
        count_query = count_query.where(
            UserOrder.product_type == int(schema_in.product_type)
        )
    if schema_in.status:
        fetch_query = fetch_query.where(UserOrder.status == int(schema_in.status))
        count_query = count_query.where(UserOrder.status == int(schema_in.status))

    total_count = await db.scalar(count_query)
    orders = (
        await fetch_query.order_by(text("-id"))
        .offset(schema_in.offset)
        .limit(schema_in.count)
        .gino.all()
    )
    data = []
    print(orders,'orders---222222222222222')
    for order in orders:
        print(order.__dict__,'order----111111111111111')

        if order.user:
            mk = await MarketUser.get(int(order.user_id))
            info = {
                "user_id": mk.id,
                "user_name": mk.name,
                "user_phone": mk.phone,
            }
        else:
            info = {"user_id": -1, "user_name": "deleted", "user_phone": "100000000000"}
        info.update(order.__dict__["__values__"])
        data.append(info)
    return OrderSearchOut(total=total_count, data=data)
