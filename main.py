from fastapi import FastAPI
from routers import news,users,favorite,history
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers


app = FastAPI()

# 注册异常处理器
register_exception_handlers(app)

# 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许的源，开发阶段运行所有，生产环境需要指定安装
    allow_credentials=True, # 运行携带cookie
    allow_methods=["*"], #
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
