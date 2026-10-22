-- Lab 1 starting state: what "production" looks like on Monday morning.
-- (Reading this file spoils some of the tasks. Try the lab first!)

-- A migration last week rebuilt the orders table and someone forgot an index.
DROP INDEX IF EXISTS idx_orders_customer_id;

-- The payment webhook retried during a provider blip on 5 Oct 2026
-- and inserted some payments twice.
INSERT INTO payments (payment_id, order_id, provider, provider_txn_id, amount, paid_ts, status)
SELECT 900000 + ROW_NUMBER() OVER (ORDER BY payment_id),
       order_id, provider, provider_txn_id, amount, paid_ts + INTERVAL '3 seconds', status
FROM payments
WHERE paid_ts::date = DATE '2026-10-05' AND status = 'captured'
ORDER BY payment_id
LIMIT 41;

-- Application user (the API connects as this user)
CREATE ROLE shop_app LOGIN PASSWORD 'shop_app_pw';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO shop_app;

ANALYZE;
