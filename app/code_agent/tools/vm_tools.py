import os
import sys

from app.code_agent.utils.mcp import create_mcp_stdio_client
from pathlib import Path

Base_dir=Path(__file__).resolve().parent.parent / 'mcp'

async def get_vm_tools():
    params = {
        'command': sys.executable,
        'args': [
            f"{Base_dir}/vm.py"
        ],
        'env': dict(os.environ),
    }

    client, tools = await create_mcp_stdio_client('vm_tools', params)

    return tools
