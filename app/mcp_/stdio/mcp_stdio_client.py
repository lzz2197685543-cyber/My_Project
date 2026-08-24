import os
from dotenv import load_dotenv
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
import asyncio
from pathlib import Path

# ============ 加载 .env 文件 ============
# 方法1: 自动查找 .env 文件（从当前目录往上找）
load_dotenv()


# 检查是否成功加载
api_key = os.getenv("DASHSCOPE_API_KEY")


# 初始化 LLM
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)


async def create_mcp_stdio_client():
    # 这一步启动了服务器，我们不需要手动启动了
    server_params = StdioServerParameters(
        command='python',
        args=['D:/sd14/ai-agent/app/mcp_/stdio/mcp_stdio_server.py']
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                print(f"成功加载 {len(tools)} 个工具")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")

                # 创建 Agent
                agent = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                )

                resp = await agent.ainvoke("14+17*5=?")
                print(f"\n回答: {resp}")
                return resp

    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    asyncio.run(create_mcp_stdio_client())