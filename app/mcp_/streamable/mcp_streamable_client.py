import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler

# ============ 加载环境变量 ============
load_dotenv()

# ============ 初始化 LLM ============
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
    callbacks=[StreamingStdOutCallbackHandler()],
)


# ============ 创建 Streamable HTTP 客户端 ============
async def create_mcp_streamable_client():
    try:
        # 创建多服务器客户端
        client = MultiServerMCPClient(
            {
                "math": {
                    "url": "http://127.0.0.1:8000/mcp",  # Streamable HTTP 端点
                    "transport": "streamable_http",  # 注意：下划线
                }
            }
        )

        # 获取所有工具
        tools = await client.get_tools()
        print(f"\n✅ 成功加载 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # ============ 创建 Agent ============
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

        # ============ 测试调用 ============
        test_cases = [
            "请计算 14 + 17 * 5 = ?",
            "计算 (100 - 25) * 4 / 3 = ?",
            "2 的 10 次方等于多少？",
            "计算 5!（5的阶乘）等于多少？",
            "生成前 10 个斐波那契数列",
        ]

        for i, query in enumerate(test_cases, 1):
            print("\n" + "=" * 60)
            print(f"🧪 测试 {i}: {query}")
            print("=" * 60)

            try:
                resp = await agent.ainvoke(query)
                print(f"\n📝 最终回答:\n{resp['output']}\n")
            except Exception as e:
                print(f"❌ 调用失败: {e}")

        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============ 高级用法：上下文管理 ============
async def advanced_usage():
    """
    展示如何优雅地管理客户端生命周期
    """
    async with MultiServerMCPClient(
            {
                "math": {
                    "url": "http://127.0.0.1:8000/mcp",
                    "transport": "streamable_http",
                }
            }
    ) as client:
        tools = await client.get_tools()
        print(f"✅ 加载了 {len(tools)} 个工具")

        # 创建 Agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

        # 多轮对话
        queries = [
            "计算 3 + 4 * 5",
            "计算 10!",
            "生成前 5 个斐波那契数列",
        ]

        for query in queries:
            print(f"\n💬 用户: {query}")
            resp = await agent.ainvoke(query)
            print(f"🤖 AI: {resp['output']}")


# ============ 入口 ============
if __name__ == '__main__':
    print("🚀 启动 Streamable HTTP MCP 客户端...")
    print("📌 请确保 Streamable HTTP 服务器已启动: python mcp_streamable_server.py")
    print("📌 访问地址: http://127.0.0.1:8000/mcp")
    print()

    # 基础用法
    asyncio.run(create_mcp_streamable_client())

    # 高级用法（取消注释使用）
    # asyncio.run(advanced_usage())