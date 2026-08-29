from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent


import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

file_tools = FileManagementToolkit(root_dir='D:\\sd14\\ai-agent\\temp').get_tools()


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
    memory=MemorySaver()

    agent=create_react_agent(
        model=qwen_llm,
        tools=file_tools,
        checkpointer=memory,
        debug=True,
    )

    return agent

def run_agent():
    config=RunnableConfig(configurable={'thread_id':1})
    agent=create_agent()
    res=agent.invoke(input={"messages":[('user','你好，我是柠檬，一个电商公司的rpa')]},config=config)
    print('='*60)
    print(res)
    print('='*60)

    res = agent.invoke(input={"messages": [('user', '我叫什么，我是做什么的？')]}, config=config)
    print('=' * 60)
    print(res)
    print('=' * 60)


if __name__ == '__main__':
    run_agent()