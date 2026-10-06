"""Shared fixtures for the GlowCart test suite."""
import pytest

import app as app_module


@pytest.fixture()
def client(monkeypatch):
    # Force demo mode: no YouCam key during tests.
    monkeypatch.delenv("YOUCAM_API_KEY", raising=False)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture()
def selfie_bytes():
    # Not a real photo — just bytes; demo mode only needs determinism.
    return b"\xff\xd8\xff" + b"fake-selfie-bytes-for-tests" * 100
