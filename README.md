# GlowCart — Your AI Beauty Counter

Snap a selfie. *Know your skin.* Shop what actually works.

GlowCart turns a selfie into a personalized beauty counter: YouCam's
**Skin Analysis API** scores 15 skin concerns, matches them to a sample
skincare catalog, builds an AM/PM routine with an INR total, and the
**Apparel VTO** (`cloth-v4`) renders garments on your own photo.

## What it does

- **Skin analysis** — upload a selfie → YouCam Skin AI scores 15 concerns
  (pores, acne, oiliness, wrinkles, dark circles, moisture, …) and reports
  skin type, with an honestly-labelled demo mode when no API key is set.
- **Matched shopping** — a sample catalog is scored against your worst
  concerns; one top pick per category (cleanser, serum, moisturizer,
  SPF, eye care, treatments).
- **Routine builder** — tick products → AM/PM routine with step order and
  total price in INR.
- **Apparel virtual try-on** — person photo + garment photo → YouCam
  `cloth-v4` renders the outfit on you (live mode) or a clearly-labelled
  placeholder in demo mode.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your YOUCAM_API_KEY
python app.py          # http://127.0.0.1:5050
```

Without a key the app runs in **demo mode**: analysis and try-on are
simulated, deterministic, and clearly labelled — never presented as a
live YouCam scan.

## Static showcase

`demo/index.html` is a self-contained simulated walkthrough, deployed at
https://arindewangan.github.io/glowcart/demo/

## Tests

```bash
python -m pytest tests/ -q   # 36 tests
```

## YouCam API

- Base: `https://yce-api-01.makeupar.com` · auth `Authorization: Bearer <key>`
- Upload: `POST /s2s/v2.0/file/ai-task` → pre-signed PUT
- Skin: `POST /s2s/v2.0/task/skin-analysis` · VTO: `POST /s2s/v2.0/task/cloth-v4`
- Poll: `GET /s2s/v2.0/task/{feature}?task_id=…`

Free 1,000 API units for hackathon participants via the Devpost redeem code.

## License

MIT
