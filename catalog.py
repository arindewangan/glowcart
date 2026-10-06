"""Sample product catalog + recommendation and routine logic.

Illustrative products and indicative INR prices for the hackathon demo.
"""
PRODUCTS = [
    {"id": "cln-gentle", "name": "GlowLab Gentle Foam Cleanser", "category": "Cleanser",
     "price_inr": 499, "size": "150 ml", "for_concerns": ["acne", "oiliness", "sensitivity"],
     "blurb": "pH-balanced daily cleanse that clears pores without stripping.",
     "am": True, "pm": True},
    {"id": "trt-bha", "name": "GlowLab 2% BHA Clarifying Serum", "category": "Treatment",
     "price_inr": 899, "size": "30 ml", "for_concerns": ["pore", "acne", "blackhead", "texture"],
     "blurb": "Salicylic acid unclogs pores and smooths rough texture.",
     "am": False, "pm": True},
    {"id": "trt-niacinamide", "name": "GlowLab 10% Niacinamide Pore Serum", "category": "Serum",
     "price_inr": 749, "size": "30 ml", "for_concerns": ["pore", "oiliness", "redness", "uneven_tone"],
     "blurb": "Refines pores and calms redness, balances oil.",
     "am": True, "pm": True},
    {"id": "mst-hyaluronic", "name": "GlowLab Hyaluronic Dew Moisturizer", "category": "Moisturizer",
     "price_inr": 649, "size": "50 ml", "for_concerns": ["moisture", "firmness", "texture"],
     "blurb": "Weightless hydration that plumps and softens.",
     "am": True, "pm": True},
    {"id": "spf-50", "name": "GlowLab Invisible SPF 50 PA++++", "category": "SPF",
     "price_inr": 699, "size": "50 ml", "for_concerns": ["age_spot", "radiance", "wrinkle"],
     "blurb": "Weightless daily UV shield — the #1 anti-aging step.",
     "am": True, "pm": False},
    {"id": "eye-caffeine", "name": "GlowLab Caffeine Eye Refresh", "category": "Eye care",
     "price_inr": 549, "size": "15 ml", "for_concerns": ["dark_circle", "eye_bag"],
     "blurb": "Depuffs and brightens tired under-eyes.",
     "am": True, "pm": True},
    {"id": "trt-retinol", "name": "GlowLab 0.3% Retinol Night Renewal", "category": "Night treatment",
     "price_inr": 999, "size": "30 ml", "for_concerns": ["wrinkle", "firmness", "uneven_tone", "texture"],
     "blurb": "Overnight renewal for fine lines and firmness (PM only).",
     "am": False, "pm": True},
    {"id": "msk-clay", "name": "GlowLab Pink Clay Pore Mask", "category": "Mask",
     "price_inr": 599, "size": "100 ml", "for_concerns": ["pore", "oiliness", "blackhead"],
     "blurb": "Weekly reset for congested pores.",
     "am": False, "pm": True},
]

BY_ID = {p["id"]: p for p in PRODUCTS}


def get_products():
    return [dict(p) for p in PRODUCTS]


def recommend_for_report(scores, top_n: int = 6):
    """Pick products targeting the worst-scoring concerns, one per category."""
    if not scores:
        return []
    ranked = sorted(scores, key=lambda s: s["score"])  # worst first
    worst = [s["action"] for s in ranked[:5]]
    scored = []
    for p in PRODUCTS:
        hits = [c for c in p["for_concerns"] if c in worst]
        if hits:
            scored.append((len(hits), p))
    scored.sort(key=lambda t: (-t[0], t[1]["price_inr"]))
    picks, seen_cats = [], set()
    for _, p in scored:
        if p["category"] in seen_cats:
            continue
        seen_cats.add(p["category"])
        q = dict(p)
        q["matched_concerns"] = [c for c in p["for_concerns"] if c in worst]
        picks.append(q)
        if len(picks) >= top_n:
            break
    return picks


def build_routine(product_ids):
    """Split chosen products into AM/PM steps with totals."""
    am, pm, total = [], [], 0
    step_am = step_pm = 1
    for pid in product_ids:
        p = BY_ID.get(pid)
        if not p:
            continue
        total += p["price_inr"]
        if p["am"]:
            am.append({"step": step_am, **{k: p[k] for k in ("id", "name", "price_inr")}})
            step_am += 1
        if p["pm"]:
            pm.append({"step": step_pm, **{k: p[k] for k in ("id", "name", "price_inr")}})
            step_pm += 1
    return {"am": am, "pm": pm, "total_inr": total, "count": len(am) + len(pm)}
