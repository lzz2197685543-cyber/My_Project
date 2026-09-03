from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.mongodb import MongoDBSaver

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

def run_agent():
    MONGODB_URI = 'mongodb://localhost:27017/'
    MONGODB_DB = 'chat'
    with MongoDBSaver.from_conn_string(MONGODB_URI, MONGODB_DB) as memory:

        agent=create_react_agent(
            model=qwen_llm,
            tools=file_tools,
            checkpointer=memory,
            debug=True,
        )
        config = RunnableConfig(configurable={'thread_id': 1})

        print("🤖 第一轮对话...")
        res = agent.invoke(
            input={"messages": [('user', '你好，我是柠檬，一个电商公司的rpa')]},
            config=config
        )
        print('=' * 60)
        print(res)
        print('=' * 60)

        memory.close()

        return agent





if __name__ == '__main__':
    run_agent()
