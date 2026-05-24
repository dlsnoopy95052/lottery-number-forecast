#!/usr/bin/env python3
"""Fetch CA lottery draw history from lotto.net year archives (last N years)."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

USER_AGENT = "CA-Lottery-Suggestion-Tool/1.0 (educational; +local)"


@dataclass(frozen=True)
class GameConfig:
    id: str
    name: str
    path: str
    main_min: int
    main_max: int
    main_count: int
    bonus_min: int | None = None
    bonus_max: int | None = None
    bonus_class: str | None = None  # e.g. mega-ball, powerball


GAMES: list[GameConfig] = [
    GameConfig(
        id="superlotto_plus",
        name="SuperLotto Plus",
        path="california-super-lotto-plus",
        main_min=1,
        main_max=47,
        main_count=5,
        bonus_min=1,
        bonus_max=27,
        bonus_class="mega-ball",
    ),
    GameConfig(
        id="powerball",
        name="Powerball",
        path="powerball",
        main_min=1,
        main_max=69,
        main_count=5,
        bonus_min=1,
        bonus_max=26,
        bonus_class="powerball",
    ),
    GameConfig(
        id="mega_millions",
        name="Mega Millions",
        path="mega-millions",
        main_min=1,
        main_max=70,
        main_count=5,
        bonus_min=1,
        bonus_max=25,
        bonus_class="mega-ball",
    ),
]

BALL_BLOCK = re.compile(
    r'<ul class="balls">(.*?)</ul>',
    re.DOTALL | re.IGNORECASE,
)
SPAN_NUM = re.compile(r"<span>\s*(\d{1,2})\s*</span>", re.IGNORECASE)
DATE_LINK = re.compile(
    r'href="[^"]*/numbers/([a-z]+-\d{1,2}-\d{4})"',
    re.IGNORECASE,
)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_draw_block(block: str, game: GameConfig) -> dict | None:
    main_nums: list[int] = []
    bonus: int | None = None

    for li in re.finditer(r"<li[^>]*>(.*?)</li>", block, re.DOTALL | re.IGNORECASE):
        chunk = li.group(0)
        m = SPAN_NUM.search(chunk)
        if not m:
            continue
        n = int(m.group(1))
        classes = li.group(0).lower()
        if (
            "power-play" in classes
            or "power_play" in classes
            or "megaplier" in classes
        ):
            continue
        if game.bonus_class and game.bonus_class in classes:
            bonus = n
        elif re.search(r'\bball\s+ball\b', classes) or (
            "ball" in classes
            and game.bonus_class not in classes
            and "mega-ball" not in classes
        ):
            main_nums.append(n)

    if len(main_nums) != game.main_count:
        return None

    main_nums.sort()
    draw: dict = {"numbers": main_nums}
    if game.bonus_min is not None:
        if bonus is None:
            return None
        draw["bonus"] = bonus
    return draw


def parse_year_page(html: str, game: GameConfig, year: int) -> list[dict]:
    draws: list[dict] = []
    date_slugs = DATE_LINK.findall(html)

    for block_html, slug in zip(BALL_BLOCK.findall(html), date_slugs):
        parsed = parse_draw_block(block_html, game)
        if not parsed:
            continue
        # slug like december-28-2024
        parts = slug.split("-")
        if len(parts) < 3:
            continue
        day = int(parts[-2])
        yr = int(parts[-1])
        month_name = "-".join(parts[:-2])
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        month = months.get(month_name)
        if not month:
            continue
        draw_date = f"{yr:04d}-{month:02d}-{day:02d}"
        if yr != year and abs(yr - year) > 1:
            continue
        draws.append({"draw_date": draw_date, **parsed})

    # De-dupe by date
    seen: set[str] = set()
    unique: list[dict] = []
    for d in sorted(draws, key=lambda x: x["draw_date"], reverse=True):
        if d["draw_date"] in seen:
            continue
        seen.add(d["draw_date"])
        unique.append(d)
    return unique


def years_for_window(years_back: int = 10) -> list[int]:
    today = date.today()
    start_year = today.year - years_back
    return list(range(start_year, today.year + 1))


def fetch_game(game: GameConfig, years: list[int]) -> list[dict]:
    all_draws: list[dict] = []
    for year in years:
        url = f"https://www.lotto.net/{game.path}/numbers/{year}"
        print(f"  {game.id} {year} ...", flush=True)
        try:
            html = fetch_html(url)
        except urllib.error.HTTPError as e:
            print(f"    skip {year}: HTTP {e.code}")
            continue
        except urllib.error.URLError as e:
            print(f"    skip {year}: {e}")
            continue
        draws = parse_year_page(html, game, year)
        print(f"    {len(draws)} draws")
        all_draws.extend(draws)
        time.sleep(1.2)

    seen: set[str] = set()
    merged: list[dict] = []
    for d in sorted(all_draws, key=lambda x: x["draw_date"], reverse=True):
        if d["draw_date"] in seen:
            continue
        seen.add(d["draw_date"])
        merged.append(d)
    return merged


def main() -> None:
    years = years_for_window(10)
    cutoff = f"{years[0]}-01-01"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated": date.today().isoformat(),
        "years_fetched": years,
        "cutoff_date": cutoff,
        "source": "https://www.lotto.net (year archives)",
        "games": {},
    }

    for game in GAMES:
        print(game.name)
        draws = fetch_game(game, years)
        draws = [d for d in draws if d["draw_date"] >= cutoff]
        out = {
            "game": game.id,
            "name": game.name,
            "main_range": [game.main_min, game.main_max],
            "main_count": game.main_count,
            "bonus_range": [game.bonus_min, game.bonus_max]
            if game.bonus_min
            else None,
            "draw_count": len(draws),
            "oldest": draws[-1]["draw_date"] if draws else None,
            "newest": draws[0]["draw_date"] if draws else None,
            "source": "https://www.lotto.net (year archives)",
            "draws": draws,
        }
        path = DATA_DIR / f"{game.id}.json"
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        manifest["games"][game.id] = {
            "file": path.name,
            "draw_count": len(draws),
            "oldest": out["oldest"],
            "newest": out["newest"],
        }
        print(f"  saved {len(draws)} draws -> {path.name}")

    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Done.")


if __name__ == "__main__":
    main()
