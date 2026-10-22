#!/usr/bin/env python3
"""
Lab 1 grader. Run from the lab1-support folder:   ./lab.sh grade   (or: python3 grade.py)

Checks the live system (API, nginx, database) and your files in work/.
Prints a score out of 100 and saves it to work/score_history.csv.

Please don't read the encoded answers below - you'll learn more by working them out.
"""
import base64
import csv
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("BASE_URL", "http://localhost:8080")
PSQL = os.environ.get("PSQL", "docker compose exec -T db psql -U shop -d shop -tAc")
_E = json.loads(base64.b64decode(
    "eyJhIjogeyJxMV90b3RhbF9yZXF1ZXN0cyI6IDQxNTE4LCAicTJfdG90YWxfNXh4IjogMTM1MCwgInEzX291dGFnZV9zdGFydF9oaG1tIjogIjE0OjA1IiwgInE0X291dGFnZV9lbmRfaGhtbSI6ICIxNDo0MSIsICJxNV9lbmRwb2ludF9tb3N0XzV4eCI6ICIvYXBpL29yZGVycy97aWR9IiwgInE2X3RvcF9pcCI6ICIxODUuMjIwLjEwMS40NyIsICJxN19wOTVfbXNfZ2V0X29yZGVyIjogOTMsICJxOF9yb290X2NhdXNlX2Vycm9yX3RleHQiOiAidG9vIG1hbnkgY2xpZW50cyIsICJxOV9zbG93ZXN0X2VuZHBvaW50X2F2ZyI6ICIvYXBpL2N1c3RvbWVycy97aWR9L29yZGVycyIsICJxMTBfcGFydG5lcl80MDFfY291bnQiOiA2OTd9LCAidCI6IHsiVEtULTEwMDEiOiAiUDEiLCAiVEtULTEwMDIiOiAiUDIiLCAiVEtULTEwMDMiOiAiUDEiLCAiVEtULTEwMDQiOiAiUDMiLCAiVEtULTEwMDUiOiAiUDIiLCAiVEtULTEwMDYiOiAiUDIiLCAiVEtULTEwMDciOiAiUDQiLCAiVEtULTEwMDgiOiAiUDQifX0="
))

results = []  # (task, check, points_got, points_max, note)


def add(task, check, ok, pts, note=""):
    results.append((task, check, pts if ok else 0, pts, note))


def http(method, url, body=None, headers=None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def sql(q):
    cmd = PSQL.split() + [q]
    try:
        out = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=60)
        return out.stdout.strip()
    except Exception as e:
        return f"ERROR {e}"


def load_json(path):
    try:
        with open(os.path.join(HERE, path)) as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------- Task 1: site down (502) ----------------
s, _ = http("GET", BASE + "/health")
add("T1", "Site reachable through nginx (GET /health = 200)", s == 200, 10, f"got {s}")
site_up = s == 200

# ---------------- Task 2: order page errors ----------------
ids = sql("SELECT order_id FROM orders WHERE discount_pct IS NULL AND order_id <= 200000 ORDER BY order_id LIMIT 3").split()
ok2, note2 = bool(ids) and site_up, ""
for oid in ids:
    exp = sql(f"""SELECT ROUND(SUM(i.quantity*i.unit_price) + MAX(o.shipping_fee), 2)
                  FROM orders o JOIN order_items i USING (order_id) WHERE o.order_id = {oid}""")
    s, body = http("GET", f"{BASE}/api/orders/{oid}")
    try:
        got = json.loads(body).get("total")
    except Exception:
        got = None
    if s != 200 or got is None or abs(float(got) - float(exp)) > 0.01:
        ok2, note2 = False, f"order {oid}: status {s}, total {got}, expected {exp}"
        break
add("T2", "Orders without a discount code load with the correct total", ok2, 10, note2)

# ---------------- Task 3: partner 401 ----------------
partner_ok = False
try:
    r = subprocess.run([sys.executable, os.path.join(HERE, "client", "place_order.py")], capture_output=True, text=True, timeout=30)
    partner_ok = r.returncode == 0
    add("T3", "Partner client places an order successfully", partner_ok, 5, r.stdout.strip()[:80])
except Exception as e:
    add("T3", "Partner client places an order successfully", False, 5, str(e))
s, _ = http("POST", BASE + "/api/orders", {"customer_id": 1, "items": [{"product_id": 1}]})
add("T3", "...and requests without an API key are still rejected (401)", partner_ok and s == 401, 3, f"got {s}")
s, _ = http("POST", BASE + "/api/orders", {"customer_id": 1, "items": [{"product_id": 1}]}, {"X-API-Key": "wrong"})
add("T3", "...and requests with a wrong API key are still rejected (401)", partner_ok and s == 401, 2, f"got {s}")

# ---------------- Task 4: slow order history ----------------
idx = sql("SELECT indexdef FROM pg_indexes WHERE tablename = 'orders'")
add("T4", "orders.customer_id is indexed", bool(re.search(r"\(\s*customer_id", idx)), 6)
plan = sql("EXPLAIN SELECT order_id FROM orders WHERE customer_id = 4242 ORDER BY order_ts DESC")
add("T4", "Order-history query uses an index (not a Seq Scan)", "Index" in plan and "Seq Scan" not in plan, 4)

# ---------------- Task 5: connection leak ----------------
fails = 0
if site_up:
    for _ in range(40):
        s, _ = http("GET", BASE + "/api/reports/daily-sales?date=2026-10-01")
        if s != 200:
            fails += 1
s, _ = http("GET", BASE + "/health")
add("T5", "40 daily-sales reports in a row succeed and the API stays healthy", site_up and fails == 0 and s == 200, 10,
    f"{fails} failed calls" if fails else "")
time.sleep(1)
held = sql("SELECT COUNT(*) FROM pg_stat_activity WHERE usename = 'shop_app'")
add("T5", "API is not holding database connections open (< 6)", held.isdigit() and int(held) < 6, 5, f"{held} held")

# ---------------- Task 6: finance report ----------------
dupes = sql("SELECT COUNT(*) - COUNT(DISTINCT provider_txn_id) FROM payments")
add("T6", "No duplicate payment transactions", dupes == "0", 4, f"{dupes} duplicates")
uq = sql("""SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'payments'
            AND indexdef ILIKE '%UNIQUE%' AND indexdef ILIKE '%provider_txn_id%'""")
add("T6", "Database now prevents duplicate provider_txn_id (unique constraint)", uq not in ("", "0"), 3)
try:
    with open(os.path.join(HERE, "db", "data", "payments.csv")) as f:
        expected_rows = sum(1 for _ in f) - 1
except Exception:
    expected_rows = -1
rows = sql("SELECT COUNT(*) FROM payments WHERE payment_id <= 200000")
add("T6", "...and no legitimate payments were deleted", dupes == "0" and rows == str(expected_rows), 3, f"{rows} vs {expected_rows}")

# ---------------- Task 7: log investigation ----------------
ans = load_json("work/answers.json")
for k, exp in _E["a"].items():
    got = ans.get(k)
    if k == "q7_p95_ms_get_order":
        ok = isinstance(got, (int, float)) and abs(got - exp) <= 3
    elif isinstance(exp, int):
        ok = got == exp or str(got).strip() == str(exp)
    else:
        ok = isinstance(got, str) and exp.lower() in got.strip().lower()
    add("T7", k, ok, 1.5)

# ---------------- Task 8: triage ----------------
tri = load_json("work/triage.json")
for k, exp in _E["t"].items():
    add("T8", f"{k} priority", str(tri.get(k, "")).strip().upper() == exp, 1.25)

# ---------------- Task 9: health check script ----------------
hc = os.path.join(HERE, "work", "healthcheck.sh")


def run_hc(url):
    try:
        return subprocess.run(["bash", hc, url], capture_output=True, text=True, timeout=20).returncode
    except Exception:
        return -1


hc_ok = site_up and run_hc(BASE + "/health") == 0
add("T9", "healthcheck.sh exits 0 for a healthy URL", hc_ok, 2)
add("T9", "...and exits non-zero for a 404", hc_ok and run_hc(BASE + "/no-such-page") not in (0, -1), 1.5)
add("T9", "...and exits non-zero when nothing is listening", hc_ok and run_hc("http://localhost:9/") not in (0, -1), 1.5)

# ---------------- Task 10: documentation ----------------


def has_sections(path, sections):
    text = open(path, encoding="utf-8").read().lower()
    return all(re.search(r"^#+\s*" + s, text, re.M) for s in sections) and len(text.split()) >= 150, text


rb_ok = False
for p in glob.glob(os.path.join(HERE, "work", "runbooks", "*.md")):
    ok, _ = has_sections(p, ["symptoms", "diagnosis", "resolution", "verification", "prevention"])
    rb_ok = rb_ok or ok
add("T10", "Runbook with Symptoms/Diagnosis/Resolution/Verification/Prevention (150+ words)", rb_ok, 2.5)
pm_ok = False
for p in glob.glob(os.path.join(HERE, "work", "postmortems", "*.md")):
    ok, text = has_sections(p, ["summary", "impact", "timeline", "root cause", "resolution", "action items"])
    pm_ok = pm_ok or (ok and len(re.findall(r"\b\d{2}:\d{2}\b", text)) >= 4)
add("T10", "Postmortem with all sections and a timeline of 4+ timestamps", pm_ok, 2.5)

# ---------------- report ----------------
total = sum(r[2] for r in results)
maxp = sum(r[3] for r in results)
print("\n  LAB 1 - TECHNICAL SUPPORT  |  grading results\n  " + "-" * 78)
cur = None
for task, check, got, mx, note in results:
    if task != cur:
        cur = task
        tt = sum(r[2] for r in results if r[0] == task)
        tm = sum(r[3] for r in results if r[0] == task)
        print(f"\n  {task}  ({tt:g}/{tm:g})")
    mark = "PASS" if got == mx else "FAIL"
    print(f"    [{mark}] {check}" + (f"   <- {note}" if note and got != mx else ""))
print("\n  " + "-" * 78)
print(f"  SCORE: {total:g} / {maxp:g}\n")
try:
    hist = os.path.join(HERE, "work", "score_history.csv")
    new = not os.path.exists(hist)
    with open(hist, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "score"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), total])
except Exception:
    pass
