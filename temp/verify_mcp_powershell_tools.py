"""End-to-end verification through the REAL app wiring.

Uses app.code_agent.tools.powershell_tools.get_stdio_powershell_tools(),
exactly what app/code_agent/agent/code_agent.py loads.
"""
import asyncio
import os
import shutil
import sys
import time

sys.path.insert(0, r"D:\sd14\ai-agent")

from app.code_agent.tools.powershell_tools import get_stdio_powershell_tools  # noqa: E402

TARGET = r"D:\sd14\ai-agent\temp\probe_verify"


async def main():
    t0 = time.time()
    tools = await get_stdio_powershell_tools()
    print(f"[get_tools] {time.time()-t0:.2f}s -> {len(tools)} tools", flush=True)
    for t in tools:
        print("   -", t.name, flush=True)

    tool = {t.name: t for t in tools}["execute_powershell_command"]

    for i in range(1, 4):
        shutil.rmtree(TARGET, ignore_errors=True)
        t0 = time.time()
        try:
            res = await asyncio.wait_for(
                tool.ainvoke({"command": f'New-Item -ItemType Directory -Path "{TARGET}" -Force | Out-Null; Write-Output "run-{i}-ok"'}),
                timeout=60,
            )
            dt = time.time() - t0
            print(f"[call {i}] {dt:6.2f}s dir_created={os.path.isdir(TARGET)} result={str(res)[:90]!r}",
                  flush=True)
        except asyncio.TimeoutError:
            print(f"[call {i}] *** TIMEOUT >60s ***", flush=True)
        except Exception as e:
            print(f"[call {i}] ERROR {type(e).__name__}: {e}", flush=True)

    # non-capturing path used by open_powershell (must not hang either)
    print("\n[check] capture_output=False path (run_powershell_command directly)", flush=True)


asyncio.run(main())
