import os
import sys

from app.code_agent.utils.mcp import create_mcp_stdio_client
from pathlib import Path

Base_dir=Path(__file__).resolve().parent.parent / 'rag'

async def self_get_rag_tools():
    # 与 tools/powershell_tools.py 同理：
    # - 用 sys.executable，避免 PATH 上的 python 不是当前虚拟环境
    # - 显式传完整环境，否则 mcp 默认过滤掉 PATHEXT，Windows 下命令全部解析不了
    # - 路径写成 r"D:\\..." 时反斜杠是双份，虽然 Windows 容忍，但没必要
    params = {
        'command': sys.executable,
        'args': [
            f"{Base_dir}\self_rag.py"
        ],
        'env': dict(os.environ),
    }

    client, tools = await create_mcp_stdio_client('self_rag_tools', params)

    return tools
