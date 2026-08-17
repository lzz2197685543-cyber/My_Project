# schemas/users.py
from typing import Optional

from pydantic import BaseModel,Field,ConfigDict


class UserRequest(BaseModel):
    username: str
    password: str


class UserInfoBase(BaseModel):
    """用户信息基础数据模型"""
    nickname: Optional[str] = Field(None,max_length=50, description='昵称')
    avatar: Optional[str] = Field(None, max_length=500, description='头像URL')
    gender: Optional[str] = Field(None, max_length=50, description='性别')
    bio: Optional[str] = Field(None, max_length=500, description='个人简介')

# user_info对应的类：基础类+Info类（id、用户名）
class UserInfoResponse(UserInfoBase):
    id:int
    username:str

    # 模型配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )

# data 数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse=Field(...,alias='userInfo')

    # 模型配置
    model_config = ConfigDict(
        populate_by_name=True,# alias：灵活适应前后端命名规范差异
        from_attributes=True # 允许从 ORM 对象属性中取值
    )



# 更新用户的模型类
class UserUpdateRequest(BaseModel):
    nickname:str=None
    avatar:str=None
    gender:str=None
    bio:str=None
    phone:str=None


class UserChangePasswordRequest(BaseModel):
    old_password: str=Field(...,alias='oldPassword',description='旧密码')
    new_password: str=Field(...,min_length=6,alias='newPassword',description='新密码')