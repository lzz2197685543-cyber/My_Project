from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool=Field(..., alias='isFavorite')

class FavoriteAddRequest(BaseModel):
    news_id: int=Field(..., alias='newsId')


# 规划两个类：一个是新闻类 + 收藏的模型类
class FavoriteNewsItemResponse(NewItemBase):
    favorite_id: int=Field(..., alias='favoriteId')
    favorite_time: datetime=Field(..., alias='favoriteTime')

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class FavoriteListResponse(BaseModel):
    list:list[FavoriteNewsItemResponse]
    total: int
    has_more: bool=Field(..., alias='hasMore')

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )