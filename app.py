"""GlowCart — Flask app wiring YouCam Skin AI + Apparel VTO into a beauty counter."""
import os

from flask import Flask, jsonify, render_template, request

import catalog
import demo_provider
import youcam
from youcam import YouCamClient, YouCamError

app = Flask(__name__)

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}
MAX_UPLOAD = 8 * 1024 * 1024  # 8 MB


def _client_or_none():
    if youcam.has_key():
        return YouCamClient()
    return None


def _validate_image(field):
    f = request.files.get(field)
    if f is None or not f.filename:
        return None, (f"Missing file: {field}", 400)
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return None, ("Only JPG/PNG images are accepted.", 400)
    data = f.read()
    if len(data) < 1024:
        return None, ("That file looks too small to be a photo.", 400)
    if len(data) > MAX_UPLOAD:
        return None, ("Image is too large (max 8 MB).", 400)
    return (data, f.filename), None


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "mode": "live" if youcam.has_key() else "demo"})


@app.get("/api/products")
def products():
    return jsonify({"sample_catalog": True, "products": catalog.get_products()})


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    (img, err) = _validate_image("selfie")
    if err:
        return jsonify({"error": err[0]}), err[1]
    data, filename = img
    client = _client_or_none()
    if client is None:
        report = demo_provider.demo_skin_report(data)
    else:
        try:
            file_id = client.upload_image(data, filename)
            task_id = client.create_task("skin-analysis", {
                "src_file_id": file_id,
                "dst_actions": youcam.SKIN_CONCERNS_SD,
            })
            payload = client.poll_task("skin-analysis", task_id)
            report = youcam.normalize_skin_report(payload)
            report["mode"] = "live"
            report["note"] = "Analyzed live with the YouCam Skin AI API."
        except YouCamError as e:
            return jsonify({"error": f"YouCam API error: {e}"}), 502
    report["recommendations"] = catalog.recommend_for_report(report["scores"])
    return jsonify(report)


@app.post("/api/tryon")
def tryon():
    (person, err) = _validate_image("person")
    if err:
        return jsonify({"error": err[0]}), err[1]
    (garment, err) = _validate_image("garment")
    if err:
        return jsonify({"error": err[0]}), err[1]
    client = _client_or_none()
    if client is None:
        return jsonify(demo_provider.demo_tryon_result())
    try:
        person_id = client.upload_image(*person)
        garment_id = client.upload_image(*garment)
        task_id = client.create_task("cloth-v4", {
            "src_file_id": person_id,
            "cloth_file_id": garment_id,
        })
        payload = client.poll_task("cloth-v4", task_id, interval=5, max_attempts=36)
        url = youcam.extract_tryon_url(payload)
        return jsonify({
            "mode": "live",
            "result_url": url,
            "note": "Rendered live with YouCam cloth-v4. AI-generated imagery is for reference only.",
        })
    except YouCamError as e:
        return jsonify({"error": f"YouCam API error: {e}"}), 502


@app.post("/api/routine")
def routine():
    body = request.get_json(force=True, silent=True) or {}
    ids = body.get("product_ids")
    if not isinstance(ids, list):
        return jsonify({"error": "product_ids must be a list"}), 400
    return jsonify(catalog.build_routine([str(i) for i in ids]))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
