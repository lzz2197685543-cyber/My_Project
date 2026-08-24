import json

from langchain.agents import initialize_agent,AgentType
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os
load_dotenv()

"""
智能体开发流程：（具备调用大模型能力（包含提示词模板）、具备大模型调用工具能力、创建智能体，由智能体调用Tool并返回结果）
第一步：初始化工具
第二步：初始化大模型
第三步：创建智能体
第四步：调用智能体
"""

#  输出模型定义
class Output(BaseModel):
    args:str=Field("输入的参数")
    result:str=Field("返回的结果")

# 定义结构化输出格式
parser=JsonOutputParser(pydantic_object=Output)
format_instructions=parser.get_format_instructions()

# ============================================================
# 第一步：初始化工具
# ============================================================
class AddInputArgs(BaseModel):
    """加法运算的参数模型"""
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool(
    description="将两个数字相加",
    args_schema=AddInputArgs,
    return_direct=False,
)
def add(a: int, b: int) -> int:
    """将两个数字相加"""
    return a + b

def create_calc_tools():
    """创建计算工具列表"""
    return [add]

calc_tools = create_calc_tools()  # 获取工具列表

# ============================================================
# 第二步：初始化大模型
# ============================================================
llm=ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)


# ============================================================
# 第三步：创建智能体
# ============================================================

agent = initialize_agent(
    tools=calc_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,# 打印详细执行过程
    )

# ============================================================
# 第四步：调用智能体
# ============================================================
system_message = '你是一位{role}专家，擅长回答{domain}领域的问题。'
user_message = '{question}'

chat_template = ChatPromptTemplate.from_messages([
    ('system', system_message),
    ('user', user_message)
])

# 填充变量生成提示词
prompt = chat_template.format_messages(
    role='计算',
    domain='使用工具进行数据计算',
    question=f'请阅读下面的问题，并返回一个严格的JSON对象，不要使用MarkDown代码块包裹！格式要求{format_instructions}，问题：12+17=？'
)

resp=agent.invoke(prompt)
print(resp)
print(resp['output'])
