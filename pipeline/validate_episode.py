from __future__ import annotations

import json
from pathlib import Path


REQUIRED = (
    "id",
    "title",
    "age_band",
    "language",
    "template",
    "narration",
    "shots",
    "made_for_kids",
)


def load_and_validate(path: Path, *, root: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in REQUIRED:
        if key not in data:
            raise ValueError(f"Episode missing required field: {key}")

    if not data.get("made_for_kids", False):
        raise ValueError("Kids channel episodes must set made_for_kids: true")

    if not isinstance(data["narration"], list) or not data["narration"]:
        raise ValueError("narration must be a non-empty list of strings")

    if not isinstance(data["shots"], list) or not data["shots"]:
        raise ValueError("shots must be a non-empty list")

    bands_path = root / "config" / "age_bands.json"
    bands = json.loads(bands_path.read_text(encoding="utf-8"))
    if data["age_band"] not in bands:
        raise ValueError(f"Unknown age_band: {data['age_band']}")

    band = bands[data["age_band"]]
    text = " ".join(data["narration"]).lower()
    for bad in band.get("forbidden", []):
        if bad.lower() in text:
            raise ValueError(
                f"Age band {data['age_band']} forbids content matching: {bad!r}"
            )

    templates = band.get("templates", [])
    if templates and data["template"] not in templates:
        # warn-level: allow but print later — keep as soft check
        data["_template_warning"] = (
            f"Template {data['template']!r} not in recommended list for "
            f"{data['age_band']}: {templates}"
        )

    data.setdefault("language", "en")
    if data["language"] != "en":
        raise ValueError("English only. Set language to \"en\".")
    return data
