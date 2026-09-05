import subprocess
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Dict, Any

mcp = FastMCP()

@mcp.tool(name='run_shell', description='执行 shell 命令')
def run_shell(
    command: Annotated[str, Field(description='要执行的命令', examples=['dir', 'ls -la'])]
) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"超时: {command}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    mcp.run(transport='stdio')