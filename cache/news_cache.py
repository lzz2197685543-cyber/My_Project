# 新闻相关的缓存方法：新闻分类的读取和写入
# key-value
from typing import Dict, Any, Optional, List

from config.redis_conf import get_json_cache,set_cache

CATEGORIES_KEY='news:categories'

# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)

# 写如新闻分类缓存:缓存的数据，过期时间
# 分类、配置7200  列表：600   详情：1800  验证码：120  -- 数据越稳定，缓存越持久
async def set_cache_categories(data:list[Dict[str,Any]],expire:int=7200):
    return await set_cache(CATEGORIES_KEY,data,expire)


# 写入缓存-新闻列表  key=news:list:{category_id}:{page}:{size}
async def set_cache_news_list(
        category_id:Optional[int],
        page:int,
        size:int,
        news_list:List[Dict[str,Any]],
        expire:int=1800
):
    category_part=category_id if category_id is not None else 'all'
    LISTS_KEY=f'news:list:{category_part}:{page}:{size}'
    await set_cache(LISTS_KEY,news_list,expire)

# 读取缓存-新闻列表
async def get_cached_news_list(
        category_id:Optional[int],
        page:int,
        size:int,
):
    category_part = category_id if category_id is not None else 'all'
    key=f'news:list:{category_part}:{page}:{size}'
    return await get_json_cache(key)