# Runbook: Orders API fails with "too many clients already"

**Service:** ShopFast Orders API + PostgreSQL   **Owner:** Platform Support   **Last updated:** 2026-10-19

## Symptoms
- Most API endpoints return HTTP 500 (through nginx you may also see 502/504).
- `/health` fails, so uptime monitoring alerts.
- App log shows `psycopg.OperationalError: connection failed: FATAL:  sorry, too many clients already`.
- Often happens in the afternoon, after Finance has run several daily-sales reports.

## Diagnosis
1. Confirm the error in the app log:
   `grep -c "too many clients" runtime_logs/app/app.log`
2. Count open connections by user and state:
   `SELECT usename, state, COUNT(*) FROM pg_stat_activity GROUP BY 1,2 ORDER BY 3 DESC;`
   A large number of `idle` connections owned by `shop_app` points to a connection leak.
3. Compare with the limit: `SHOW max_connections;` (20 in this environment).
4. Find which code path opens connections without closing them. In `app.py`, `daily_sales()` appends each new connection to `_report_connections` and never closes it.

## Resolution
- **Immediate mitigation:** restart the API to release connections: `docker compose restart api`.
  If you can't restart, terminate idle app sessions:
  `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='shop_app' AND state='idle';`
- **Permanent fix:** open the report connection with `with get_conn() as conn:` so it is closed after every request, and remove the `_report_connections` list. Deploy and restart the API.

## Verification
- Call the report 40 times: `for i in $(seq 40); do curl -s -o /dev/null -w "%{http_code}\n" "localhost:8080/api/reports/daily-sales?date=2026-10-01"; done | sort | uniq -c` shows only 200s.
- `SELECT COUNT(*) FROM pg_stat_activity WHERE usename='shop_app';` stays low (under 5).
- `/health` returns 200.

## Prevention
- Alert when `shop_app` connections exceed 70% of `max_connections`.
- Add a load test for the reports endpoint to CI.
- Consider a connection pool (psycopg_pool or PgBouncer) with a hard cap per worker.
- Code review checklist item: every connection must be opened with a context manager.

## Escalation
If connections climb again after the fix, escalate to the Orders API development team with the output of the pg_stat_activity query and the last 200 lines of the app log.
