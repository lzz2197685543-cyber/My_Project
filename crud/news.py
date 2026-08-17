# crud/news.py
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import Category, News
from schemas.base import NewItemBase
from cache.news_cache import get_cached_categories,set_cache_categories,get_cached_news_list,set_cache_news_list


# ============================================================
# 数据库操作层 - 新闻相关 CRUD
# ============================================================

# ------------------------------------------------------------
# 1. 分类管理
# ------------------------------------------------------------

async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    获取新闻分类列表

    功能：获取所有新闻分类，支持分页查询

    Args:
        db: 异步数据库会话
        skip: 跳过的记录数（分页偏移量），默认 0
        limit: 返回的最大记录数，默认 100

    Returns:
        List[Category]: 分类列表
    """
    # 先尝试从缓存中获取数据
    cached_categories=await get_cached_categories()
    if cached_categories:
        return cached_categories

    stm = select(Category).offset(skip).limit(limit)
    result=await db.execute(stm)
    categories=result.scalars().all()

    # 写入缓存
    if categories:
        cache_categor=jsonable_encoder(categories)
        await set_cache_categories(cache_categor)
    return categories


# ------------------------------------------------------------
# 2. 新闻列表查询
# ------------------------------------------------------------

async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 100):
    """
    获取指定分类的新闻列表（分页）
    """
    # 先尝试从缓存获取新闻列表
    page = skip // limit + 1
    cache_list = await get_cached_news_list(category_id, page, limit)
    if cache_list:
        # 使用 Pydantic 模型将缓存数据转换为 News ORM 对象
        # 1. 先用 NewItemBase 验证数据（缓存数据是驼峰格式）
        # 2. 然后转换为 ORM 模型
        return [
            News(**NewItemBase(**item).model_dump())  # 转换为下划线格式
            for item in cache_list
        ]

    result = await db.execute(
        select(News)
        .where(News.category_id == category_id)
        .offset(skip)
        .limit(limit)
    )
    new_list = result.scalars().all()
    if new_list:
        new_data = [NewItemBase.model_validate(item).model_dump(mode="json", by_alias=True) for item in new_list]
        await set_cache_news_list(category_id, page, limit, new_data, expire=1800)

    return new_list


async def get_news_count(db: AsyncSession, category_id: int):
    """
    获取指定分类的新闻总数

    用途：用于前端分页组件计算总页数

    Args:
        db: 异步数据库会话
        category_id: 分类 ID

    Returns:
        int: 新闻总数
    """
    result = await db.execute(
        select(func.count(News.id))
        .where(News.category_id == category_id)
    )
    return result.scalar_one()  # 使用 scalar_one() 确保结果唯一


# ------------------------------------------------------------
# 3. 新闻详情
# ------------------------------------------------------------

async def get_news_detail(db: AsyncSession, news_id: int):
    """
    获取新闻详情

    Args:
        db: 异步数据库会话
        news_id: 新闻 ID

    Returns:
        News | None: 新闻对象或 None（不存在时）
    """
    result = await db.execute(select(News).where(News.id == news_id))
    return result.scalar_one_or_none()


async def increase_news_views(db: AsyncSession, news_id: int):
    """
    增加新闻浏览量

    处理流程：
    1. 使用数据库原子操作：views = views + 1
    2. 避免并发问题（无需先查询再更新）
    3. 检查是否成功更新

    注意：使用 SQL 级别的原子操作，避免在高并发下出现数据不一致

    Args:
        db: 异步数据库会话
        news_id: 新闻 ID

    Returns:
        bool: 更新成功返回 True，新闻不存在返回 False
    """
    # 原子操作：直接在当前值上 +1
    result = await db.execute(
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    await db.commit()

    # 检查是否真的有数据被更新
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, category_id: int, news_id: int, limit: int = 5):
    """
    获取相关新闻推荐

    推荐策略：
    1. 排除当前新闻（避免推荐自己）
    2. 同分类下的其他新闻
    3. 按浏览量降序排列（热门优先）
    4. 再按发布时间降序排列（最新优先）
    5. 返回指定数量的推荐新闻

    Args:
        db: 异步数据库会话
        category_id: 分类 ID
        news_id: 当前新闻 ID（用于排除）
        limit: 推荐数量，默认 5 条

    Returns:
        List[Dict]: 相关新闻列表，格式化为前端需要的字段
    """
    # 构建查询语句
    stmt = (
        select(News)
        .where(
            News.id != news_id,  # 排除当前新闻
            News.category_id == category_id  # 同分类
        )
        .order_by(
            News.views.desc(),  # 优先级1：浏览量降序
            News.publish_time.desc()  # 优先级2：发布时间降序
        )
        .limit(limit)
    )

    # 执行查询
    result = await db.execute(stmt)
    related_news = result.scalars().all()

    # 格式化为前端需要的结构
    # 注意：这里手动构建字典是为了控制返回字段和命名格式
    return [
        {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "image": news.image,
            "author": news.author,
            "publishTime": news.publish_time,  # 转换为驼峰命名
            "categoryId": news.category_id,  # 转换为驼峰命名
            "views": news.views
        }
        for news in related_news
    ]

# ------------------------------------------------------------
# 4. 综合查询（可选）- 用于首页/聚合场景
# ------------------------------------------------------------

# 如果后续需要，可以在这里添加：
# - async def get_hot_news(): 获取热门新闻
# - async def get_latest_news(): 获取最新新闻
# - async def search_news(): 搜索新闻
# - async def get_news_by_category(): 批量获取多个分类的新闻