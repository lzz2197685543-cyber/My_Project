# crud/favorite.py
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


# ============================================================
# 数据库操作层 - 收藏相关 CRUD
# ============================================================

# ------------------------------------------------------------
# 1. 查询操作
# ------------------------------------------------------------

async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
) -> bool:
    """
    检查用户是否收藏了指定新闻

    功能：判断用户是否已收藏某篇新闻，用于前端展示收藏状态

    处理流程：
    1. 查询收藏表，匹配 user_id 和 news_id
    2. 如果存在记录则返回 True，否则返回 False

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        news_id: 新闻 ID

    Returns:
        bool: 已收藏返回 True，未收藏返回 False
    """
    # 查询收藏记录
    query = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(query)
    favorite = result.scalar_one_or_none()

    # 存在记录表示已收藏
    return favorite is not None


# ------------------------------------------------------------
# 2. 创建操作
# ------------------------------------------------------------

async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    """
    添加新闻收藏

    处理流程：
    1. 创建收藏记录（user_id + news_id）
    2. 保存到数据库
    3. 刷新对象以获取自动生成的字段（如 id、created_at）

    注意：
    - 调用前应检查是否已收藏，避免重复收藏
    - 收藏时间由数据库自动生成（通过模型默认值）

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        news_id: 新闻 ID

    Returns:
        Favorite: 创建的收藏记录对象（包含 ID 和创建时间）
    """
    # 创建收藏记录
    favorite = Favorite(user_id=user_id, news_id=news_id)

    # 保存到数据库
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)  # 刷新以获取数据库生成的字段

    return favorite


# ------------------------------------------------------------
# 3. 删除操作
# ------------------------------------------------------------

async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
) -> bool:
    """
    取消新闻收藏（删除单条收藏记录）

    处理流程：
    1. 先查询用户对该新闻的收藏记录
    2. 如果存在则删除，返回 True
    3. 如果不存在则返回 False

    注意：
    - 采用"先查询再删除"策略，确保删除的是正确记录
    - 返回布尔值方便上层判断操作是否成功

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        news_id: 新闻 ID

    Returns:
        bool: 删除成功返回 True，记录不存在返回 False
    """
    # 1. 查询要删除的收藏记录
    query = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(query)
    favorite = result.scalar_one_or_none()

    # 2. 如果记录存在，执行删除
    if favorite:
        await db.delete(favorite)
        await db.commit()
        return True

    return False


async def clear_all_favorite(
        db: AsyncSession,
        user_id: int,
) -> int:
    """
    清空用户所有收藏

    处理流程：
    1. 使用批量删除语句删除该用户的所有收藏记录
    2. 提交事务
    3. 返回删除的记录数

    注意：
    - 使用批量删除（一条 SQL 语句），性能优于逐条删除
    - 此操作不可逆，建议前端添加二次确认

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        int: 实际删除的记录数（如果没有记录则返回 0）
    """
    # 批量删除用户所有收藏
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    # 返回删除的行数（如果没有删除任何记录，返回 0）
    return result.rowcount or 0


# ------------------------------------------------------------
# 4. 列表查询（分页）
# ------------------------------------------------------------

async def get_favorites_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
):
    """
    获取用户收藏列表（分页）

    功能：
    1. 统计用户总收藏数
    2. 获取指定页码的收藏列表
    3. 连表查询收藏表 + 新闻表，获取完整新闻信息

    数据组装说明：
    - 使用 JOIN 查询，一次查询获取所有需要的数据
    - 返回：新闻对象 + 收藏时间 + 收藏记录ID
    - 按收藏时间降序排列（最新的在前）

    查询结果格式：
        rows: [(News, favorite_time, favorite_id), ...]
        total: 总收藏数

    性能优化：
    - 使用 JOIN 避免 N+1 查询问题
    - 分页查询避免一次加载大量数据

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        page: 页码（从1开始），默认 1
        page_size: 每页数量，默认 10

    Returns:
        tuple: (rows, total)
            - rows: 收藏列表（包含新闻信息和收藏元数据）
            - total: 总收藏数
    """
    # 1. 查询总收藏数
    count_query = select(func.count(Favorite)).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 2. 获取收藏列表（连表查询 + 分页）
    skip = (page - 1) * page_size

    stmt = (
        select(
            News,  # 新闻对象（所有字段）
            Favorite.created_at.label("favorite_time"),  # 收藏时间（别名）
            Favorite.id.label("favorite_id"),  # 收藏记录ID（别名）
        )
        .join(Favorite, Favorite.news_id == News.id)  # 连表查询
        .where(Favorite.user_id == user_id)  # 筛选当前用户
        .order_by(Favorite.created_at.desc())  # 按收藏时间降序（最新优先）
        .offset(skip)  # 分页偏移量
        .limit(page_size)  # 每页数量
    )

    result = await db.execute(stmt)
    rows = result.all()

    return rows, total


# ============================================================
# 扩展功能（预留）
# ============================================================

"""
后续可扩展的 CRUD 方法：
- 批量取消收藏：删除多个收藏记录
- 检查批量收藏状态：一次性检查多篇新闻的收藏状态
- 获取收藏统计：按分类统计收藏数量
- 搜索收藏：在收藏列表中搜索新闻
- 收藏排序：按新闻发布时间、浏览量等排序
"""

# 示例：批量检查收藏状态（后续可扩展）
# async def batch_check_favorite(db: AsyncSession, user_id: int, news_ids: List[int]) -> Dict[int, bool]:
#     """
#     批量检查多篇新闻的收藏状态
#     
#     Args:
#         db: 异步数据库会话
#         user_id: 用户 ID
#         news_ids: 新闻 ID 列表
#         
#     Returns:
#         Dict[int, bool]: {news_id: is_favorite}
#     """
#     query = select(Favorite.news_id).where(
#         Favorite.user_id == user_id,
#         Favorite.news_id.in_(news_ids)
#     )
#     result = await db.execute(query)
#     favorite_news_ids = set(result.scalars().all())
#     return {news_id: news_id in favorite_news_ids for news_id in news_ids}