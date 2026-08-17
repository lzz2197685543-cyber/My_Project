from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum, Text, Index,ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

class BaseModel(DeclarativeBase):
    pass





# 用户模型类
class User(BaseModel):
    __tablename__ = 'user'

    # 创建索引
    __table_args__ = (
        Index('username_UNIQUE','username'),
        Index('phone_UNIQUE','phone'),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='用户ID'
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='用户名'
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='密码'
    )

    nickname: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment='昵称'
    )

    avatar: Mapped[Optional[str]] = mapped_column(
        String(500),
        default='https://apac.ossforai.com/2026/08/13/32acafaa-7d81-4509-9b40-69e515b214e2.png',
        nullable=True,
        comment='头像URL'
    )

    gender: Mapped[str] = mapped_column(
        default='unknown',
        nullable=False,
        comment='性别'
    )

    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        default='内心丰盈者，独行也如众',
        nullable=True,
        comment='个人简介'
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment='手机号'
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment='创建时间'
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        comment='更新时间'
    )

    def __repr__(self):
        return f'<User(id={self.id}, username={self.username}, nickname={self.nickname}, gender={self.gender.value})>'


# 用户令牌模型类
class UserToken(BaseModel):
    __tablename__ = 'user_token'

    # 创建索引
    __table_args__ = (
        Index('token_UNIQUE', 'token'),
        Index('fk_user_token_user_idx', 'user_id'),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='令牌ID'
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        comment='用户ID'
    )

    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='令牌'
    )

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        comment='过期时间'
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment='创建时间'
    )


    def __repr__(self):
        return f'<UserToken(id={self.id}, user_id={self.user_id}, token={self.token[:10]}..., expires_at={self.expires_at})>'