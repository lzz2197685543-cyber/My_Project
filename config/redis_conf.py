from typing import Any
import redis.asyncio as redis
import json

# 创建redis的连接对象
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,  # 是否将字节数据解码为字符串
    protocol=2  # 🔑 强制使用 RESP2 协议，避免 HELLO 命令问题
)

# ✅ 修复：读取字符串
async def get_cache(key: str):
    try:
        return await redis_client.get(key)  # 🔑 添加 await
    except Exception as e:
        print(f'获取缓存失败：{e}')
        return None

# ✅ 修复：读取列表或字典
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)  # 🔑 添加 await
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f'获取缓存失败:{e}')
        return None

# ✅ 修复：设置缓存
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, expire, value)  # 🔑 添加 await
        return True
    except Exception as e:
        print(f'设置缓存失败:{e}')
        return False