#!/usr/bin/env python3
import re, urllib.request, time, sys, os
from datetime import datetime, timedelta

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8','ignore')

def parse_ebay(html):
    # Simple heuristics for popular listing blocks on eBay search results
    titles = re.findall(r'<span class="s-item__title">([^<]+)</span>', html, re.I)
    prices = re.findall(r'<span class="s-item__price">\$?([0-9,]+(?:\.[0-9]{2})?)</span>', html, re.I)
    links = re.findall(r'href="(https?://[^\"]+)"', html)
    items = []
    for i, t in enumerate(titles[:10]):
        if i < len(prices):
            try:
                p = float(prices[i].replace(',', ''))
            except:
                continue
            if p <= 450:
                link = links[i] if i < len(links) else ''
                items.append({'title': t.strip(), 'price': prices[i], 'link': link})
    return items

def main():
    base_dir = os.path.expanduser("~/.hermes/cron")
    os.makedirs(base_dir, exist_ok=True)

    start_file = os.path.join(base_dir, "ebay_gpu_watch_start")
    if not os.path.exists(start_file):
        with open(start_file, 'w') as f:
            f.write(datetime.utcnow().strftime('%Y-%m-%d'))
        start_date = datetime.utcnow()
    else:
        with open(start_file) as f:
            start_date = datetime.strptime(f.read().strip(), '%Y-%m-%d')

    # End condition: 7-day window
    if (datetime.utcnow() - start_date).days >= 7:
        print("Monitor window ended; exiting without fetch.")
        return 0

    queries = [
        ("RX 6800 16GB used", "https://www.ebay.com/sch/i.html?_nkw=RX+6800+16GB+used&_sop=15"),
        ("RX 6800 XT 16GB used", "https://www.ebay.com/sch/i.html?_nkw=RX+6800+XT+16GB+used&_sop=15"),
        ("RTX 3060 Ti 8GB used", "https://www.ebay.com/sch/i.html?_nkw=RTX+3060+Ti+8GB+used&_sop=15"),
    ]

    lines = []
    lines.append("Ebay GPU Auction Monitor - " + datetime.utcnow().strftime("%Y-%m-%d"))
    for label, url in queries:
        try:
            html = fetch(url)
        except Exception as e:
            lines.append(f"{label}: fetch error: {e}")
            continue
        items = parse_ebay(html)
        lines.append("")
        lines.append(label + ":")
        if not items:
            lines.append("  None found within price band or parsing failed.")
        else:
            for it in items[:3]:
                lines.append(f"  - {it['title']}  |  {it['price']} USD  |  {it['link']}")

    out_path = os.path.join(os.path.expanduser("~/.hermes/cron"), "ebay_gpu_watch_" + datetime.utcnow().strftime("%Y%m%d") + ".txt")
    with open(out_path, 'w') as f:
        f.write("\n".join(lines))

    return 0

if __name__ == "__main__":
    sys.exit(main())