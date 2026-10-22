# Postmortem: Orders API outage, Friday 16 October 2026

**Date of incident:** 2026-10-16   **Severity:** P1   **Author:** Support Engineer   **Status:** Final

## Summary
Between 14:05 and 14:41 UTC the ShopFast Orders API failed for most requests because PostgreSQL refused new connections ("too many clients already"). The website, mobile app and partner integration were affected for 37 minutes. Service recovered after the API container was restarted.

## Impact
- Duration: 37 minutes (14:05-14:41 UTC).
- 1,350 requests returned 5xx errors across the day, almost all inside the outage window; during the window around 72% of requests failed.
- `/api/orders/{id}` was the most affected endpoint (699 failed requests), so customers could not open orders.
- Health checks failed, triggering alerts.

## Timeline
- 13:58 - App log shows report connections being cached for re-use (18 held).
- 14:05 - First "too many clients already" errors; 5xx rate exceeds 20%.
- 14:12 - Uptime monitoring alerts on-call.
- 14:30 - On-call confirms API errors, database itself healthy.
- 14:41 - API container restarted; connections released; error rate returns to normal.
- 14:45 - Monitoring green.

## Root Cause
The `daily_sales()` endpoint opened a new database connection for every report request and stored it in a module-level list (`_report_connections`) without ever closing it. Each gunicorn worker accumulated idle connections until PostgreSQL reached `max_connections` (20). After that, every endpoint, including `/health`, failed to connect. Evidence: app log errors `FATAL: sorry, too many clients already`, and `pg_stat_activity` showing many idle `shop_app` sessions.

## Resolution
Short term: restart of the API container released the leaked connections. Permanent fix: the report endpoint now uses `with get_conn() as conn:` so the connection is closed after each request, and the caching list was removed.

## Action Items
| Action | Owner | Due |
|---|---|---|
| Deploy connection-leak fix | Orders API team | 2026-10-20 |
| Alert when app connections > 70% of max_connections | Platform Support | 2026-10-23 |
| Add load test for reports endpoint to CI | QA | 2026-10-30 |
| Evaluate PgBouncer connection pooling | Platform | 2026-11-13 |

## Lessons Learned
- Went well: restart was a quick mitigation.
- Went badly: the same outage happened twice before without a root cause analysis.
- Lucky: it happened on a Friday afternoon, not during a sales campaign.
