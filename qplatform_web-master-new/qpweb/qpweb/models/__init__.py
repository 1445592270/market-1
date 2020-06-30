# modified from sqlacodegen db_url > market_models.py
import datetime

from gino.ext.starlette import Gino

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


class FuturesModel(Base):
    __tablename__ = 'futures_model'

    id = Column(INTEGER(11), primary_key=True)
    no = Column(VARCHAR(64), comment='模型编号')
    name = Column(VARCHAR(64), comment='模型名称')
    treaty = Column(VARCHAR(64), comment='合约名')


class WkAuthentication(Base):
    __tablename__ = 'wk_authentication'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    real_name = Column(VARCHAR(255), nullable=False, comment='真实姓名')
    papers_type = Column(INTEGER(11), nullable=False, server_default=text("'1'"), comment='证件类型')
    papers_num = Column(VARCHAR(64), nullable=False, comment='证件号码')
    check_status = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='审核状态、\n0: 未审核 1: 已审核')
    check_time = Column(DateTime, comment='认证时间')


class WkBroker(Base):
    __tablename__ = 'wk_broker'

    id = Column(INTEGER(11), primary_key=True)
    broker = Column(VARCHAR(255), nullable=False)
    name = Column(VARCHAR(255), nullable=False, comment='公司名称')
    ip = Column(VARCHAR(255))
    port = Column(INTEGER(11))
    disable = Column(INTEGER(1), server_default=text("'0'"))


class WkCashStat(Base):
    __tablename__ = 'wk_cash_stat'

    id = Column(INTEGER(11), primary_key=True, comment='id')
    aq = Column(Float(16, True), nullable=False, server_default=text("'0.0000'"), comment='策略资金')
    wk = Column(Float(16, True), nullable=False, server_default=text("'0.0000'"), comment='五矿资金')
    date = Column(VARCHAR(10), nullable=False, unique=True, comment='统计日期字符串类型')
    total = Column(Float(16, True), nullable=False, server_default=text("'0.0000'"))


class WkDatum(Base):
    __tablename__ = 'wk_data'

    id = Column(INTEGER(11), primary_key=True)
    data_type = Column(INTEGER(11), nullable=False, comment='数据类型 比如：数据字典 新手指引')
    img_href = Column(VARCHAR(255), comment='图片地址')
    title = Column(VARCHAR(255), nullable=False, comment='标题')
    summary = Column(VARCHAR(255), comment='摘要')
    content = Column(LONGTEXT, comment='文章内容 markdown 书写')
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    pub_status = Column(INTEGER(1), server_default=text("'0'"), comment='0: 未发布，1: 已发布')
    html = Column(LONGTEXT, comment='mark 转 html')


class WkDic(Base):
    __tablename__ = 'wk_dic'
    __table_args__ = (
        Index('wk_dic_key_value_uindex', 'key', 'value', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    key = Column(VARCHAR(64), nullable=False, comment='索引（英文）\\neg:\\nsex,bank_card_type...')
    key_desc = Column(VARCHAR(64), nullable=False, comment='索引的中文描述、\neg: key=sex\\n 性别')
    value = Column(VARCHAR(64), nullable=False, comment='索引值（为保证唯一需要加上 key 前缀）\\neg: key=sex\\nsex-girl,sex-boy')
    value_desc = Column(VARCHAR(64), nullable=False, comment='索引值表述、\neg;value=sex-boy\\n 男')
    security_level = Column(INTEGER(11), nullable=False, comment='安全级别，防止管理误删')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkFeedback(Base):
    __tablename__ = 'wk_feedback'

    id = Column(INTEGER(11), primary_key=True)
    phone = Column(VARCHAR(25), comment='手机号')
    content = Column(TEXT, nullable=False, comment='反馈内容')
    user_id = Column(INTEGER(11), nullable=False, comment='用户的 id')
    status = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='0: 未解决，1: 已解决，2: 忽略')
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    update_by = Column(INTEGER(11), comment='处理人 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')


class WkFuture(Base):
    __tablename__ = 'wk_futures'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(255), nullable=False, server_default=text("'期货名称'"), comment='期货名称')
    read = Column(VARCHAR(255), comment='发送方 多个邮箱用，分割')
    send = Column(VARCHAR(255), comment='策略邮箱来源 多个邮箱来源用；分割')
    aim = Column(VARCHAR(255), comment='处理类')


class WkFuturesContract(Base):
    __tablename__ = 'wk_futures_contract'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(255), nullable=False)
    price = Column(Float(16, True), nullable=False)
    handling_fee = Column(INTEGER(4))
    market = Column(String(255, 'utf8mb4_general_ci'), nullable=False)
    disable = Column(INTEGER(1), server_default=text("'0'"))
    desc = Column(VARCHAR(255))
    float_price = Column(Float(10, True), server_default=text("'0.0000'"))
    margin = Column(Float(16, True))
    fee = Column(Float(10, True), server_default=text("'0.0000'"), comment='手续费')


class WkFuturesEmail(Base):
    __tablename__ = 'wk_futures_email'

    id = Column(INTEGER(11), primary_key=True)
    date = Column(VARCHAR(8), nullable=False)
    run_time = Column(VARCHAR(64))
    local_time = Column(VARCHAR(64))
    name = Column(VARCHAR(6))
    contract = Column(VARCHAR(16), nullable=False)
    price = Column(VARCHAR(255), nullable=False)
    num = Column(Float(10, True), server_default=text("'0.0000'"), comment='数量')
    bs = Column(INTEGER(1), nullable=False)
    pk = Column(INTEGER(1), nullable=False)
    md5 = Column(VARCHAR(255), unique=True)
    sendTime = Column(DateTime, nullable=False)
    origin = Column(INTEGER(1), server_default=text("'0'"), comment='0 表示邮箱提示 1 自定义')
    email = Column(VARCHAR(255))
    is_read = Column(INTEGER(2), server_default=text("'0'"))
    futures_id = Column(INTEGER(11), server_default=text("'1'"), comment='wk_futures 的 id, 表示策略标识')


class WkFuturesEmailMonitor(Base):
    __tablename__ = 'wk_futures_email_monitor'

    id = Column(INTEGER(11), primary_key=True)
    account = Column(VARCHAR(255), nullable=False)
    password = Column(VARCHAR(255))
    disable = Column(INTEGER(1), nullable=False, server_default=text("'0'"))


class WkFuturesLevel(Base):
    __tablename__ = 'wk_futures_level'

    id = Column(INTEGER(11), primary_key=True)
    level = Column(INTEGER(2), nullable=False, comment='用户等级')
    min = Column(INTEGER(8), nullable=False, comment='资金量 单位：万、\r\\nnull 表示无上限')
    max = Column(INTEGER(8), comment='资金量 单位：万')
    proportion = Column(INTEGER(4), nullable=False, comment='买入的仓位 单位：%')


class WkFuturesLevelContract(Base):
    __tablename__ = 'wk_futures_level_contract'

    id = Column(INTEGER(11), primary_key=True)
    contract_id = Column(INTEGER(11), nullable=False)
    level_id = Column(INTEGER(11), nullable=False)


class WkFuturesOrderNo(Base):
    __tablename__ = 'wk_futures_order_no'

    id = Column(INTEGER(11), primary_key=True)
    orderNo = Column(BIGINT(32), nullable=False)


class WkFuturesProperty(Base):
    __tablename__ = 'wk_futures_properties'

    id = Column(INTEGER(11), primary_key=True)
    key = Column(VARCHAR(64), nullable=False)
    value = Column(VARCHAR(64), nullable=False)
    desc = Column(VARCHAR(255), comment='配置描述')


class WkFuturesTrade(Base):
    __tablename__ = 'wk_futures_trade'
    __table_args__ = (
        Index('wk_futures_trade_real_id_email_id_uindex', 'real_id', 'email_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    real_id = Column(INTEGER(11), nullable=False)
    email_id = Column(INTEGER(11))
    status = Column(INTEGER(1), server_default=text("'0'"), comment='状态 0 待处理 1 完成 -1 失败')
    fail_info = Column(VARCHAR(255))
    order_no = Column(VARCHAR(64))
    order_sys_no = Column(VARCHAR(64))
    create_time = Column(DateTime)


class WkManager(Base):
    __tablename__ = 'wk_manager'

    id = Column(INTEGER(11), primary_key=True, comment='主键')
    account = Column(VARCHAR(64), nullable=False, unique=True, comment='账号')
    nick_name = Column(VARCHAR(64), comment='昵称')
    password = Column(VARCHAR(64), nullable=False, comment='密码')
    real_name = Column(VARCHAR(64), comment='真实姓名')
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    recently_login = Column(DateTime, comment='最近登录时间')


class WkManagerRole(Base):
    __tablename__ = 'wk_manager_role'

    id = Column(INTEGER(11), primary_key=True, comment='主键')
    manager_id = Column(INTEGER(11), nullable=False, comment='管理员的 id')
    role_id = Column(INTEGER(11), nullable=False, comment='角色的 id')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkMarketManagerSetting(Base):
    __tablename__ = 'wk_market_manager_setting'

    id = Column(INTEGER(11), primary_key=True)
    key = Column(VARCHAR(50), unique=True, server_default=text("''"))
    value = Column(VARCHAR(50), server_default=text("''"))
    extra = Column(VARCHAR(50), server_default=text("''"))
    create_time = Column(DATETIME(fsp=6), index=True, server_default=text("CURRENT_TIMESTAMP(6)"))
    update_time = Column(DATETIME(fsp=6), server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))


class WkMsg(Base):
    __tablename__ = 'wk_msg'

    id = Column(INTEGER(11), primary_key=True)
    title = Column(VARCHAR(255), nullable=False, comment='标题')
    content = Column(TEXT, nullable=False, comment='消息内容')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    user_id = Column(INTEGER(11), nullable=False, index=True, comment='用户 id')
    status = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='阅读状态 0: 未读 1: 已读')


class WkPower(Base):
    __tablename__ = 'wk_power'

    id = Column(INTEGER(11), primary_key=True)
    type = Column(INTEGER(11), nullable=False, comment='权限类型『引用数据字典』')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkReal(Base):
    __tablename__ = 'wk_real'

    id = Column(INTEGER(11), primary_key=True)
    trade_id = Column(INTEGER(11), nullable=False, comment='证券账户 id')
    backtest_id = Column(INTEGER(11), nullable=False, comment='回测 id')
    name = Column(VARCHAR(255), nullable=False, comment='模拟自定义名称')
    init_money = Column(Float(16, True), comment='初始资金')
    frequency = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    start_date = Column(Date, comment='实盘开始时间')
    stat = Column(INTEGER(1), nullable=False, server_default=text("'4'"), comment='状态 1: 进行，2: 待开启，3: 停止，4: 审核中，5: 未通过')
    run_stat = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='策略运行状态')
    task_id = Column(VARCHAR(32), comment='任务 id: 用来获取 mongdb 中各种数据')
    check_stat = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='人工审核状态 0 未审核 1 已通过 2 拒绝')
    aq_stat = Column(INTEGER(1), server_default=text("'0'"), comment='是否量化家策略 0: 不是量化家策略 1: 是量化家策略')
    aq_end_date = Column(Date, comment='量化策略结束时间')
    update_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    create_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    check_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='实盘审核时间')
    info_auto = Column(VARCHAR(255), comment='审核不通过的原因')
    info_opera = Column(VARCHAR(255), comment='手动审核不通过的原因')
    opera_status = Column(INTEGER(1), server_default=text("'1'"), comment='1: 自动 2: 人工')
    user_id = Column(INTEGER(11), nullable=False, comment='用户的 id')
    type = Column(INTEGER(11), server_default=text("'1'"), comment='1: 股票、\n2: 期货')
    futures_id = Column(INTEGER(11), comment='wk_futures 期货表的 id 策略来源')
    is_buy = Column(TINYINT(4), server_default=text("'0'"), comment='是否是购买的策略')
    buy_task_id = Column(String(255, 'utf8mb4_general_ci'), server_default=text("''"), comment='如果是购买的策略则为购买的策略模拟 taskid')


class WkRealPwdword(Base):
    __tablename__ = 'wk_real_pwdword'

    id = Column(INTEGER(11), primary_key=True)
    token = Column(VARCHAR(64), nullable=False, comment='标识')
    type = Column(INTEGER(1), nullable=False, comment='1:aq 量化代码 2: 五矿量化映射代码')
    sid = Column(INTEGER(11), comment='type=2 时生效')
    action = Column(INTEGER(1), nullable=False, comment='1: 新建 2: 续费')
    remain_times = Column(INTEGER(4), nullable=False, server_default=text("'1'"), comment='剩余次数')


class WkRole(Base):
    __tablename__ = 'wk_role'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(64), nullable=False, unique=True, comment='角色名称')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkRolePower(Base):
    __tablename__ = 'wk_role_power'

    id = Column(INTEGER(11), primary_key=True)
    role_id = Column(INTEGER(11), nullable=False, comment='角色 id')
    power = Column(INTEGER(11), nullable=False, comment='权限 id')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkSimpleImg(Base):
    __tablename__ = 'wk_simple_img'

    id = Column(INTEGER(11), primary_key=True)
    img_href = Column(VARCHAR(255), comment='图片地址')
    img_title = Column(VARCHAR(255), comment='图片标题')
    img_jump = Column(VARCHAR(255), comment='跳转地址')
    img_desc = Column(VARCHAR(255), comment='图片简述')
    dic_img_type = Column(INTEGER(11), comment='数据字典的图片类型 参考：wk_dic 表')
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    order = Column(INTEGER(11), comment='排序')
    content = Column(LONGTEXT, comment='内容')


class WkSimpleTitle(Base):
    __tablename__ = 'wk_simple_title'

    id = Column(INTEGER(11), primary_key=True)
    title_img = Column(VARCHAR(255), comment='标题图')
    title = Column(VARCHAR(255), comment='标题')
    content = Column(TEXT, comment='内容')
    dic_title_type = Column(INTEGER(11), comment='类型、\n 参考 dic')
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkSimulation(Base):
    __tablename__ = 'wk_simulation'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    backtest_id = Column(INTEGER(11), nullable=False, comment='回测 id')
    name = Column(VARCHAR(255), nullable=False, comment='模拟自定义名称')
    init_money = Column(Float(16, True), nullable=False, comment='初始资金')
    frequency = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    start_date = Column(Date, nullable=False, comment='模拟开始时间')
    stat = Column(INTEGER(1), nullable=False, server_default=text("'2'"), comment='模拟运行状态 1: 运行中，2: 关闭')
    run_stat = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='策略运行状态')
    task_id = Column(VARCHAR(32), comment='任务 id: 用来获取 mongdb 中各种数据')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    is_on = Column(TINYINT(4), server_default=text("'0'"), comment='是否是上架的策略')
    is_buy = Column(TINYINT(4), server_default=text("'0'"), comment='是否是购买的策略')
    market_id = Column(INTEGER(11), server_default=text("'0'"), comment='如果是购买的策略则为策略超市的策略 id')
    buy_task_id = Column(String(255, 'utf8mb4_general_ci'), server_default=text("''"), comment='如果是购买的策略则为购买的模拟交易 task_id')


class WkStrategy(Base):
    __tablename__ = 'wk_strategy'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(255), nullable=False, comment='自定义名称')
    user_id = Column(INTEGER(11), nullable=False, comment='用户的 id')
    code = Column(TEXT, comment='策略代码')
    init_money = Column(Float(16, True), server_default=text("'100000.00'"), comment='初始资金')
    frequency = Column(INTEGER(1), server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    start_date = Column(Date, server_default=text("'2018-06-06'"), comment='开始日期')
    end_date = Column(Date, server_default=text("'2018-08-08'"), comment='结束日期')
    update_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    create_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    status = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='0: 正常，1: 删除')


class WkStrategyBacktest(Base):
    __tablename__ = 'wk_strategy_backtest'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    strategy_id = Column(INTEGER(11), comment='策略 id')
    name = Column(VARCHAR(64), nullable=False, comment='回测的名称')
    code = Column(TEXT, nullable=False, comment='回测代码')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    init_money = Column(Float(16, True), comment='初始资金')
    frequency = Column(INTEGER(1), server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    task_id = Column(VARCHAR(32), comment='任务 id: 用来获取 mongdb 中各种数据')
    update_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    run_stat = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='策略运行状态')
    run_begin = Column(INTEGER(16), comment='运行开始时间戳（秒）')
    run_end = Column(INTEGER(16), comment='运行结束时间戳（秒）')


class WkStrategyCompile(Base):
    __tablename__ = 'wk_strategy_compile'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    strategy_id = Column(INTEGER(11), nullable=False, comment='策略 id')
    name = Column(VARCHAR(64), nullable=False, comment='编译名称')
    code = Column(TEXT, comment='编译的代码')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    init_money = Column(Float(16, True), comment='初始资金')
    frequency = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='创建时间')
    task_id = Column(VARCHAR(64), comment='任务 id')
    update_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    run_stat = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='运行状态')
    run_begin = Column(INTEGER(16), comment='运行开始时间戳（秒）')
    run_end = Column(INTEGER(16), comment='运行结束时间戳（秒）')


class WkSysMsg(Base):
    __tablename__ = 'wk_sys_msg'

    id = Column(INTEGER(11), primary_key=True)
    publish_status = Column(INTEGER(1), server_default=text("'0'"), comment='下架和发布、\r\\n0: 未发布、\r\\n1: 已发布')
    title = Column(VARCHAR(255), nullable=False)
    content = Column(TEXT, nullable=False, comment='内容')
    read_times = Column(INTEGER(11), server_default=text("'0'"), comment='阅读次数')
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    send_all = Column(INTEGER(1), comment='是否发送给全部 1: 全部')
    send_time = Column(DateTime, comment='发送时间')


class WkSysParam(Base):
    __tablename__ = 'wk_sys_param'
    __table_args__ = (
        Index('wk_dic_key_value_uindex', 'key', 'value', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    key = Column(VARCHAR(64), nullable=False, comment='索引（英文）\\neg:\\nsex,bank_card_type...')
    key_desc = Column(VARCHAR(64), nullable=False, comment='索引的中文描述、\neg: key=sex\\n 性别')
    value = Column(VARCHAR(64), nullable=False, comment='索引值（为保证唯一需要加上 key 前缀）\\neg: key=sex\\nsex-girl,sex-boy')
    value_desc = Column(VARCHAR(64), nullable=False, comment='索引值表述、\neg;value=sex-boy\\n 男')
    security_level = Column(INTEGER(11), nullable=False, server_default=text("'5'"), comment='安全级别，防止管理误删')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkSysStrategy(Base):
    __tablename__ = 'wk_sys_strategy'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(255), nullable=False, comment='自定义名称')
    code = Column(TEXT, nullable=False, comment='策略代码')
    original_name = Column(VARCHAR(255), nullable=False, server_default=text("''"), comment='量化家策略原始名称')
    suit_money = Column(Float(10, True), comment='适合资金')
    pub_status = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='上架状态 0: 未上架 1: 已上架')
    pub_time = Column(DateTime, comment='上架时间')
    show_status = Column(INTEGER(1), server_default=text("'0'"), comment='展示状态 0: 未展示 1: 展示到首页')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), nullable=False, comment='创建的 id')
    update_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')


class WkSysStrategyBacktest(Base):
    __tablename__ = 'wk_sys_strategy_backtest'

    id = Column(INTEGER(11), primary_key=True)
    strategy_id = Column(INTEGER(11), nullable=False, comment='策略 id')
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, nullable=False, comment='结束日期')
    init_money = Column(Float(16, True), nullable=False, comment='初始资金')
    frequency = Column(INTEGER(1), nullable=False, server_default=text("'1'"), comment='回测频率 1: 日频 2: 分频')
    task_id = Column(VARCHAR(32), comment='任务 id: 用来获取 mongdb 中各种数据')
    update_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    create_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')


class WkTradeAccount(Base):
    __tablename__ = 'wk_trade_account'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    real_name = Column(VARCHAR(255), nullable=False, comment='真实姓名')
    account_type = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='账户类型')
    account_num = Column(VARCHAR(64), nullable=False, comment='证券账号')
    account_pas = Column(VARCHAR(64), nullable=False, comment='证券交易密码')
    check_status = Column(INTEGER(1), nullable=False, server_default=text("'0'"), comment='审核状态、\n0: 未审核 1: 已审核 -1: 取消审核')
    permission = Column(INTEGER(2), server_default=text("'0'"), comment='0-15 二进制规律 |沪 深。创。科|->|0 1 1 0| ')
    bind = Column(INTEGER(1), server_default=text("'0'"), comment='绑定状态 0: 未绑定 1: 已绑定')
    check_time = Column(DateTime, comment='认证时间')
    broker_id = Column(INTEGER(11))
    total = Column(Float(16, True), comment='最近一次查询的总资产')
    cash = Column(Float(16, True), comment='最近一次查询的可用资金')


class WkTradeDay(Base):
    __tablename__ = 'wk_trade_days'

    id = Column(INTEGER(10), primary_key=True)
    cal_date = Column(VARCHAR(8), nullable=False, unique=True)
    is_open = Column(TINYINT(1), nullable=False)


class WkTradeStat(Base):
    __tablename__ = 'wk_trade_stat'
    __table_args__ = (
        Index('wk_trade_stat_trade_id_date_uindex', 'trade_id', 'date', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    trade_id = Column(INTEGER(11), nullable=False, comment='交易账户的 id')
    total = Column(Float(16, True), server_default=text("'0.0000'"), comment='总资产')
    cash = Column(Float(16, True), nullable=False, server_default=text("'0.0000'"), comment='可用资金')
    date = Column(Date, nullable=False, comment='统计日期')
    bal = Column(Float(16, True), server_default=text("'0.0000'"), comment='资金余额')
    fund = Column(Float(16, True), server_default=text("'0.0000'"), comment='资金资产')


class WkUser(Base):
    __tablename__ = 'wk_user'

    id = Column(INTEGER(11), primary_key=True, comment='主键')
    phone = Column(VARCHAR(64), nullable=False, unique=True, comment='手机号')
    summary = Column(VARCHAR(255), server_default=text("''"), comment='个人简介')
    nick_name = Column(VARCHAR(64), comment='昵称')
    password = Column(VARCHAR(64), nullable=False, comment='密码')
    real_name = Column(VARCHAR(64), comment='真实姓名')
    head_img = Column(LONGTEXT, comment='头像地址链接')
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建的时间')
    create_by = Column(INTEGER(11), comment='创建的 id')
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='最近修改时间')
    update_by = Column(INTEGER(11), comment='修改人 id')
    recently_login = Column(DateTime, comment='最近登录时间')
    ip = Column(VARCHAR(16), comment='ip 地址')
    mac = Column(VARCHAR(64), comment='mac 地址')
    hddr = Column(VARCHAR(64), comment='硬盘序列号')
    cpu_id = Column(VARCHAR(64), comment='CPU id')


class WkUserOrder(Base):
    __tablename__ = 'wk_user_order'

    id = Column(INTEGER(11), primary_key=True)
    order_no = Column(VARCHAR(32), nullable=False, index=True, server_default=text("''"), comment='订单 id')
    user_id = Column(INTEGER(11), nullable=False, index=True, server_default=text("'0'"), comment='用户 id')
    status = Column(TINYINT(4), server_default=text("'0'"), comment='订单状态，1= 待支付，2= 支付成功，3= 支付失败，4= 取消支付 / 超时')
    item_id = Column(INTEGER(11), index=True, server_default=text("'0'"), comment='商品 id')
    trade_no = Column(VARCHAR(48), server_default=text("''"), comment='支付平台订单号')
    out_trade_no = Column(VARCHAR(32), server_default=text("''"), comment='外部订单号')
    amount = Column(Float(11, True), server_default=text("'0'"), comment='金额')
    pay_amount = Column(Float(11, True), server_default=text("'0'"), comment='支付金额')
    order_type = Column(TINYINT(4), server_default=text("'0'"), comment='订单类型')
    days = Column(INTEGER(11), server_default=text("'0'"), comment='购买期限')
    pay_time = Column(DATETIME(fsp=6), comment='支付时间')
    expire_time = Column(DATETIME(fsp=6), comment='过期时间')
    create_time = Column(DATETIME(fsp=6), index=True, server_default=text("CURRENT_TIMESTAMP(6)"))
    update_time = Column(DATETIME(fsp=6), server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    desc = Column(VARCHAR(255), server_default=text("''"), comment='描述')
    account = Column(VARCHAR(50), server_default=text("''"))
    user_name = Column(VARCHAR(50), server_default=text("''"))


class WkUserStrategyOrder(Base):
    __tablename__ = 'wk_user_strategy_order'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='用户 id')
    sim_id = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='模拟 id')
    strategy_market_id = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='策略超市 id')
    task_id = Column(VARCHAR(32), nullable=False, server_default=text("''"))
    name = Column(VARCHAR(30), server_default=text("''"))
    remarks = Column(VARCHAR(20), server_default=text("''"), comment='备注')
    strategy_type = Column(TINYINT(4), server_default=text("'0'"), comment='策略类型')
    transfer_notify = Column(TINYINT(3), server_default=text("'0'"), comment='调仓通知')
    token = Column(VARCHAR(32), server_default=text("''"), comment='口令')
    order_time = Column(DATETIME(fsp=6), comment='购买时间')
    expire_time = Column(DATETIME(fsp=6), comment='到期时间')
    create_time = Column(DATETIME(fsp=6), index=True, server_default=text("CURRENT_TIMESTAMP(6)"))
    update_time = Column(DATETIME(fsp=6), server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    order_no = Column(VARCHAR(32), index=True, server_default=text("''"), comment='订单号')


class WkUserSysMsg(Base):
    __tablename__ = 'wk_user_sys_msg'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(INTEGER(11), nullable=False, comment='用户 id')
    sys_msg_id = Column(INTEGER(11), nullable=False, comment='系统消息 id')
    status = Column(INTEGER(11), server_default=text("'0'"), comment='阅读状态、\n0: 未读 1: 已读')
