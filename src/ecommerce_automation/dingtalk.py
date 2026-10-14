"""Callable helpers for DingTalk group bots and multidimensional tables."""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Iterable

from ._optional import require


class DingTalkTokenProvider:
    """Fetch and cache an app access token in memory for this provider instance."""

    def __init__(self, client_id: str, client_secret: str, *, timeout: float = 15, client: Any = None):
        if not client_id or not client_secret:
            raise ValueError("client_id and client_secret are required")
        self._httpx = require("httpx", "dingtalk")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._client = client or self._httpx.Client(timeout=timeout)
        self._token: str | None = None
        self._expires_at = 0.0

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if not force_refresh and self._token and time.monotonic() < self._expires_at - 300:
            return self._token
        try:
            response = self._client.get(
                "https://oapi.dingtalk.com/gettoken",
                params={"appkey": self.client_id, "appsecret": self.client_secret},
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            raise RuntimeError("DingTalk token request failed") from None
        if not isinstance(payload, dict) or payload.get("errcode") != 0 or not payload.get("access_token"):
            raise RuntimeError("DingTalk did not return a valid access token")
        self._token = str(payload["access_token"])
        self._expires_at = time.monotonic() + float(payload.get("expires_in", 7200))
        return self._token

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DingTalkTokenProvider":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class DingTalkTableClient:
    """Upload records to a DingTalk multidimensional table in sequential batches.

    Network errors are not automatically retried because a write may already have
    reached DingTalk. Resolve the batch outcome before submitting it again.
    """

    def __init__(
        self,
        base_id: str,
        sheet_id: str | None,
        operator_id: str,
        access_token: str | Callable[[], str] | DingTalkTokenProvider,
        *,
        timeout: float = 30,
        client: Any = None,
        progress: Callable[[str], None] | None = print,
    ):
        if not base_id or not operator_id:
            raise ValueError("base_id and operator_id are required")
        self._httpx = require("httpx", "dingtalk")
        self.base_id = base_id
        self.sheet_id = sheet_id
        self.operator_id = operator_id
        self._access_token = access_token
        self._progress = progress
        self._client = client or self._httpx.Client(timeout=timeout)
        self._base_url = f"https://api.dingtalk.com/v1.0/notable/bases/{base_id}"
        self._sheet_url = f"{self._base_url}/sheets/{sheet_id}" if sheet_id else None

    def upload_records(
        self,
        records: Iterable[dict[str, Any]],
        *,
        batch_size: int = 100,
        delay: float = 0,
    ) -> list[dict[str, Any]]:
        rows = list(records)
        if batch_size < 1 or delay < 0:
            raise ValueError("batch_size must be positive and delay must be non-negative")
        if any(not isinstance(row, dict) for row in rows):
            raise TypeError("records must be dictionaries")
        results = []
        total_batches = (len(rows) + batch_size - 1) // batch_size
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            batch_number = start // batch_size + 1
            try:
                payload = self._request(
                    "POST", f"{self._require_sheet_url()}/records",
                    json={"records": [{"fields": item} for item in batch]},
                )
            except Exception as error:
                message = f"多维表上传失败：第 {batch_number}/{total_batches} 批，记录 {start + 1}-{start + len(batch)}：{error}"
                self._report(message)
                raise RuntimeError(message) from error
            results.append(payload)
            self._report(
                f"多维表上传成功：第 {batch_number}/{total_batches} 批，"
                f"记录 {start + 1}-{start + len(batch)}，共 {len(batch)} 条"
            )
            if delay and start + batch_size < len(rows):
                time.sleep(delay)
        return results

    def list_sheets(self) -> list[dict[str, Any]]:
        """Return all sheets (tables) under this multidimensional-table document."""
        payload = self._request("GET", f"{self._base_url}/sheets")
        sheets = payload.get("sheets", payload.get("value", payload.get("data", [])))
        if isinstance(sheets, dict):
            sheets = sheets.get("sheets", sheets.get("value", []))
        if not isinstance(sheets, list):
            raise RuntimeError("DingTalk returned an unexpected sheets response")
        return sheets

    def query_records(
        self,
        *,
        max_results: int = 100,
        next_token: str | None = None,
        filter: str | None = None,
        sort: list[dict[str, Any]] | None = None,
        field_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query one page of records from the configured sheet."""
        if not 1 <= max_results <= 1000:
            raise ValueError("max_results must be between 1 and 1000")
        params: dict[str, Any] = {"maxResults": max_results}
        if next_token:
            params["nextToken"] = next_token
        if filter is not None:
            params["filter"] = filter
        if sort is not None:
            params["sort"] = json.dumps(sort, ensure_ascii=False)
        if field_names is not None:
            params["fieldNames"] = json.dumps(field_names, ensure_ascii=False)
        return self._request(
            "GET", f"{self._require_sheet_url()}/records", params=params,
        )

    def delete_records(
        self,
        record_ids: Iterable[str],
        *,
        batch_size: int = 100,
        delay: float = 0,
    ) -> list[dict[str, Any]]:
        """Delete record IDs in batches and report each completed batch."""
        ids = list(record_ids)
        if not ids or any(not item for item in ids):
            raise ValueError("record_ids must contain at least one non-empty ID")
        if batch_size < 1 or delay < 0:
            raise ValueError("batch_size must be positive and delay must be non-negative")
        results = []
        total_batches = (len(ids) + batch_size - 1) // batch_size
        for start in range(0, len(ids), batch_size):
            batch = ids[start:start + batch_size]
            batch_number = start // batch_size + 1
            try:
                result = self._request(
                    "POST", f"{self._require_sheet_url()}/records/delete",
                    json={"recordIds": batch},
                )
                self._require_delete_success(result, "删除记录")
            except Exception as error:
                message = f"多维表删除失败：第 {batch_number}/{total_batches} 批，记录 {start + 1}-{start + len(batch)}：{error}"
                self._report(message)
                raise RuntimeError(message) from error
            results.append(result)
            self._report(
                f"多维表删除成功：第 {batch_number}/{total_batches} 批，"
                f"记录 {start + 1}-{start + len(batch)}，共 {len(batch)} 条"
            )
            if delay and start + batch_size < len(ids):
                time.sleep(delay)
        return results

    def delete_sheet(self, sheet_id: str) -> dict[str, Any]:
        """Delete a sheet under this document. This operation cannot be undone."""
        if not sheet_id:
            raise ValueError("sheet_id is required")
        result = self._request("DELETE", f"{self._base_url}/sheets/{sheet_id}")
        self._require_delete_success(result, "删除工作表")
        return result

    @staticmethod
    def _require_delete_success(payload: dict[str, Any], operation: str) -> None:
        if payload.get("success") is not True:
            raise RuntimeError(f"钉钉{operation}失败：{payload}")

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        token = self._get_access_token()
        params = {"operatorId": self.operator_id, **kwargs.pop("params", {})}
        response = self._client.request(
            method,
            url,
            params=params,
            headers={"x-acs-dingtalk-access-token": token},
            **kwargs,
        )
        # print("RAW response:", response.text)
        if response.status_code == 401 and isinstance(self._access_token, DingTalkTokenProvider):
            token = self._access_token.get_access_token(force_refresh=True)
            response = self._client.request(
                method,
                url,
                params=params,
                headers={"x-acs-dingtalk-access-token": token},
                **kwargs,
            )
        try:
            response.raise_for_status()
            payload = response.json() if response.content else {}
        except Exception as error:
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:500]
            status = getattr(response, "status_code", "unknown")
            raise RuntimeError(f"HTTP {status}: {detail}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("DingTalk returned an unexpected table response")
        return payload

    def _report(self, message: str) -> None:
        if self._progress is not None:
            self._progress(message)

    def _get_access_token(self) -> str:
        if isinstance(self._access_token, DingTalkTokenProvider):
            return self._access_token.get_access_token()
        token = self._access_token() if callable(self._access_token) else self._access_token
        if not token:
            raise ValueError("A DingTalk access token is required")
        return token

    def _require_sheet_url(self) -> str:
        if not self._sheet_url:
            raise ValueError("sheet_id is required for this operation")
        return self._sheet_url

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DingTalkTableClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def upload_dingtalk_records(
    records: Iterable[dict[str, Any]],
    *,
    client_id: str,
    client_secret: str,
    base_id: str,
    sheet_id: str,
    operator_id: str,
    batch_size: int = 100,
    delay: float = 0,
    progress: Callable[[str], None] | None = print,
) -> list[dict[str, Any]]:
    """Fetch an app token, upload records, and close both clients automatically."""
    with DingTalkTokenProvider(client_id, client_secret) as token:
        with DingTalkTableClient(base_id, sheet_id, operator_id, token, progress=progress) as table:
            return table.upload_records(records, batch_size=batch_size, delay=delay)


def list_dingtalk_sheets(
    *, client_id: str, client_secret: str, base_id: str, operator_id: str,
) -> list[dict[str, Any]]:
    """List all sheets under a DingTalk multidimensional-table document."""
    with DingTalkTokenProvider(client_id, client_secret) as token:
        with DingTalkTableClient(base_id, None, operator_id, token) as table:
            return table.list_sheets()


def query_dingtalk_records(
    *, client_id: str, client_secret: str, base_id: str, sheet_id: str, operator_id: str,
    max_results: int = 100, next_token: str | None = None,
    filter: str | None = None, sort: list[dict[str, Any]] | None = None,
    field_names: list[str] | None = None,
) -> dict[str, Any]:
    """Query one page of records and close HTTP clients automatically."""
    with DingTalkTokenProvider(client_id, client_secret) as token:
        with DingTalkTableClient(base_id, sheet_id, operator_id, token) as table:
            return table.query_records(
                max_results=max_results, next_token=next_token, filter=filter,
                sort=sort, field_names=field_names,
            )


def delete_dingtalk_records(
    record_ids: Iterable[str], *, client_id: str, client_secret: str,
    base_id: str, sheet_id: str, operator_id: str,
    batch_size: int = 100, delay: float = 0,
) -> list[dict[str, Any]]:
    """Delete selected records and close HTTP clients automatically."""
    with DingTalkTokenProvider(client_id, client_secret) as token:
        with DingTalkTableClient(base_id, sheet_id, operator_id, token) as table:
            return table.delete_records(record_ids, batch_size=batch_size, delay=delay)


def delete_dingtalk_sheet(
    target_sheet_id: str, *, client_id: str, client_secret: str,
    base_id: str, operator_id: str,
) -> dict[str, Any]:
    """Delete a sheet from a multidimensional-table document."""
    with DingTalkTokenProvider(client_id, client_secret) as token:
        with DingTalkTableClient(base_id, None, operator_id, token) as table:
            return table.delete_sheet(target_sheet_id)
