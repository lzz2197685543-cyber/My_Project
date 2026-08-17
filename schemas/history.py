from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewItemBase


class HistoryAddRequest(BaseModel):
    news_id: int=Field(..., alias='newsId')


class HistoryNewsItemResponse(NewItemBase):
    view_time: datetime = Field(..., alias='viewTime')  # 改为 view_time
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class HistoryListResponse(BaseModel):
    list:list[HistoryNewsItemResponse]
    total:int
    has_more:bool=Field(..., alias='hasMore')
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )