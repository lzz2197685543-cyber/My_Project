# crud/users.py
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils.security import get_password_hash, verify_password


# ============================================================
# 数据库操作层 - 用户相关 CRUD
# ============================================================

# ------------------------------------------------------------
# 1. 用户查询操作
# ------------------------------------------------------------

async def get_user_by_username(db: AsyncSession, username: str):
    """
    根据用户名查询用户信息

    Args:
        db: 异步数据库会话
        username: 用户名

    Returns:
        User | None: 用户对象或 None
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_token(db: AsyncSession, token: str):
    """
    根据 Token 查询用户信息（验证 Token 有效性）

    处理流程：
    1. 根据 Token 查询 UserToken 记录
    2. 检查 Token 是否存在且未过期
    3. 根据 user_id 查询对应的用户信息

    Args:
        db: 异步数据库会话
        token: 访问令牌

    Returns:
        User | None: 用户对象（Token 有效）或 None（Token 无效/过期）
    """
    # 1. 查询 Token 记录
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    # 2. 验证 Token 是否存在且未过期
    if not db_token or db_token.expires_at < datetime.now():
        return None

    # 3. 查询对应用户信息
    result = await db.execute(select(User).where(User.id == db_token.user_id))
    return result.scalar_one_or_none()


# ------------------------------------------------------------
# 2. 用户创建操作
# ------------------------------------------------------------

async def create_user(db: AsyncSession, user_data: UserRequest):
    """
    创建新用户

    处理流程：
    1. 使用 bcrypt 对密码进行哈希加密
    2. 创建 User 对象
    3. 保存到数据库

    密码加密说明：
    - 使用 passlib + bcrypt 进行加密
    - 安装：pip install bcrypt==4.0.1 passlib==1.7.4

    Args:
        db: 异步数据库会话
        user_data: 用户注册数据 (username, password)

    Returns:
        User: 创建成功的用户对象（包含自增 ID）
    """
    # 1. 密码加密
    hashed_password = get_password_hash(user_data.password)

    # 2. 创建用户对象
    user = User(username=user_data.username, password=hashed_password)

    # 3. 保存到数据库
    db.add(user)
    await db.commit()
    await db.refresh(user)  # 刷新以获取数据库生成的字段（如 id）

    return user


# ------------------------------------------------------------
# 3. Token 管理操作
# ------------------------------------------------------------

async def create_token(db: AsyncSession, user_id: int):
    """
    生成或更新用户的访问令牌

    处理流程：
    1. 使用 uuid4 生成唯一令牌
    2. 设置过期时间为 7 天
    3. 检查用户是否已有 Token
       - 有：更新现有 Token
       - 无：创建新 Token

    Token 说明：
    - Token 是服务器下发的身份凭证
    - 客户端需在请求头中携带：Authorization: Bearer <token>
    - 作用：解决 HTTP 无状态问题，实现身份验证

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        str: 生成的 Token 字符串
    """
    # 1. 生成 Token 和设置过期时间
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)

    # 2. 查询用户是否已有 Token
    result = await db.execute(select(UserToken).where(UserToken.user_id == user_id))
    user_token = result.scalar_one_or_none()

    # 3. 更新或创建 Token
    if user_token:
        # 更新现有 Token
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        # 创建新 Token
        user_token = UserToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(user_token)

    await db.commit()
    return token


# ------------------------------------------------------------
# 4. 用户认证操作
# ------------------------------------------------------------

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    验证用户登录凭证

    处理流程：
    1. 根据用户名查询用户
    2. 用户存在 → 验证密码是否匹配
    3. 验证通过 → 返回用户对象

    Args:
        db: 异步数据库会话
        username: 用户名
        password: 明文密码

    Returns:
        User | None: 验证通过返回用户对象，否则返回 None
    """
    # 1. 查询用户
    user = await get_user_by_username(db, username)
    if not user:
        return None

    # 2. 验证密码（使用 CryptContext.verify()）
    if not verify_password(password, user.password):
        return None

    return user


# ------------------------------------------------------------
# 5. 用户信息更新操作
# ------------------------------------------------------------

async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    """
    更新用户信息

    处理流程：
    1. 使用 Pydantic 模型的 model_dump() 提取要更新的字段
    2. 执行 UPDATE 操作（只更新传递的字段）
    3. 检查是否成功更新
    4. 返回更新后的用户信息

    注意：
    - exclude_unset=True: 只更新客户端显式传递的字段
    - exclude_none=True: 排除值为 None 的字段

    Args:
        db: 异步数据库会话
        username: 用户名
        user_data: 要更新的用户数据

    Returns:
        User: 更新后的用户对象

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    # 1. 构建更新语句（只更新传递的字段）
    sql = update(User).where(
        User.username == username
    ).values(
        **user_data.model_dump(
            exclude_unset=True,  # 只包含客户端显式设置的字段
            exclude_none=True,  # 排除值为 None 的字段
        )
    )

    # 2. 执行更新
    result = await db.execute(sql)
    await db.commit()

    # 3. 检查是否更新成功
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail='用户不存在')

    # 4. 获取并返回更新后的用户信息
    updated_user = await get_user_by_username(db, username)
    return updated_user


# ------------------------------------------------------------
# 6. 密码修改操作
# ------------------------------------------------------------

async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str):
    """
    修改用户密码

    处理流程：
    1. 验证旧密码是否正确
    2. 对新密码进行哈希加密
    3. 更新用户密码
    4. 提交到数据库

    安全说明：
    - 必须先验证旧密码，防止未授权修改
    - 新密码使用 bcrypt 加密存储

    Args:
        db: 异步数据库会话
        user: 当前登录的用户对象
        old_password: 旧密码（明文）
        new_password: 新密码（明文）

    Returns:
        bool: 修改成功返回 True，旧密码错误返回 False

    Raises:
        HTTPException: 其他错误会由上层处理
    """
    # 1. 验证旧密码
    if not verify_password(old_password, user.password):
        return False

    # 2. 加密新密码
    hash_new_pwd = get_password_hash(new_password)

    # 3. 更新密码
    user.password = hash_new_pwd

    # 4. 保存到数据库
    # 注意：db.add(user) 确保 SQLAlchemy 能追踪到这个对象的变更
    # 即使 Session 状态发生变化，也能保证更新成功
    db.add(user)
    await db.commit()

    return True