"""Honestly-labelled demo mode: deterministic simulated results.

Used when no YouCam API key is configured. Every response carries
mode="demo" and a clear note that results are simulated — never
presented as a live YouCam scan.
"""
import hashlib

from youcam import CONCERN_LABELS

DEMO_LABEL = "demo"

CONCERN_ORDER = [a for a in CONCERN_LABELS]  # 15 concerns, stable order
SKIN_TYPES = ["Combination", "Oily", "Dry", "Normal", "Sensitive"]


def _seeded_floats(seed: bytes, n: int):
    h = hashlib.sha256(seed).digest()
    out = []
    for i in range(n):
        chunk = h[(i * 4) % len(h):(i * 4) % len(h) + 4]
        out.append(int.from_bytes(chunk, "big") / 0xFFFFFFFF)
    return out


def demo_skin_report(image_bytes: bytes) -> dict:
    vals = _seeded_floats(image_bytes, len(CONCERN_ORDER))
    scores = []
    for action, v in zip(CONCERN_ORDER, vals):
        score = round(5 + v * 93, 1)  # 5..98 deterministic
        scores.append({
            "action": action,
            "label": CONCERN_LABELS[action],
            "score": score,
            "stars": round(score / 20, 1),
        })
    skin_type = SKIN_TYPES[int(_seeded_floats(image_bytes, 1)[0] * len(SKIN_TYPES))
                           % len(SKIN_TYPES)]
    return {
        "mode": DEMO_LABEL,
        "demo_label": DEMO_LABEL,
        "scores": scores,
        "skin_type": skin_type,
        "note": ("Demo mode — simulated analysis for illustration only, "
                 "not a real AI scan. Add a YouCam API key for live results."),
    }


def demo_tryon_result() -> dict:
    return {
        "mode": DEMO_LABEL,
        "result_url": None,
        "note": ("Demo mode — add a YouCam API key to render a live virtual "
                 "try-on. This placeholder is for reference only."),
    }
