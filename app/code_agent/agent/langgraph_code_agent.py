from langchain_core.messages import convert_to_messages
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import MemorySaver

from app.code_agent.model.qwen import qwen_llm
from app.code_agent.tools.shell_tools import get_stdio_shell_tools
from app.code_agent.tools.file_tools import file_tools

import asyncio

def pretty_print_messages(update,last_message=False):
    print(update.items())
    for node_name,node_update in update.items():
        update_label=f'Update from node {node_name}'
        print(update_label)

        messages=convert_to_messages(node_update['messages'])
        if last_message:
            messages=messages[-1:]

        for message in messages:
            pretty_message=message.pretty_repr(html=True)
            print(pretty_message)

        print('\n\n')

async def run_agent():
    memory = MemorySaver()
    shell_tools = await get_stdio_shell_tools()

    research_agent = create_react_agent(
        model=qwen_llm,
        tools=shell_tools + file_tools,
        name='research_expert',
        prompt='你是一个技术方案设计专家，专门负责设计技术方案，请不要直接写代码',
    )

    code_agent = create_react_agent(
        model=qwen_llm,
        tools=shell_tools + file_tools,
        name='code_expert',
        prompt='你是一个编程专家，请根据 research_expert 设计的技术方案来实现代码'
    )

    supervisor_agent = create_supervisor(
        agents=[research_agent, code_agent],
        model=qwen_llm,
        prompt=(
                "你是一个团队主管，负责管理一名研究专家和一名代码专家。"
                "对于任务规划和任务研究，请使用 research_agent。"
                "对于代码问题，请使用 code_agent。"
                )
    )

    app = supervisor_agent.compile(checkpointer=memory)

    while True:
        user_input=input('用户：')

        if user_input.lower() == 'exit':
            break

        config=RunnableConfig(configurable={"thread_id":2},recursion_limit=100)

        async for chunk in app.astream(input={'messages':user_input},config=config):
            pretty_print_messages(chunk,last_message=True)




if __name__ == '__main__':
    asyncio.run(run_agent())

