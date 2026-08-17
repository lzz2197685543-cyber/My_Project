from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import Integer, ForeignKey, TIMESTAMP, UniqueConstraint, Index, DateTime
from datetime import datetime
from models.users import User
from models.news import News
from sqlalchemy.sql import func
from typing import Optional

class BaseModel(DeclarativeBase):
    pass

class Favorite(BaseModel):
    __tablename__ = 'favorite'

    # UniqueConstraint唯一约束，一篇文章只能收藏一次
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),
        Index('i_fk_favorite_user_idx', 'user_id'),
        Index('i_fk_favorite_news_idx', 'news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='收藏id')
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(User.id),
        nullable=False,
        comment='用户id'
    )
    news_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(News.id),
        nullable=False,
        comment='新闻id'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment='收藏时间'
    )

    def __repr__(self):
        return f'<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id})>'