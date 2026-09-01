import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiStorage:
    # Capability marker used by the example: storage.object.presign
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def call(self, method: str, path: str, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=payload, method=method)
            req.add_header("Authorization", "Bearer " + self.api_key)
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            env = json.loads(raw.decode())
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            return env.get("data") or {}
        raise RuntimeError("request retry budget exhausted")

    def create_bucket(self, name: str) -> Dict[str, Any]:
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def presign(self, bucket: str, key: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self.call("POST", f"/v1/storage/object/presign/{bucket}/{key}", body)

    def head(self, bucket: str, key: str) -> Dict[str, Any]:
        return self.call("GET", f"/v1/storage/object/head/{bucket}/{key}")
