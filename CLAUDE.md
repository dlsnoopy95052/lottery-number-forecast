# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A static CA Lottery number suggestion tool. The main UI is `ca-lottery.html` — a single-file, no-build frontend that loads pre-computed frequency data from `data/lottery-summary.js` (or falls back to `data/summary.json`). There are no npm packages, no bundler, and no test suite.

## Running the UI

Open `ca-lottery.html` in a browser **via a local HTTP server** (not `file://`, which blocks `fetch()`):

```
python -m http.server 8080
# then open http://localhost:8080/ca-lottery.html
```

`random.html` and `tictactoe.html` work fine opened directly as files.

## Data pipeline (Python scripts — run in order)

All scripts live in `scripts/` and write to `data/`. No dependencies beyond the standard library.

```
# 1. Fetch draw history for SuperLotto Plus, Powerball (lotto.net scraper)
python scripts/fetch_ca_lottery.py

# 2. Fetch Mega Millions if missing/stale (same scraper, targeted)
python scripts/fetch_missing_games.py

# 3. Supplement Fantasy 5 from DrawAnalytics API (lotto.net lacks this game)
python scripts/fetch_drawanalytics.py

# 4. Build frequency summary consumed by the UI
python scripts/build_summary.py

# 5. (Optional) Snapshot current jackpot amounts
python scripts/fetch_jackpots.py
```

Step 4 must run last — it reads the per-game JSON files and writes both `data/summary.json` and `data/lottery-summary.js` (the JS file embeds the summary as `window.LOTTERY_SUMMARY` so the page works without a server).

## Architecture

### Data flow

```
lotto.net (HTML scraper)        → data/{game}.json     (raw draw history)
drawanalytics.com (JSON API)    → data/fantasy5.json   (supplement)
drawanalytics.com (JSON API)    → data/jackpots.json + data/jackpots.js
build_summary.py                → data/summary.json + data/lottery-summary.js
```

### Per-game JSON schema (`data/{game}.json`)

```json
{
  "game": "superlotto_plus",
  "main_range": [1, 47],
  "main_count": 5,
  "bonus_range": [1, 27],   // null for games with no bonus ball
  "draw_count": 1085,
  "oldest": "2016-01-02",
  "newest": "2026-05-23",
  "draws": [
    { "draw_date": "2026-05-23", "numbers": [3, 12, 27, 31, 44], "bonus": 7 }
  ]
}
```

### Summary JSON (`data/summary.json` / `data/lottery-summary.js`)

`build_summary.py` picks a **shared analysis period** anchored to the SuperLotto Plus date range so all games are comparable. It emits `main_freq` and `bonus_freq` as index-addressed arrays (index = ball number, value = draw count).

### Frontend (`ca-lottery.html`)

All logic is inline JavaScript. Key entry points:
- `suggestNumbers(game, mode)` — implements the four pick strategies (balanced / hot / cold / random) using `weightedSample()` and `uniformSample()`
- `refreshJackpots()` — tries the DrawAnalytics live API first, falls back to the bundled `window.LOTTERY_JACKPOTS` snapshot
- `loadSummary()` — uses `window.LOTTERY_SUMMARY` if present, otherwise fetches `data/summary.json`
- `jackpotOdds(g)` — computes jackpot odds from game rules: `C(pool, main_count) × bonus_pool_size`; no hardcoding, works for any game
- `formatOdds(n)` — formats large odds as "1 in 302.6M" etc.; displayed in each jackpot card as `.jp-odds`

### Remotes

- `origin` → GitHub (`https://github.com/dlsnoopy95052/proj1.git`)
- `lotto` → local Gitea (internal network only)
- `lottery` → GitHub (`https://github.com/dlsnoopy95052/lottery-number-forecast.git`)
