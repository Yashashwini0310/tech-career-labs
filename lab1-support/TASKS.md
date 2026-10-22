# Lab 1 – Technical / Application Support

## The scenario

It's **Monday 19 October 2026, 08:00**. You've just joined **ShopFast**, an Irish online retailer, as an **Application Support Engineer (L2)**. The on-call engineer from last week has gone on holiday. Your queue is in `tickets/tickets.json`, and production isn't in good shape.

**System overview**

```
 Customers / mobile app / partner (GreenCart)
                 │
          nginx  (port 8080)            ← edge proxy, access logs in runtime_logs/nginx/
                 │
       Orders API (Flask, port 5000)    ← code in app/app.py, logs in runtime_logs/app/
                 │
       PostgreSQL 16 (port 5432)        ← database "shop": customers, products, orders, order_items, payments
```

**Useful commands**

| What | Command |
|---|---|
| Start the lab | `./lab.sh start` |
| Container status | `./lab.sh status` |
| Follow API logs | `./lab.sh logs api` (or `nginx`, `db`) |
| Open the database as admin | `./lab.sh psql` |
| Restart a service after a fix | `./lab.sh restart api` (or `nginx`) |
| Check your score | `./lab.sh grade` |
| Start again from scratch | `./lab.sh reset` |
| Call the API | `curl -i http://localhost:8080/api/orders/1` |

**Rules, like a real job:**

- Fix the **root cause**, not just the symptom. For example, restarting a service might hide a problem, but the grader checks that it stays fixed.
- Don't weaken security to make something work. For example, don't remove the API key check.
- Write down what you find. Tasks 7 and 10 need your notes.

**Priority definitions (used in Task 8):**

| Priority | Meaning |
|---|---|
| **P1 – Critical** | Service down for all or most users, OR revenue fully blocked for a key partner or sales channel |
| **P2 – High** | Major function broken or wrong for many users (partial workaround exists), financial data inaccurate, or high risk of a repeat outage |
| **P3 – Medium** | Degraded performance or a minor function issue; system still usable |
| **P4 – Low** | Requests, questions, cosmetic issues |

---

## Tasks (100 points)

### Task 1 – The site is down (10 pts) · ticket TKT-1001
Every request through `http://localhost:8080` returns **502 Bad Gateway**, but the API answers on port 5000.
- Find out why nginx can't reach the API, and fix it.
- **Done when:** `curl -i http://localhost:8080/health` returns `200`.

### Task 2 – Order pages show an error (10 pts) · ticket TKT-1002
Some orders open fine (`/api/orders/1`), and others return **500** (try `/api/orders/2`).
- Use the API logs to find the exact error and the line of code.
- Work out what those orders have in common (check them in the database).
- Fix the code, restart the API, and make sure the **total is still calculated correctly**.

### Task 3 – Partner orders rejected (10 pts) · ticket TKT-1003
GreenCart's integration (`client/place_order.py`) gets **401 Unauthorized** on every order.
- Run `python3 client/place_order.py` to reproduce it.
- Find out what changed on our side (hint: check comments in config files) and fix the partner's configuration.
- **Don't** remove or weaken the API key check. Requests without a valid key must still get 401.

### Task 4 – Slow order history (10 pts) · ticket TKT-1004
`/api/customers/<id>/orders` got slow after last week's database migration.
- Time it: `curl -o /dev/null -s -w "%{time_total}\n" http://localhost:8080/api/customers/42/orders`
- In `./lab.sh psql`, run `EXPLAIN ANALYZE` on the query the endpoint uses. What is the plan doing?
- Fix it at the database level, then compare the time and plan before and after.

### Task 5 – The API falls over in the afternoon (15 pts) · ticket TKT-1006
Run this a few times and watch what happens to the whole API:
```bash
for i in $(seq 30); do curl -s -o /dev/null -w "%{http_code} " "http://localhost:8080/api/reports/daily-sales?date=2026-10-01"; done; echo
curl -i http://localhost:8080/health
```
- Find the error in the logs, and check database connections with `SELECT usename, state, COUNT(*) FROM pg_stat_activity GROUP BY 1, 2;`
- A restart "fixes" it for a while, but find and fix the real bug in the code.

### Task 6 – Finance says the numbers are wrong (10 pts) · ticket TKT-1005
`/api/reports/daily-sales?date=2026-10-05` shows more revenue than the payment providers settled.
- Investigate the `payments` table for that day. What's wrong with the data?
- Clean it up **without deleting real payments**, and make the database prevent this from happening again.
- Bonus (not graded): what was the overstatement in euro? Finance will ask.

### Task 7 – Investigate Friday's outage (15 pts) · historical logs
`logs/access.log` (nginx) and `logs/app.log` (API) are from **Friday 16 Oct 2026**. Use `grep`, `awk`, `sort`, `uniq`, `cut`, or a Python script if you prefer. Fill in `work/answers.json`:

| Key | Question |
|---|---|
| `q1_total_requests` | Total number of requests in access.log |
| `q2_total_5xx` | Number of requests with a 5xx status code |
| `q3_outage_start_hhmm` | First minute (HH:MM) where more than 20% of requests were 5xx |
| `q4_outage_end_hhmm` | Last minute (HH:MM) where more than 20% of requests were 5xx |
| `q5_endpoint_most_5xx` | Endpoint with the most 5xx errors. Replace numeric IDs with `{id}` and ignore query strings, e.g. `/api/products/{id}` |
| `q6_top_ip` | IP address that sent the most requests (and what was it doing?) |
| `q7_p95_ms_get_order` | 95th percentile response time in ms for successful (200) `GET /api/orders/{id}` requests, from the `rt=` field (±3 ms accepted) |
| `q8_root_cause_error_text` | The database error message in app.log that explains the outage |
| `q9_slowest_endpoint_avg` | Endpoint (same `{id}` format) with the highest average response time for 200 responses |
| `q10_partner_401_count` | How many partner order submissions were rejected with 401 that day |

### Task 8 – Triage the queue (10 pts)
Using the priority table above, give every ticket in `tickets/tickets.json` a priority in `work/triage.json` (`"P1"` to `"P4"`).
Bonus (not graded): write a short first reply for TKT-1003 and TKT-1005, as you would to the customer.

### Task 9 – Write a health check (5 pts)
Complete `work/healthcheck.sh` so that `bash work/healthcheck.sh <url>`:
- prints one status line with a timestamp, and
- exits `0` if the URL returns HTTP 200, and non-zero for any other code or if nothing is listening.

Bonus: schedule it every minute with `cron` and log the output.

### Task 10 – Document it (5 pts)
- **Runbook** for Task 5, in `work/runbooks/` (use `templates/runbook_template.md`). It must have Symptoms, Diagnosis, Resolution, Verification and Prevention sections, and at least 150 words.
- **Postmortem** for Friday's outage, in `work/postmortems/` (use `templates/postmortem_template.md`). It must have all sections and a timeline with at least 4 timestamps. Use the numbers from Task 7.

---

**Stuck?** Read `hints/HINTS.md`, which has three levels of hints per task. Only open `solutions/` after you've tried.

When you reach **80+**, read `CV_NOTES.md`.
