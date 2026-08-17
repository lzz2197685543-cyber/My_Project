from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import Integer, ForeignKey, TIMESTAMP, Index
from datetime import datetime
from models.users import User
from models.news import News
from sqlalchemy.sql import func

class BaseModel(DeclarativeBase):
    pass

class History(BaseModel):
    __tablename__ = 'history'

    # 索引定义
    __table_args__ = (
        Index('fk_history_news_idx', 'news_id'),
        Index('fk_history_user_idx', 'user_id'),
        Index('idx_view_time', 'view_time'),  # 注意：图片中是 desc，但Index默认升序
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='历史记录id'
    )
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
    view_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment='浏览时间'
    )

    def __repr__(self):
        return f'<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>'