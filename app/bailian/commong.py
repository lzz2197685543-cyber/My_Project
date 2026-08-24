from langchain_core.prompts import PromptTemplate,ChatPromptTemplate,ChatMessagePromptTemplate,FewShotPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

llm=ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)


system_message='你是一位{role}专家，擅长回答{domain}领域的问题。'
user_message='{question}'

# 创建提示词模板
system_template=ChatMessagePromptTemplate.from_template(
    template=system_message,
    role='system',
)

user_template=ChatMessagePromptTemplate.from_template(
    template=user_message,
    role='user',
)

chat_prompt=ChatPromptTemplate.from_messages([
    system_template,
    user_template
])


class AddInputArgs(BaseModel):
    """加法运算的参数模型"""
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool(
    description="将两个数字相加",
    args_schema=AddInputArgs,
    return_direct=True,  # 工具结果直接返回给用户，不继续传递给LLM
)
def add(a: int, b: int) -> int:
    """将两个数字相加"""
    return a + b

def create_calc_tools():
    """创建计算工具列表"""
    return [add]

calc_tools = create_calc_tools()  # 获取工具列表