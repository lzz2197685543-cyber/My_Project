from fastapi import Header, HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_database
from crud import users



async def get_current_user(
        authorization: str = Header(..., alias='Authorization'),
        db: AsyncSession = Depends(get_database),
):
    token = authorization.replace('Bearer ', '')
    user=await users.get_user_by_token(db,token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='无效的令牌或者已经过期的令牌')
    return user
