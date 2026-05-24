import re
import urllib.request

UA = "CA-Lottery-Suggestion-Tool/1.0"
url = "https://www.lotteryusa.com/california/fantasy-5/"
html = urllib.request.urlopen(
    urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30
).read().decode("utf-8", "replace")

# Each draw block
blocks = re.split(r"c-result__block", html)
print("blocks", len(blocks))
for b in blocks[1:3]:
    date_m = re.search(r"c-result__date[^>]*>\s*([^<]+?)\s*<", b)
    nums = re.findall(r"c-ball__item[^>]*>\s*(\d{1,2})\s*<", b)
    if not nums:
        nums = re.findall(r'class="c-ball[^"]*"[^>]*>\s*(\d{1,2})\s*<', b)
    print("date", date_m.group(1).strip() if date_m else "?", "nums", nums)

all_nums = re.findall(r"c-ball__item[^>]*>\s*(\d{1,2})\s*<", html)
print("total ball items", len(all_nums), "draws est", len(all_nums) // 5)
