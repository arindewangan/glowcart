"""Tests for catalog.py — matching and routine builder."""
import catalog


def _scores(**kw):
    out = []
    for a, l in [("pore", "Pores"), ("acne", "Acne"), ("oiliness", "Oiliness"),
                 ("wrinkle", "Wrinkles"), ("moisture", "Hydration")]:
        s = {"action": a, "label": l, "score": 80.0, "stars": 4.0}
        if a in kw:
            s["score"] = kw[a]
        out.append(s)
    return out


def test_recommend_targets_worst_concerns():
    recs = catalog.recommend_for_report(_scores(pore=20.0, acne=25.0))
    ids = [r["id"] for r in recs]
    # BHA serum and gentle cleanser both target pore+acne hardest — either order is fine
    assert set(ids[:2]) == {"trt-bha", "cln-gentle"}
    assert recs[0]["matched_concerns"]


def test_recommend_one_per_category():
    recs = catalog.recommend_for_report(_scores(pore=10.0, acne=10.0, oiliness=10.0,
                                                wrinkle=10.0, moisture=10.0), top_n=6)
    cats = [r["category"] for r in recs]
    assert len(cats) == len(set(cats))


def test_recommend_empty_scores():
    assert catalog.recommend_for_report([]) == []


def test_routine_splits_am_pm():
    r = catalog.build_routine(["cln-gentle", "trt-bha", "spf-50", "mst-hyaluronic",
                               "eye-caffeine", "trt-retinol"])
    am_ids = [p["id"] for p in r["am"]]
    pm_ids = [p["id"] for p in r["pm"]]
    assert "spf-50" in am_ids and "spf-50" not in pm_ids
    assert "trt-retinol" in pm_ids and "trt-retinol" not in am_ids  # PM-only
    assert "cln-gentle" in am_ids and "cln-gentle" in pm_ids
    assert r["total_inr"] == sum(catalog.BY_ID[i]["price_inr"] for i in
                                 ["cln-gentle", "trt-bha", "spf-50",
                                  "mst-hyaluronic", "eye-caffeine", "trt-retinol"])
    assert [p["step"] for p in r["am"]] == list(range(1, len(am_ids) + 1))


def test_routine_ignores_unknown_ids():
    r = catalog.build_routine(["nope", "cln-gentle"])
    assert r["count"] == 1


def test_products_have_required_fields():
    for p in catalog.get_products():
        assert {"id", "name", "category", "price_inr", "for_concerns", "blurb"} <= set(p)
        assert p["price_inr"] > 0
