#!/usr/bin/env python3
"""Build compact frequency summary for the web UI (shared analysis period for all games)."""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

GAME_ORDER = ["superlotto_plus", "fantasy5", "powerball", "mega_millions"]
YEARS_BACK = 10


def period_bounds() -> tuple[str, str]:
    """Use one window for every game: Jan 1 (10 years ago) through newest SuperLotto draw."""
    start = f"{date.today().year - YEARS_BACK}-01-01"
    sl_path = DATA_DIR / "superlotto_plus.json"
    if sl_path.exists():
        sl = json.loads(sl_path.read_text(encoding="utf-8"))
        end = sl.get("newest") or date.today().isoformat()
        if sl.get("oldest"):
            start = max(start, sl["oldest"][:10])
    else:
        end = date.today().isoformat()
    return start, end


def filter_draws(draws: list[dict], start: str, end: str) -> list[dict]:
    return [d for d in draws if start <= d["draw_date"] <= end]


def valid_draw(draw: dict, raw: dict) -> bool:
    """Keep only draws matching the game's current number matrix."""
    main_min, main_max = raw["main_range"]
    nums = draw.get("numbers") or []
    if len(nums) != raw["main_count"]:
        return False
    if not all(main_min <= n <= main_max for n in nums):
        return False
    if raw.get("bonus_range") and "bonus" in draw:
        bmin, bmax = raw["bonus_range"]
        if not (bmin <= draw["bonus"] <= bmax):
            return False
    return True


def summarize(path: Path, period_start: str, period_end: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    draws = [
        d
        for d in filter_draws(raw.get("draws", []), period_start, period_end)
        if valid_draw(d, raw)
    ]
    main_max = raw["main_range"][1]
    bonus_max = raw["bonus_range"][1] if raw.get("bonus_range") else 0
    main_freq = [0] * (main_max + 1)
    bonus_freq = [0] * (bonus_max + 1) if bonus_max else []

    for draw in draws:
        for n in draw["numbers"]:
            main_freq[n] += 1
        if "bonus" in draw and bonus_max:
            bonus_freq[draw["bonus"]] += 1

    oldest = draws[-1]["draw_date"] if draws else None
    newest = draws[0]["draw_date"] if draws else None

    return {
        "game": raw["game"],
        "name": raw["name"],
        "main_range": raw["main_range"],
        "main_count": raw["main_count"],
        "bonus_range": raw.get("bonus_range"),
        "draw_count": len(draws),
        "oldest": oldest,
        "newest": newest,
        "source": raw.get("source") or "https://www.lotto.net (year archives)",
        "main_freq": main_freq,
        "bonus_freq": bonus_freq if bonus_max else None,
        "full_data_oldest": raw.get("oldest"),
        "full_data_newest": raw.get("newest"),
        "full_data_count": raw.get("draw_count"),
    }


def main() -> None:
    period_start, period_end = period_bounds()
    games = {}
    for game_id in GAME_ORDER:
        path = DATA_DIR / f"{game_id}.json"
        if path.exists():
            games[game_id] = summarize(path, period_start, period_end)

    out = {
        "generated": date.today().isoformat(),
        "analysis_period": {
            "start": period_start,
            "end": period_end,
            "label": f"{period_start} to {period_end}",
        },
        "games": games,
    }
    (DATA_DIR / "summary.json").write_text(json.dumps(out), encoding="utf-8")
    js_path = DATA_DIR / "lottery-summary.js"
    js_path.write_text(
        "window.LOTTERY_SUMMARY = " + json.dumps(out) + ";\n",
        encoding="utf-8",
    )

    manifest_path = DATA_DIR / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    manifest["analysis_period"] = out["analysis_period"]
    manifest["generated"] = out["generated"]
    for gid, info in games.items():
        manifest.setdefault("games", {})[gid] = {
            "file": f"{gid}.json",
            "draw_count": info["draw_count"],
            "oldest": info["oldest"],
            "newest": info["newest"],
            "analysis_period": out["analysis_period"],
        }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Period: {period_start} -> {period_end}")
    for gid, g in games.items():
        print(f"  {gid}: {g['draw_count']} draws ({g['oldest']} .. {g['newest']})")
    print(f"Wrote summary.json, lottery-summary.js")


if __name__ == "__main__":
    main()
