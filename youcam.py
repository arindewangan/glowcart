"""Minimal YouCam AI API (YCE) client.

Docs: https://yce.perfectcorp.com/ai-api
Auth: Authorization: Bearer <API key>
"""
import os
import time

import requests

BASE_URL = os.environ.get("YOUCAM_BASE_URL", "https://yce-api-01.makeupar.com")
API_KEY = os.environ.get("YOUCAM_API_KEY", "")

# 16 documented Skin Diagnosis actions (15 concerns + skin type classifier).
SKIN_CONCERNS_SD = [
    "pore", "acne", "oiliness", "wrinkle", "dark_circle", "eye_bag",
    "moisture", "redness", "sensitivity", "radiance", "firmness",
    "age_spot", "uneven_tone", "texture", "blackhead", "skin_type",
]

MAX_IMAGE_BYTES = 8 * 1024 * 1024


class YouCamError(RuntimeError):
    pass


def has_key() -> bool:
    return bool(os.environ.get("YOUCAM_API_KEY"))


class YouCamClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key if api_key is not None else API_KEY
        if not self.api_key:
            raise YouCamError("no_key: set YOUCAM_API_KEY to call the YouCam API")
        self.base_url = (base_url or BASE_URL).rstrip("/")

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _post(self, path, payload, timeout=30):
        r = requests.post(self.base_url + path, headers=self._headers(),
                          json=payload, timeout=timeout)
        if r.status_code != 200:
            raise YouCamError(f"HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    def upload_image(self, data: bytes, filename: str = "upload.jpg") -> str:
        """Upload bytes via the file/ai-task pre-signed URL flow. Returns file_id."""
        if len(data) > MAX_IMAGE_BYTES:
            raise YouCamError("image too large (max 8 MB)")
        resp = self._post("/s2s/v2.0/file/ai-task", {
            "files": [{"file_name": filename, "file_type": "image"}],
        })
        try:
            f0 = resp["data"]["files"][0]
            file_id = f0["file_id"]
            req = f0["requests"][0]
        except (KeyError, IndexError, TypeError):
            raise YouCamError(f"unexpected upload response shape: {str(resp)[:200]}")
        put = requests.put(req["url"], data=data,
                           headers=req.get("headers") or {}, timeout=60)
        if put.status_code not in (200, 201, 204):
            raise YouCamError(f"upload PUT failed: HTTP {put.status_code}")
        return file_id

    def create_task(self, feature: str, payload: dict) -> str:
        resp = self._post(f"/s2s/v2.0/task/{feature}", payload, timeout=30)
        try:
            return resp["data"]["task_id"]
        except (KeyError, TypeError):
            raise YouCamError(f"unexpected task response shape: {str(resp)[:200]}")

    def poll_task(self, feature: str, task_id: str, interval: int = 3,
                  max_attempts: int = 40) -> dict:
        url = f"{self.base_url}/s2s/v2.0/task/{feature}"
        for _ in range(max_attempts):
            r = requests.get(url, headers=self._headers(),
                             params={"task_id": task_id}, timeout=30)
            if r.status_code != 200:
                raise YouCamError(f"HTTP {r.status_code}: {r.text[:200]}")
            data = r.json().get("data", {})
            status = str(data.get("task_status", "")).lower()
            if status in ("success", "completed", "done"):
                return r.json()
            if status in ("error", "failed"):
                raise YouCamError(f"task failed: {data.get('message', status)}")
            time.sleep(interval)
        raise YouCamError("task did not finish in time")


CONCERN_LABELS = {
    "pore": "Pores", "acne": "Acne", "oiliness": "Oiliness",
    "wrinkle": "Wrinkles", "dark_circle": "Dark circles", "eye_bag": "Eye bags",
    "moisture": "Hydration", "redness": "Redness", "sensitivity": "Sensitivity",
    "radiance": "Radiance", "firmness": "Firmness", "age_spot": "Age spots",
    "uneven_tone": "Uneven tone", "texture": "Texture", "blackhead": "Blackheads",
}


def normalize_skin_report(payload: dict) -> dict:
    """Normalize a YouCam skin-analysis result payload into our report shape."""
    try:
        results = payload["data"]["results"]
        raw_scores = results["scores"]
        skin_type = results.get("skin_type", {}).get("value", "")
    except (KeyError, TypeError, AttributeError):
        raise YouCamError("unexpected skin-analysis result shape")
    scores = []
    for s in raw_scores:
        action = s.get("action", "")
        if action == "skin_type":
            continue
        score = float(s.get("ui_score", s.get("score", 0)))
        scores.append({
            "action": action,
            "label": CONCERN_LABELS.get(action, action.replace("_", " ").title()),
            "score": round(score, 1),
            "stars": round(score / 20, 1),
        })
    return {"mode": "live", "scores": scores, "skin_type": skin_type or "Unknown"}


def extract_tryon_url(payload: dict) -> str | None:
    try:
        results = payload["data"]["results"]
    except (KeyError, TypeError):
        return None
    for key in ("url", "result_url", "image_url"):
        if results.get(key):
            return results[key]
    images = results.get("images") or []
    if images:
        first = images[0]
        return first.get("url") if isinstance(first, dict) else first
    return None
