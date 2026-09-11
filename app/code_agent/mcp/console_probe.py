"""读取指定进程的控制台窗口内容 / 窗口句柄（独立进程运行）。

为什么必须放在独立进程里：
AttachConsole 会改变"调用进程"与 console 的绑定关系。MCP stdio 服务进程
自己的 stdin/stdout 是 JSON-RPC 管道，直接在它里面 AttachConsole 会破坏它的
运行环境，所以这里每个动作都由一个短命子进程完成，读完就退出。

用法:
    python console_probe.py read <pid> [max_lines]
    python console_probe.py hwnd <pid>
    python console_probe.py info <pid>
    python console_probe.py send <pid>        # 待发送文本从 stdin 按 UTF-8 读入
    python console_probe.py key <pid> <name>  # up/down/left/right/return/ctrl+c ...

stdout: 读取到的文本 / 窗口句柄 / 写入的记录数
stderr: 失败原因
退出码: 0 成功 / 2 无法附加控制台 / 3 读取或写入失败 / 4 参数错误
"""

import ctypes
import sys
from ctypes import wintypes

# 调用方按 UTF-8 解码我们的输出，这里先固定输出编码，避免中文变成乱码
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
ERROR_NOT_SUPPORTED = 50
ERROR_INVALID_HANDLE = 6


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", wintypes.WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]


kernel32.AttachConsole.argtypes = [wintypes.DWORD]
kernel32.AttachConsole.restype = wintypes.BOOL
kernel32.FreeConsole.argtypes = []
kernel32.FreeConsole.restype = wintypes.BOOL
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE,
                                                ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
kernel32.ReadConsoleOutputCharacterW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR,
                                                 wintypes.DWORD, COORD,
                                                 ctypes.POINTER(wintypes.DWORD)]
kernel32.ReadConsoleOutputCharacterW.restype = wintypes.BOOL
kernel32.GetConsoleWindow.argtypes = []
kernel32.GetConsoleWindow.restype = wintypes.HWND
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def _fail(code: int, message: str):
    print(message, file=sys.stderr)
    sys.exit(code)


def _attach(pid: int, device: str = "CONOUT$"):
    """把自己挂到 pid 的控制台上，返回设备句柄（默认输出缓冲区）。

    device="CONIN$" 时拿到的是输入缓冲区句柄，可以向该控制台注入按键。
    """
    kernel32.FreeConsole()  # 先脱离自己的 console，否则 AttachConsole 会失败
    if not kernel32.AttachConsole(pid):
        err = ctypes.get_last_error()
        _fail(2, f"AttachConsole({pid}) 失败（错误码 {err}）：该进程没有控制台，"
                 f"或它由 Windows Terminal / ConPTY 托管且不允许附加")

    handle = kernel32.CreateFileW(device, GENERIC_READ | GENERIC_WRITE,
                                  FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                                  OPEN_EXISTING, 0, None)
    if not handle or handle == wintypes.HANDLE(-1).value:
        err = ctypes.get_last_error()
        _fail(3, f"打开 {device} 失败（错误码 {err}）")
    return handle


def do_hwnd(pid: int) -> int:
    _attach(pid)
    hwnd = kernel32.GetConsoleWindow()
    if not hwnd:
        _fail(2, "该控制台没有窗口句柄（可能是无窗口/ConPTY 托管）")
    return int(hwnd)


def do_read(pid: int, max_lines: int) -> str:
    handle = _attach(pid)

    info = CONSOLE_SCREEN_BUFFER_INFO()
    if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
        err = ctypes.get_last_error()
        hint = ""
        if err in (ERROR_NOT_SUPPORTED, ERROR_INVALID_HANDLE):
            hint = ("（该终端很可能由 Windows Terminal / ConPTY 托管，"
                    "ConPTY 不提供可读的屏幕缓冲区）")
        _fail(3, f"GetConsoleScreenBufferInfo 失败（错误码 {err}）{hint}")

    width = info.dwSize.X
    if width <= 0:
        _fail(3, "控制台缓冲区宽度为 0，无法读取")

    top, bottom = info.srWindow.Top, info.srWindow.Bottom

    buf = ctypes.create_unicode_buffer(width + 1)
    read = wintypes.DWORD()
    lines = []

    # 必须把整个可见区域读下来再去尾部空行。
    # 窗口通常有几十行高（实测 49/29 行），而内容只占顶部几行，
    # 若直接取"窗口最后 max_lines 行"，读到的全是底部空白，
    # 结果就是"终端当前没有可读内容"这种假象。
    for row in range(top, bottom + 1):
        ok = kernel32.ReadConsoleOutputCharacterW(handle, buf, width, COORD(0, row),
                                                 ctypes.byref(read))
        if not ok:
            err = ctypes.get_last_error()
            if not lines:
                hint = ""
                if err in (ERROR_NOT_SUPPORTED, ERROR_INVALID_HANDLE):
                    hint = ("（该终端很可能由 Windows Terminal / ConPTY 托管，"
                            "ConPTY 不支持读取屏幕缓冲区）")
                _fail(3, f"ReadConsoleOutputCharacter 失败（错误码 {err}）{hint}")
            break
        lines.append(buf[:read.value].rstrip())

    # 去掉尾部空行，但保留中间的空行结构
    while lines and not lines[-1]:
        lines.pop()

    # max_lines 只用来截断"确实有内容"的部分
    if max_lines > 0 and len(lines) > max_lines:
        lines = lines[-max_lines:]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 向目标控制台注入按键
#
# 为什么不用 pyautogui 发按键：pyautogui 走的是"合成键盘事件 -> 系统送给当前
# 前台窗口"，因此 (1) 必须抢占前台焦点，焦点一丢按键就发到别的窗口；(2) 实测
# pyautogui.write("echo DSH_PROBE_OK") 打进终端后空格被吃掉，变成
# echoDSH_PROBE_OK，命令直接报 CommandNotFoundException。
#
# WriteConsoleInput 是把按键记录直接写进"目标控制台自己的输入缓冲区"，
# 跟焦点无关、不会打错窗口、也不会丢字符，中文等非 ASCII 字符同样支持。
# ---------------------------------------------------------------------------
KEY_EVENT = 0x0001
LEFT_CTRL_PRESSED = 0x0008
VK_RETURN = 0x0D

VK_MAP = {
    "return": VK_RETURN, "enter": VK_RETURN,
    "escape": 0x1B, "esc": 0x1B, "tab": 0x09, "space": 0x20,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
}
for _ch in "abcdefghijklmnopqrstuvwxyz0123456789":
    VK_MAP[_ch] = ord(_ch.upper())


class _CharUnion(ctypes.Union):
    _fields_ = [("UnicodeChar", ctypes.c_wchar), ("AsciiChar", ctypes.c_char)]


class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", _CharUnion),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class _EventUnion(ctypes.Union):
    _fields_ = [("KeyEvent", KEY_EVENT_RECORD), ("_pad", ctypes.c_byte * 16)]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", _EventUnion)]


kernel32.WriteConsoleInputW.argtypes = [wintypes.HANDLE,
                                        ctypes.POINTER(INPUT_RECORD),
                                        wintypes.DWORD,
                                        ctypes.POINTER(wintypes.DWORD)]
kernel32.WriteConsoleInputW.restype = wintypes.BOOL


def _record(key_down: bool, vk: int, char: str, ctrl: bool = False) -> INPUT_RECORD:
    rec = INPUT_RECORD()
    rec.EventType = KEY_EVENT
    key = rec.Event.KeyEvent
    key.bKeyDown = 1 if key_down else 0
    key.wRepeatCount = 1
    key.wVirtualKeyCode = vk
    key.wVirtualScanCode = 0
    # 命名按键（up/escape/tab...）没有对应字符，UnicodeChar 必须是"\0"。
    # 直接赋空字符串会抛 TypeError: one character unicode string expected，
    # 之前只用 return 测过，所以这个坑漏掉了。
    key.uChar.UnicodeChar = char if char else "\x00"
    key.dwControlKeyState = LEFT_CTRL_PRESSED if ctrl else 0
    return rec


def _write_records(handle, records) -> int:
    array = (INPUT_RECORD * len(records))(*records)
    written = wintypes.DWORD()
    if not kernel32.WriteConsoleInputW(handle, array, len(records),
                                       ctypes.byref(written)):
        _fail(3, f"WriteConsoleInput 失败（错误码 {ctypes.get_last_error()}）")
    return written.value


def do_send(pid: int, text: str) -> int:
    """把文本当作键盘输入写进目标控制台。"""
    handle = _attach(pid, "CONIN$")
    records = []
    for ch in text:
        if ch in "\r\n":
            records.append(_record(True, VK_RETURN, "\r"))
            records.append(_record(False, VK_RETURN, "\r"))
            continue
        records.append(_record(True, 0, ch))
        records.append(_record(False, 0, ch))
    if not records:
        return 0
    return _write_records(handle, records)


def do_key(pid: int, name: str) -> int:
    """向目标控制台发送一个命名按键（up/down/left/right/return/ctrl+c...）。"""
    handle = _attach(pid, "CONIN$")
    name = name.strip().lower()

    if name in ("ctrl+c", "ctrlc", "^c"):
        records = [_record(True, 0x43, "\x03", ctrl=True),
                   _record(False, 0x43, "\x03", ctrl=True)]
        return _write_records(handle, records)

    vk = VK_MAP.get(name)
    if vk is None:
        _fail(4, f"不支持的按键: {name}；支持: "
                 f"{', '.join(sorted(VK_MAP))}, ctrl+c")

    char = "\r" if vk == VK_RETURN else (name if len(name) == 1 else "")
    records = [_record(True, vk, char), _record(False, vk, char)]
    return _write_records(handle, records)


def do_info(pid: int) -> str:
    """输出控制台缓冲区信息，用于诊断"读出来是空的"这类问题。"""
    import json

    handle = _attach(pid)
    info = CONSOLE_SCREEN_BUFFER_INFO()
    if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
        _fail(3, f"GetConsoleScreenBufferInfo 失败（错误码 {ctypes.get_last_error()}）")
    return json.dumps({
        "pid": pid,
        "hwnd": int(kernel32.GetConsoleWindow()),
        "buffer_size": [info.dwSize.X, info.dwSize.Y],
        "window": [info.srWindow.Left, info.srWindow.Top,
                   info.srWindow.Right, info.srWindow.Bottom],
        "cursor": [info.dwCursorPosition.X, info.dwCursorPosition.Y],
    }, ensure_ascii=False)


def main() -> int:
    if len(sys.argv) < 3:
        _fail(4, __doc__ or "参数不足")

    action = sys.argv[1].lower()
    try:
        pid = int(sys.argv[2])
    except ValueError:
        _fail(4, f"pid 不是整数: {sys.argv[2]}")

    if action == "hwnd":
        print(do_hwnd(pid))
        return 0

    if action == "info":
        print(do_info(pid))
        return 0

    if action == "read":
        max_lines = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        print(do_read(pid, max_lines))
        return 0

    if action == "send":
        # 文本从 stdin 读，避免命令行引号/编码问题
        text = sys.stdin.buffer.read().decode("utf-8", "replace")
        print(do_send(pid, text))
        return 0

    if action == "key":
        if len(sys.argv) < 4:
            _fail(4, "key 动作需要按键名，例如: key <pid> return")
        print(do_key(pid, sys.argv[3]))
        return 0

    _fail(4, f"未知动作: {action}（支持 read / hwnd / info / send / key）")
    return 4


if __name__ == "__main__":
    sys.exit(main())
