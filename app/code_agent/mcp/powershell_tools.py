import subprocess
import time
import psutil
import os
import sys
import tempfile
from typing import Annotated, List
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 尝试导入 win32gui（用于精确窗口管理）
try:
    import win32gui
    import win32process
    import win32con

    HAS_WIN32GUI = True
except ImportError:
    HAS_WIN32GUI = False
    print("⚠️ 未安装 pywin32，窗口管理功能将受限", file=sys.stderr, flush=True)

mcp = FastMCP()


def run_powershell_command(command: str, capture_output: bool = True, timeout: int = 10):
    """执行 PowerShell 命令"""
    try:
        cmd = ["powershell.exe", "-Command", command]
        if capture_output:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            # 调试信息
            print(f"✅ 命令执行完成: {command[:50]}", file=sys.stderr, flush=True)
            print(f"   返回码: {result.returncode}", file=sys.stderr, flush=True)
            print(f"   输出长度: {len(result.stdout)}", file=sys.stderr, flush=True)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            result = subprocess.run(cmd, timeout=timeout)
            return "", "", result.returncode
    except subprocess.TimeoutExpired:
        print(f"⏰ 命令超时: {command[:50]}", file=sys.stderr, flush=True)
        return "", f"命令执行超时（{timeout}秒）", 1
    except Exception as e:
        print(f"❌ 执行异常: {e}", file=sys.stderr, flush=True)
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


def find_powershell_window():
    """精确查找真正的 PowerShell 窗口（排除 Conda/CMD）"""
    if not HAS_WIN32GUI:
        return None

    try:
        def enum_windows_callback(hwnd, hwnds):
            # 只检查可见窗口
            if not win32gui.IsWindowVisible(hwnd):
                return True

            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True

            # 获取窗口进程
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name().lower()
            except:
                return True

            # 精确匹配：必须是 PowerShell.exe 进程，且窗口标题包含 PowerShell
            if 'powershell.exe' in process_name:
                # 排除 Conda 或 CMD 窗口
                if 'conda' not in title.lower() and 'cmd' not in title.lower():
                    hwnds.append(hwnd)

            return True

        hwnds = []
        win32gui.EnumWindows(enum_windows_callback, hwnds)

        if hwnds:
            return hwnds[0]

        return None

    except Exception as e:
        print(f"查找窗口失败: {e}", file=sys.stderr, flush=True)
        return None


def activate_powershell_window():
    """激活真正的 PowerShell 窗口"""
    try:
        import sys

        # 方法1：使用 win32gui 精确查找
        hwnd = find_powershell_window()

        if hwnd:
            # 如果窗口最小化则恢复
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # 激活窗口
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)

            title = win32gui.GetWindowText(hwnd)
            print(f"✅ 已激活 PowerShell 窗口: {title}", file=sys.stderr, flush=True)
            return True

        # 方法2：使用 pygetwindow 作为备选（如果已安装）
        try:
            import pygetwindow as gw
            # 尝试多种可能的标题
            windows = []
            for title_pattern in ['Windows PowerShell', 'PowerShell', 'powershell']:
                found = gw.getWindowsWithTitle(title_pattern)
                if found:
                    windows.extend(found)

            # 去重并过滤掉 Conda
            windows = list(set(windows))
            windows = [w for w in windows if 'conda' not in w.title.lower() and 'cmd' not in w.title.lower()]

            if windows:
                window = windows[0]
                window.activate()
                time.sleep(0.5)
                print(f"✅ 已激活窗口: {window.title}", file=sys.stderr, flush=True)
                return True
        except ImportError:
            pass
        except Exception as e:
            print(f"pygetwindow 备选方案失败: {e}", file=sys.stderr, flush=True)

        print("❌ 未找到 PowerShell 窗口", file=sys.stderr, flush=True)
        return False

    except Exception as e:
        print(f"激活窗口失败: {e}", file=sys.stderr, flush=True)
        return False


@mcp.tool(name="get_powershell_processes", description="获取所有 PowerShell 进程信息")
def get_all_powershell_processes() -> str:
    """获取所有正在运行的 PowerShell 进程列表"""
    try:
        processes = get_powershell_processes()
        if not processes:
            return "当前没有运行的 PowerShell 进程"

        result = "PowerShell 进程列表:\n"
        result += f"{'PID':<10} {'名称':<20}\n"
        result += "-" * 30 + "\n"
        for proc in processes:
            result += f"{proc['pid']:<10} {proc['name']:<20}\n"
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
def open_new_powershell(working_directory: Annotated[
    str, Field(description="可选的工作目录，为空则使用当前目录", examples="C:\\Users")] = "") -> str:
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


@mcp.tool(name="execute_powershell_command", description="直接执行 PowerShell 命令并返回结果（推荐使用）")
def execute_powershell_command(
        command: Annotated[str, Field(description="要执行的 PowerShell 命令", examples="Get-Process")]) -> str:
    """直接执行 PowerShell 命令并返回结果（不通过 GUI，最可靠的方式）"""
    try:
        print("-" * 50, file=sys.stderr, flush=True)
        print(f"execute_powershell_command: {command}", file=sys.stderr, flush=True)
        print("-" * 50, file=sys.stderr, flush=True)

        stdout, stderr, returncode = run_powershell_command(command, timeout=15)

        if returncode != 0:
            if stderr:
                return f"命令执行失败 (返回码: {returncode}):\n{stderr}"
            else:
                return f"命令执行失败，返回码: {returncode}"

        if stdout:
            return f"命令执行成功:\n{stdout}"
        else:
            return "命令执行成功，但没有输出"

    except Exception as e:
        print(f"execute_powershell_command 异常: {e}", file=sys.stderr, flush=True)
        return f"执行 PowerShell 命令失败: {str(e)}"


@mcp.tool(name="execute_in_new_window", description="在新的 PowerShell 窗口中执行命令并保持窗口打开")
def execute_in_new_window(
        command: Annotated[str, Field(description="要执行的 PowerShell 命令", examples="Get-Process")]) -> str:
    """在新的 PowerShell 窗口中执行命令，窗口保持打开状态（适合需要查看实时输出的场景）"""
    try:
        # 创建临时 PowerShell 脚本
        ps_script = f"""
Write-Host "执行命令: {command}"
Write-Host "-" * 50
{command}
Write-Host "-" * 50
if ($LASTEXITCODE -ne 0) {{
    Write-Host "⚠️ 命令执行失败，退出码: $LASTEXITCODE" -ForegroundColor Red
}} else {{
    Write-Host "✅ 命令执行完成！" -ForegroundColor Green
}}
Write-Host ""
Read-Host "按 Enter 键退出..."
"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
            f.write(ps_script)
            script_path = f.name

        # 在新的 PowerShell 窗口中执行
        subprocess.Popen([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path
        ], creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0)

        time.sleep(1)  # 等待窗口打开

        return f"✅ 已在新 PowerShell 窗口执行命令:\n{command}\n\n窗口将保持打开状态，执行完成后按 Enter 键退出。"

    except Exception as e:
        return f"❌ 执行失败: {str(e)}"


@mcp.tool(name="run_powershell_script", description="[不推荐] 通过 GUI 向 PowerShell 窗口发送命令（可能激活错误窗口）")
def run_powershell_script(script: Annotated[
    str, Field(description="要在 PowerShell 窗口中执行的脚本命令", examples="Get-Location")]) -> str:
    """通过 GUI 向活动的 PowerShell 窗口发送命令（不推荐，建议使用 execute_powershell_command）"""
    try:
        print("-" * 50, file=sys.stderr, flush=True)
        print(f"run_powershell_script: {script}", file=sys.stderr, flush=True)
        print("⚠️ 此方法不可靠，建议使用 execute_powershell_command", file=sys.stderr, flush=True)
        print("-" * 50, file=sys.stderr, flush=True)

        # 1. 检查是否有 PowerShell 进程在运行
        processes = get_powershell_processes()
        if not processes:
            return "❌ 没有找到运行中的 PowerShell 进程。\n💡 建议使用 'execute_powershell_command' 或 'execute_in_new_window' 工具。"

        # 2. 尝试激活 PowerShell 窗口
        if not activate_powershell_window():
            return "❌ 无法激活 PowerShell 窗口。\n💡 建议使用 'execute_powershell_command' 或 'execute_in_new_window' 工具。"

        # 3. 发送命令（使用 pyautogui）
        try:
            import pyautogui

            # 设置安全选项
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1

            # 清空当前输入行（如果有的话）
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.2)

            # 确保光标在命令行末尾
            pyautogui.press('end')
            time.sleep(0.1)

            # 输入命令
            pyautogui.write(script, interval=0.02)
            time.sleep(0.3)

            # 按 Enter 执行命令
            pyautogui.press('enter')

            return f"✅ 命令已发送到 PowerShell 窗口: {script}\n\n⚠️ 注意：无法获取命令执行结果。如需查看结果，请切换到 PowerShell 窗口。\n💡 建议使用 'execute_powershell_command' 获取结果。"

        except ImportError:
            return "❌ 需要安装 pyautogui 才能使用此功能。\n💡 建议使用 'execute_powershell_command' 或 'execute_in_new_window' 工具。"
        except Exception as e:
            return f"❌ 发送命令失败: {str(e)}\n💡 建议使用 'execute_powershell_command' 或 'execute_in_new_window' 工具。"

    except Exception as e:
        return f"❌ 执行失败: {str(e)}"


if __name__ == '__main__':
    # 启动 MCP 服务器
    print("🚀 启动 PowerShell MCP 服务器", file=sys.stderr, flush=True)
    print(f"📦 依赖状态: {'✅ pywin32 已安装' if HAS_WIN32GUI else '⚠️ pywin32 未安装（窗口管理功能受限）'}",
          file=sys.stderr, flush=True)
    mcp.run(transport="stdio")