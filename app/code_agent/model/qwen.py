import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


# 检查是否成功加载
api_key = os.getenv("DASHSCOPE_API_KEY")


# 初始化 LLM
qwen_llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)