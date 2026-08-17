from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 异步数据库连接URL（使用aiomysql驱动）
ASYNC_DATABASE_URL = 'mysql+aiomysql://root:1234@localhost:3306/news_app?charset=utf8'

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,          # 输出SQL日志（开发环境开启）
    pool_size=10,       # 连接池常驻连接数
    max_overflow=20,    # 峰值时最大额外连接数
    pool_recycle=1800,  # 连接回收时间（秒），避免连接超时
    pool_pre_ping=True, # 使用前检查连接是否有效
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后会话不会过期，避免重新查询
)

# 会话依赖项
async def get_database():
    """FastAPI依赖项：管理数据库会话生命周期"""
    async with AsyncSessionLocal() as session:
        try:
            yield session          # 将会话注入路由函数
            await session.commit() # 无异常则提交事务
        except Exception as e:
            await session.rollback() # 有异常则回滚
            raise
        finally:
            await session.close()    # 确保会话关闭