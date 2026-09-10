import locale
import os
import subprocess
import sys
import time
from typing import Annotated

import psutil
import pyautogui

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()


def _log(*args):
    """诊断信息一律写 stderr。

    stdout 是 MCP stdio 传输的 JSON-RPC 通道，往 stdout 写任何非 JSON 内容
    都会破坏协议（客户端会把非法行直接丢掉）。
    """
    print(*args, file=sys.stderr, flush=True)


def _decode(data: bytes) -> str:
    """PowerShell 输出编码随系统代码页变化，按字节读取后带兜底地解码。"""
    if not data:
        return ""
    for encoding in ("utf-8", locale.getpreferredencoding(False)):
        if not encoding:
            continue
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def run_powershell_command(command: str, capture_output: bool = True, timeout: int = 120):
    """执行 PowerShell 命令

    这里是之前"卡死"的根源，下面几点缺一不可：

    1. stdin=subprocess.DEVNULL —— 子进程绝不能继承本进程的 stdin。MCP stdio 服务的
       stdin 是 JSON-RPC 管道，被 powershell 继承后它会阻塞在这根管道上读输入，
       命令要等到客户端断开（管道 EOF）才真正执行，表现出来就是 Agent 永久卡住。
    2. shell=False —— 不再套一层 cmd.exe /c，避免引号被 cmd 二次解析，也少创建进程。
    3. -NoProfile -NonInteractive —— 不加载用户 profile，不等待任何交互输入。
    4. timeout —— 命令超时直接报错返回，绝不无限等待。
    """
    cmd = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        command,
    ]
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                shell=False,
                timeout=timeout,
            )
            return (
                _decode(result.stdout).strip(),
                _decode(result.stderr).strip(),
                result.returncode,
            )

        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            shell=False,
            timeout=timeout,
        )
        return "", "", result.returncode
    except subprocess.TimeoutExpired:
        return "", f"命令执行超时（超过 {timeout} 秒）", 1
    except Exception as e:
        return "", str(e), 1


def get_powershell_processes():
    """获取所有 PowerShell 进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'powershell' in proc.info['name'].lower():
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': proc.info['cmdline']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def activate_powershell_window():
    """激活 PowerShell 窗口"""
    try:
        # 设置 pyautogui 的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        # 使用 Alt+Tab 切换到 PowerShell 窗口
        # 首先尝试通过窗口标题查找
        windows = pyautogui.getWindowsWithTitle('Windows PowerShell')
        if not windows:
            windows = pyautogui.getWindowsWithTitle('PowerShell')

        if windows:
            # 激活第一个找到的 PowerShell 窗口
            window = windows[0]
            window.activate()
            time.sleep(0.5)  # 等待窗口激活
            return True
        else:
            # 如果没找到窗口，尝试通过快捷键
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            return False
    except Exception as e:
        print(f"激活 PowerShell 窗口失败: {e}")
        return False


@mcp.tool(name="get_powershell_processes", description="获取所有 PowerShell 进程信息")
def get_all_powershell_processes() -> str:
    """获取所有正在运行的 PowerShell 进程列表"""
    try:
        processes = get_powershell_processes()
        if not processes:
            return "当前没有运行的 PowerShell 进程"

        result = "PowerShell 进程列表:\n"
        for proc in processes:
            result += f"PID: {proc['pid']}, 名称: {proc['name']}\n"
        return result
    except Exception as e:
        return f"获取 PowerShell 进程失败: {str(e)}"


@mcp.tool(name="close_powershell", description="关闭所有 PowerShell 进程")
def close_all_powershell() -> str:
    """关闭所有 PowerShell 进程"""
    try:
        processes = get_powershell_processes()
        if not processes:
            return "没有找到需要关闭的 PowerShell 进程"

        closed_count = 0
        for proc_info in processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.terminate()
                closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return f"已成功关闭 {closed_count} 个 PowerShell 进程"
    except Exception as e:
        return f"关闭 PowerShell 进程失败: {str(e)}"


@mcp.tool(name="open_powershell", description="打开新的 PowerShell 窗口")
def open_new_powershell(working_directory:
Annotated[str, Field(description="可选的工作目录，为空则使用当前目录", examples="C:\\Users")] = "") -> str:
    """打开新的 PowerShell 窗口"""
    try:
        if working_directory and os.path.exists(working_directory):
            # 在指定目录打开 PowerShell
            command = f'Start-Process powershell -WorkingDirectory "{working_directory}"'
        else:
            # 在当前目录打开 PowerShell
            command = 'Start-Process powershell'

        stdout, stderr, returncode = run_powershell_command(command, capture_output=False)

        if returncode != 0 and stderr:
            return f"打开 PowerShell 失败: {stderr}"

        time.sleep(2)  # 等待窗口打开
        processes = get_powershell_processes()
        return f"PowerShell 已打开，当前运行进程数: {len(processes)}"
    except Exception as e:
        return f"打开 PowerShell 失败: {str(e)}"


@mcp.tool(name="run_powershell_script", description="通过 pyautogui 向 PowerShell 窗口发送命令")
def run_powershell_script(script:
Annotated[str, Field(description="要在 PowerShell 窗口中执行的脚本命令", examples="Get-Location")]) -> str:
    """通过 pyautogui 向活动的 PowerShell 窗口发送命令"""
    try:
        _log("-" * 50)
        _log("run_powershell_script (pyautogui):")
        _log(script)
        _log("-" * 50)

        # 检查是否有 PowerShell 进程在运行
        processes = get_powershell_processes()
        if not processes:
            return "没有找到运行中的 PowerShell 进程，请先打开 PowerShell 窗口"

        # 激活 PowerShell 窗口
        if not activate_powershell_window():
            return "无法激活 PowerShell 窗口，请确保 PowerShell 窗口已打开"

        # 清空当前输入行（如果有的话）
        pyautogui.hotkey('ctrl', 'c')  # 取消当前命令
        time.sleep(0.2)

        # 确保光标在命令行
        pyautogui.press('end')
        time.sleep(0.1)

        # 输入命令
        pyautogui.write(script, interval=0.02)
        time.sleep(0.3)

        # 按 Enter 执行命令
        pyautogui.press('enter')

        return f"命令已发送到 PowerShell 窗口: {script}"

    except Exception as e:
        return f"发送 PowerShell 命令失败: {str(e)}"


@mcp.tool(name="execute_powershell_command", description="直接执行 PowerShell 命令并返回结果")
def execute_powershell_command(command:
Annotated[str, Field(description="要执行的 PowerShell 命令", examples="Get-Process")]) -> str:
    """直接执行 PowerShell 命令并返回结果（不通过 GUI）"""
    try:
        _log("-" * 50)
        _log("execute_powershell_command:")
        _log(command)
        _log("-" * 50)

        stdout, stderr, returncode = run_powershell_command(command)

        if returncode != 0:
            if stderr:
                return f"命令执行失败: {stderr}"
            else:
                return "命令执行失败，但没有错误信息"

        if stdout:
            return f"命令执行成功:\n{stdout}"
        else:
            return "命令执行成功，但没有输出"

    except Exception as e:
        return f"执行 PowerShell 命令失败: {str(e)}"


if __name__ == '__main__':
    mcp.run(transport="stdio")
    # 测试代码（注释掉）
    # close_all_powershell()
    # open_new_powershell()
    # process = get_all_powershell_processes()
    # print(process)
    # run_powershell_script("Get-Location")