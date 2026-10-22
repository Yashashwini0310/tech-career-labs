# Lab 1 – Solutions

Only read this after you've tried. Model answers for Tasks 7–10 are in `solutions/work/`.

## Task 1 – nginx 502
**Cause:** `nginx/nginx.conf` forwards to `api:5001`, but gunicorn listens on `5000`. nginx's error log shows `connect() failed (111: Connection refused) while connecting to upstream`.
**Fix:** change to `server api:5000;` then `./lab.sh restart nginx`.
**Interview angle:** "502 means the proxy is up but the upstream isn't answering correctly. I check the proxy's error log first, then confirm the upstream host and port."

## Task 2 – 500 on orders without a discount code
**Cause:** `discount_pct` is `NULL` for orders where no discount code was used (about 30% of orders). `subtotal * None` raises `TypeError`.
**Fix (app/app.py):**
```python
discount_amount = subtotal * (order["discount_pct"] or 0) / 100
```
Then `./lab.sh restart api`.
**Better long term:** decide whether NULL should exist at all. A `DEFAULT 0 NOT NULL` column plus a data backfill removes the whole class of bug.

## Task 3 – Partner 401
**Cause:** the API key was rotated on 14 Oct (change CHG-20261014-07), but the partner wasn't given the new key. The access log shows 697 rejected POSTs on Friday alone.
**Fix:** update `client/client.env` with `API_KEY=sk_live_shopfast_2026Q4_9f3c`.
**Process lesson:** key rotations need a partner communication step in the change plan. This is a change management failure, not a code bug.

## Task 4 – Slow order history
**Cause:** the migration dropped `idx_orders_customer_id`, so every lookup is a sequential scan of 200,000 rows.
**Fix:**
```sql
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
```
EXPLAIN goes from `Seq Scan on orders` to `Bitmap Index Scan on idx_orders_customer_id`. Execution time drops from about 20–40 ms to under 1 ms in the database. In production, with millions of rows, the difference would be seconds.
In production use `CREATE INDEX CONCURRENTLY` to avoid locking writes.

## Task 5 – Connection leak
**Cause:** `daily_sales()` opens a connection, appends it to `_report_connections` "for re-use", and never closes it. Each gunicorn worker leaks one connection per report. With `max_connections = 20`, the database runs out, and every endpoint, including `/health`, fails with `FATAL: sorry, too many clients already`. A restart releases the connections, which is why the outage always "fixed itself" after a restart.
**Fix:**
```python
@app.get("/api/reports/daily-sales")
def daily_sales():
    ...
    with get_conn() as conn:
        row = conn.execute(...).fetchone()
    return jsonify(...)
```
And delete the `_report_connections` list. Then `./lab.sh restart api`.
**Immediate mitigation without a restart:**
```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'shop_app' AND state = 'idle';
```

## Task 6 – Duplicate payments
**Cause:** the payment webhook retried during a provider blip on 5 Oct and inserted 41 payments twice (same `provider_txn_id`, a new `payment_id` from 900001, and a timestamp 3 seconds later).
**Investigate:**
```sql
SELECT provider_txn_id, COUNT(*), SUM(amount)
FROM payments GROUP BY 1 HAVING COUNT(*) > 1;

-- overstatement for Finance
SELECT SUM(a.amount) FROM payments a JOIN payments b
  ON a.provider_txn_id = b.provider_txn_id AND a.payment_id > b.payment_id;
```
**Fix:** see `solutions/fixes.sql`.
```sql
DELETE FROM payments a USING payments b
WHERE a.provider_txn_id = b.provider_txn_id AND a.payment_id > b.payment_id;
ALTER TABLE payments ADD CONSTRAINT uq_payments_provider_txn_id UNIQUE (provider_txn_id);
```
**Real-world note:** take a backup (`CREATE TABLE payments_backup_20261019 AS SELECT * FROM payments;`) and get approval before deleting financial data. The webhook should also be made idempotent (`INSERT ... ON CONFLICT (provider_txn_id) DO NOTHING`).

## Task 7 – Log answers
| Question | Answer | One way to get it |
|---|---|---|
| q1 | 41,518 | `wc -l logs/access.log` |
| q2 | 1,350 | `awk '$9 >= 500' logs/access.log \| wc -l` |
| q3 / q4 | 14:05 / 14:41 | per-minute error rate (Python below) |
| q5 | /api/orders/{id} | normalise paths, count 5xx |
| q6 | 185.220.101.47 | `awk '{print $1}' logs/access.log \| sort \| uniq -c \| sort -rn \| head -3`. It's a scraper (`python-requests`) pulling product pages 09:10–10:50. |
| q7 | 93 ms | sort rt values, nearest-rank p95 |
| q8 | "FATAL: sorry, too many clients already" | `grep -o "FATAL.*" logs/app.log \| sort \| uniq -c` |
| q9 | /api/customers/{id}/orders | about 590 ms average, the missing index from Task 4 |
| q10 | 697 | `grep '"POST /api/orders' logs/access.log \| awk '$9 == 401' \| wc -l` |

```python
import re, math
from collections import Counter, defaultdict
rows = []
for line in open("logs/access.log"):
    m = re.search(r'^(\S+) .*?:(\d\d:\d\d):\d\d .*?"(\w+) (\S+) [^"]*" (\d{3}) .* rt=([\d.]+)', line)
    rows.append((m[1], m[2], m[3], re.sub(r"/\d+", "/{id}", m[4].split("?")[0]), int(m[5]), float(m[6])))
per_min = defaultdict(lambda: [0, 0])
for ip, hm, meth, path, st, rt in rows:
    per_min[hm][0] += 1
    per_min[hm][1] += st >= 500
bad = sorted(k for k, (t, e) in per_min.items() if e / t > 0.2)
print("outage", bad[0], "-", bad[-1])
print(Counter(p for _, _, _, p, s, _ in rows if s >= 500).most_common(1))
rts = sorted(rt for _, _, m, p, s, rt in rows if m == "GET" and p == "/api/orders/{id}" and s == 200)
print("p95 ms", round(rts[math.ceil(0.95 * len(rts)) - 1] * 1000))
```

**The story:** Friday's outage (Task 7) is the same connection leak as Task 5. The slowest endpoint is the missing index from Task 4. The 401s are Task 3. Real incidents connect like this, which is why logs matter.

## Task 8 – Triage
| Ticket | Priority | Why |
|---|---|---|
| TKT-1001 | P1 | Site down for everyone |
| TKT-1002 | P2 | Major function broken for many users, but new orders still work |
| TKT-1003 | P1 | Revenue fully blocked for a key partner, contractual 4h SLA |
| TKT-1004 | P3 | Slow but works |
| TKT-1005 | P2 | Financial data inaccurate, month-end deadline |
| TKT-1006 | P2 | Not down now, but high risk of a repeat outage |
| TKT-1007 | P4 | Access request |
| TKT-1008 | P4 | Cosmetic |

**Order of work:** TKT-1001 first (nothing else can be verified while the site is down), then TKT-1003, then TKT-1006 (it'll take the site down again), TKT-1002, TKT-1005, TKT-1004, then the P4s.
