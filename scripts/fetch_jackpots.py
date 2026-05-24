#!/usr/bin/env python3
"""Fetch current jackpot amounts from DrawAnalytics (latest draw per game)."""

from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE = "https://www.drawanalytics.com/api/v1/california"
UA = "CA-Lottery-Suggestion-Tool/1.0 (educational; +local)"

GAMES = {
    "superlotto_plus": "SuperLotto Plus",
    "fantasy5": "Fantasy 5",
    "powerball": "Powerball",
    "mega_millions": "Mega Millions",
}


def fetch_latest(game_id: str) -> dict:
    url = f"{BASE}/{game_id}/latest"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=20).read())
    d = raw["data"]
    return {
        "jackpot": d.get("jackpot"),
        "draw_date": d.get("draw_date"),
        "draw_number": d.get("draw_number"),
    }


def main() -> None:
    jackpots: dict = {}
    for gid, name in GAMES.items():
        try:
            jackpots[gid] = {"name": name, **fetch_latest(gid)}
        except Exception as e:
            jackpots[gid] = {"name": name, "error": str(e)}

    out = {
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "drawanalytics.com/api/v1/california/{game}/latest",
        "note": "Amount from most recent draw result; next-draw jackpot may differ.",
        "games": jackpots,
    }
    (DATA_DIR / "jackpots.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (DATA_DIR / "jackpots.js").write_text(
        "window.LOTTERY_JACKPOTS = " + json.dumps(out) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote jackpots for {len(GAMES)} games -> data/jackpots.json")


if __name__ == "__main__":
    main()
