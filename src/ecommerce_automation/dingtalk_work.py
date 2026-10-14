"""DingTalk work notifications and user ID lookup helpers."""

from __future__ import annotations

from typing import Any, Iterable

from .dingtalk import DingTalkTokenProvider
from ._optional import require


class DingTalkWorkNotifier:
    """Send DingTalk work notifications and look up user/operator IDs."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        agent_id: str | None = None,
        *,
        timeout: float = 10,
        client: Any = None,
    ):
        self._httpx = require("httpx", "dingtalk")
        self.agent_id = str(agent_id) if agent_id is not None else None
        self.timeout = timeout
        self._token = DingTalkTokenProvider(client_id, client_secret, timeout=timeout)
        self._client = client or self._httpx.Client(timeout=timeout)

    def send_text(self, user_ids: str | Iterable[str], title: str, text: str) -> dict[str, Any]:
        """Send a text work notification to one or more DingTalk user IDs."""
        if not self.agent_id:
            raise ValueError("agent_id is required to send a work notification")
        if isinstance(user_ids, str):
            user_ids = [user_ids]
        ids = [str(user_id) for user_id in user_ids]
        if not ids or any(not user_id for user_id in ids):
            raise ValueError("user_ids must contain at least one non-empty user ID")
        return self._post(
            "/topapi/message/corpconversation/asyncsend_v2",
            {
                "agent_id": int(self.agent_id),
                "userid_list": ",".join(ids),
                "msg": {"msgtype": "text", "text": {"content": f"{title}\n{text}"}},
            },
        )

    def get_user_id_by_mobile(self, mobile: str) -> str:
        """Return a DingTalk userid for a mobile number."""
        if not mobile:
            raise ValueError("mobile is required")
        payload = self._post("/topapi/v2/user/getbymobile", {"mobile": mobile})
        user_id = payload.get("result", {}).get("userid")
        if not user_id:
            raise RuntimeError(f"DingTalk response did not contain a userid: {payload}")
        return str(user_id)

    def get_union_id_by_user_id(self, user_id: str) -> str:
        """Return the unionId (operatorId for multidimensional tables) for a userid."""
        if not user_id:
            raise ValueError("user_id is required")
        payload = self._post("/topapi/v2/user/get", {"userid": user_id})
        union_id = payload.get("result", {}).get("unionid")
        if not union_id:
            raise RuntimeError(f"DingTalk response did not contain a unionid: {payload}")
        return str(union_id)

    def get_operator_id_by_mobile(self, mobile: str) -> str:
        """Resolve mobile -> userid -> unionId/operatorId."""
        return self.get_union_id_by_user_id(self.get_user_id_by_mobile(mobile))

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(
            f"https://oapi.dingtalk.com{path}",
            params={"access_token": self._token.get_access_token()},
            json=body,
        )
        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:500]
            raise RuntimeError(f"DingTalk request failed (HTTP {response.status_code}): {detail}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("DingTalk returned an unexpected response")
        if payload.get("errcode") != 0:
            raise RuntimeError(f"DingTalk request failed: {payload}")
        return payload

    def close(self) -> None:
        self._client.close()
        self._token.close()

    def __enter__(self) -> "DingTalkWorkNotifier":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def send_dingtalk_work_text(
    user_ids: str | Iterable[str],
    title: str,
    text: str,
    *,
    client_id: str,
    client_secret: str,
    agent_id: str,
) -> dict[str, Any]:
    """Send one work notification and close HTTP clients automatically."""
    with DingTalkWorkNotifier(client_id, client_secret, agent_id) as notifier:
        return notifier.send_text(user_ids, title, text)


def get_dingtalk_user_id_by_mobile(
    mobile: str, *, client_id: str, client_secret: str,
) -> str:
    with DingTalkWorkNotifier(client_id, client_secret) as notifier:
        return notifier.get_user_id_by_mobile(mobile)


def get_dingtalk_union_id_by_user_id(
    user_id: str, *, client_id: str, client_secret: str,
) -> str:
    with DingTalkWorkNotifier(client_id, client_secret) as notifier:
        return notifier.get_union_id_by_user_id(user_id)


def get_dingtalk_operator_id_by_mobile(
    mobile: str, *, client_id: str, client_secret: str,
) -> str:
    with DingTalkWorkNotifier(client_id, client_secret) as notifier:
        return notifier.get_operator_id_by_mobile(mobile)
