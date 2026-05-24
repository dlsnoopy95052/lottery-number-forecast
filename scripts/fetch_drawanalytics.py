#!/usr/bin/env python3
"""Supplement lottery JSON from DrawAnalytics (recent draws when lotto.net is blocked)."""

import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE = "https://www.drawanalytics.com/api/v1/california"

GAMES = ["fantasy5"]


def fetch_all(game: str, start: str = "2016-01-01") -> list[dict]:
    draws: list[dict] = []
    offset = 0
    limit = 100
    while True:
        url = f"{BASE}/{game}/results?start_date={start}&limit={limit}&offset={offset}"
        raw = json.loads(urllib.request.urlopen(url).read())
        batch = raw["data"]
        if not batch:
            break
        for row in batch:
            d = {
                "draw_date": row["draw_date"],
                "numbers": sorted(row["numbers"]),
            }
            if row.get("bonus_ball") is not None:
                d["bonus"] = row["bonus_ball"]
            draws.append(d)
        total = raw["meta"]["total"]
        offset += limit
        if offset >= total:
            break
    return draws


def main() -> None:
    meta_path = DATA_DIR / "manifest.json"
    manifest = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    for game in GAMES:
        print(game, flush=True)
        draws = fetch_all(game)
        path = DATA_DIR / f"{game}.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        # Do not replace a large historical file with a smaller API snapshot.
        if existing.get("draw_count", 0) > len(draws):
            print(f"  keep existing {existing.get('draw_count', 0)} draws")
            continue

        cfg = {
            "fantasy5": ([1, 39], 5, None),
            "powerball": ([1, 69], 5, [1, 26]),
            "mega_millions": ([1, 70], 5, [1, 25]),
        }[game]
        out = {
            "game": game,
            "name": game.replace("_", " ").title(),
            "main_range": cfg[0],
            "main_count": cfg[1],
            "bonus_range": cfg[2],
            "draw_count": len(draws),
            "oldest": draws[-1]["draw_date"] if draws else None,
            "newest": draws[0]["draw_date"] if draws else None,
            "source": "drawanalytics.com (supplement)",
            "draws": draws,
        }
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"  saved {len(draws)} draws")
        manifest.setdefault("games", {})[game] = {
            "file": path.name,
            "draw_count": len(draws),
            "oldest": out["oldest"],
            "newest": out["newest"],
            "source": out["source"],
        }

    manifest["drawanalytics_sync"] = date.today().isoformat()
    meta_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
