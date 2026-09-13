import asyncio
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mcp import StdioServerParameters,stdio_client,ClientSession

load_dotenv()


# 检查是否成功加载
api_key = os.getenv("DASHSCOPE_API_KEY")

github_key=os.getenv("GITHUB_KEY")


# 初始化 LLM
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)

async def mcp_playwright_client():

    server_parameters = StdioServerParameters(
        command= "npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_key }
    )

    async with stdio_client(server_parameters) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            # 获取 MCP Tools
            tools=await load_mcp_tools(session)
            # print(tools)

            agent=create_react_agent(
                model=llm,
                tools=tools,
                debug=True
            )

            resp = await agent.ainvoke(input={'messages': [('user', 'lzz2197685543-cyber有哪些代码仓库，Star数是多少？')]})

            print(resp)

asyncio.run(mcp_playwright_client())