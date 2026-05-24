#!/usr/bin/env python3
"""Fetch Powerball + Mega Millions history (lotto.net) without re-downloading SuperLotto."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_ca_lottery import (  # noqa: E402
    DATA_DIR,
    GAMES,
    date,
    fetch_game,
    json,
    years_for_window,
)

FETCH_IDS = {"mega_millions"}


def main() -> None:

    years = years_for_window(10)
    cutoff = f"{years[0]}-01-01"
    manifest_path = DATA_DIR / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )

    for game in GAMES:
        if game.id not in FETCH_IDS:
            continue
        print(game.name)
        draws = fetch_game(game, years)
        draws = [d for d in draws if d["draw_date"] >= cutoff]
        out = {
            "game": game.id,
            "name": game.name,
            "main_range": [game.main_min, game.main_max],
            "main_count": game.main_count,
            "bonus_range": [game.bonus_min, game.bonus_max] if game.bonus_min else None,
            "draw_count": len(draws),
            "oldest": draws[-1]["draw_date"] if draws else None,
            "newest": draws[0]["draw_date"] if draws else None,
            "source": "https://www.lotto.net (year archives)",
            "draws": draws,
        }
        path = DATA_DIR / f"{game.id}.json"
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        manifest.setdefault("games", {})[game.id] = {
            "file": path.name,
            "draw_count": len(draws),
            "oldest": out["oldest"],
            "newest": out["newest"],
        }
        print(f"  saved {len(draws)} draws")

    manifest["generated"] = date.today().isoformat()
    manifest["cutoff_date"] = cutoff
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
