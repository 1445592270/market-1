# modified from sqlacodegen db_url > market_models.py
import datetime

from gino.ext.starlette import Gino
from uuid import UUID
# coding: utf-8
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from market import config

db = Gino(
    dsn=config.PG_DB_DSN,
    pool_min_size=config.PG_DB_POOL_MIN_SIZE,
    pool_max_size=config.PG_DB_POOL_MAX_SIZE,
    echo=config.PG_DB_ECHO,
    ssl=config.PG_DB_SSL,
    use_connection_for_request=config.PG_DB_USE_CONNECTION_FOR_REQUEST,
    retry_limit=config.PG_DB_RETRY_LIMIT,
    retry_interval=config.PG_DB_RETRY_INTERVAL,
)


class Coupon(db.Model):
    __tablename__ = "coupon"

    id = Column(Integer, primary_key=True)
    category = Column(
        SmallInteger,
        nullable=False,
        comment="deduce_day: 1\\ndeduce_cash: 2\\ncash_discount: 3",
    )
    value = Column(Float(53), nullable=False)
    total_cnt = Column(Integer, nullable=False)
    limit_cnt = Column(Integer, nullable=False)
    disable = Column(Boolean, nullable=False, server_default=text("false"))
    start_dt = Column(DateTime, nullable=False, server_default=func.now())
    msg = Column(Text, server_default="", nullable=True)
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    expire_dt = Column(DateTime, nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MarketAdminUser(db.Model):
    __tablename__ = "marketadminuser"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(32), index=True)
    name = Column(String(32), nullable=False, unique=True)
    phone = Column(String(14), nullable=False, unique=True)
    email = Column(String(63), nullable=True, unique=True)
    password = Column(String(128), nullable=False)
    scope1 = Column(String(32), nullable=False)
    scope2 = Column(SmallInteger, nullable=False, comment="su: 1")
    status = Column(
        SmallInteger,
        nullable=False,
        server_default="1",
        comment="normal: 1\\ninactive: 2\\ndisabled: 3\\ndeleted: 4",
    )
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PushInfo(db.Model):
    __tablename__ = "pushinfo"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    qstrategy_id = Column(String(32), nullable=False)
    task_id = Column(String(32), nullable=False, index=True)
    contact = Column(String(14), server_default="", nullable=True)
    status = Column(
        SmallInteger,
        nullable=False,
        comment="normal: 1\\ndisabled: 2\\nexpired: 3",
        server_default="1",
    )
    push_method = Column(
        SmallInteger, nullable=False, comment="wechat: 1\\nemail: 2\\npost: 3"
    )
    push_id = Column(String(1024), nullable=False)
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StrategyMarket(db.Model):
    __tablename__ = "strategymarket"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    domain = Column(String(1024), nullable=False)
    #info = Column(Text, server_default="", nullable=True)
    status = Column(
        SmallInteger,
        nullable=False,
        server_default="1",
        comment="normal: 1\\ndisabled: 2\\ndeleted: 3",
    )
    #create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    #update_dt = Column(
    #    DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    #)


class Tag(db.Model):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    tag_type = Column(
        SmallInteger,
        nullable=False,
        server_default=text("1"),
        comment="tag: 1\\nstyle: 2",
    )
    deleted = Column(Boolean, nullable=False, server_default=text("false"))
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UserCollection(db.Model):
    __tablename__ = "usercollection"

    id = Column(Integer, primary_key=True)
    url = Column(String(1024), nullable=False)
    product_id = Column(String(32), nullable=False, index=True)
    #product_id = Column(UUID, nullable=False, index=True)
    product_type = Column(
        SmallInteger, nullable=False, comment="qstrategy: 1\\npackage: 2\\nvip: 3"
    )
    user_id = Column(Integer, nullable=False)
    canceled = Column(Boolean, nullable=False)
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MarketUser(db.Model):
    __tablename__ = "marketuser"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(64), nullable=False, index=True)
    name = Column(String(32), nullable=False, unique=True)
    phone = Column(String(14), nullable=False, unique=True)
    email = Column(String(63), nullable=True, unique=True)
    broker_id = Column(String(32), server_default="", nullable=True)
    password = Column(String(128), nullable=False)
    status = Column(
        SmallInteger,
        nullable=False,
        comment="normal: 1\\ninactive: 2\\ndisabled: 3\\ndeleted: 4",
        server_default="1",
    )
    #create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    #update_dt = Column(
    #    DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    #)
    market_id = Column(ForeignKey("strategymarket.id", ondelete="SET NULL"))

    market = relationship("StrategyMarket")


class ReviewRecord(db.Model):
    __tablename__ = "reviewrecord"

    id = Column(Integer, primary_key=True)
    product_id = Column(String(32), nullable=False, index=True)
    #product_id = Column(UUID, nullable=False, index=True)
    product_type = Column(
        SmallInteger, nullable=False, comment="qstrategy: 1\\npackage: 2\\nvip: 3"
    )
    operation = Column(SmallInteger, nullable=False, comment="online: 1\\noffline: 2")
    user_id = Column(Integer, nullable=False)
    contact = Column(String(14), nullable=False)
    review_dt = Column(DateTime)
    review_status = Column(
        SmallInteger,
        nullable=False,
        comment="wait: 1\\naccepted: 2\\nrejected: 3\\ndeleted: 4",
        server_default="1",
    )
    review_msg = Column(Text)
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    market_id = Column(ForeignKey("strategymarket.id", ondelete="SET NULL"))

    market = relationship("StrategyMarket")


class StrategyPackage(db.Model):
    __tablename__ = "strategypackage"

    product_id = Column(String(32), primary_key=True)
    #product_id = Column(UUID, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    tags = Column(JSONB(astext_type=Text()), nullable=False)
    desc = Column(Text, nullable=False)
    status = Column(
        SmallInteger,
        nullable=False,
        comment="online_review: 1\\nonline_rejected: 2\\nonline: 3\\noffline_review: 4\\noffline_rejected: 5\\noffline: 6\\ndeleted: 7",
        server_default="2",
    )
    limit_copy = Column(Integer, server_default=text("10000"), nullable=False)
    limit_interval = Column(Integer, server_default=text("10000"), nullable=False)
    view_cnt = Column(Integer, server_default=text("0"), nullable=False)
    collect_cnt = Column(Integer, server_default=text("0"), nullable=False)
    share_cnt = Column(Integer, server_default=text("0"), nullable=False)
    buyout_price = Column(Float(53), nullable=False)
    enable_discount = Column(Boolean, server_default=text("false"), nullable=False)
    allow_coupon = Column(Boolean, server_default=text("false"), nullable=False)
    period_prices = Column(JSONB(astext_type=Text()), nullable=True)
    discount_info = Column(JSONB(astext_type=Text()), nullable=True)
    online_dt = Column(DateTime)
    offline_dt = Column(DateTime)
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    market_id = Column(ForeignKey("strategymarket.id", ondelete="SET NULL"))

    market = relationship("StrategyMarket")


class QStrategy(db.Model):
    __tablename__ = "qstrategy"

    product_id = Column(String(32), primary_key=True)
    #product_id = Column(UUID, primary_key=True)
    sim_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    author_name = Column(String(32), server_default="", nullable=True)
    task_id = Column(String(32), nullable=False, index=True)
    sim_start_cash = Column(Float(53), nullable=False)
    sim_start_dt = Column(DateTime, nullable=False)
    sim_name = Column(String(128), nullable=False)
    bt_task_id = Column(String(32), nullable=True)
    name = Column(String(128), nullable=False)
    buyout_price = Column(Float(53), nullable=False)
    total_cnt = Column(Integer, server_default=text("1000"), nullable=False)
    category = Column(
        SmallInteger,
        server_default=text("1"),
        nullable=False,
        comment="stock: 1\\nfutures: 2",
    )
    style = Column(String(32), server_default="", nullable=True)
    tags = Column(JSONB(astext_type=Text()), nullable=True)
    ideas = Column(Text, server_default="", nullable=True)
    desc = Column(Text, server_default="", nullable=True)
    suit_money = Column(Float(53), nullable=False)
    limit_copy = Column(Integer, server_default=text("10000"), nullable=False)
    limit_interval = Column(Integer, server_default=text("10000"), nullable=False)
    sell_cnt = Column(Integer, server_default=text("0"), nullable=False)
    sell_cnt_show = Column(Integer, server_default=text("0"), nullable=False)
    online_dt = Column(DateTime)
    offline_dt = Column(DateTime)
    view_cnt = Column(Integer, server_default=text("0"), nullable=False)
    collect_cnt = Column(Integer, server_default=text("0"), nullable=False)
    share_cnt = Column(Integer, server_default=text("0"), nullable=False)
    enable_discount = Column(Boolean, server_default=text("false"), nullable=False)
    allow_coupon = Column(Boolean, server_default=text("false"), nullable=False)
    status = Column(
        SmallInteger,
        nullable=False,
        comment="online_review: 1\\nonline_rejected: 2\\nonline: 3\\noffline_review: 4\\noffline_rejected: 5\\noffline: 6\\ndeleted: 7",
        server_default="1",
    )
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    period_prices = Column(JSONB(astext_type=Text()), nullable=True)
    discount_info = Column(JSONB(astext_type=Text()), nullable=False)
    market_id = Column(ForeignKey("strategymarket.id", ondelete="SET NULL"))
    package_id = Column(ForeignKey("strategypackage.product_id", ondelete="SET NULL"))

    market = relationship("StrategyMarket")
    package = relationship("StrategyPackage")


class UserOrder(db.Model):
    __tablename__ = "userorder"

    id = Column(Integer, primary_key=True)
    product_id = Column(String(32), nullable=False, index=True)
    #product_id = Column(UUID, nullable=False, index=True)
    product_type = Column(
        SmallInteger, nullable=False, comment="qstrategy: 1\\npackage: 2\\nvip: 3"
    )
    total_cash = Column(Float(53), nullable=False)
    total_days = Column(Integer, nullable=False)
    days = Column(Integer, nullable=False)
    gift_days = Column(Integer, server_default=text("0"), nullable=False)
    coupon_days = Column(Integer, server_default=text("0"), nullable=False)
    coupon_cash = Column(Float(53), server_default=text("0"), nullable=False)
    pay_cash = Column(Float(53), nullable=False)
    payed_cash = Column(Float(53), nullable=False)
    pay_dt = Column(DateTime)
    expire_dt = Column(DateTime)
    status = Column(
        SmallInteger,
        nullable=False,
        server_default="1",
        comment="unpayed: 1\\npayed: 2\\ncalceled: 3\\nexpierd: 4\\ndeleted: 9",
    )
    create_dt = Column(DateTime, server_default=func.now(), nullable=False)
    update_dt = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    # foreign pay info
    foreign_order_id = Column(String(32), nullable=False)
    pay_id = Column(String(48), nullable=False)
    pay_method = Column(SmallInteger, nullable=False, comment="offline: 1\\nwechat: 2")
    pay_url = Column(String(255), nullable=False)
    delete = Column(Boolean,default=False)
    source = Column(String(32), server_default="pc", nullable=False)
    # coupon list
    coupon = Column(JSONB(astext_type=Text()))
    product_snapshot = Column(JSONB(astext_type=Text()), nullable=False)
    user_id = Column(ForeignKey("marketuser.id", ondelete="SET NULL"))

    user = relationship("Marketuser")
