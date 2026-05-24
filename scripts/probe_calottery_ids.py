import json
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BASE = "https://www.calottery.com/api/DrawGameApi/DrawGamePastDrawResults/{gid}/1/3"
CANDIDATES = list(range(1, 30)) + [8, 12, 15, 17, 20, 24, 25]

for gid in CANDIDATES:
    url = BASE.format(gid=gid)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        raw = urllib.request.urlopen(req, timeout=15).read()
        data = json.loads(raw)
        draws = data.get("PreviousDraws") or data.get("previousDraws") or []
        if not draws:
            continue
        d0 = draws[0]
        nums = d0.get("WinningNumbers") or d0.get("winningNumbers")
        print("id", gid, "draws", len(draws), "date", d0.get("DrawDate"), "keys", list(nums.keys())[:8] if isinstance(nums, dict) else nums)
    except Exception as e:
        pass
    time.sleep(0.3)
