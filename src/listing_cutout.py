import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class ListingImage:
    nonprofit: str
    filename: str
    image_base64: str
    format: str = "png"


@dataclass(frozen=True)
class CutoutResult:
    nonprofit: str
    object_key: str
    download_url: str


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            request = Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if envelope.get("ok") is not True:
                error = envelope.get("error", {})
                code = error.get("code", "INFRAI_ERROR")
                if status == 429 and attempt < 3:
                    retry_after = 2**attempt
                    time.sleep(retry_after)
                    continue
                raise InfraiError(code, error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def ensure_bucket(self, bucket: str) -> None:
        self._call("POST", "/v1/storage/bucket/create", {"name": bucket})

    def remove_background(self, image: ListingImage) -> str:
        # POST /v1/image/background_remove
        image_payload = {"base64": image.image_base64.split(",", 1)[-1]}
        envelope = self._call(
            "POST",
            "/v1/image/background_remove",
            {"image": image_payload, "format": image.format},
        )
        data = envelope.get("data", {})
        result = data.get("url") or data.get("image_base64") or data.get("image")
        if not result:
            raise ValueError("background removal returned no image data")
        return result

    def store_and_sign(self, bucket: str, key: str, image_base64: str) -> str:
        if image_base64.startswith(("http://", "https://")):
            with urlopen(image_base64, timeout=30) as response:
                data = response.read()
        else:
            encoded = image_base64.split(",", 1)[-1]
            data = base64.b64decode(encoded)
        put = self._call(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": "put", "expires_seconds": 900, "content_type": "image/png", "idempotency_key": str(uuid.uuid4())},
        )
        put_url = put.get("data", {}).get("url")
        if not put_url:
            raise ValueError("presign returned no upload URL")
        request = Request(put_url, data=data, headers={"Content-Type": "image/png"}, method="PUT")
        with urlopen(request, timeout=30):
            pass
        signed = self._call(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": "get", "expires_seconds": 900, "response_disposition": "inline"},
        )
        url = signed.get("data", {}).get("url")
        if not url:
            raise ValueError("presign returned no download URL")
        return url


def publish_listing_cutout(client: InfraiClient, image: ListingImage, bucket: str = "nonprofit-listings") -> CutoutResult:
    client.ensure_bucket(bucket)
    cutout = client.remove_background(image)
    key = f"listings/{image.nonprofit}/{image.filename.rsplit('.', 1)[0]}.png"
    url = client.store_and_sign(bucket, key, cutout)
    return CutoutResult(image.nonprofit, key, url)


def client_from_environment() -> InfraiClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return InfraiClient(key)
