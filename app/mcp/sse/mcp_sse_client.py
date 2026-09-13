import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# ============ 加载环境变量 ============
load_dotenv()

# ============ 初始化 LLM ============
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)

# ============ 创建 SSE 客户端 ============
async def create_mcp_sse_client():
    try:
        # 创建多服务器客户端
        client = MultiServerMCPClient(
            {
                "math": {
                    "url": "http://127.0.0.1:8000/sse",  # SSE 端点
                    "transport": "sse",                   # 指定传输方式
                }
            }
        )

        # 获取所有工具
        tools = await client.get_tools()
        print(f"✅ 成功加载 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # ============ 创建 Agent ============
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
        )

        # ============ 测试调用 ============
        print("\n" + "="*50)
        print("🧪 测试 1: 基础运算")
        print("="*50)
        resp1 = await agent.ainvoke("请计算 14 + 17 * 5 = ?")
        print(f"\n📝 回答: {resp1['output']}\n")

        print("="*50)
        print("🧪 测试 2: 复杂表达式")
        print("="*50)
        resp2 = await agent.ainvoke("计算 (100 - 25) * 4 / 3 = ?")
        print(f"\n📝 回答: {resp2['output']}\n")

        print("="*50)
        print("🧪 测试 3: 幂运算")
        print("="*50)
        resp3 = await agent.ainvoke("计算 2 的 10 次方等于多少？")
        print(f"\n📝 回答: {resp3['output']}\n")

        return resp1

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============ 入口 ============
if __name__ == '__main__':
    print("🚀 启动 SSE MCP 客户端...")
    print("📌 请确保 SSE 服务器已启动: python mcp_sse_server.py")
    print()
    asyncio.run(create_mcp_sse_client())