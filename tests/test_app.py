"""Tests for app.py — routes, validation, demo routing."""
import io

import app as app_module


def _img(content=b"x" * 5000, name="selfie.jpg"):
    return (io.BytesIO(content), name)


def test_health_demo(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "mode": "demo"}


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "GlowCart" in html
    assert "Analyze my skin" in html


def test_products(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    d = r.get_json()
    assert d["sample_catalog"] is True
    assert len(d["products"]) >= 8


def test_analyze_demo_end_to_end(client, selfie_bytes):
    r = client.post("/api/analyze", data={"selfie": _img(selfie_bytes)},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    d = r.get_json()
    assert d["mode"] == "demo"
    assert len(d["scores"]) == 15
    assert d["skin_type"]
    assert len(d["recommendations"]) >= 4
    assert "simulated" in d["note"].lower()


def test_analyze_rejects_missing(client):
    r = client.post("/api/analyze", data={}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_analyze_rejects_bad_extension(client):
    r = client.post("/api/analyze", data={"selfie": _img(b"x" * 5000, "evil.txt")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_analyze_rejects_tiny_file(client):
    r = client.post("/api/analyze", data={"selfie": _img(b"tiny")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_tryon_demo(client, selfie_bytes):
    r = client.post("/api/tryon",
                    data={"person": _img(selfie_bytes, "person.jpg"),
                          "garment": _img(b"g" * 6000, "dress.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    d = r.get_json()
    assert d["mode"] == "demo"
    assert d["result_url"] is None
    assert "demo mode" in d["note"].lower()


def test_tryon_rejects_missing_garment(client, selfie_bytes):
    r = client.post("/api/tryon", data={"person": _img(selfie_bytes)},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_routine(client):
    r = client.post("/api/routine", json={"product_ids": ["cln-gentle", "spf-50"]})
    assert r.status_code == 200
    d = r.get_json()
    assert d["total_inr"] == 499 + 699
    assert any(p["id"] == "spf-50" for p in d["am"])


def test_routine_bad_payload(client):
    r = client.post("/api/routine", json={"product_ids": "nope"})
    assert r.status_code == 400
