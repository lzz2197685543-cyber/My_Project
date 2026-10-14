from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Protocol

from .http import HttpClient, RetryPolicy
from .errors import PermanentError


class Notifier(Protocol):
    def send_text(self, text: str) -> None: ...


class LogNotifier:
    def __init__(self, logger):
        self.logger = logger

    def send_text(self, text: str) -> None:
        self.logger.info("notification=%s", text)


class DingTalkNotifier:
    def __init__(self, access_token: str, secret: str, *, timeout: float = 15, transport=None):
        if not access_token or not secret:
            raise ValueError("DingTalk access_token and signing secret are required")
        self._access_token = access_token
        self._secret = secret
        self._client = HttpClient(
            "https://oapi.dingtalk.com", timeout=timeout,
            policy=RetryPolicy(max_attempts=1), transport=transport,
        )

    def send_text(self, text: str, *, at_mobiles=None, is_at_all: bool = False) -> None:
        message = {
            "msgtype": "text",
            "text": {"content": text},
            "at": {"atMobiles": list(at_mobiles or ()), "isAtAll": is_at_all},
        }
        self._send(message)

    def send_markdown(self, title: str, text: str, *, at_mobiles=None, is_at_all: bool = False) -> None:
        message = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"atMobiles": list(at_mobiles or ()), "isAtAll": is_at_all},
        }
        self._send(message)

    def _send(self, message: dict) -> None:
        timestamp = str(int(time.time() * 1000))
        signing_message = f"{timestamp}\n{self._secret}".encode("utf-8")
        signature = base64.b64encode(hmac.new(
            self._secret.encode("utf-8"), signing_message, hashlib.sha256,
        ).digest()).decode("ascii")
        payload = self._client.request_json(
            "POST", "/robot/send", replay_safe=False,
            params={"access_token": self._access_token, "timestamp": timestamp, "sign": signature},
            json=message,
        )
        if not isinstance(payload, dict) or type(payload.get("errcode")) is not int or payload["errcode"] != 0:
            raise PermanentError("DingTalk did not confirm delivery (errcode must be 0)")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def send_dingtalk_text(
    access_token: str,
    secret: str,
    text: str,
    *,
    at_mobiles=None,
    is_at_all: bool = False,
) -> None:
    """Send one signed group-bot text message."""
    with DingTalkNotifier(access_token, secret) as bot:
        bot.send_text(text, at_mobiles=at_mobiles, is_at_all=is_at_all)


def send_dingtalk_markdown(
    access_token: str,
    secret: str,
    title: str,
    text: str,
    *,
    at_mobiles=None,
    is_at_all: bool = False,
) -> None:
    """Send one signed group-bot Markdown message."""
    with DingTalkNotifier(access_token, secret) as bot:
        bot.send_markdown(title, text, at_mobiles=at_mobiles, is_at_all=is_at_all)
