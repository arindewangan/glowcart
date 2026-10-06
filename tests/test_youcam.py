"""Tests for youcam.py — provider layer with mocked HTTP.

No real network calls: every HTTP interaction is monkeypatched.
"""
import pytest
import requests

import youcam
from youcam import YouCamClient, YouCamError


class _FakeResp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def _client():
    return YouCamClient(api_key="test-key", base_url="https://example.test")


def test_no_key_raises():
    with pytest.raises(YouCamError, match="no_key"):
        YouCamClient(api_key="")


def test_has_key(monkeypatch):
    monkeypatch.delenv("YOUCAM_API_KEY", raising=False)
    assert youcam.has_key() is False
    monkeypatch.setenv("YOUCAM_API_KEY", "k")
    assert youcam.has_key() is True


def test_upload_image_flow(monkeypatch):
    posts, puts = [], []

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append((url, json))
        return _FakeResp(200, {
            "data": {"files": [{
                "file_id": "fid-123",
                "requests": [{"method": "PUT", "url": "https://put.example/x",
                              "headers": {}}],
            }]}
        })

    def fake_put(url, data=None, headers=None, timeout=None):
        puts.append((url, data))
        return _FakeResp(200)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "put", fake_put)
    c = _client()
    fid = c.upload_image(b"imgbytes", "selfie.jpg")
    assert fid == "fid-123"
    assert posts[0][0].endswith("/s2s/v2.0/file/ai-task")
    assert puts[0][0] == "https://put.example/x"
    assert puts[0][1] == b"imgbytes"
    assert posts[0][1] is not None


def test_upload_sends_bearer_auth(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["headers"] = headers
        return _FakeResp(200, {"data": {"files": []}})

    monkeypatch.setattr(requests, "post", fake_post)
    c = _client()
    with pytest.raises(YouCamError):
        c.upload_image(b"x")
    assert captured["headers"]["Authorization"] == "Bearer test-key"


def test_upload_rejects_oversize():
    c = _client()
    with pytest.raises(YouCamError, match="too large"):
        c.upload_image(b"x" * (youcam.MAX_IMAGE_BYTES + 1))


def test_create_task_returns_task_id(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        assert url.endswith("/s2s/v2.0/task/skin-analysis")
        assert json["dst_actions"]
        return _FakeResp(200, {"data": {"task_id": "task-9"}})

    monkeypatch.setattr(requests, "post", fake_post)
    c = _client()
    assert c.create_task("skin-analysis", {"dst_actions": ["pore"]}) == "task-9"


def test_poll_success(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(params)
        status = "running" if len(calls) < 2 else "success"
        return _FakeResp(200, {"data": {"task_status": status, "results": {"ok": True}}})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(youcam.time, "sleep", lambda s: None)
    c = _client()
    data = c.poll_task("skin-analysis", "task-9", interval=0, max_attempts=3)
    assert data["data"]["task_status"] == "success"
    assert calls[0]["task_id"] == "task-9"


def test_poll_error_raises(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return _FakeResp(200, {"data": {"task_status": "error", "message": "bad face"}})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(youcam.time, "sleep", lambda s: None)
    c = _client()
    with pytest.raises(YouCamError, match="task failed"):
        c.poll_task("skin-analysis", "t", interval=0, max_attempts=2)


def test_poll_timeout_raises(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return _FakeResp(200, {"data": {"task_status": "running"}})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(youcam.time, "sleep", lambda s: None)
    c = _client()
    with pytest.raises(YouCamError, match="did not finish"):
        c.poll_task("skin-analysis", "t", interval=0, max_attempts=2)


def test_http_error_raises(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResp(401, {}, text="unauthorized")

    monkeypatch.setattr(requests, "post", fake_post)
    c = _client()
    with pytest.raises(YouCamError, match="HTTP 401"):
        c._post("/s2s/v2.0/file/ai-task", {})


def test_normalize_skin_report():
    payload = {"data": {"results": {
        "scores": [
            {"action": "pore", "ui_score": 52},
            {"action": "acne", "ui_score": 61.5},
        ],
        "skin_type": {"value": "Combination"},
    }}}
    rep = youcam.normalize_skin_report(payload)
    assert rep["skin_type"] == "Combination"
    assert rep["scores"][0] == {"action": "pore", "label": "Pores",
                                "score": 52.0, "stars": 2.6}
    assert rep["scores"][1]["label"] == "Acne"


def test_normalize_bad_shape_raises():
    with pytest.raises(YouCamError):
        youcam.normalize_skin_report({"nope": True})


def test_extract_tryon_url():
    assert youcam.extract_tryon_url(
        {"data": {"results": {"url": "https://cdn.example/r.jpg"}}}
    ) == "https://cdn.example/r.jpg"
    assert youcam.extract_tryon_url({"data": {}}) is None


def test_skin_concerns_count():
    # 16 documented SD actions (15 concerns + skin type)
    assert len(youcam.SKIN_CONCERNS_SD) == 16
