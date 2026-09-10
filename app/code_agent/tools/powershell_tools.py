import sys

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_powershell_tools():
    # 用 sys.executable 而不是字符串 'python'：
    # 用 'python' 时 MCP 服务走的是 PATH 上的解释器，一旦它不是当前虚拟环境，
    # 服务进程会因为 import mcp/pyautogui/psutil 失败直接退出，客户端就会一直等。
    params = {
        'command': sys.executable,
        'args': [
            r"D:\sd14\ai-agent\app\code_agent\mcp\powershell_tools.py"
        ]
    }

    client, tools = await create_mcp_stdio_client('powershell_tools', params)

    return tools
