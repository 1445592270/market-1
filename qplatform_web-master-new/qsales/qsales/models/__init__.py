# modified from sqlacodegen db_url > market_models.py
import datetime

# coding: utf-8
from sqlalchemy import CHAR, DECIMAL, Column, DateTime, String, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from gino.ext.starlette import Gino
from qpweb import config

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


class LatestManagementAssetStatistic(db.Model):
    __tablename__ = 'latest_management_asset_statistics'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    role_type = Column(TINYINT(4), comment='角色类型 1 为推广商 2 位推广经理')
    manage_total_assets = Column(DECIMAL(16, 2), comment='管理总资产')
    total_number_of_accounts_opened = Column(BIGINT(20), comment='总的已开户数量')
    update_time = Column(BIGINT(20), comment='更新时间')
    total_strategic_cost = Column(DECIMAL(16, 2), comment='总的策略费用')
    total_strategic_cost_update_time = Column(BIGINT(20), comment='总的策略费用更新时间')


class PromoterStatistic(db.Model):
    __tablename__ = 'promoter_statistics'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    role_type = Column(TINYINT(4), comment='角色类型 1 为推广商 2 位推广经理')
    daily_trading_volume = Column(DECIMAL(16, 2), comment='日交易量')
    monthly_transaction_volume = Column(DECIMAL(16, 2), comment='月交易量')
    total_transaction_volume = Column(DECIMAL(16, 2), comment='总交易量')
    daily_total_commission = Column(DECIMAL(16, 2), comment='日的总佣金')
    brokerage_cost_per_day = Column(DECIMAL(16, 2), comment='日的券商成本')
    daily_remaining_commission = Column(DECIMAL(16, 2), comment='日的剩余佣金')
    total_monthly_commission = Column(DECIMAL(16, 2), comment='月的总佣金')
    brokerage_cost_per_month = Column(DECIMAL(16, 2), comment='月的券商成本')
    months_remaining_commission = Column(DECIMAL(16, 2), comment='月的剩余佣金')
    total_total_commission = Column(DECIMAL(16, 2), comment='总的总佣金')
    total_brokerage_cost = Column(DECIMAL(16, 2), comment='总的券商成本')
    total_remaining_commission = Column(DECIMAL(16, 2), comment='总的剩余佣金')
    create_time = Column(BIGINT(20), comment='创建时间')
    creation_time_int = Column(INTEGER(11), comment='创建时间 yyMMdd')


class UserCommissionStatistic(db.Model):
    __tablename__ = 'user_commission_statistics'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    daily_trading_volume = Column(DECIMAL(16, 2), comment='日交易量')
    monthly_transaction_volume = Column(DECIMAL(16, 2), comment='月交易量')
    total_transaction_volume = Column(DECIMAL(16, 2), comment='总交易量')
    daily_total_commission = Column(DECIMAL(16, 2), comment='日的总佣金')
    brokerage_cost_per_day = Column(DECIMAL(16, 2), comment='日的券商成本')
    daily_remaining_commission = Column(DECIMAL(16, 2), comment='日的剩余佣金')
    total_monthly_commission = Column(DECIMAL(16, 2), comment='月的总佣金')
    brokerage_cost_per_month = Column(DECIMAL(16, 2), comment='月的券商成本')
    months_remaining_commission = Column(DECIMAL(16, 2), comment='月的剩余佣金')
    total_total_commission = Column(DECIMAL(16, 2), comment='总的总佣金')
    total_brokerage_cost = Column(DECIMAL(16, 2), comment='总的券商成本')
    total_remaining_commission = Column(DECIMAL(16, 2), comment='总的剩余佣金')
    create_time = Column(BIGINT(20), comment='创建时间')
    creation_time_int = Column(INTEGER(11), comment='创建时间 yyMMdd')


class UserLatestFundStatistic(db.Model):
    __tablename__ = 'user_latest_fund_statistics'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    total_assets = Column(DECIMAL(16, 2), comment='总资产')
    stock_market_value = Column(DECIMAL(16, 2), comment='证券市值')
    available_funds = Column(DECIMAL(16, 2), comment='可用资金')
    profit_and_loss = Column(DECIMAL(16, 2), comment='盈亏')
    asset_update_time = Column(BIGINT(20), comment='资产更新时间')
    number_of_accounts = Column(INTEGER(11), comment='开户数量')
    real_status = Column(TINYINT(4), comment='用户最新实盘状态 1: 进行，2: 待开启，3: 停止，4: 审核中，5: 未通过')
    real_update_time = Column(BIGINT(20), comment='实盘状态更新时间')
    strategic_cost = Column(DECIMAL(16, 2), comment='策略费用')
    strategic_cost_update_time = Column(BIGINT(20), comment='策略费用更新时间')


class WkCompany(db.Model):
    __tablename__ = 'wk_company'

    id = Column(String(36), primary_key=True)
    company_name = Column(String(500), comment='公司名称')
    qr_code_imageurl = Column(String(500), comment='二维码图片 URL')
    operate_id = Column(String(36), comment='操作人 id(*用户 id)')
    type_of_company = Column(TINYINT(4), comment='公司类型：0 期货，1 股票')
    create_time = Column(BIGINT(20), comment='添加时间')
    delete_status = Column(TINYINT(4), comment='删除状态：0 存在，1 已删除')


class WkLoginLog(db.Model):
    __tablename__ = 'wk_login_log'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    log_in_time = Column(BIGINT(20), comment='登录时间')
    log_in_day = Column(String(36), comment='yyyy-MM-dd')
    login_ip = Column(String(30), comment='登录 ip')
    login_status = Column(TINYINT(4), comment='登录状态 (1 正常 2 异常）')
    login_type = Column(TINYINT(4), comment='登录类型 (1 登录 2 登出）')


class WkOperationLog(db.Model):
    __tablename__ = 'wk_operation_log'

    id = Column(String(36), primary_key=True)
    content = Column(String(500), comment='操作内容')
    result = Column(String(36), comment='操作结果 (*成功 / 失败 format)')
    mdule = Column(String(36), comment='操作模块')
    user_id = Column(String(36), comment='操作人')
    login_ip = Column(String(30), comment='登录 ip')
    create_time_day = Column(String(36), comment='yyyy-MM-dd')
    create_time = Column(BIGINT(20), comment='创建时间 (*操作日期）')
    update_time = Column(BIGINT(20), comment='修改时间')


class WkRole(db.Model):
    __tablename__ = 'wk_role'

    id = Column(String(36), primary_key=True)
    role_name = Column(String(30), comment='角色名称')
    role_description = Column(String(50), comment='角色描述')
    role_level = Column(TINYINT(4), comment='角色等级')
    role_number = Column(String(20), comment='角色编号 100001 超级管理员，100002 普通管理员，100003 代理商 (*广告运营商），100004 经纪人 (*二级广告运营商），100005 客户')
    delete_status = Column(TINYINT(4), comment='删除状态：0 存在，1 已删除')


class WkUserAscription(db.Model):
    __tablename__ = 'wk_user_ascription'

    id = Column(String(36), primary_key=True, server_default=text("''"), comment='用户匹配表')
    effective_removal_of_id = Column(String(36), comment='生效时移除 id')
    user_phone = Column(String(11), server_default=text("''"), comment='手机号码')
    ascription_to_him_type = Column(INTEGER(11), comment='归属给他 类型 (*1 代理商 2 经纪人）')
    user_referral_code = Column(String(50), server_default=text("''"), comment='归属推荐码')
    ascription_date_time = Column(DateTime, comment='归属时间 (*提交归属时间）')
    effective_start_time = Column(DateTime, comment='生效开始时间')
    effective_end_time = Column(DateTime, comment='生效结束时间')
    state = Column(INTEGER(1), server_default=text("'1'"), comment='状态（1: 未生效，2 已生效）')
    del_state = Column(CHAR(2), nullable=False, server_default=text("'0'"), comment='删除状态：0 存在，1 已删除 ')


class WkUserInfo(db.Model):
    __tablename__ = 'wk_user_info'

    id = Column(String(36), primary_key=True, server_default=text("''"), comment='用户表')
    user_name = Column(String(20), nullable=False, server_default=text("''"), comment='姓名')
    user_phone = Column(String(11), nullable=False, server_default=text("''"), comment='用户电话号码')
    user_pwd = Column(String(50), server_default=text("''"), comment='用户密码')
    user_herf = Column(String(255), nullable=False, server_default=text("''"), comment='股票个人链接 (*经济人有两个个人链接）')
    user_qr_code = Column(String(255), nullable=False, server_default=text("''"), comment='股票二维码 (*经纪人有两个二维码）')
    user_referral_code = Column(String(50), nullable=False, index=True, comment='用户推荐码')
    user_up_referral_code = Column(String(50), comment='用户上级推荐码')
    user_role = Column(String(20), comment='用户角色：100003 代理商，100004 经纪人，100005 客户')
    register_date_time = Column(DateTime, nullable=False, comment='注册时间 / 添加时间')
    del_state = Column(CHAR(1), nullable=False, server_default=text("'0'"), comment='删除状态：0 存在，1 已删除')
    user_herf_futures = Column(String(255), comment='期货个人链接 (*经济人有两个个人链接）')
    user_qr_code_futures = Column(String(255), comment='期货二维码 (*经纪人有两个二维码）')
    type = Column(TINYINT(4), comment='区分客户用 (*1 为期货 2 为股票）')
    identity_number = Column(String(50), comment='身份证号码')
    last_login_time = Column(BIGINT(20), comment='最近登录时间')
    wk_company_futures_id = Column(String(36), comment='公司 (*期货公司 id)')
    wk_company_securities_id = Column(String(36), comment='公司 (*证券公司 id)')


class WkUserRole(db.Model):
    __tablename__ = 'wk_user_role'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), comment='用户 id')
    role_id = Column(String(36), comment='角色 id')
    delete_status = Column(TINYINT(4), comment='删除状态：0 存在，1 已删除')
