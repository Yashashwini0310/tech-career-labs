# Lab 1 – What you can honestly say afterwards

Only claim what you actually did. Practice labs go under **Projects**, never under a job.

## CV project entry (once you score 80+)

**Production Support Simulation – ShopFast Orders Platform** | Docker, nginx, Flask, PostgreSQL, Bash, Linux
- Diagnosed and resolved 6 simulated production incidents across nginx, a Python API and PostgreSQL, including a 502 upstream misconfiguration, a NULL-handling bug, an expired partner API key, a missing index and a database connection leak.
- Analysed 41,000+ nginx and application log lines with grep, awk and Python to reconstruct a 37-minute outage, isolate the root cause ("too many clients") and identify a scraper responsible for 10% of traffic.
- Restored a dropped index that turned a sequential scan of 200,000 rows into an index scan, and removed duplicate payment records with a unique constraint to prevent recurrence.
- Wrote a runbook, a postmortem and a Bash health-check script, and triaged an 8-ticket queue against P1–P4 definitions.

## Interview stories (STAR) this lab gives you
- **"Tell me about a time you found a root cause others missed."** → Task 5/7: the outage "fixed by restart" was a connection leak. Evidence: pg_stat_activity, max_connections, app log.
- **"How do you troubleshoot a 502?"** → Task 1: proxy error log → upstream host/port → fix → verify with curl.
- **"How do you prioritise?"** → Task 8: impact × urgency, revenue and SLA, workaround available or not.
- **"A query is slow. What do you do?"** → Task 4: EXPLAIN ANALYZE, Seq Scan vs Index Scan, CREATE INDEX CONCURRENTLY in production.

## Keywords this covers (for job ads)
L2/L3 support, incident management, root cause analysis, log analysis, Linux, Bash, grep/awk, nginx, REST APIs, curl, PostgreSQL, SQL, EXPLAIN, indexing, Docker, runbooks, postmortems, SLA, ticket triage, change management.
