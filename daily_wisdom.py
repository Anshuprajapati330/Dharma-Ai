import json
import os
import random
from functools import lru_cache


DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@lru_cache(maxsize=1)
def _load_wisdom_items():
    items = []
    if not os.path.isdir(DATA_FOLDER):
        return tuple(items)

    for filename in sorted(os.listdir(DATA_FOLDER)):
        if not filename.endswith(".json"):
            continue

        try:
            with open(os.path.join(DATA_FOLDER, filename), "r", encoding="utf-8") as data_file:
                records = json.load(data_file)
        except (OSError, json.JSONDecodeError):
            continue

        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            continue

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue

            english = str(record.get("translation") or record.get("ethical_principle") or "").strip()
            if not english:
                continue

            source = str(record.get("source") or os.path.splitext(filename)[0])
            chapter = record.get("chapter")
            verse = record.get("verse")
            title = record.get("title")
            if chapter is not None and verse is not None:
                reference = f"{source}, Chapter {chapter}, Verse {verse}"
            elif title:
                reference = f"{source} - {title}"
            else:
                reference = source

            items.append({
                "key": f"{filename}:{index}",
                "english": english,
                "hindi": str(record.get("hindi_meaning") or english).strip(),
                "reference": reference,
            })

    return tuple(items)


def get_daily_wisdom(previous=None):
    items = _load_wisdom_items()

    if not items:
        return {
            "key": "fallback",
            "english": "Act with clarity and compassion.",
            "hindi": "स्पष्टता और करुणा के साथ कर्म करें।",
            "reference": "Dharma-AI",
        }

    previous_key = previous.get("key") if isinstance(previous, dict) else None
    choices = [item for item in items if item["key"] != previous_key] or list(items)
    return dict(random.choice(choices))
