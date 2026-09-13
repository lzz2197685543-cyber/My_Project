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
        args=["-y", "@executeautomation/playwright-mcp-server"]
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

            resp = await agent.ainvoke(input={'messages': [('user', '在百度中查询江门今天的天气,读取页码信息并告诉我江门今天的温度、湿度、出行的建议')]})

            message=resp['messages']
            for message in message:
                if isinstance(message,HumanMessage):
                    print('用户：',message.content)
                elif isinstance(message,AIMessage):
                    if message.content:
                        print('助理:',message.content)
                    else:
                        for tool_call in message.tool_calls:
                            print('助理[调用工具]：',tool_call['name'],tool_call['args'])
                elif isinstance(message,ToolMessage):
                    print('调用工具:',message.name)

asyncio.run(mcp_playwright_client())