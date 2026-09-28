import os
import sys

from app.code_agent.utils.mcp import create_mcp_stdio_client
from pathlib import Path

Base_dir=Path(__file__).resolve().parent.parent / 'mcp'

async def get_stdio_shell_tools():
    # 与 tools/powershell_tools.py 同理：
    # - 用 sys.executable，避免 PATH 上的 python 不是当前虚拟环境
    # - 显式传完整环境，否则 mcp 默认过滤掉 PATHEXT，Windows 下命令全部解析不了
    params = {
        'command': sys.executable,
        'args': [

            f"{Base_dir}/shell_tools.py"
        ],
        'env': dict(os.environ),
    }

    client, tools = await create_mcp_stdio_client('shell_tools', params)

    return tools
