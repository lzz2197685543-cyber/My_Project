import os
import sys

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_powershell_tools():
    # 1) 用 sys.executable 而不是字符串 'python'：
    #    用 'python' 时 MCP 服务走的是 PATH 上的解释器，一旦它不是当前虚拟环境，
    #    服务进程会因为 import mcp/pyautogui/psutil 失败直接退出，客户端就会一直等。
    #    路径用原始字符串、单个反斜杠，不要写成 r"D:\\..."（双反斜杠会被原样传下去）。
    # 2) env=os.environ 必须显式传：
    #    mcp 客户端默认只用 get_default_environment() 透传一小撮变量
    #    （APPDATA/HOMEDRIVE/HOMEPATH/LOCALAPPDATA/PATH/PROCESSOR_ARCHITECTURE/
    #     SYSTEMDRIVE/SYSTEMROOT/TEMP/USERNAME/USERPROFILE），Windows 下不含 PATHEXT。
    #    缺了 PATHEXT，服务里 spawn 出来的 powershell 只把 .CPL 当可执行文件：
    #      - node / npm / cmd 全部"无法将 xx 项识别为 cmdlet"（实测就是这个现象）
    #      - & "C:\...\node.exe" -v 被当成文档，静默无输出（CantActivateDocumentInPipeline）
    #      - npm.ps1 里 $LASTEXITCODE 未设置，报 RuntimeException
    #    实测对照：不传 PATHEXT 时 Get-Command node 为空、node.exe -v 无输出；
    #    传完整环境后 node.exe / cmd.exe 都能正常解析。
    params = {
        'command': sys.executable,
        'args': [
            r"D:\sd14\ai-agent\app\code_agent\mcp\powershell_tools.py"
        ],
        'env': dict(os.environ),
    }

    client, tools = await create_mcp_stdio_client('powershell_tools', params)

    return tools
