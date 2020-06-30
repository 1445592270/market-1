import logging

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from market.models import Tag, db
from market.schemas.base import CommonOut
from market.schemas.tag import TagBatDel, TagCreate, TagSearch, TagSearchOut, TagUpdate

logger = logging.getLogger(__name__)


async def add_tag(schema_in: TagCreate):
    """添加标签或者风格"""
    name_list = schema_in.name
    if isinstance(name_list, str):
        name_list = [name_list]

    for tag_name in name_list:
        try:
            await Tag.create(name=tag_name, tag_type=int(schema_in.tag_type))
        except IntegrityError:
            raise HTTPException(status_code=400, detail="创建标签 / 风格失败，请检查名字是否重复")
        except Exception:
            logger.exception("create tag failed: %s", schema_in.json())
            raise HTTPException(status_code=400, detail="数据库错误")

    return CommonOut()


async def edit_tag(schema_in: TagUpdate):
    """编辑标签或者风格的名字"""
    try:
        await Tag.update.values(name=schema_in.name).where(
            Tag.id == schema_in.id
        ).gino.status()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="更新标签 / 风格失败，请检查名字是否重复")
    except Exception:
        logger.exception("create tag failed: %s", schema_in.json())
        raise HTTPException(status_code=400, detail="数据库错误")
    return CommonOut()


async def del_tag(schema_in: TagBatDel):
    """删除标签或风格，可传单个 id 或者 id 列表"""
    id_list = schema_in.id
    if isinstance(id_list, int):
        id_list = [id_list]
    await Tag.update.values(deleted=True).where(Tag.id.in_(id_list)).gino.status()
    return CommonOut()


async def search_tag(schema_in: TagSearch):
    """根据名字和类型查询标签或者风格"""
    count_query = db.select([db.func.count(Tag.id)]).where(Tag.deleted == False)
    fetch_query = Tag.query.where(Tag.deleted == False)

    if schema_in.tag_type:
        count_query = count_query.where(Tag.tag_type == int(schema_in.tag_type))
        fetch_query = fetch_query.where(Tag.tag_type == int(schema_in.tag_type))
    if schema_in.name:
        count_query = count_query.where(Tag.name.contains(schema_in.name))
        fetch_query = fetch_query.where(Tag.name.contains(schema_in.name))
    elif schema_in.fuzzy:
        count_query = count_query.where(Tag.name.contains(schema_in.fuzzy))
        fetch_query = fetch_query.where(Tag.name.contains(schema_in.fuzzy))
    total_count = await db.scalar(count_query)
    order_bys = []
    for key in schema_in.order_bys:
        if not key.startswith("-"):
            if not hasattr(Tag, key):
                logger.warning("get tag has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(Tag, key))
        else:
            if not hasattr(Tag, key[1:]):
                logger.warning("get tag has invalid order_by key: %s", key)
                continue
            order_bys.append(getattr(Tag, key[1:]).desc())

    tags = (
        await fetch_query.order_by(*order_bys)
        .offset(schema_in.offset)
        .limit(schema_in.count)
        .gino.all()
    )
    return TagSearchOut(total=total_count, data=tags)


async def show_tag(tag_id: int):
    """查看标签或者风格"""
    return await Tag.get_or_404(tag_id)
