#!/usr/bin/env python3
"""Fetch CA Fantasy 5 via calottery.com API (paginated)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
# Common Fantasy 5 game ids seen in CA Lottery apps / scrapers
GAME_IDS = [7, 9, 10, 11, 17, 20, 24, 25, 26, 27, 28]
CUTOFF = f"{date.today().year - 10}-01-01"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.calottery.com/draw-games/fantasy-5",
    "Origin": "https://www.calottery.com",
}


def try_game_id(gid: int) -> list[dict] | None:
    draws: list[dict] = []
    for page in range(1, 80):
        url = (
            f"https://www.calottery.com/api/DrawGameApi/"
            f"DrawGamePastDrawResults/{gid}/{page}/50"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            raw = json.loads(urllib.request.urlopen(req, timeout=20).read())
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
            return None
        batch = raw.get("PreviousDraws") or []
        if not batch:
            break
        for row in batch:
            wn = row.get("WinningNumbers") or {}
            nums = []
            bonus = None
            for key in sorted(wn.keys(), key=lambda k: int(k) if str(k).isdigit() else 999):
                entry = wn[key]
                n = int(entry["Number"]) if isinstance(entry, dict) else int(entry)
                if isinstance(entry, dict) and entry.get("IsSpecial"):
                    if len(nums) >= 5:
                        bonus = n
                    else:
                        nums.append(n)
                else:
                    nums.append(n)
            if len(nums) == 5 and all(1 <= x <= 39 for x in nums):
                dd = row.get("DrawDate", "")[:10]
                draws.append({"draw_date": dd, "numbers": sorted(nums[:5])})
        time.sleep(0.25)
        if len(batch) < 50:
            break
    if len(draws) < 200:
        return None
    return draws


def main() -> None:
    for gid in GAME_IDS:
        print(f"try game id {gid} ...", flush=True)
        draws = try_game_id(gid)
        if not draws:
            print("  no")
            continue
        draws = [d for d in draws if d["draw_date"] >= CUTOFF]
        seen: set[str] = set()
        merged = []
        for d in sorted(draws, key=lambda x: x["draw_date"], reverse=True):
            if d["draw_date"] in seen:
                continue
            seen.add(d["draw_date"])
            merged.append(d)
        print(f"  got {len(merged)} draws")
        out = {
            "game": "fantasy5",
            "name": "Fantasy 5",
            "main_range": [1, 39],
            "main_count": 5,
            "bonus_range": None,
            "draw_count": len(merged),
            "oldest": merged[-1]["draw_date"] if merged else None,
            "newest": merged[0]["draw_date"] if merged else None,
            "source": "https://www.calottery.com/api",
            "draws": merged,
        }
        (DATA_DIR / "fantasy5.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )
        return
    print("No working game id found.")


if __name__ == "__main__":
    main()
