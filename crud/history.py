# crud/history.py
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News


# ============================================================
# 数据库操作层 - 浏览历史相关 CRUD
# ============================================================

# ------------------------------------------------------------
# 1. 添加/更新浏览历史
# ------------------------------------------------------------

async def add_history(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    """
    添加或更新浏览历史记录

    功能：
    1. 如果用户已浏览过该新闻 → 更新浏览时间（刷新为当前时间）
    2. 如果用户未浏览过该新闻 → 创建新的浏览记录

    处理流程：
    1. 查询是否存在该用户对该新闻的历史记录
    2. 存在 → 更新 view_time 为当前时间
    3. 不存在 → 创建新记录
    4. 处理并发冲突（使用 IntegrityError 回退）

    并发处理说明：
    - 使用 try-except 捕获 IntegrityError（唯一约束冲突）
    - 发生冲突时回滚事务，重新查询并返回已存在的记录
    - 确保在高并发下不会重复创建记录

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        news_id: 新闻 ID

    Returns:
        History: 历史记录对象（更新后或新创建的）
    """
    # 1. 查询是否存在历史记录
    stmt = select(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)
    existing_history = result.scalar_one_or_none()

    if existing_history:
        # 2. 存在 → 更新浏览时间
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history
    else:
        # 3. 不存在 → 创建新记录
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)

        try:
            await db.commit()
            await db.refresh(history)
            return history
        except IntegrityError:
            # 4. 处理并发插入冲突
            # 场景：两个请求同时插入相同的 (user_id, news_id)
            await db.rollback()
            # 重新查询，此时已有其他请求创建了记录
            result = await db.execute(stmt)
            return result.scalar_one()


# ------------------------------------------------------------
# 2. 查询浏览历史列表
# ------------------------------------------------------------

async def get_history(
        db: AsyncSession,
        user_id: int,
        page: int,
        page_size: int,
) -> tuple[int, list]:
    """
    获取用户的浏览历史列表（分页）

    功能：
    1. 统计用户总浏览记录数
    2. 获取指定页码的浏览历史
    3. 连表查询历史表 + 新闻表，获取完整新闻信息

    查询结果说明：
    - 返回新闻对象 + 浏览时间
    - 按浏览时间降序排列（最新的在前）
    - 支持分页查询

    数据组装格式：
        rows: [(News, view_time), ...]
        total: 总记录数

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        tuple[int, list]: (total, rows)
            - total: 总浏览记录数
            - rows: 历史记录列表（包含新闻信息和浏览时间）
    """
    # 1. 查询总记录数
    count_stmt = select(func.count()).select_from(History).where(
        History.user_id == user_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 2. 计算分页偏移量
    offset = (page - 1) * page_size

    # 3. 查询分页数据（连表查询）
    history_stmt = (
        select(
            News,  # 新闻对象（所有字段）
            History.view_time.label("view_time"),  # 浏览时间（别名）
        )
        .join(History, History.news_id == News.id)  # 连表查询
        .where(History.user_id == user_id)  # 筛选当前用户
        .order_by(History.view_time.desc())  # 按浏览时间降序（最新优先）
        .offset(offset)  # 分页偏移量
        .limit(page_size)  # 每页数量
    )

    history_result = await db.execute(history_stmt)
    rows = history_result.all()

    return total, rows


# ------------------------------------------------------------
# 3. 删除单条浏览历史
# ------------------------------------------------------------

async def delete_history(
        db: AsyncSession,
        user_id: int,
        history_id: int,
) -> bool:
    """
    删除单条浏览历史记录

    处理流程：
    1. 查询是否存在该记录（同时验证用户权限）
    2. 存在 → 删除记录，返回 True
    3. 不存在 → 抛出 404 异常

    安全说明：
    - 查询时同时匹配 history_id 和 user_id，确保用户只能删除自己的记录
    - 防止用户删除其他用户的历史记录

    Args:
        db: 异步数据库会话
        user_id: 用户 ID（用于权限验证）
        history_id: 历史记录 ID

    Returns:
        bool: 删除成功返回 True

    Raises:
        HTTPException 404: 记录不存在或无权删除时抛出
    """
    # 1. 查询记录（同时验证用户权限）
    stmt = select(History).where(
        History.id == history_id,
        History.user_id == user_id
    )
    result = await db.execute(stmt)
    existing_history = result.scalar_one_or_none()

    # 2. 记录不存在 → 抛出异常
    if not existing_history:
        raise HTTPException(
            status_code=404,
            detail='历史记录不存在'
        )

    # 3. 删除记录
    await db.delete(existing_history)
    await db.commit()
    return True


# ------------------------------------------------------------
# 4. 清空所有浏览历史
# ------------------------------------------------------------

async def clear_history(
        db: AsyncSession,
        user_id: int,
) -> int:
    """
    清空用户的所有浏览历史

    处理流程：
    1. 使用批量删除语句删除该用户的所有历史记录
    2. 提交事务
    3. 返回删除的记录数

    性能优化：
    - 使用 delete() 批量删除，一条 SQL 语句完成
    - 避免逐条删除带来的性能开销

    注意：
    - 此操作不可逆，建议前端添加二次确认
    - 清空后无法恢复，请谨慎使用

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        int: 实际删除的记录数（如果没有记录则返回 0）
    """
    # 批量删除用户所有历史记录
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount or 0


# ============================================================
# 扩展功能（预留）
# ============================================================

"""
后续可扩展的 CRUD 方法：
- 批量删除历史：删除指定多个历史记录
- 按时间范围删除：删除某段时间内的浏览历史
- 历史记录统计：统计用户浏览最多的分类
- 历史记录搜索：在浏览记录中搜索新闻
- 清除过期历史：自动删除超过30天的历史记录
- 导出历史记录：导出为 CSV 或 JSON 格式
"""

# 示例：按时间范围删除（后续可扩展）
# async def delete_history_by_date_range(
#     db: AsyncSession,
#     user_id: int,
#     start_date: datetime,
#     end_date: datetime
# ) -> int:
#     """
#     删除指定时间范围内的浏览历史
#     
#     Args:
#         db: 异步数据库会话
#         user_id: 用户 ID
#         start_date: 开始时间
#         end_date: 结束时间
#         
#     Returns:
#         int: 删除的记录数
#     """
#     stmt = delete(History).where(
#         History.user_id == user_id,
#         History.view_time.between(start_date, end_date)
#     )
#     result = await db.execute(stmt)
#     await db.commit()
#     return result.rowcount or 0

# 示例：获取用户浏览最多的分类（后续可扩展）
# async def get_most_viewed_categories(
#     db: AsyncSession,
#     user_id: int,
#     limit: int = 5
# ):
#     """
#     获取用户浏览最多的新闻分类
#     
#     Args:
#         db: 异步数据库会话
#         user_id: 用户 ID
#         limit: 返回的分类数量
#         
#     Returns:
#         List[Dict]: 分类浏览统计
#     """
#     stmt = (
#         select(
#             News.category_id,
#             func.count(History.id).label("view_count")
#         )
#         .join(History, History.news_id == News.id)
#         .where(History.user_id == user_id)
#         .group_by(News.category_id)
#         .order_by(func.count(History.id).desc())
#         .limit(limit)
#     )
#     result = await db.execute(stmt)
#     return result.all()