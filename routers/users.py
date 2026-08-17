# routers/users.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest
from config.db_conf import get_database
from crud import users
from starlette import status
from utils.response import success_response
from utils.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["users"])


# ============================================================
# 1. 用户注册
# ============================================================
@router.post("/register")
async def register_user(user_data: UserRequest, db: AsyncSession = Depends(get_database)):
    """
    用户注册功能

    处理流程：
    1. 检查用户名是否已存在 → 存在则返回错误
    2. 创建新用户（密码使用 passlib 加密）
    3. 生成访问令牌（使用 uuid.uuid4() 生成临时 Token）
    4. 返回注册成功响应（包含 Token 和用户信息）

    Token 说明：
    - Token 是服务器下发的身份凭证，用于后续请求的身份验证
    - 客户端需将 Token 放在请求头中：Authorization: Bearer <token>
    - 作用：解决 HTTP 无状态问题，实现"登录后持续验证"

    请求参数：UserRequest (username, password)
    响应数据：UserAuthResponse (token, user_info)
    """
    # 1. 检查用户是否存在
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='用户已经存在')

    # 2. 创建用户（密码加密）
    user = await users.create_user(db, user_data)

    # 3. 生成访问令牌
    token = await users.create_token(db, user.id)

    # 4. 组装响应数据（model_validate 自动转换 ORM 对象）
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user)
    )

    return success_response(message='注册成功', data=response_data)


# ============================================================
# 2. 用户登录
# ============================================================
@router.post("/login")
async def login_user(user_data: UserRequest, db: AsyncSession = Depends(get_database)):
    """
    用户登录功能

    处理流程：
    1. 验证用户名是否存在
    2. 验证密码是否正确（使用 CryptContext.verify()）
    3. 验证通过 → 生成访问令牌
    4. 返回登录成功响应（包含 Token 和用户信息）

    请求参数：UserRequest (username, password)
    响应数据：UserAuthResponse (token, user_info)
    """
    # 1-2. 验证用户名和密码
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误')

    # 3. 生成访问令牌
    token = await users.create_token(db, user.id)

    # 4. 组装响应数据
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user)
    )

    return success_response(message='登录成功', data=response_data)


# ============================================================
# 3. 获取用户信息
# ============================================================
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息

    处理流程：
    1. 通过依赖注入 get_current_user 验证 Token 并获取用户对象
    2. 返回用户信息

    请求头要求：Authorization: Bearer <token>
    响应数据：UserInfoResponse (用户详细信息)
    """
    return success_response(
        message='获取用户信息成功',
        data=UserInfoResponse.model_validate(user)
    )


# ============================================================
# 4. 更新用户信息
# ============================================================
@router.put("/update")
async def update_user(
        user_data: UserUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    更新当前登录用户信息

    处理流程：
    1. 验证 Token 有效性（通过依赖注入）
    2. 获取当前用户信息
    3. 使用用户提交的数据更新用户信息
    4. 返回更新后的用户信息

    请求头要求：Authorization: Bearer <token>
    请求参数：UserUpdateRequest (可更新的用户字段)
    响应数据：UserInfoResponse (更新后的用户信息)
    """
    updated_user = await users.update_user(db, user.username, user_data)

    return success_response(
        message='更新用户信息成功',
        data=UserInfoResponse.model_validate(updated_user)
    )


# ============================================================
# 5. 修改密码
# ============================================================
@router.put("/password")
async def update_password(
        password_data: UserChangePasswordRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    修改当前登录用户密码

    处理流程：
    1. 验证 Token 有效性（通过依赖注入）
    2. 获取当前用户信息
    3. 验证旧密码是否正确
    4. 将新密码加密后更新到数据库
    5. 返回修改成功响应

    请求头要求：Authorization: Bearer <token>
    请求参数：UserChangePasswordRequest (old_password, new_password)
    响应数据：成功消息
    """
    # 执行密码修改（内部包含旧密码验证和新密码加密）
    res_change_pwd = await users.change_password(
        db,
        user,
        password_data.old_password,
        password_data.new_password
    )

    if not res_change_pwd:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='修改密码失败，请稍后再试'
        )

    return success_response(message='修改密码成功')