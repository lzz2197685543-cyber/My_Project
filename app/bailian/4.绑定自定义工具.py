"""
工具调用五步法（使用 @tool 装饰器版本）
1. 开发工具函数
2. 将工具函数转为LangChain Tool对象
3. 将大模型和Tool对象绑定
4. 调用大模型，尝试让大模型调用工具
5. 调用工具
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field

load_dotenv()

# ============================================================
# 第一步：开发工具函数
# ============================================================
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


# ============================================================
# 第二步：将工具函数转为LangChain Tool对象
# ============================================================
# 注意：@tool 装饰器已经自动将函数转换为Tool对象
# 可以直接使用 add 作为工具对象
def create_calc_tools():
    """创建计算工具列表"""
    return [add]

calc_tools = create_calc_tools()  # 获取工具列表


# ============================================================
# 第三步：将大模型和Tool对象绑定
# ============================================================
# 3.1 初始化大模型
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)

# 3.2 创建提示词模板
chat_template = ChatPromptTemplate.from_messages([
    ('system', "你是一位{role}专家，擅长回答{domain}领域的问题。当需要进行数学计算时，请使用 'add' 工具。"),
    ('user', '{question}')
])

# 3.3 绑定工具到大模型（使用 calc_tools 或直接使用 [add]）
llm_with_tools = llm.bind_tools(calc_tools)  # 或者 llm.bind_tools([add])

# 3.4 构建处理链
chain = chat_template | llm_with_tools


# ============================================================
# 第四步：调用大模型，尝试让大模型调用工具
# ============================================================
resp = chain.invoke(input={
    "role": "计算",
    "domain": "数学计算",
    "question": "14+17=?"
})

print("=" * 50)
print("第四步：大模型的响应")
print("=" * 50)
print(f"原始响应: {resp}")
print(f"\n工具调用信息: {resp.tool_calls}")


# ============================================================
# 第五步：调用工具
# ============================================================
# 5.1 创建工具字典（用于查找对应的工具函数）
tool_dict = {
    'add': add,  # 直接存储被装饰的函数引用
}

print("\n" + "=" * 50)
print("第五步：执行工具调用")
print("=" * 50)

for tool_call in resp.tool_calls:
    print(f"  工具名称: {tool_call['name']}")
    print(f"  参数: {tool_call['args']}")
    print(f"  调用ID: {tool_call['id']}")

    # 获取工具名称和参数
    func_name = tool_call['name']
    args = tool_call['args']

    # 5.2 根据工具名称执行对应的工具函数
    if func_name in tool_dict:
        tool_result = tool_dict[func_name].invoke(args)  # 实际执行工具
        print(f"  ✅ 计算结果: {tool_result}")
    else:
        print(f"  ❌ 错误: 未找到工具 {func_name}")