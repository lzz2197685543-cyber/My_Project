# routers/favorite.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_database
from models.users import User
from utils.auth import get_current_user
from crud.favorite import (
    is_news_favorite,
    add_news_favorite,
    remove_news_favorite,
    get_favorites_list,
    clear_all_favorite
)
from utils.response import success_response
from schemas.favorite import (
    FavoriteCheckResponse,
    FavoriteAddRequest,
    FavoriteListResponse
)

# 创建 APIRouter 实例
router = APIRouter(prefix="/api/favorite", tags=["favorite"])

# ============================================================
# 收藏模块 - 路由层
# ============================================================

"""
功能说明：
1. 检查收藏状态 - 判断用户是否已收藏某篇新闻
2. 添加收藏 - 用户收藏新闻
3. 取消收藏 - 用户取消收藏新闻
4. 收藏列表 - 获取用户的所有收藏（分页）
5. 清空收藏 - 一键清空所有收藏

权限要求：
    所有接口都需要用户登录认证（依赖 get_current_user）
"""


# ------------------------------------------------------------
# 1. 检查收藏状态
# ------------------------------------------------------------
@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId", description="新闻ID"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    检查当前用户是否收藏了指定新闻

    处理流程：
    1. 验证用户登录状态（通过依赖注入）
    2. 在收藏表中查询是否存在该用户的该新闻记录
    3. 返回布尔值结果

    Args:
        news_id: 新闻 ID（前端传参为 newsId）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：
        - isFavorite: 是否已收藏（True/False）
    """
    # 查询收藏状态
    is_favorite = await is_news_favorite(db, user.id, news_id)

    # 组装响应数据
    data = FavoriteCheckResponse(isFavorite=is_favorite)
    return success_response(message='检查收藏状态成功', data=data)


# ------------------------------------------------------------
# 2. 添加收藏
# ------------------------------------------------------------
@router.post("/add")
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    添加新闻收藏

    处理流程：
    1. 验证用户登录状态（通过依赖注入）
    2. 验证新闻是否存在
    3. 检查是否已收藏（防止重复收藏）
    4. 创建收藏记录

    注意：
    - 重复收藏会自动忽略（不会报错）
    - 收藏成功后，前端应更新 UI 状态

    Args:
        data: 收藏请求数据（包含 news_id）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：添加收藏成功消息
    """
    result = await add_news_favorite(db, user.id, data.news_id)
    # result 包含收藏记录详情
    return success_response(message='添加收藏成功', data=result)


# ------------------------------------------------------------
# 3. 取消收藏
# ------------------------------------------------------------
@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias="newsId", description="新闻ID"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    取消新闻收藏

    处理流程：
    1. 验证用户登录状态（通过依赖注入）
    2. 在收藏表中删除该用户的该新闻记录
    3. 检查是否删除成功

    Args:
        news_id: 新闻 ID（前端传参为 newsId）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：取消收藏成功消息

    Raises:
        HTTPException 404: 收藏记录不存在时抛出
    """
    result = await remove_news_favorite(db, user.id, news_id)

    # 检查是否删除成功
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='收藏记录不存在'
        )

    return success_response(message='取消收藏成功')


# ------------------------------------------------------------
# 4. 获取收藏列表
# ------------------------------------------------------------
@router.get("/list")
async def get_favorite_list(
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(
            default=10,
            ge=1,
            le=100,
            alias="pageSize",
            description="每页数量，最大100"
        ),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    获取用户收藏列表（分页）

    功能：
    1. 获取当前用户的所有收藏
    2. 支持分页查询
    3. 返回总数和是否还有更多数据

    处理流程：
    1. 验证用户登录状态（通过依赖注入）
    2. 查询收藏列表（连表查询：收藏表 + 新闻表）
    3. 组装数据（包含新闻信息和收藏时间）
    4. 计算是否还有更多数据

    返回数据说明：
    - list: 收藏列表（包含新闻详情 + 收藏时间 + 收藏ID）
    - total: 总收藏数
    - hasMore: 是否还有更多数据

    Args:
        page: 页码（从1开始）
        page_size: 每页数量（默认10，最大100）
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：收藏列表数据
    """
    # 1. 获取收藏列表和总数
    rows, total = await get_favorites_list(db, user.id, page, page_size)

    # 2. 组装收藏列表数据
    # rows 格式: [(news, favorite_time, favorite_id), ...]
    favorite_list = [
        {
            **news.__dict__,  # 解包新闻对象的所有属性
            'favorite_time': favorite_time,  # 添加收藏时间
            'favorite_id': favorite_id  # 添加收藏记录ID
        }
        for news, favorite_time, favorite_id in rows
    ]

    # 3. 判断是否还有更多数据
    has_more = total > page * page_size

    # 4. 组装响应数据
    data = FavoriteListResponse(
        list=favorite_list,
        total=total,
        has_more=has_more
    )

    return success_response(message='获取收藏列表成功', data=data)


# ------------------------------------------------------------
# 5. 清空所有收藏
# ------------------------------------------------------------
@router.delete("/clear")
async def remove_all_favorite(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    清空用户所有收藏

    处理流程：
    1. 验证用户登录状态（通过依赖注入）
    2. 删除该用户的所有收藏记录
    3. 返回删除的记录数

    注意：
    - 此操作不可逆，建议前端添加二次确认
    - 删除所有收藏后，前端应刷新列表

    Args:
        user: 当前登录用户（依赖注入）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：包含删除的记录数
    """
    # 清空所有收藏
    total = await clear_all_favorite(db, user.id)

    return success_response(
        message=f'清空了{total}条收藏记录',
        data={'deleted_count': total}
    )


# ============================================================
# 扩展接口（预留）
# ============================================================

"""
后续可扩展的接口：
- 批量取消收藏：DELETE /api/favorite/batch-remove?ids=1,2,3
- 收藏统计：GET /api/favorite/stats
- 收藏分类统计：GET /api/favorite/category-stats
- 收藏新闻搜索：GET /api/favorite/search?keyword=xxx
- 收藏新闻排序：GET /api/favorite/list?sort=time/views
"""