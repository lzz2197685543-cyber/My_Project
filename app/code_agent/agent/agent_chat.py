from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.prebuilt import create_react_agent

from app.code_agent.model.qwen import qwen_llm
from app.code_agent.tools.file_tools import file_tools



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
            input={"messages": [('user', '我是谁？')]},
            config=config
        )
        print('=' * 60)
        print(res)
        print('=' * 60)

        memory.close()

        return agent

if __name__ == '__main__':
    run_agent()

