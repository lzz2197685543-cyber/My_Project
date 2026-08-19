from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat

app = FastAPI(title="DeepSeek Chat API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue3 开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "DeepSeek Chat API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)