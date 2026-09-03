from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.redis import RedisSaver

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

file_tools = FileManagementToolkit(root_dir='E:\\Ai_Agent\\temp').get_tools()


load_dotenv()


# 检查是否成功加载
api_key = os.getenv("DASHSCOPE_API_KEY")


# 初始化 LLM
qwen_llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)

def create_agent():
    # 我们这里使用的Docker容器内的redis不是本地的，所以本地的关掉或者用不同的端口号
    with RedisSaver.from_conn_string('redis://localhost:6379/0') as memory:
        memory.setup()

        agent=create_react_agent(
            model=qwen_llm,
            tools=file_tools,
            checkpointer=memory,
            debug=True,
        )

        return agent

def run_agent():
    config = RunnableConfig(configurable={'thread_id': 1})
    agent = create_agent()

    print("🤖 第一轮对话...")
    res = agent.invoke(
        input={"messages": [('user', '你好，我是柠檬，一个电商公司的rpa')]},
        config=config
    )
    print('=' * 60)
    print(res)
    print('=' * 60)

    print("\n🤖 第二轮对话（测试记忆）...")
    res = agent.invoke(
        input={"messages": [('user', '我叫什么，我是做什么的？')]},
        config=config
    )
    print('=' * 60)
    print(res)
    print('=' * 60)


if __name__ == '__main__':
    run_agent()
