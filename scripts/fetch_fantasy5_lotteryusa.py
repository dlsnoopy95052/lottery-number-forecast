#!/usr/bin/env python3
"""Fetch CA Fantasy 5 from lotteryusa.com paginated year listings."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UA = "CA-Lottery-Suggestion-Tool/1.0 (educational; +local)"

ROW_RE = re.compile(
    r'c-draw-card__draw-date-sub">([^<]+)</span>.*?c-draw-card__ball-list">(.*?)</ul>',
    re.DOTALL,
)
BALL_RE = re.compile(r"c-ball[^>]*>\s*(\d{1,2})\s*<")


def parse_page(html: str) -> list[dict]:
    draws: list[dict] = []
    for date_str, balls_html in ROW_RE.findall(html):
        nums = [int(x) for x in BALL_RE.findall(balls_html)]
        if len(nums) != 5:
            continue
        dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
        draws.append(
            {
                "draw_date": dt.strftime("%Y-%m-%d"),
                "numbers": sorted(nums),
            }
        )
    return draws


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def main() -> None:
    # lotteryusa uses ?year=YYYY on the year archive page
    years = list(range(date.today().year - 10, date.today().year + 1))
    cutoff = f"{years[0]}-01-01"
    all_draws: list[dict] = []

    for year in years:
        url = f"https://www.lotteryusa.com/california/fantasy-5/year?year={year}"
        print(year, flush=True)
        try:
            html = fetch_url(url)
        except urllib.error.HTTPError:
            url = f"https://www.lotteryusa.com/california/fantasy-5/{year}"
            try:
                html = fetch_url(url)
            except Exception as e:
                print(f"  skip: {e}")
                continue
        except Exception as e:
            print(f"  skip: {e}")
            continue
        batch = parse_page(html)
        print(f"  {len(batch)} draws")
        all_draws.extend(batch)
        time.sleep(1.0)

    seen: set[str] = set()
    merged: list[dict] = []
    for d in sorted(all_draws, key=lambda x: x["draw_date"], reverse=True):
        if d["draw_date"] in seen or d["draw_date"] < cutoff:
            continue
        seen.add(d["draw_date"])
        merged.append(d)

    out = {
        "game": "fantasy5",
        "name": "Fantasy 5",
        "main_range": [1, 39],
        "main_count": 5,
        "bonus_range": None,
        "draw_count": len(merged),
        "oldest": merged[-1]["draw_date"] if merged else None,
        "newest": merged[0]["draw_date"] if merged else None,
        "source": "https://www.lotteryusa.com/california/fantasy-5",
        "draws": merged,
    }
    path = DATA_DIR / "fantasy5.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"saved {len(merged)} draws -> {path.name}")


if __name__ == "__main__":
    main()
