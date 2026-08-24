from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import asyncio
import os
import json

load_dotenv()

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)

file_toolskit=FileManagementToolkit(root_dir='/temp')
file_tools=file_toolskit.get_tools()


async def create_mcp_client():
    amap_key = os.getenv('GAODE_API_KEY')
    if not amap_key:
        raise ValueError("请设置 GAODE_API_KEY 环境变量")

    # 高德 MCP 配置
    client = MultiServerMCPClient({
        "amap": {
            "url": f"https://mcp.amap.com/sse?key={amap_key}",
            "transport": "sse",
            "headers": {
                "Content-Type": "application/json",
            }
        }
    })

    tools = await client.get_tools()
    return client, tools


async def create_and_run_agent():
    try:
        # 创建 MCP 客户端并获取工具
        client, tools = await create_mcp_client()
        print(f"成功加载 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")

        # 创建 Agent
        agent = initialize_agent(
            tools=tools+file_tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

        # 构建提示词
        prompt_template = PromptTemplate.from_template(
            """你是一个智能助手，可以调用高德MCP工具。\n\n 问题{input}"""
        )

        user_input = """
           目标:
            - 国庆期间（2026年10月1日–10月7日），从海口出发，完成海南环岛骑行
            - 路线选择：东线进、西线出（或环线），每日规划具体行程
            - 考虑出行时间、路线规划，以及10月海南天气状况（热带季风气候，注意台风与降雨）
           
           要求：
           - 制作网页来展示环岛骑行路线和景点位置，输出一个HTML页面到 D:/sd14/ai-agent/temp/ 目录下
           -网页使用简约美观的页面风格，景区以卡片形式展示图片
           -行程规划结果需支持在高德地图APP中展示，并集成到H5页面中

        """

        prompt = prompt_template.format(input=user_input)

        # 执行 Agent
        print("\n正在规划旅行路线...")
        resp = await agent.ainvoke(prompt)

        print("回答：",resp['output'])


    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_and_run_agent())