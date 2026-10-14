from __future__ import annotations

import asyncio
import time
from pathlib import Path

from ._optional import require
from .errors import AuthenticationError
from .logging import safe_name


class BrowserSession:
    """Async Playwright session with an account-specific persistent profile."""

    def __init__(
        self, profile_root: str | Path, *, platform: str, account: str,
        headless: bool = False, timeout_ms: float = 30000,
    ):
        self.profile = Path(profile_root).resolve() / safe_name(platform) / safe_name(account)
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        if self._playwright is not None:
            raise RuntimeError("BrowserSession is already open")
        api = require("playwright.async_api", "browser")
        self.profile.mkdir(parents=True, exist_ok=True)
        self._playwright = await api.async_playwright().start()
        try:
            self.context = await self._playwright.chromium.launch_persistent_context(
                str(self.profile), headless=self.headless,
            )
            self.context.set_default_timeout(self.timeout_ms)
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            return self
        except BaseException:
            await self.aclose()
            raise

    @property
    def request(self):
        if self.context is None:
            raise RuntimeError("BrowserSession is not open")
        return self.context.request

    async def wait_for_login(self, predicate, *, timeout: float = 120, interval: float = 1, logger=None):
        """Async predicate(page) must validate the site's own logged-in state."""
        if self.page is None:
            raise RuntimeError("BrowserSession is not open")
        if timeout <= 0 or interval <= 0:
            raise ValueError("timeout and interval must be positive")
        deadline = time.monotonic() + timeout
        announced = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AuthenticationError("Login timed out; complete login in the account browser")
            try:
                if await asyncio.wait_for(predicate(self.page), timeout=remaining):
                    return
            except asyncio.TimeoutError:
                raise AuthenticationError("Login check timed out") from None
            if not announced and logger is not None:
                logger.warning("login_required: complete login in the open browser")
                announced = True
            await asyncio.sleep(min(interval, max(0, deadline - time.monotonic())))

    async def aclose(self):
        try:
            if self.context is not None:
                await self.context.close()
        finally:
            try:
                if self._playwright is not None:
                    await self._playwright.stop()
            finally:
                self._playwright = self.context = self.page = None

    async def __aexit__(self, *args):
        await self.aclose()
