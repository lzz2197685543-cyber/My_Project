import asyncio
import os
from pathlib import Path

from ecommerce_automation import ProjectPaths
from ecommerce_automation.browser import BrowserSession


async def main():
    login_url = os.getenv("BROWSER_DEMO_URL")
    if not login_url:
        print("Set BROWSER_DEMO_URL to a real platform login URL before running this example.")
        return
    paths = ProjectPaths(Path(__file__).resolve().parent / "browser_demo")
    async with BrowserSession(
        paths.data / "profiles", platform="temu", account="shop_demo",
        headless=os.getenv("BROWSER_HEADLESS", "0") == "1",
    ) as browser:
        await browser.page.goto(login_url, wait_until="domcontentloaded")

        async def logged_in(page):
            # 替换成平台真实的“已登录”信号；不要用 URL 非空判断。
            return await page.locator("[data-testid='account-menu']").is_visible()

        await browser.wait_for_login(logged_in, timeout=120)
        print("登录态有效，后续业务逻辑放在这里")


if __name__ == "__main__":
    asyncio.run(main())
