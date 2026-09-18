import asyncio
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import initialize_agent, AgentType

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-5vz62sfwt5od2rps.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)


async def advanced_usage():
    # ✅ 新用法：直接创建实例，不再用 async with
    client = MultiServerMCPClient(
        {
            "钉钉 AI 表格": {
                "url": "https://mcp-gw.dingtalk.com/server/73e3cd9dac166be7e8cae28acbf2fe758949eb993db28ca11f374af4583df9e7?key=48fa8471419357d1be42c4bc2295ac97",
                "transport": "streamable_http",
            }
        }
    )

    tools = await client.get_tools()
    print(f"✅ 加载了 {len(tools)} 个工具")
    for i in  tools:
        print(i)

    # agent = initialize_agent(
    #     tools=tools,
    #     llm=llm,
    #     agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    #     verbose=True,
    # )

    # queries = [
    #     ""
    # ]
    #
    # for query in queries:
    #     print(f"\n💬 用户: {query}")
    #     resp = await agent.ainvoke({"input": query})   # 注意：传 dict
    #     print(f"🤖 AI: {resp['output']}")


if __name__ == '__main__':
    asyncio.run(advanced_usage())