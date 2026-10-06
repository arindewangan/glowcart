"""Tests for demo_provider.py — honestly-labelled demo mode."""
import demo_provider


def test_demo_report_shape(selfie_bytes):
    r = demo_provider.demo_skin_report(selfie_bytes)
    assert r["mode"] == "demo"
    assert r["demo_label"] == demo_provider.DEMO_LABEL
    # 15 scored concerns (skin_type is reported separately)
    assert len(r["scores"]) == 15
    for s in r["scores"]:
        assert 5.0 <= s["score"] <= 98.0
        assert 0.0 <= s["stars"] <= 5.0
        assert s["label"]
    assert r["skin_type"] in {"Combination", "Oily", "Dry", "Normal", "Sensitive"}


def test_demo_report_deterministic(selfie_bytes):
    r1 = demo_provider.demo_skin_report(selfie_bytes)
    r2 = demo_provider.demo_skin_report(selfie_bytes)
    assert r1["scores"] == r2["scores"]
    assert r1["skin_type"] == r2["skin_type"]


def test_demo_report_differs_per_image():
    r1 = demo_provider.demo_skin_report(b"photo-one" * 100)
    r2 = demo_provider.demo_skin_report(b"photo-two" * 100)
    assert r1["scores"] != r2["scores"]


def test_demo_report_labelled_not_ai(selfie_bytes):
    r = demo_provider.demo_skin_report(selfie_bytes)
    blob = (r["note"] + " ".join(s["label"] for s in r["scores"])).lower()
    assert "simulated" in blob
    assert "not a real ai" in blob


def test_demo_tryon_labelled():
    r = demo_provider.demo_tryon_result()
    assert r["mode"] == "demo"
    assert r["result_url"] is None
    assert "demo mode" in r["note"].lower()
    assert "reference only" in r["note"].lower()
