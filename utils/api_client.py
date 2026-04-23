from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import requests

from configs.settings import APISettings


DEFAULT_TIMEOUT = 30


@dataclass
class APIClient:
    settings: APISettings
    timeout: int = DEFAULT_TIMEOUT
    recorder: Any | None = None

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(self.settings.default_headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> requests.Response:
        url = f"{self.settings.base_url}{path}"
        merged_headers = dict(self.session.headers)
        if headers:
            for key, value in headers.items():
                if value is None:
                    merged_headers.pop(key, None)
                else:
                    merged_headers[key] = value
        started_at = perf_counter()
        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=merged_headers,
            params=params,
            json=json,
            timeout=self.timeout,
        )
        elapsed_ms = (perf_counter() - started_at) * 1000
        if self.recorder is not None:
            self.recorder.record(
                service=self.settings.name,
                method=method,
                base_url=self.settings.base_url,
                path=path,
                request_headers=merged_headers,
                params=params,
                json_body=json,
                response=response,
                elapsed_ms=elapsed_ms,
            )
        return response

    def get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request("GET", path, headers=headers, params=params)

    def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> requests.Response:
        return self.request("POST", path, headers=headers, params=params, json=json)

    def patch(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> requests.Response:
        return self.request("PATCH", path, headers=headers, params=params, json=json)

    def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> requests.Response:
        return self.request("DELETE", path, headers=headers, params=params, json=json)
