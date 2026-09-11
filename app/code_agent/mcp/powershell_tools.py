import json
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
    """激活 PowerShell 窗口（兼容旧调用：先定位终端，再切到前台）"""
    pid, hwnd = _resolve_terminal()
    if pid is None:
        return False
    return _activate_terminal(hwnd)


# ---------------------------------------------------------------------------
# 终端定位与按键
#
# 旧实现用 pyautogui.getWindowsWithTitle('Windows PowerShell' / 'PowerShell')
# 再取 windows[0]：这是"标题包含即匹配"的模糊匹配，顺序还不确定，本机只要有别的
# 标题含 PowerShell 的窗口（用户自己的终端、IDE 终端）就可能把按键发到错的窗口；
# 实测这里 getWindowsWithTitle('PowerShell') 也会直接返回 []，于是旧代码会退化成
# 一次 alt+tab 就返回失败，或者把字打进了别的窗口。
#
# 现在以"进程 -> 控制台窗口句柄"为准：
#   open_powershell 用 -PassThru 拿到自己开的那个 PID，
#   再由 console_probe.py 在独立子进程里 AttachConsole + GetConsoleWindow 取出该
#   终端的 HWND。定位是确定的，按键才知道发给了谁。
# ---------------------------------------------------------------------------
_CONSOLE_PROBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "console_probe.py")

# 终端状态必须落盘：
# langchain-mcp-adapters 每次工具调用都会新建一个 session，也就是起一个全新的
# MCP 服务进程，模块级变量在两次调用之间根本不存在。实测后果是 open_powershell
# 记下的 PID 在下一次 get_terminal_text 里已经丢了，只能退化成"扫描所有 powershell
# 进程"，可能读到别的终端。
_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           ".powershell_terminal.json")


def _load_terminal_state():
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"pid": data.get("pid"), "hwnd": data.get("hwnd")}
    except Exception:
        return {"pid": None, "hwnd": None}


def _store_terminal_state(pid, hwnd):
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"pid": pid, "hwnd": hwnd}, f)
    except Exception as e:
        _log(f"保存终端状态失败: {e}")


def _self_and_ancestors():
    """本进程及其所有祖先 PID。

    关闭终端时要避开这些：旧实现"杀掉所有名字含 powershell 的进程"会把 agent
    自己所在的终端、乃至托管本服务的 shell 一起杀掉（实测把调用方的 shell 干掉，
    测试进程以 exit code 15 结束）。
    """
    pids = set()
    try:
        proc = psutil.Process(os.getpid())
        pids.add(proc.pid)
        for parent in proc.parents():
            pids.add(parent.pid)
    except Exception:
        pass
    return pids


def _probe_console(action: str, pid: int, *extra, timeout: int = 20):
    """在独立子进程里向目标终端查询信息。返回 (ok, 文本)。

    必须独立进程：console_probe 里的 AttachConsole 会改变调用进程与 console 的
    绑定关系，在本服务进程里做会破坏它自己的 stdio 环境。
    """
    argv = [sys.executable, _CONSOLE_PROBE, action, str(pid), *[str(e) for e in extra]]
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                shell=False, timeout=timeout)
    except Exception as e:
        return False, f"调用 console_probe 失败: {e}"

    if result.returncode == 0:
        return True, _decode(result.stdout).strip()
    return False, _decode(result.stderr).strip() or f"console_probe 退出码 {result.returncode}"


def _resolve_terminal():
    """定位要操作的终端，返回 (pid, hwnd)；找不到返回 (None, None)。

    优先用 open_powershell 记下来的 PID；没有记录时才扫描所有 powershell 进程，
    并优先挑最新创建的那个（最可能就是刚打开的那个终端）。
    """
    state = _load_terminal_state()
    candidates = []

    tracked = state.get("pid")
    if tracked and psutil.pid_exists(tracked):
        candidates.append(tracked)

    others = []
    for proc in get_powershell_processes():
        if proc["pid"] in candidates:
            continue
        try:
            others.append((psutil.Process(proc["pid"]).create_time(), proc["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            others.append((0, proc["pid"]))
    others.sort(reverse=True)
    candidates.extend(pid for _, pid in others)

    for pid in candidates:
        ok, payload = _probe_console("hwnd", pid)
        if ok and payload.isdigit() and int(payload) > 0:
            _store_terminal_state(pid, int(payload))
            return pid, int(payload)

    _store_terminal_state(None, None)
    return None, None


def _activate_terminal(hwnd: int) -> bool:
    """把目标控制台窗口切到前台。

    SetForegroundWindow 受 Windows 前台锁限制：调用方不是前台进程时会静默失败
    （这正是"字打进去了但回车像没生效"的典型成因）。失败时把当前线程的输入队列
    挂到前台线程上再试一次，这是标准的 AttachThreadInput 绕法。
    """
    try:
        import win32api
        import win32con
        import win32gui
        import win32process

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        except Exception:
            pass

        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            current = win32api.GetCurrentThreadId()
            try:
                fg_thread = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
            except Exception:
                fg_thread = 0
            tgt_thread = win32process.GetWindowThreadProcessId(hwnd)[0]

            attached = []
            try:
                for other in (fg_thread, tgt_thread):
                    if other and other != current:
                        win32process.AttachThreadInput(current, other, True)
                        attached.append(other)
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetForegroundWindow(hwnd)
            finally:
                for other in attached:
                    try:
                        win32process.AttachThreadInput(current, other, False)
                    except Exception:
                        pass

        time.sleep(0.4)
        return win32gui.GetForegroundWindow() == hwnd
    except Exception as e:
        _log(f"_activate_terminal({hwnd}) 失败: {e}")
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


@mcp.tool(name="close_powershell", description="关闭 PowerShell 终端（优先关闭 open_powershell 打开的那个）")
def close_all_powershell() -> str:
    """关闭 PowerShell 终端"""
    try:
        # 优先只关掉 open_powershell 打开的那个终端
        state = _load_terminal_state()
        tracked = state.get("pid")
        if tracked and psutil.pid_exists(tracked):
            try:
                psutil.Process(tracked).terminate()
                _store_terminal_state(None, None)
                return f"已关闭终端 (PID={tracked})"
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                _log(f"关闭 PID={tracked} 失败，回退到关闭全部: {e}")

        processes = get_powershell_processes()
        if not processes:
            _store_terminal_state(None, None)
            return "没有找到需要关闭的 PowerShell 进程"

        # 兜底路径：本机所有 powershell 都关，但绝不碰自己及自己的祖先进程，
        # 否则会把 agent 所在终端 / 托管本服务的 shell 一起杀掉。
        protected = _self_and_ancestors()
        closed_count = 0
        skipped = []
        for proc_info in processes:
            if proc_info['pid'] in protected:
                skipped.append(proc_info['pid'])
                continue
            try:
                psutil.Process(proc_info['pid']).terminate()
                closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        _store_terminal_state(None, None)
        result = f"已成功关闭 {closed_count} 个 PowerShell 进程"
        if skipped:
            result += f"（跳过 {len(skipped)} 个受保护进程: {skipped}）"
        return result
    except Exception as e:
        return f"关闭 PowerShell 进程失败: {str(e)}"


@mcp.tool(name="open_powershell", description="打开新的 PowerShell 窗口")
def open_new_powershell(working_directory:
Annotated[str, Field(description="可选的工作目录，为空则使用当前目录", examples="C:\\Users")] = "") -> str:
    """打开新的 PowerShell 窗口"""
    try:
        if working_directory and os.path.exists(working_directory):
            # 在指定目录打开 PowerShell
            launch = f'Start-Process powershell -WorkingDirectory "{working_directory}"'
        else:
            # 在当前目录打开 PowerShell
            launch = 'Start-Process powershell'

        # -PassThru 把我们打开的这个 PowerShell 的 PID 打出来：后续定位窗口、发按键
        # 都以它为准，不再靠窗口标题模糊匹配。
        command = f'{launch} -PassThru | Select-Object -ExpandProperty Id'
        stdout, stderr, returncode = run_powershell_command(command)

        pid = None
        for line in stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                break

        if pid is None:
            return (f"打开 PowerShell 失败: 没能拿到新终端的 PID"
                    f"（stdout={stdout!r}, stderr={stderr!r}）")

        _store_terminal_state(pid, None)
        hwnd = None

        # Start-Process 返回时控制台窗口往往还没建好，这里等一下
        deadline = time.time() + 15
        while time.time() < deadline:
            ok, payload = _probe_console("hwnd", pid)
            if ok and payload.isdigit() and int(payload) > 0:
                hwnd = int(payload)
                _store_terminal_state(pid, hwnd)
                break
            time.sleep(0.5)

        if hwnd:
            return (f"PowerShell 已打开 (PID={pid}, 窗口句柄={hwnd})；"
                    f"接下来用 run_powershell_script 输入命令，"
                    f"用 get_terminal_text 查看终端内容")
        return (f"PowerShell 已打开 (PID={pid})，但暂未取到控制台窗口句柄"
                f"（可能不是经典 console 窗口）；调用 get_terminal_text 时会自动重试")
    except Exception as e:
        return f"打开 PowerShell 失败: {str(e)}"


def _inject_text(pid: int, text: str, timeout: int = 20):
    """把文本写进目标控制台的输入缓冲区。返回 (ok, 说明)。"""
    argv = [sys.executable, _CONSOLE_PROBE, "send", str(pid)]
    try:
        result = subprocess.run(argv, input=text.encode("utf-8"),
                                capture_output=True, shell=False, timeout=timeout)
    except Exception as e:
        return False, f"调用 console_probe 失败: {e}"

    if result.returncode == 0:
        return True, _decode(result.stdout).strip()
    return False, _decode(result.stderr).strip() or f"console_probe 退出码 {result.returncode}"


def _inject_key(pid: int, name: str, timeout: int = 20):
    """向目标控制台发送一个命名按键。返回 (ok, 说明)。"""
    argv = [sys.executable, _CONSOLE_PROBE, "key", str(pid), name]
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                shell=False, timeout=timeout)
    except Exception as e:
        return False, f"调用 console_probe 失败: {e}"

    if result.returncode == 0:
        return True, _decode(result.stdout).strip()
    return False, _decode(result.stderr).strip() or f"console_probe 退出码 {result.returncode}"


@mcp.tool(name="run_powershell_script", description="向 PowerShell 终端输入一条命令并回车")
def run_powershell_script(script:
Annotated[str, Field(description="要在 PowerShell 窗口中执行的脚本命令", examples="Get-Location")]) -> str:
    """向目标 PowerShell 终端输入命令并回车"""
    try:
        _log("-" * 50)
        _log("run_powershell_script:")
        _log(script)
        _log("-" * 50)

        pid, hwnd = _resolve_terminal()
        if pid is None:
            return "没有找到可用的 PowerShell 终端，请先调用 open_powershell 打开终端"

        # 首选：把按键直接写进该控制台自己的输入缓冲区。
        # 与窗口焦点无关，既不会把命令打进别的窗口，也不会像 pyautogui 那样丢字符
        # （实测 pyautogui.write("echo A B") 空格被吃掉，变成 echoAB 后报
        #  CommandNotFoundException）。中文等非 ASCII 字符同样支持。
        _inject_key(pid, "ctrl+c")  # 清掉输入行残留
        ok_text, detail_text = _inject_text(pid, script)
        ok_enter, detail_enter = _inject_key(pid, "return")

        if ok_text and ok_enter:
            return (f"已向终端 (PID={pid}) 输入命令并回车: {script}\n"
                    f"下一步请调用 get_terminal_text 查看终端输出，确认结果后再继续")

        # 回退：pyautogui 合成按键（需要窗口真的在前台，且只支持 ASCII）
        _log(f"控制台注入失败，回退 pyautogui: text={detail_text}; enter={detail_enter}")
        if not _activate_terminal(hwnd):
            return (f"无法向终端 (PID={pid}) 注入命令，且窗口无法切到前台"
                    f"（窗口句柄={hwnd}）；注入失败原因: {detail_text}")

        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        pyautogui.press('end')
        time.sleep(0.1)
        pyautogui.write(script, interval=0.02)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)

        return (f"已通过 pyautogui 向终端 (PID={pid}) 输入命令并回车: {script}\n"
                f"下一步请调用 get_terminal_text 查看终端输出，确认结果后再继续")
    except Exception as e:
        return f"发送 PowerShell 命令失败: {str(e)}"


@mcp.tool(name="get_terminal_text",
          description="读取 PowerShell 终端窗口里当前显示的内容（查看命令输出、交互式提示）")
def get_terminal_text(max_lines:
Annotated[int, Field(description="读取最后多少行，默认 60", examples=60)] = 60) -> str:
    """读取终端屏幕上的文本"""
    try:
        pid, hwnd = _resolve_terminal()
        if pid is None:
            return "没有找到可读取的 PowerShell 终端，请先调用 open_powershell 打开终端"

        ok, payload = _probe_console("read", pid, max_lines)
        if not ok:
            return f"读取终端文本失败 (PID={pid}): {payload}"

        _log(f"get_terminal_text: PID={pid}, {len(payload.splitlines())} 行")
        return payload if payload else "终端当前没有可读内容"
    except Exception as e:
        return f"读取终端文本失败: {str(e)}"


# terminal.txt 里写的按键名 -> console_probe.py 的按键名
_KEY_ALIASES = {
    "up": "up", "down": "down", "left": "left", "right": "right",
    "return": "return", "enter": "return", "回车": "return",
    "escape": "escape", "esc": "escape", "tab": "tab", "space": "space",
    "backspace": "backspace", "delete": "delete", "insert": "insert",
    "home": "home", "end": "end", "pageup": "pageup", "pagedown": "pagedown",
    "y": "y", "n": "n", "a": "a", "b": "b", "c": "c", "ctrl+c": "ctrl+c",
}

# console_probe 按键名 -> pyautogui 键名（仅 pyautogui 回退路径使用）
_PYAUTOGUI_KEYS = {"return": "enter", "escape": "esc"}


@mcp.tool(name="send_terminal_keyboard_key",
          description="向 PowerShell 终端发送按键（交互式命令用：up/down/left/right/return 等）")
def send_terminal_keyboard_key(key:
Annotated[str, Field(description="按键名：up / down / left / right / return / escape / tab / y / n 等",
                     examples="return")]) -> str:
    """向终端发送单个按键"""
    try:
        name = (key or "").strip().lower()
        mapped = _KEY_ALIASES.get(name)
        if mapped is None:
            supported = ", ".join(sorted(_KEY_ALIASES))
            return f"不支持的按键: {key!r}；支持: {supported}"

        pid, hwnd = _resolve_terminal()
        if pid is None:
            return "没有找到可用的 PowerShell 终端，请先调用 open_powershell 打开终端"

        # 首选：直接注入目标控制台的输入缓冲区（与焦点无关）
        ok, detail = _inject_key(pid, mapped)
        if not ok:
            # 回退：pyautogui 合成按键，需要窗口真的在前台
            _log(f"控制台注入失败，回退 pyautogui: {detail}")
            if not _activate_terminal(hwnd):
                return (f"无法向终端 (PID={pid}) 注入按键，且窗口无法切到前台"
                        f"（窗口句柄={hwnd}）；注入失败原因: {detail}")
            if mapped == "ctrl+c":
                pyautogui.hotkey('ctrl', 'c')
            else:
                pyautogui.press(_PYAUTOGUI_KEYS.get(mapped, mapped))
            time.sleep(0.3)

        _log(f"send_terminal_keyboard_key: PID={pid}, key={name} -> {mapped}")
        return (f"已向终端 (PID={pid}) 发送按键: {name}\n"
                f"下一步请调用 get_terminal_text 查看终端变化")
    except Exception as e:
        return f"发送按键失败: {str(e)}"


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
                return f"命令执行失败 (退出码 {returncode}): {stderr}"
            return f"命令执行失败 (退出码 {returncode})，但没有错误信息"

        # 退出码为 0 时也可能有 stderr：npm、git、pip 这类工具的提示、警告、
        # 进度信息全走 stderr。旧实现只在 returncode != 0 时才展示 stderr，
        # agent 因此只能看到"命令执行成功，但没有输出"，然后反复重试。
        if stdout and stderr:
            return f"命令执行成功:\n{stdout}\n\n[stderr]\n{stderr}"
        if stdout:
            return f"命令执行成功:\n{stdout}"
        if stderr:
            return f"命令执行成功，但没有 stdout 输出；stderr 内容如下:\n{stderr}"
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