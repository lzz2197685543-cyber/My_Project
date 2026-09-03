from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.redis import RedisSaver
from langgraph.prebuilt import create_react_agent

from app.code_agent.model.qwen import qwen_llm
from app.code_agent.tools.file_tools import file_tools



def create_agent():
    # 使用同步的RedisSaver
    # 我们这里使用的Docker容器内的redis不是本地的，所以本地的关掉或者用不同的端口号
    with RedisSaver.from_conn_string('redis://localhost:6379/0') as memory:
        memory.setup()

        agent = create_react_agent(
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

