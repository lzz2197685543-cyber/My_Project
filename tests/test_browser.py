import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ecommerce_automation.browser import BrowserSession
from ecommerce_automation.errors import AuthenticationError


class BrowserTests(unittest.IsolatedAsyncioTestCase):
    def fake_runtime(self):
        page = object()
        context = SimpleNamespace(
            pages=[page], request=object(), set_default_timeout=Mock(),
            close=AsyncMock(), new_page=AsyncMock(),
        )
        runtime = SimpleNamespace(
            chromium=SimpleNamespace(launch_persistent_context=AsyncMock(return_value=context)),
            stop=AsyncMock(),
        )
        api = SimpleNamespace(async_playwright=lambda: SimpleNamespace(start=AsyncMock(return_value=runtime)))
        return api, runtime, context, page

    async def test_persistent_profile_and_context_cleanup(self):
        api, runtime, context, page = self.fake_runtime()
        with tempfile.TemporaryDirectory() as directory:
            with patch("ecommerce_automation.browser.require", return_value=api):
                async with BrowserSession(directory, platform="jst", account="shop1") as browser:
                    expected = Path(directory).resolve() / "jst" / "shop1"
                    runtime.chromium.launch_persistent_context.assert_awaited_once_with(str(expected), headless=False)
                    self.assertIs(browser.page, page)
                    self.assertIs(browser.request, context.request)
                    checks = AsyncMock(side_effect=[False, True])
                    await browser.wait_for_login(checks, timeout=1, interval=0.001)
                context.close.assert_awaited_once()
                runtime.stop.assert_awaited_once()

    async def test_failed_launch_stops_playwright(self):
        api, runtime, context, page = self.fake_runtime()
        runtime.chromium.launch_persistent_context.side_effect = RuntimeError("profile busy")
        with tempfile.TemporaryDirectory() as directory:
            with patch("ecommerce_automation.browser.require", return_value=api):
                with self.assertRaises(RuntimeError):
                    async with BrowserSession(directory, platform="jst", account="shop1"):
                        self.fail("Launch must fail")
        runtime.stop.assert_awaited_once()

    async def test_login_predicate_cannot_exceed_deadline(self):
        api, runtime, context, page = self.fake_runtime()
        async def blocked(page):
            await asyncio.sleep(10)
        with tempfile.TemporaryDirectory() as directory:
            with patch("ecommerce_automation.browser.require", return_value=api):
                async with BrowserSession(directory, platform="jst", account="shop1") as browser:
                    with self.assertRaises(AuthenticationError):
                        await browser.wait_for_login(blocked, timeout=0.01)

    async def test_stop_runs_even_if_context_close_fails(self):
        api, runtime, context, page = self.fake_runtime()
        context.close.side_effect = RuntimeError("browser already crashed")
        with tempfile.TemporaryDirectory() as directory:
            with patch("ecommerce_automation.browser.require", return_value=api):
                with self.assertRaises(RuntimeError):
                    async with BrowserSession(directory, platform="jst", account="shop1"):
                        pass
        runtime.stop.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
