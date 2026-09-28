import json
import locale
import os
import shlex
import subprocess
import sys
import time
from typing import Annotated

import psutil

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()

# 默认使用的 shell；可按需改成 zsh / pwsh
DEFAULT_SHELL = os.environ.get("MCP_SHELL", "bash")

# 每个 MCP 服务用固定的 tmux session 名，避免污染用户已有 session
SESSION_NAME = os.environ.get("MCP_TMUX_SESSION", "mcp_terminal")

# 状态文件：记录当前 session 名（对应 Windows 版的 .powershell_terminal.json）
_STATE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".linux_terminal.json"
)


def _log(*args):
    """诊断信息一律写 stderr，stdout 是 MCP stdio 的 JSON-RPC 通道。"""
    print(*args, file=sys.stderr, flush=True)


def _decode(data: bytes) -> str:
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


def _run(argv, timeout=120, input_bytes=None):
    """统一的子进程封装。返回 (stdout, stderr, returncode)。"""
    try:
        result = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            input=input_bytes,
            capture_output=True,
            shell=False,
            timeout=timeout,
        )
        return _decode(result.stdout).strip(), _decode(result.stderr).strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", f"命令执行超时（超过 {timeout} 秒）", 1
    except FileNotFoundError as e:
        return "", f"命令不存在: {e}", 127
    except Exception as e:
        return "", str(e), 1


def _have_tmux() -> bool:
    out, _, code = _run(["bash", "-lc", "command -v tmux"], timeout=10)
    return code == 0 and bool(out)


# ---------------------------------------------------------------------------
# session 状态管理
# ---------------------------------------------------------------------------
def _load_state():
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"session": None}


def _store_state(session):
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"session": session}, f)
    except Exception as e:
        _log(f"保存终端状态失败: {e}")


def _tmux_has_session(session: str) -> bool:
    _, _, code = _run(["tmux", "has-session", "-t", session], timeout=10)
    return code == 0


def _resolve_session():
    """返回当前可用的 tmux session 名；没有则返回 None。"""
    state = _load_state()
    session = state.get("session")
    if session and _tmux_has_session(session):
        return session
    if session:
        # 记录的 session 已经不在了，清掉
        _store_state(None)
    return None


def _list_mcp_sessions():
    """列出所有可能由本服务创建的 session。"""
    out, _, code = _run(
        ["tmux", "list-sessions", "-F", "#{session_name}"], timeout=10
    )
    if code != 0:
        return []
    return [s.strip() for s in out.splitlines() if s.strip()]


# ---------------------------------------------------------------------------
# 工具：执行纯命令（不经过终端，对应 execute_powershell_command）
# ---------------------------------------------------------------------------
def _execute_shell_command(command: str, timeout: int = 120):
    """用登录 shell 执行命令。bash -lc 会加载 profile，行为更接近用户手敲。"""
    return _run([DEFAULT_SHELL, "-lc", command], timeout=timeout)


# ---------------------------------------------------------------------------
# 工具实现
# ---------------------------------------------------------------------------
@mcp.tool(name="open_terminal", description="打开一个新的交互式终端（tmux session）")
def open_terminal(
    working_directory: Annotated[
        str, Field(description="可选的工作目录，为空则使用当前目录", examples="/home/user")
    ] = "",
) -> str:
    """打开一个新的 tmux session 作为交互式终端。"""
    try:
        if not _have_tmux():
            return "系统未安装 tmux，请先安装：sudo apt install tmux"

        if _resolve_session():
            existing = _load_state().get("session")
            return f"终端已存在 (session={existing})，如需新建请先调用 close_terminal"

        session = SESSION_NAME
        # 避免和用户已有 session 重名
        if _tmux_has_session(session):
            session = f"{SESSION_NAME}_{int(time.time())}"

        cwd = working_directory if working_directory and os.path.isdir(working_directory) else os.getcwd()

        # -d 后台启动；-x/-y 指定初始尺寸，保证 capture-pane 能拿到合理行数
        argv = ["tmux", "new-session", "-d", "-s", session, "-c", cwd]
        _, stderr, code = _run(argv, timeout=20)
        if code != 0:
            return f"打开终端失败: {stderr}"

        # 让 session 里跑一个交互式 shell
        _run(["tmux", "send-keys", "-t", session, DEFAULT_SHELL, "C-m"], timeout=20)

        _store_state(session)
        return (
            f"终端已打开 (session={session}, 工作目录={cwd})；"
            f"用 run_terminal_script 输入命令，用 get_terminal_text 查看终端内容"
        )
    except Exception as e:
        return f"打开终端失败: {str(e)}"


@mcp.tool(name="close_terminal", description="关闭本服务打开的终端（tmux session）")
def close_terminal() -> str:
    """关闭终端。只关本服务记录/创建的 session，不动用户自己的。"""
    try:
        session = _resolve_session()
        if session is None:
            # 没记录时，只清理名字带本服务前缀的 session
            closed = []
            for s in _list_mcp_sessions():
                if s == SESSION_NAME or s.startswith(f"{SESSION_NAME}_"):
                    _run(["tmux", "kill-session", "-t", s], timeout=10)
                    closed.append(s)
            _store_state(None)
            if closed:
                return f"已关闭终端: {', '.join(closed)}"
            return "没有找到需要关闭的终端"

        _run(["tmux", "kill-session", "-t", session], timeout=10)
        _store_state(None)
        return f"已关闭终端 (session={session})"
    except Exception as e:
        return f"关闭终端失败: {str(e)}"


@mcp.tool(
    name="run_terminal_script",
    description="向交互式终端输入一条命令并回车（对应 Windows 版的 run_powershell_script）",
)
def run_terminal_script(
    script: Annotated[
        str, Field(description="要在终端中执行的命令", examples="ls -la")
    ],
) -> str:
    """向终端输入命令并回车。"""
    try:
        _log("-" * 50)
        _log("run_terminal_script:")
        _log(script)
        _log("-" * 50)

        session = _resolve_session()
        if session is None:
            return "没有可用的终端，请先调用 open_terminal 打开终端"

        # 清掉输入行残留，再输入命令。tmux send-keys 的 -l 表示按字面量发送，
        # 避免命令里的 ; | 等被 tmux 当成按键名解析。
        _run(["tmux", "send-keys", "-t", session, "C-c"], timeout=10)
        time.sleep(0.05)
        _, stderr, code = _run(
            ["tmux", "send-keys", "-t", session, "-l", "--", script], timeout=20
        )
        if code != 0:
            return f"输入命令失败: {stderr}"
        _run(["tmux", "send-keys", "-t", session, "C-m"], timeout=10)
        time.sleep(0.2)

        return (
            f"已向终端 (session={session}) 输入命令并回车: {script}\n"
            f"下一步请调用 get_terminal_text 查看终端输出，确认结果后再继续"
        )
    except Exception as e:
        return f"发送命令失败: {str(e)}"


@mcp.tool(
    name="get_terminal_text",
    description="读取终端窗口里当前显示的内容（查看命令输出、交互式提示）",
)
def get_terminal_text(
    max_lines: Annotated[
        int, Field(description="读取最后多少行，默认 60", examples=60)
    ] = 60,
) -> str:
    """抓取 tmux pane 当前屏幕文本。"""
    try:
        session = _resolve_session()
        if session is None:
            return "没有可读取的终端，请先调用 open_terminal 打开终端"

        # -p 输出到 stdout，-S -N 表示从倒数 N 行开始抓
        out, stderr, code = _run(
            ["tmux", "capture-pane", "-t", session, "-p", "-S", f"-{max_lines}"],
            timeout=20,
        )
        if code != 0:
            return f"读取终端文本失败 (session={session}): {stderr}"

        text = out.rstrip("\n")
        _log(f"get_terminal_text: session={session}, {len(text.splitlines())} 行")
        return text if text else "终端当前没有可读内容"
    except Exception as e:
        return f"读取终端文本失败: {str(e)}"


# tmux 按键名基本和原版一致，这里做一层别名映射
_KEY_ALIASES = {
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "return": "Enter", "enter": "Enter", "回车": "Enter",
    "escape": "Escape", "esc": "Escape", "tab": "Tab", "space": "Space",
    "backspace": "BSpace", "delete": "DC", "insert": "IC",
    "home": "Home", "end": "End", "pageup": "PPage", "pagedown": "NPage",
    "y": "y", "n": "n", "a": "a", "b": "b", "c": "c",
    "ctrl+c": "C-c", "ctrl+d": "C-d", "ctrl+z": "C-z",
    "ctrl+l": "C-l", "ctrl+a": "C-a", "ctrl+e": "C-e",
}


@mcp.tool(
    name="send_terminal_keyboard_key",
    description="向终端发送按键（交互式命令用：up/down/left/right/return 等）",
)
def send_terminal_keyboard_key(
    key: Annotated[
        str,
        Field(
            description="按键名：up / down / left / right / return / escape / tab / y / n 等",
            examples="return",
        ),
    ],
) -> str:
    """向终端发送单个按键。"""
    try:
        name = (key or "").strip().lower()
        mapped = _KEY_ALIASES.get(name)
        if mapped is None:
            supported = ", ".join(sorted(_KEY_ALIASES))
            return f"不支持的按键: {key!r}；支持: {supported}"

        session = _resolve_session()
        if session is None:
            return "没有可用的终端，请先调用 open_terminal 打开终端"

        _, stderr, code = _run(
            ["tmux", "send-keys", "-t", session, mapped], timeout=20
        )
        if code != 0:
            return f"发送按键失败: {stderr}"

        time.sleep(0.15)
        _log(f"send_terminal_keyboard_key: session={session}, key={name} -> {mapped}")
        return (
            f"已向终端 (session={session}) 发送按键: {name}\n"
            f"下一步请调用 get_terminal_text 查看终端变化"
        )
    except Exception as e:
        return f"发送按键失败: {str(e)}"


@mcp.tool(
    name="execute_shell_command",
    description="直接执行 shell 命令并返回结果（不经过交互式终端，对应 Windows 版的 execute_powershell_command）",
)
def execute_shell_command(
    command: Annotated[
        str, Field(description="要执行的 shell 命令", examples="ls -la")
    ],
) -> str:
    """直接执行命令并返回结果。"""
    try:
        _log("-" * 50)
        _log("execute_shell_command:")
        _log(command)
        _log("-" * 50)

        stdout, stderr, returncode = _execute_shell_command(command)

        if returncode != 0:
            if stderr:
                return f"命令执行失败 (退出码 {returncode}): {stderr}"
            return f"命令执行失败 (退出码 {returncode})，但没有错误信息"

        # 退出码 0 也可能有 stderr（警告/进度），一并展示
        if stdout and stderr:
            return f"命令执行成功:\n{stdout}\n\n[stderr]\n{stderr}"
        if stdout:
            return f"命令执行成功:\n{stdout}"
        if stderr:
            return f"命令执行成功，但没有 stdout 输出；stderr 内容如下:\n{stderr}"
        return "命令执行成功，但没有输出"
    except Exception as e:
        return f"执行命令失败: {str(e)}"


@mcp.tool(name="list_terminal_processes", description="列出当前终端里前台运行的进程")
def list_terminal_processes() -> str:
    """列出 tmux pane 里当前的前台进程（辅助调试）。"""
    try:
        session = _resolve_session()
        if session is None:
            return "没有可用的终端，请先调用 open_terminal 打开终端"

        out, stderr, code = _run(
            ["tmux", "list-panes", "-t", session, "-F",
             "#{pane_pid} #{pane_current_command}"],
            timeout=10,
        )
        if code != 0:
            return f"查询失败: {stderr}"
        return f"终端进程:\n{out}"
    except Exception as e:
        return f"查询失败: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

