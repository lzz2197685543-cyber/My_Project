# routers/history.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from utils.auth import get_current_user
from models.users import User
from schemas.history import HistoryAddRequest, HistoryListResponse
from utils.response import success_response
from crud.history import add_history, get_history, delete_history, clear_history

# 创建 APIRouter 实例
router = APIRouter(prefix="/api/history", tags=["history"])

# ============================================================
# 浏览历史模块 - 路由层
# ============================================================

"""
功能说明：
1. 添加浏览历史 - 用户浏览新闻时记录（存在则更新浏览时间）
2. 获取历史列表 - 获取用户的所有浏览记录（分页）
3. 删除单条历史 - 删除指定的浏览记录
4. 清空所有历史 - 一键清空所有浏览记录

权限要求：
    所有接口都需要用户登录认证（依赖 get_current_user）

业务规则：
    - 浏览相同新闻时，只更新浏览时间，不重复创建记录
    - 历史列表按浏览时间降序排列（最新的在前）
    - 清空操作不可逆，建议前端添加二次确认
"""


# ------------------------------------------------------------
# 1. 添加浏览历史
# ------------------------------------------------------------
@router.post("/add")
async def add_news_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    添加或更新浏览历史

    功能：
    1. 验证用户登录状态（通过依赖注入）
    2. 检查用户是否已浏览过该新闻
    3. 已浏览 → 更新浏览时间为当前时间
    4. 未浏览 → 创建新的浏览记录

    业务场景：
    - 用户点击新闻详情时调用
    - 用于记录用户的阅读足迹
    - 支持个性化推荐和浏览历史展示

    注意：
    - 同一用户浏览同一新闻只保留一条记录
    - 浏览时间会随着每次查看而更新

    Args:
        data: 浏览历史请求数据（包含 news_id）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：添加浏览历史成功消息
    """
    # 添加或更新浏览历史
    result = await add_history(db, user.id, data.news_id)

    return success_response(message='添加浏览历史成功')


# ------------------------------------------------------------
# 2. 获取浏览历史列表
# ------------------------------------------------------------
@router.get("/list")
async def get_history_list(
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(
            default=10,
            ge=1,
            le=100,
            alias='pageSize',
            description="每页数量，最大100"
        ),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    获取用户的浏览历史列表（分页）

    功能：
    1. 获取当前用户的所有浏览记录
    2. 支持分页查询
    3. 连表查询获取完整的新闻信息
    4. 返回总数和是否还有更多数据

    返回数据说明：
    - list: 历史记录列表（包含新闻详情 + 浏览时间）
    - total: 总记录数
    - hasMore: 是否还有更多数据

    排序规则：
    - 按浏览时间降序排列（最新浏览的在前）

    数据组装：
    - 联表查询 History + News 表
    - 一条查询获取所有需要的数据
    - 避免 N+1 查询问题

    Args:
        page: 页码（从1开始），默认 1
        page_size: 每页数量（默认10，最大100）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：浏览历史列表数据
    """
    # 1. 获取浏览历史列表和总数
    total, rows = await get_history(db, user.id, page, page_size)

    # 2. 组装历史列表数据
    # rows 格式: [(news, view_time), ...]
    history_list = [
        {
            **news.__dict__,  # 解包新闻对象的所有属性
            'view_time': view_time  # 添加浏览时间
        }
        for news, view_time in rows
    ]

    # 3. 判断是否还有更多数据
    has_more = total > page * page_size

    # 4. 组装响应数据
    data = HistoryListResponse(
        list=history_list,
        total=total,
        has_more=has_more
    )

    return success_response(message='获取浏览历史成功', data=data)


# ------------------------------------------------------------
# 3. 删除单条浏览历史
# ------------------------------------------------------------
@router.delete("/delete/{history_id}")
async def delete_news_history(
        history_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    删除单条浏览历史记录

    功能：
    1. 验证用户登录状态（通过依赖注入）
    2. 验证该记录是否属于当前用户（权限检查）
    3. 删除指定的历史记录

    使用场景：
    - 用户手动删除某条浏览记录
    - 清理不需要的历史记录

    Args:
        history_id: 历史记录 ID（路径参数）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：删除成功消息

    Raises:
        HTTPException 404: 历史记录不存在或无权删除时抛出
    """
    # 删除历史记录（内部包含权限验证）
    result = await delete_history(db, user.id, history_id)

    # 如果删除失败，抛出 404 异常
    if not result:
        raise HTTPException(
            status_code=404,
            detail='历史记录不存在'
        )

    return success_response(message='删除浏览历史成功')


# ------------------------------------------------------------
# 4. 清空所有浏览历史
# ------------------------------------------------------------
@router.delete("/clear")
async def clear_news_history(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    清空用户的所有浏览历史

    功能：
    1. 验证用户登录状态（通过依赖注入）
    2. 删除该用户的所有浏览记录
    3. 返回删除的记录数

    使用场景：
    - 用户主动清空所有浏览记录
    - 保护隐私或清理空间

    注意事项：
    - 此操作不可逆，建议前端添加二次确认
    - 清空后无法恢复

    Args:
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：包含删除的记录数
    """
    # 清空所有浏览历史
    deleted_count = await clear_history(db, user.id)

    return success_response(
        message=f'清空了{deleted_count}条浏览历史',
        data={'deleted_count': deleted_count}
    )


