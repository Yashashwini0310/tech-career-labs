#!/usr/bin/env python3
"""Generates the historical logs for Task 7 (Friday 16 Oct 2026 outage) and prints the answers.
This lives in solutions/ because reading it spoils the task."""
import math
import os
import random
from datetime import datetime, timedelta

rng = random.Random(1016)
DAY = datetime(2026, 10, 16)
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(OUT, exist_ok=True)

OUT_START = DAY.replace(hour=14, minute=5)
OUT_END = DAY.replace(hour=14, minute=41, second=59)
SCRAPER = "185.220.101.47"
UAS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0) Safari/604.1",
       "ShopFastApp/4.12 (Android 14)", "ShopFastApp/4.12 (iOS 18.0)", "Mozilla/5.0 (Macintosh) Firefox/131.0"]

lines = []   # (ts, ip, method, path, status, bytes, ua, rt)


def rand_ip():
    return f"{rng.choice([31, 37, 46, 78, 86, 89, 109, 176, 188, 212])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


clients = [rand_ip() for _ in range(3000)]
partner_ip = "52.18.44.201"


def pick_endpoint():
    r = rng.random()
    if r < 0.45:
        return "GET", f"/api/orders/{rng.randint(1, 200000)}"
    if r < 0.60:
        return "GET", f"/api/customers/{rng.randint(1, 20000)}/orders"
    if r < 0.90:
        return "GET", f"/api/products/{rng.randint(1, 500)}"
    if r < 0.95:
        return "GET", "/health"
    if r < 0.98:
        return "GET", f"/api/reports/daily-sales?date=2026-10-{rng.randint(1, 15):02d}"
    return "POST", "/api/orders"


def normal_rt(path):
    if path.startswith("/api/customers"):
        return rng.lognormvariate(math.log(0.55), 0.35)
    if path.startswith("/api/reports"):
        return rng.lognormvariate(math.log(0.30), 0.3)
    if path == "/health":
        return rng.lognormvariate(math.log(0.004), 0.3)
    return rng.lognormvariate(math.log(0.045), 0.45)


# organic traffic with a daily curve
for minute in range(24 * 60):
    hour = minute / 60
    rate = 12 + 30 * max(0, math.sin((hour - 6) / 18 * math.pi))  # requests per minute
    n = int(rng.gauss(rate, rate * 0.1))
    for _ in range(max(n, 1)):
        ts = DAY + timedelta(minutes=minute, seconds=rng.random() * 60)
        method, path = pick_endpoint()
        ip = partner_ip if method == "POST" else rng.choice(clients)
        ua = "GreenCart-Integration/2.3" if method == "POST" else rng.choice(UAS)
        in_outage = OUT_START <= ts <= OUT_END
        if in_outage and path != "/health" and rng.random() < 0.72:
            status = rng.choice([500, 500, 500, 502, 504])
            rt = 30.0 if status == 504 else rng.uniform(0.001, 0.02)
            size = 0 if status != 500 else 96
        elif in_outage and path == "/health" and rng.random() < 0.8:
            status, rt, size = 500, rng.uniform(0.001, 0.01), 96
        else:
            rt = normal_rt(path)
            if method == "POST":
                status, size = 401, 27          # partner still using the old key
            elif path.startswith("/api/orders/") and rng.random() < 0.012:
                status, size = 500, 96          # the NULL discount bug
            elif path.startswith("/api/orders/") and rng.random() < 0.01:
                status, size = 404, 22
            else:
                status, size = 200, rng.randint(180, 2400)
        lines.append((ts, ip, method, path, status, size, ua, rt))

# scraper burst 09:10-10:50
for _ in range(4200):
    ts = DAY.replace(hour=9, minute=10) + timedelta(seconds=rng.random() * 100 * 60)
    lines.append((ts, SCRAPER, "GET", f"/api/products/{rng.randint(1, 500)}", 200, rng.randint(300, 600),
                  "python-requests/2.31.0", rng.lognormvariate(math.log(0.03), 0.3)))

lines.sort(key=lambda x: x[0])

with open(os.path.join(OUT, "access.log"), "w") as f:
    for ts, ip, m, p, s, b, ua, rt in lines:
        f.write(f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S")} +0000] "{m} {p} HTTP/1.1" {s} {b} "-" "{ua}" rt={rt:.3f}\n')

# app.log
with open(os.path.join(OUT, "app.log"), "w") as f:
    def w(ts, level, msg):
        f.write(f"{ts.strftime('%Y-%m-%d %H:%M:%S')},{rng.randint(0, 999):03d} {level} [orders-api] {msg}\n")
    reports_seen = 0
    for ts, ip, m, p, s, b, ua, rt in lines:
        if ip == SCRAPER:
            continue
        if s == 200 and rng.random() < 0.08:
            w(ts, "INFO", f"{m} {p.split('?')[0]} -> 200 in {rt * 1000:.1f}ms")
        elif s == 401:
            w(ts, "WARNING", f"Rejected order: invalid API key from {ip}")
            w(ts, "INFO", f"{m} {p} -> 401 in {rt * 1000:.1f}ms")
        elif s == 500 and not (OUT_START <= ts <= OUT_END):
            w(ts, "ERROR", f"Unhandled error on {m} {p}")
            f.write("Traceback (most recent call last):\n  File \"/app/app.py\", line 86, in get_order\n"
                    "    discount_amount = subtotal * order[\"discount_pct\"] / 100\n"
                    "TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'NoneType'\n")
        elif s in (500, 502, 504) and OUT_START <= ts <= OUT_END:
            if s == 500:
                w(ts, "ERROR", f"Unhandled error on {m} {p.split('?')[0]}")
                f.write("Traceback (most recent call last):\n  File \"/app/app.py\", line 42, in get_conn\n"
                        "    return psycopg.connect(DB_DSN, row_factory=dict_row, connect_timeout=5)\n"
                        "psycopg.OperationalError: connection failed: FATAL:  sorry, too many clients already\n")
            elif s == 504:
                w(ts, "WARNING", f"Worker timeout (pid:{rng.choice([7, 8])}) while handling {m} {p.split('?')[0]}")
        if p.startswith("/api/reports") and s == 200:
            reports_seen += 1
            if reports_seen % 3 == 0:
                w(ts, "INFO", f"Report connection cached for re-use (held: {min(reports_seen // 3, 18)})")

# ---- answers ----
import re
from collections import Counter

def norm(p):
    return re.sub(r"/\d+", "/{id}", p.split("?")[0])

total = len(lines)
fivexx = [l for l in lines if l[4] >= 500]
by_min = {}
for l in lines:
    k = l[0].strftime("%H:%M")
    t, e = by_min.get(k, (0, 0))
    by_min[k] = (t + 1, e + (1 if l[4] >= 500 else 0))
bad = sorted(k for k, (t, e) in by_min.items() if e / t > 0.20)
ep = Counter(norm(l[3]) for l in fivexx).most_common(3)
ip = Counter(l[1] for l in lines).most_common(3)
rts = sorted(l[7] for l in lines if l[2] == "GET" and norm(l[3]) == "/api/orders/{id}" and l[4] == 200)
p95 = rts[math.ceil(0.95 * len(rts)) - 1] * 1000
slow = Counter()
cnt = Counter()
for l in lines:
    if l[4] == 200:
        slow[norm(l[3])] += l[7]
        cnt[norm(l[3])] += 1
avg = sorted(((slow[k] / cnt[k]) * 1000, k) for k in cnt)[-1]
print("total", total, "5xx", len(fivexx), "bad minutes", bad[0], bad[-1], len(bad))
print("endpoint", ep, "ip", ip)
print("p95_orders_ms", round(p95), "slowest_avg", avg)
print("401 count", sum(1 for l in lines if l[4] == 401))
