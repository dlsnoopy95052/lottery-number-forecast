import re
import urllib.request

UA = "CA-Lottery-Suggestion-Tool/1.0"
html = urllib.request.urlopen(
    urllib.request.Request(
        "https://www.lotteryusa.com/california/fantasy-5/",
        headers={"User-Agent": UA},
    ),
    timeout=30,
).read().decode("utf-8", "replace")

for pat in [
    r"c-ball",
    r"result__num",
    r"winning-number",
    r"data-number",
    r'"numbers"',
]:
    print(pat, len(re.findall(pat, html, re.I)))

# find first sequence of 5 two-digit numbers near a date
m = re.search(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}.{0,200}",
    html,
    re.I | re.DOTALL,
)
print("sample date region:", m.group()[:250] if m else "none")

# JSON embedded?
for key in ["draws", "winningNumbers", "results"]:
    if key in html:
        print("has", key)

idx = html.find("c-results")
print("c-results idx", idx, html[idx : idx + 1500] if idx >= 0 else "")
