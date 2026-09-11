"""Final verification: knowledge-base flow through the real app wiring.

close -> open -> run_powershell_script -> get_terminal_text -> send key -> get_text -> close
"""
import asyncio
import sys
import time

sys.path.insert(0, r"D:\sd14\ai-agent")

from app.code_agent.tools.powershell_tools import get_stdio_powershell_tools  # noqa: E402

REPORT = r"D:\sd14\ai-agent\temp\final_report.txt"
lines = []


def note(m=""):
    lines.append(str(m))


async def main():
    tools = await get_stdio_powershell_tools()
    t = {x.name: x for x in tools}
    note("已注册工具 (%d): %s" % (len(t), ", ".join(sorted(t))))
    note("")

    note("1) close_powershell: " + str(await t["close_powershell"].ainvoke({})))
    note("")

    note("2) open_powershell:")
    note("   " + str(await t["open_powershell"].ainvoke(
        {"working_directory": r"D:\sd14\ai-agent\temp"})))
    note("")

    note("3) run_powershell_script('echo HELLO WORLD 中文'):")
    note("   " + str(await t["run_powershell_script"].ainvoke(
        {"script": "echo HELLO WORLD 中文"})))
    time.sleep(2.0)

    note("4) get_terminal_text  <-- 命令真的执行了吗？")
    txt = str(await t["get_terminal_text"].ainvoke({"max_lines": 40}))
    note("   " + txt.replace("\n", "\n   "))
    note("")

    note("5) send_terminal_keyboard_key('return') 后，再用 get_terminal_text 确认:")
    note("   " + str(await t["send_terminal_keyboard_key"].ainvoke({"key": "return"})))
    time.sleep(1.5)
    note("   " + str(await t["get_terminal_text"].ainvoke({"max_lines": 40})).replace("\n", "\n   "))
    note("")

    note("6) 交互式场景演练：git --version 后发送按键")
    note("   " + str(await t["run_powershell_script"].ainvoke({"script": "Get-Location"})))
    time.sleep(1.5)
    note("   " + str(await t["get_terminal_text"].ainvoke({"max_lines": 40})).replace("\n", "\n   "))
    note("")

    note("7) close_powershell: " + str(await t["close_powershell"].ainvoke({})))


asyncio.run(main())

with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
