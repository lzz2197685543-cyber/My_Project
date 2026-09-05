import time
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from app.code_agent.model.qwen import qwen_llm
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.file_saver import CheckpointSaver
from app.code_agent.tools.shell_tools import get_stdio_shell_tools
import asyncio
from colorama import init, Fore, Style

init(autoreset=True)

# 颜色配置
C = {
    'ai': Fore.GREEN + Style.BRIGHT,
    'tool': Fore.YELLOW + Style.BRIGHT,
    'result': Fore.CYAN + Style.BRIGHT,
    'time': Fore.MAGENTA,
    'dim': Fore.WHITE + Style.DIM,
}


def print_step(step_num):
    """打印步骤标题 - 简洁版"""
    print(f"\n{C['dim']}━━━ 第 {step_num} 步 ━━━")


def print_ai(content):
    """打印AI思考"""
    print(f"{C['ai']}🤖AI思考 \n {content}")


def print_tool_call(name, args):
    """打印工具调用"""
    print(f"{C['tool']}🔧 调用 {name}")
    print(f"   {C['dim']}参数: {args}")


def print_tool_result(name, content, duration):
    """打印工具执行结果"""
    print(f"{C['result']}✅ {name} {C['time']}⏱️ {duration:.2f}s")
    # 截断过长内容
    if len(content) > 100:
        print(f"   {content[:100]}...")
    else:
        print(f"   {content}")


async def run_agent():
    memory = CheckpointSaver(base_dir='D:\\sd14\\ai-agent\\temp\\checkpoint')
    shell_tools = await get_stdio_shell_tools()
    tools = file_tools + shell_tools

    agent = create_react_agent(
        model=qwen_llm,
        tools=tools,
        checkpointer=memory,
        debug=False,
    )
    config = RunnableConfig(configurable={'thread_id': 3})

    while True:
        user_input = input(f"\n{C['ai']}你: ")
        if user_input == 'q':
            break

        print(f"\n{C['ai']}💭 思考中...")

        iteration_count = 0
        last_tool_time = time.time()

        async for chunk in agent.astream(input={'messages': user_input}, config=config):
            iteration_count += 1
            print_step(iteration_count)

            for node_name, node_output in chunk.items():
                if 'messages' not in node_output:
                    continue

                for msg in node_output['messages']:
                    if isinstance(msg, AIMessage):
                        # AI 响应
                        if msg.content:
                            print_ai(msg.content)
                        # 工具调用
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool in msg.tool_calls:
                                print_tool_call(tool["name"], tool["args"])

                    elif isinstance(msg, ToolMessage):
                        # 工具执行结果
                        tool_name = getattr(msg, 'name', 'unknown')
                        current_time = time.time()
                        duration = current_time - last_tool_time
                        last_tool_time = current_time
                        print_tool_result(tool_name, msg.content, duration)


if __name__ == '__main__':
    asyncio.run(run_agent())