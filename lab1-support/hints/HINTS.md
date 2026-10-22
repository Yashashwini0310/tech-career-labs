# Lab 1 hints

Each task has three levels. Read one level at a time.

---

## Task 1 – 502 Bad Gateway
1. A 502 from a proxy means "I couldn't get a valid response from the server behind me". Check what nginx itself logged: `./lab.sh logs nginx` or `cat runtime_logs/nginx/error.log`.
2. Compare the address nginx forwards to (in `nginx/nginx.conf`) with the port the API actually listens on (see `app/Dockerfile` and `docker-compose.yml`).
3. Fix the `upstream` block, then `./lab.sh restart nginx`.

## Task 2 – 500 on some orders
1. `grep -A4 ERROR runtime_logs/app/app.log | tail -20` shows the traceback.
2. `SELECT order_id, discount_pct FROM orders WHERE order_id IN (1, 2);` What's different about order 2?
3. In Python, `Decimal * None` fails. Treat a missing discount as 0%.

## Task 3 – 401 for the partner
1. Compare the key the partner sends (`client/client.env`) with the key the API expects (`app/api.env`).
2. Read the comment above `API_KEY` in `app/api.env`. Someone rotated the key and didn't tell the partner.
3. Update the partner's configuration with the new key. In real life you'd send it to them through a secure channel, never in a ticket comment.

## Task 4 – Slow order history
1. `EXPLAIN ANALYZE SELECT order_id, order_ts, status, channel FROM orders WHERE customer_id = 42 ORDER BY order_ts DESC;`
2. "Seq Scan on orders" means PostgreSQL reads all 200,000 rows to find about 10. Check what indexes exist: `\d orders`
3. `CREATE INDEX ... ON orders (customer_id);` then run EXPLAIN ANALYZE again and compare.

## Task 5 – Afternoon outage
1. After the curl loop, the log says `too many clients already`. PostgreSQL has a connection limit: `SHOW max_connections;`
2. `SELECT usename, state, COUNT(*) FROM pg_stat_activity GROUP BY 1, 2;` Who is holding all those idle connections?
3. Look at `daily_sales()` in `app/app.py`. Every call opens a connection. Is it ever closed? Compare it with how the other endpoints open connections.

## Task 6 – Finance numbers
1. `SELECT provider_txn_id, COUNT(*) FROM payments GROUP BY 1 HAVING COUNT(*) > 1;`
2. The duplicates have the same `provider_txn_id` but a different `payment_id` and a timestamp 3 seconds later. Keep the original (the lower `payment_id`).
3. `DELETE ... USING ...` to remove the duplicates, then `ALTER TABLE payments ADD CONSTRAINT ... UNIQUE (provider_txn_id);`

## Task 7 – Log investigation
1. Useful building blocks: `wc -l`, `awk '{print $9}'` (status code), `awk '{print $1}'` (IP), `sort | uniq -c | sort -rn | head`.
2. Time per minute: `awk '{print substr($4, 14, 5)}'` gives HH:MM. For an error rate per minute, count the total and the 5xx per minute. Python with a dictionary is easier for this one.
3. For the p95: collect the `rt=` values for successful GET /api/orders/<number>, sort them, and take the value at position ceil(0.95 × n). Multiply by 1000 for ms. For the root cause, `grep -c` the different ERROR messages in app.log.

## Task 8 – Triage
1. Ask: how many users are affected? Is money blocked? Is there a workaround?
2. Two tickets are P1. Two are P4.
3. A partner with 700+ orders blocked and a contractual 4-hour SLA is "revenue fully blocked for a key partner".

## Task 9 – Health check
1. `curl -s -o /dev/null -w "%{http_code}" URL` prints just the status code.
2. Add `--max-time 5` so it doesn't hang. If nothing is listening, curl prints `000`.
3. Compare with `if [ "$code" = "200" ]; then ... exit 0; else ... exit 1; fi`.

## Task 10 – Documentation
1. Write it for a colleague woken up at 3am: exact commands, exact expected output.
2. Use the real numbers from Task 7 in the postmortem's Impact section.
3. Action items need an owner and a due date, or they never happen.
