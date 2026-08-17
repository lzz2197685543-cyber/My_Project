# routers/news.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud import news

# 创建 APIRouter 实例
router = APIRouter(prefix="/api/news", tags=["news"])

# ============================================================
# 新闻模块 - 路由层
# ============================================================

"""
接口开发流程：
1. 模块化路由 → 定义 API 接口规范
2. 定义模型类 → 创建数据库表（数据库设计文档）
3. 在 crud 层封装数据库操作方法
4. 在路由处理函数中调用 crud 方法，返回响应结果

跨域资源共享（CORS）说明：
    CORS 是一种浏览器安全机制，允许 Web 应用向不同源的服务器发起跨域 HTTP 请求。

    同源策略的三个条件：
    - 协议相同（http/https）
    - 域名相同
    - 端口相同

    CORS 中间件作用：
    后端通过设置响应头，主动告知浏览器允许哪些前端源访问。
"""


# ------------------------------------------------------------
# 1. 获取新闻分类列表
# ------------------------------------------------------------
@router.get("/categories")
async def get_categories(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_database)
):
    """
    获取所有新闻分类

    功能：获取系统中所有的新闻分类，支持分页

    Args:
        skip: 跳过的记录数（分页偏移量），默认 0
        limit: 返回的最大记录数，默认 100
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：
        - code: 状态码
        - message: 提示信息
        - data: 分类列表
    """
    categories = await news.get_categories(db, skip, limit)

    return {
        "code": 200,
        "message": "success",
        "data": categories
    }


# ------------------------------------------------------------
# 2. 获取新闻列表（分页）
# ------------------------------------------------------------
@router.get("/list")
async def get_news_list(
        category_id: int = Query(..., alias="categoryId", description="分类ID"),
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(
            default=10,
            alias="pageSize",
            le=100,
            description="每页数量，最大100"
        ),
        db: AsyncSession = Depends(get_database)
):
    """
    获取指定分类的新闻列表（分页）

    功能：
    1. 根据分类 ID 获取新闻列表
    2. 支持分页查询
    3. 返回总数和是否还有更多数据

    分页参数说明：
    - page: 页码（从1开始）
    - page_size: 每页数量（默认10，最大100）
    - categoryId: 分类ID（必填）

    响应数据结构：
    - list: 当前页的新闻列表
    - total: 该分类的新闻总数
    - hasMore: 是否还有更多数据

    Args:
        category_id: 分类 ID（从查询参数获取）
        page: 页码
        page_size: 每页数量
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：包含新闻列表、总数和是否有更多数据
    """
    # 1. 计算分页偏移量
    skip = (page - 1) * page_size

    # 2. 获取新闻列表
    news_list = await news.get_news_list(db, category_id, skip, page_size)

    # 3. 获取新闻总数
    total = await news.get_news_count(db, category_id)

    # 4. 判断是否还有更多数据
    # 判断逻辑：(已跳过的 + 当前页数量) < 总数 → 还有更多
    has_more = (skip + len(news_list)) < total

    return {
        "code": 200,
        "message": "success",
        "data": {
            'list': news_list,
            'total': total,
            'hasMore': has_more
        }
    }


# ------------------------------------------------------------
# 3. 获取新闻详情
# ------------------------------------------------------------
@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(..., alias="id", description="新闻ID"),
        db: AsyncSession = Depends(get_database)
):
    """
    获取新闻详情

    功能：
    1. 获取新闻详细信息
    2. 自动增加浏览量（+1）
    3. 获取相关新闻推荐（同分类，最多5条）

    处理流程：
    1. 查询新闻详情
    2. 新闻存在 → 浏览量 +1（原子操作）
    3. 获取相关新闻推荐（同分类、排除自身、按热度排序）
    4. 组合返回完整数据

    相关新闻推荐策略：
    - 同分类下的其他新闻
    - 按浏览量降序（热门优先）
    - 按发布时间降序（最新优先）
    - 最多返回 5 条

    Args:
        news_id: 新闻 ID（从查询参数获取，前端传 id）
        db: 异步数据库会话（依赖注入）

    Returns:
        JSON 响应：包含新闻详情和相关推荐

    Raises:
        HTTPException 404: 新闻不存在时抛出
    """
    # 1. 获取新闻详情
    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail='新闻不存在')

    # 2. 增加浏览量（原子操作）
    view_result = await news.increase_news_views(db, news_detail.id)
    if not view_result:
        raise HTTPException(status_code=404, detail='新闻不存在')

    # 3. 获取相关新闻推荐
    related_news = await news.get_related_news(
        db,
        category_id=news_detail.category_id,
        news_id=news_detail.id
    )

    # 4. 组装响应数据
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,  # 驼峰命名
            "categoryId": news_detail.category_id,  # 驼峰命名
            "views": news_detail.views,
            "relatedNews": related_news
        }
    }


# ============================================================
# 扩展接口（预留）
# ============================================================

"""
后续可扩展的接口：
- 搜索新闻：GET /api/news/search?keyword=xxx
- 获取热门新闻：GET /api/news/hot
- 获取最新新闻：GET /api/news/latest
- 新闻收藏/点赞：POST /api/news/{id}/favorite
- 获取新闻评论：GET /api/news/{id}/comments
"""